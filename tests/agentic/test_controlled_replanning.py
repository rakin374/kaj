from __future__ import annotations

import pytest

from kaj.ast import Block, PlanRegion, TaskDeclaration
from kaj.pipeline import compile_source, parse_source
from kaj.runtime import (
    InMemoryTaskStore,
    PlannerAdapter,
    PlannerAdapterResult,
    PlannerProposal,
    PlanPatch,
    TaskPersistenceError,
    TaskRuntime,
    TaskStartError,
    TaskState,
)
from kaj.runtime.persistence import TaskSnapshot, TaskStore

SOURCE = """task Planned() -> Int {
    goal "finish safely"
    plan {
    }
    return 42
}
"""


def compiled():  # type: ignore[no-untyped-def]
    result = compile_source(SOURCE)
    assert result.diagnostics == ()
    assert result.resolution is not None and result.types is not None
    return result


def plan_block(source: str) -> Block:
    parsed = parse_source(f"task P() -> None {{ plan {{ {source} }} return none }}")
    assert parsed.diagnostics == ()
    task = parsed.program.statements[0]
    assert isinstance(task, TaskDeclaration)
    region = next(item for item in task.body.statements if isinstance(item, PlanRegion))
    return region.body


class InitialPlanner(PlannerAdapter):
    def request_plan(self, request):  # type: ignore[no-untyped-def]
        return PlannerAdapterResult.immediate(
            PlannerProposal(
                plan_block('step first { print("first") } step old { print("old") }')
            )
        )


class PauseAfterFirst:
    def __init__(self) -> None:
        self.runtime: TaskRuntime | None = None
        self.instance = None
        self.lines: list[str] = []

    def write_line(self, text: str) -> None:
        self.lines.append(text)
        if text == "first":
            assert self.runtime is not None and self.instance is not None
            self.runtime.request_pause(self.instance)


def paused_runtime(store: TaskStore | None = None) -> tuple[TaskRuntime, object, PauseAfterFirst]:
    result = compiled()
    output = PauseAfterFirst()
    runtime = TaskRuntime(
        result.program,
        result.resolution,
        result.types,
        output=output,
        planner_adapter=InitialPlanner(),
        store=store,
    )
    output.runtime = runtime
    instance = runtime.create_task("Planned")
    output.instance = instance
    runtime.run_task(instance)
    assert instance.state is TaskState.PAUSED
    return runtime, instance, output


def patch_for(instance, source: str) -> PlanPatch:  # type: ignore[no-untyped-def]
    assert instance.accepted_plan_fingerprint is not None
    return PlanPatch(
        instance.plan_revision,
        instance.accepted_plan_fingerprint,
        plan_block(source),
    )


def test_accepted_replan_replaces_only_pending_suffix() -> None:
    runtime, instance, output = paused_runtime()
    original_fingerprint = instance.accepted_plan_fingerprint
    assert instance.plan_revision == 1

    request = runtime.request_replan(instance.id, "old strategy is obsolete")
    assert request.purpose == "replan"
    assert request.current_plan_revision == 1
    assert request.completed_steps == ("first",)
    assert request.pending_steps == ("old",)
    runtime.complete_replan_request(
        instance.id, request.attempt_id, patch_for(instance, 'step new { print("new") }')
    )

    assert instance.state is TaskState.COMPLETED
    assert instance.plan_revision == 2
    assert instance.accepted_plan_fingerprint != original_fingerprint
    assert output.lines == ["first", "new"]
    assert [(step.definition.name, step.state.value) for step in instance.step_executions] == [
        ("first", "completed"),
        ("new", "completed"),
    ]


def test_invalid_patch_is_atomic_and_retries_without_increment() -> None:
    runtime, instance, _ = paused_runtime()
    old_plan = instance.accepted_plan
    old_fingerprint = instance.accepted_plan_fingerprint
    request = runtime.request_replan(instance.id, "try invalid future")
    runtime.complete_replan_request(
        instance.id, request.attempt_id, patch_for(instance, "step bad { unknown() }")
    )
    retry = runtime.get_planner_request(instance.id)
    assert instance.state is TaskState.WAITING_FOR_PLANNER
    assert instance.plan_revision == 1
    assert instance.accepted_plan is old_plan
    assert instance.accepted_plan_fingerprint == old_fingerprint
    assert retry is not None and retry.attempt_id != request.attempt_id
    assert instance.planning_attempts[-2].status == "rejected"


