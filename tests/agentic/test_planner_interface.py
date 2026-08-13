from __future__ import annotations

import pytest

from kaj.ast import PlanRegion, TaskDeclaration
from kaj.formatting import format_program
from kaj.pipeline import compile_source, parse_source
from kaj.runtime import (
    InMemoryTaskStore,
    PlannerAdapter,
    PlannerAdapterResult,
    PlannerProposal,
    TaskRuntime,
    TaskStartError,
    TaskState,
)
from kaj.serialization import ast_from_json, ast_to_json

SOURCE = """task Planned() -> Int {
    goal "make a result"
    plan {
    }
    return 42
}
"""


def compiled(source: str = SOURCE):  # type: ignore[no-untyped-def]
    result = compile_source(source)
    assert result.diagnostics == ()
    assert result.resolution is not None and result.types is not None
    return result


def proposal(source: str) -> PlannerProposal:
    parsed = parse_source(f"task P() -> None {{ plan {{ {source} }} return none }}")
    assert parsed.diagnostics == ()
    task = parsed.program.statements[0]
    assert isinstance(task, TaskDeclaration)
    region = next(item for item in task.body.statements if isinstance(item, PlanRegion))
    return PlannerProposal(region.body)


class PendingPlanner(PlannerAdapter):
    def request_plan(self, request):  # type: ignore[no-untyped-def]
        return PlannerAdapterResult.pending_result()


class ImmediatePlanner(PlannerAdapter):
    def request_plan(self, request):  # type: ignore[no-untyped-def]
        return PlannerAdapterResult.immediate(proposal("step work { let value = 1 }"))


def runtime_for(adapter=None, store=None) -> TaskRuntime:  # type: ignore[no-untyped-def]
    result = compiled()
    return TaskRuntime(
        result.program, result.resolution, result.types, planner_adapter=adapter, store=store
    )


def test_plan_syntax_format_ast_and_duplicate_placement() -> None:
    parsed = parse_source(SOURCE)
    assert parsed.diagnostics == ()
    assert format_program(parsed.program) == SOURCE
    encoded = ast_to_json(parsed.program)
    assert ast_from_json(encoded) == parsed.program
    assert "TASK_PLAN_OUTSIDE_TASK" in [item.code for item in parse_source("plan {}").diagnostics]
    duplicate = compile_source("task P() -> None { plan {} plan {} return none }")
    assert "TASK_DUPLICATE_PLAN_REGION" in [item.code for item in duplicate.diagnostics]


def test_async_request_and_valid_proposal_execution() -> None:
    runtime = runtime_for(PendingPlanner())
    instance = runtime.start_task("Planned")
    assert instance.state is TaskState.WAITING_FOR_PLANNER
    request = runtime.get_planner_request(instance.id)
    assert request is not None
    assert request.task_id == str(instance.id)
    assert request.goal == "make a result"
    runtime.complete_planner_request(
        instance.id, request.attempt_id, proposal("step work { let value = 1 }")
    )
    assert instance.state is TaskState.COMPLETED and instance.result == 42
    assert instance.accepted_plan_fingerprint


def test_invalid_proposal_rejected_and_new_attempt_created() -> None:
    runtime = runtime_for(PendingPlanner())
    instance = runtime.start_task("Planned")
    first = runtime.get_planner_request(instance.id)
    assert first is not None
    runtime.complete_planner_request(instance.id, first.attempt_id, proposal("unknown()"))
    second = runtime.get_planner_request(instance.id)
    assert instance.state is TaskState.WAITING_FOR_PLANNER
    assert second is not None and second.attempt_id != first.attempt_id
    with pytest.raises(TaskStartError) as stale:
        runtime.complete_planner_request(instance.id, first.attempt_id, proposal(""))
    assert stale.value.code == "PLANNER_ATTEMPT_STALE"


def test_duplicate_and_wrong_task_responses() -> None:
    runtime = runtime_for(PendingPlanner())
    one = runtime.start_task("Planned")
    two = runtime.start_task("Planned")
    request = runtime.get_planner_request(one.id)
    assert request is not None
    with pytest.raises(TaskStartError) as wrong:
        runtime.complete_planner_request(two.id, request.attempt_id, proposal(""))
    assert wrong.value.code == "PLANNER_RESPONSE_TASK_MISMATCH"
    runtime.complete_planner_request(one.id, request.attempt_id, proposal(""))
    with pytest.raises(TaskStartError) as duplicate:
        runtime.complete_planner_request(one.id, request.attempt_id, proposal(""))
    assert duplicate.value.code == "PLANNER_RESPONSE_DUPLICATE"


def test_synchronous_adapter_and_persistence_restore() -> None:
    immediate = runtime_for(ImmediatePlanner()).start_task("Planned")
    assert immediate.state is TaskState.COMPLETED

    store = InMemoryTaskStore()
    first_runtime = runtime_for(PendingPlanner(), store)
    waiting = first_runtime.start_task("Planned")
    request = first_runtime.get_planner_request(waiting.id)
    assert request is not None
    second_runtime = runtime_for(PendingPlanner(), store)
    restored = second_runtime.restore_task(waiting.id)
    restored_request = second_runtime.get_planner_request(restored.id)
    assert restored.state is TaskState.WAITING_FOR_PLANNER
    assert restored_request is not None and restored_request.attempt_id == request.attempt_id
    second_runtime.complete_planner_request(restored.id, request.attempt_id, proposal(""))
    saved = store.load(str(restored.id))
    assert saved.accepted_plan_json is not None
    assert saved.accepted_plan_fingerprint
