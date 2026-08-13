from __future__ import annotations

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


class PendingCapability(CapabilityAdapter):
    @property
    def capability_type(self) -> str:
        return "Counter"

    @property
    def host_binding_id(self) -> str:
        return "counter-conformance"

    def invoke(self, request_id, operation, arguments):  # type: ignore[no-untyped-def]
        del request_id, operation, arguments
        return CapabilityAdapterResult.pending()


class OnePlan(PlannerAdapter):
    def __init__(self, value: PlannerProposal) -> None:
        self.value = value

    def request_plan(self, request):  # type: ignore[no-untyped-def]
        del request
        return PlannerAdapterResult.immediate(self.value)


def test_contract_human_interaction_persists_and_resumes_exact_continuation() -> None:
    source = """task Review() -> Bool {
    goal "approve"
    invariant { true }
    success(result: Bool) { result }
    let approved = confirm("Approve?")
    return approved
}
"""
    store = InMemoryTaskStore()
    first = runtime_for(source, store=store)
    waiting = first.start_task("Review")
    interaction = waiting.pending_interaction
    assert interaction is not None and waiting.state is TaskState.WAITING_FOR_HUMAN

    second = runtime_for(source, store=store)
    restored = second.restore_task(waiting.id)
    second.respond_to_interaction(restored.id, interaction.id, True)
    assert restored.state is TaskState.COMPLETED and restored.result is True


def test_capability_wait_persistence_result_and_invariant() -> None:
    source = """capability Counter { fn read() -> Int }
task Read() -> Int {
    use Counter as counter
    invariant { true }
    let value = counter.read()
    return value
}
"""
    store = InMemoryTaskStore()
    registry = CapabilityRegistry()
    adapter = PendingCapability()
    first = runtime_for(source, store=store, capability_registry=registry)
    task = first.create_task("Read")
    first.bind_capability(task, "counter", adapter)
    first.run_task(task)
    request = task.pending_capability_request
    assert request is not None and task.state is TaskState.WAITING_FOR_CAPABILITY

    second = runtime_for(source, store=store, capability_registry=registry)
    restored = second.restore_task(task.id)
    second.reconcile_capability_request(restored.id, request.id, 7)
    assert restored.state is TaskState.COMPLETED and restored.result == 7


def test_child_human_interaction_and_relationship_survive_restart() -> None:
    source = """task Child() -> Int { return ask<Int>("Value?") }
task Parent() -> Int { let child = start Child() return await child }
"""
    store = InMemoryTaskStore()
    first = runtime_for(source, store=store)
    parent = first.start_task("Parent")
    child_id = parent.waiting_on_task_id
    assert child_id is not None

    second = runtime_for(source, store=store)
    restored_parent = second.restore_task(parent.id)
    second.resume_task(restored_parent)
    child = second.task(child_id)
    assert child is not None and child.pending_interaction is not None
    second.respond_to_interaction(child.id, child.pending_interaction.id, 42)
    assert restored_parent.state is TaskState.COMPLETED
    assert restored_parent.result == 42


def test_planner_can_compose_child_but_cannot_bypass_runtime_execution() -> None:
    source = """task Child() -> Int { return 21 }
task Parent() -> Int { goal "compose" plan {} return 42 }
"""
    planner = OnePlan(
        proposal("step compose { let child = start Child() let value = await child }")
    )
    runtime = runtime_for(source, planner_adapter=planner)
    parent = runtime.start_task("Parent")
    assert parent.state is TaskState.COMPLETED and parent.result == 42
    assert len(parent.child_task_ids) == 1
    child = runtime.task(parent.child_task_ids[0])
    assert child is not None and child.result == 21
