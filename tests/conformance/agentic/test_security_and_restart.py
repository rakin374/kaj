from __future__ import annotations

import pytest

from kaj.ast import PlanRegion, TaskDeclaration
from kaj.pipeline import compile_source, parse_source
from kaj.runtime import (
    CapabilityAdapter,
    CapabilityAdapterResult,
    CapabilityRegistry,
    InMemoryTaskStore,
    PlannerAdapter,
    PlannerAdapterResult,
    PlannerProposal,
    TaskRuntime,
    TaskStartError,
    TaskState,
)


def runtime_for(source: str, **kwargs):  # type: ignore[no-untyped-def]
    result = compile_source(source)
    assert result.diagnostics == ()
    assert result.resolution is not None and result.types is not None
    return TaskRuntime(result.program, result.resolution, result.types, **kwargs)


def proposal(source: str) -> PlannerProposal:
    parsed = parse_source(f"task P() -> None {{ plan {{ {source} }} return none }}")
    assert parsed.diagnostics == ()
    task = parsed.program.statements[0]
    assert isinstance(task, TaskDeclaration)
    region = next(item for item in task.body.statements if isinstance(item, PlanRegion))
    return PlannerProposal(region.body)


class PendingPlanner(PlannerAdapter):
    def request_plan(self, request):  # type: ignore[no-untyped-def]
        del request
        return PlannerAdapterResult.pending_result()


class PendingCounter(CapabilityAdapter):
    @property
    def capability_type(self) -> str:
        return "Counter"

    @property
    def host_binding_id(self) -> str:
        return "counter-restart"

    def invoke(self, request_id, operation, arguments):  # type: ignore[no-untyped-def]
        del request_id, operation, arguments
        return CapabilityAdapterResult.pending()


class NativeLeak(CapabilityAdapter):
    @property
    def capability_type(self) -> str:
        return "Counter"

    @property
    def host_binding_id(self) -> str:
        return "native-leak"

    def invoke(self, request_id, operation, arguments):  # type: ignore[no-untyped-def]
        del request_id, operation, arguments
        return CapabilityAdapterResult.immediate(object())  # type: ignore[arg-type]


def test_restart_matrix_preserves_all_observable_lifecycle_states() -> None:
    ready_store = InMemoryTaskStore()
    ready_runtime = runtime_for("task T() -> Int { return 1 }", store=ready_store)
    ready = ready_runtime.create_task("T")
    ready_runtime.ready_task(ready)
    assert runtime_for("task T() -> Int { return 1 }", store=ready_store).restore_task(
        ready.id
    ).state is TaskState.READY

    human_store = InMemoryTaskStore()
    human_source = 'task T() -> Bool { return confirm("ok?") }'
    human = runtime_for(human_source, store=human_store).start_task("T")
    assert runtime_for(human_source, store=human_store).restore_task(
        human.id
    ).state is TaskState.WAITING_FOR_HUMAN

    planner_store = InMemoryTaskStore()
    planner_source = 'task T() -> Int { goal "x" plan {} return 1 }'
    planner = runtime_for(
        planner_source, store=planner_store, planner_adapter=PendingPlanner()
    ).start_task("T")
    assert runtime_for(
        planner_source, store=planner_store, planner_adapter=PendingPlanner()
    ).restore_task(planner.id).state is TaskState.WAITING_FOR_PLANNER

    completed_store = InMemoryTaskStore()
    completed = runtime_for("task T() -> Int { return 1 }", store=completed_store).start_task(
        "T"
    )
    assert runtime_for("task T() -> Int { return 1 }", store=completed_store).restore_task(
        completed.id
    ).state is TaskState.COMPLETED

    failed_store = InMemoryTaskStore()
    failed_source = "task T() -> Decimal { return 1 / 0 }"
    failed = runtime_for(failed_source, store=failed_store).start_task("T")
    assert runtime_for(failed_source, store=failed_store).restore_task(
        failed.id
    ).state is TaskState.FAILED

    cancelled_store = InMemoryTaskStore()
    cancelled_runtime = runtime_for(human_source, store=cancelled_store)
    cancelled = cancelled_runtime.start_task("T")
    cancelled_runtime.cancel_task(cancelled)
    assert runtime_for(human_source, store=cancelled_store).restore_task(
        cancelled.id
    ).state is TaskState.CANCELLED


def test_capability_restart_is_indeterminate_and_task_scoped() -> None:
    source = """capability Counter { fn read() -> Int }
task T() -> Int { use Counter as counter return counter.read() }
"""
    store = InMemoryTaskStore()
    registry = CapabilityRegistry()
    adapter = PendingCounter()
    first = runtime_for(source, store=store, capability_registry=registry)
    one = first.create_task("T")
    two = first.create_task("T")
    first.bind_capability(one, "counter", adapter)
    assert registry.resolve(str(one.id), "counter") is not None
    assert registry.resolve(str(two.id), "counter") is None
    first.run_task(one)
    request = one.pending_capability_request
    assert request is not None

    restored = runtime_for(
        source, store=store, capability_registry=registry
    ).restore_task(one.id)
    assert restored.pending_capability_request is not None
    with pytest.raises(TaskStartError) as replay:
        runtime_for(source, store=store, capability_registry=registry).complete_capability_request(
            restored.id, request.id, 1
        )
    assert replay.value.code in {"CAPABILITY_REQUEST_NOT_FOUND", "CAPABILITY_REQUEST_INDETERMINATE"}


def test_native_host_value_is_contained_as_stable_runtime_failure() -> None:
    source = """capability Counter { fn read() -> Int }
task T() -> Int { use Counter as counter return counter.read() }
"""
    runtime = runtime_for(source)
    task = runtime.create_task("T")
    runtime.bind_capability(task, "counter", NativeLeak())
    runtime.run_task(task)
    assert task.state is TaskState.FAILED
    assert task.failure is not None
    assert task.failure.code == "CAPABILITY_RETURN_MISMATCH"
    assert "object at" not in task.failure.message


def test_stale_human_and_planner_responses_do_not_mutate_other_tasks() -> None:
    human_source = 'task T() -> Bool { return confirm("ok?") }'
    runtime = runtime_for(human_source)
    one = runtime.start_task("T")
    two = runtime.start_task("T")
    assert one.pending_interaction is not None and two.pending_interaction is not None
    with pytest.raises(TaskStartError) as stale:
        runtime.respond_to_interaction(one.id, two.pending_interaction.id, True)
    assert stale.value.code == "TASK_INTERACTION_STALE"
    assert one.state is TaskState.WAITING_FOR_HUMAN
    assert two.state is TaskState.WAITING_FOR_HUMAN

    planner_source = 'task T() -> Int { goal "x" plan {} return 1 }'
    planner_runtime = runtime_for(planner_source, planner_adapter=PendingPlanner())
    first = planner_runtime.start_task("T")
    second = planner_runtime.start_task("T")
    first_request = planner_runtime.get_planner_request(first.id)
    assert first_request is not None
    with pytest.raises(TaskStartError) as wrong_task:
        planner_runtime.complete_planner_request(
            second.id, first_request.attempt_id, proposal("")
        )
    assert wrong_task.value.code == "PLANNER_RESPONSE_TASK_MISMATCH"
    assert first.state is TaskState.WAITING_FOR_PLANNER
    assert second.state is TaskState.WAITING_FOR_PLANNER