def test_stale_revision_fingerprint_attempt_and_duplicate_are_rejected() -> None:
    runtime, instance, _ = paused_runtime()
    request = runtime.request_replan(instance.id, "replace")
    good = patch_for(instance, "step new { let x = 1 }")
    with pytest.raises(TaskStartError) as revision:
        runtime.complete_replan_request(
            instance.id,
            request.attempt_id,
            PlanPatch(0, good.base_plan_fingerprint, good.replacement_pending_plan),
        )
    assert revision.value.code == "PLANNER_PLAN_REVISION_STALE"
    with pytest.raises(TaskStartError) as fingerprint:
        runtime.complete_replan_request(
            instance.id,
            request.attempt_id,
            PlanPatch(1, "wrong", good.replacement_pending_plan),
        )
    assert fingerprint.value.code == "PLANNER_PLAN_FINGERPRINT_MISMATCH"
    with pytest.raises(TaskStartError) as attempt:
        runtime.complete_replan_request(instance.id, "stale", good)
    assert attempt.value.code == "PLANNER_ATTEMPT_STALE"
    runtime.complete_replan_request(instance.id, request.attempt_id, good)
    with pytest.raises(TaskStartError) as duplicate:
        runtime.complete_replan_request(instance.id, request.attempt_id, good)
    assert duplicate.value.code == "PLANNER_RESPONSE_DUPLICATE"


def test_replan_requires_safe_non_waiting_boundary() -> None:
    result = compiled()
    runtime = TaskRuntime(
        result.program, result.resolution, result.types, planner_adapter=InitialPlanner()
    )
    created = runtime.create_task("Planned")
    with pytest.raises(TaskStartError) as no_plan:
        runtime.request_replan(created.id, "too early")
    assert no_plan.value.code == "PLANNER_REPLAN_NOT_ALLOWED"

    runtime, paused, _ = paused_runtime()
    runtime.request_replan(paused.id, "already waiting")
    with pytest.raises(TaskStartError) as waiting:
        runtime.request_replan(paused.id, "not a boundary")
    assert waiting.value.code == "PLANNER_REPLAN_UNSAFE_BOUNDARY"


def test_replan_state_and_accepted_revision_restore_exactly() -> None:
    store = InMemoryTaskStore()
    runtime, instance, _ = paused_runtime(store)
    request = runtime.request_replan(instance.id, "persist this request")

    result = compiled()
    restored_runtime = TaskRuntime(
        result.program,
        result.resolution,
        result.types,
        planner_adapter=InitialPlanner(),
        store=store,
    )
    restored = restored_runtime.restore_task(instance.id)
    restored_request = restored_runtime.get_planner_request(restored.id)
    assert restored.state is TaskState.WAITING_FOR_PLANNER
    assert restored.plan_revision == 1
    assert restored_request is not None
    assert restored_request.attempt_id == request.attempt_id
    assert restored_request.replan_reason == "persist this request"

    restored_runtime.complete_replan_request(
        restored.id,
        request.attempt_id,
        patch_for(restored, "step restored { let x = 1 }"),
    )
    again = TaskRuntime(
        result.program,
        result.resolution,
        result.types,
        planner_adapter=InitialPlanner(),
        store=store,
    ).restore_task(restored.id)
    assert again.plan_revision == 2
    assert again.accepted_plan_fingerprint == restored.accepted_plan_fingerprint


class RejectRevisionTwoStore(InMemoryTaskStore):
    def save(self, snapshot: TaskSnapshot) -> None:
        if snapshot.plan_revision == 2:
            raise TaskPersistenceError("TASK_PERSISTENCE_WRITE_FAILED", "injected failure")
        super().save(snapshot)


def test_persistence_failure_does_not_expose_new_revision() -> None:
    runtime, instance, _ = paused_runtime(RejectRevisionTwoStore())
    old_plan = instance.accepted_plan
    old_fingerprint = instance.accepted_plan_fingerprint
    request = runtime.request_replan(instance.id, "will fail to commit")
    with pytest.raises(TaskPersistenceError):
        runtime.complete_replan_request(
            instance.id, request.attempt_id, patch_for(instance, "step new { let x = 1 }")
        )
    assert instance.plan_revision == 1
    assert instance.accepted_plan is old_plan
    assert instance.accepted_plan_fingerprint == old_fingerprint
    assert instance.state is TaskState.WAITING_FOR_PLANNER
    assert instance.planning_attempt is not None
