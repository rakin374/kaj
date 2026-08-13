from __future__ import annotations

import pytest

from kaj.capabilities import CapabilityIdentity
from kaj.formatting import format_program
from kaj.pipeline import compile_source, parse_source, parse_source
from kaj.runtime import (
    CapabilityAdapter,
    CapabilityAdapterResult,
    CapabilityRequestId,
    InMemoryTaskStore,
    TaskRuntime,
    TaskStartError,
    TaskState,
)
from kaj.runtime.values import RuntimeValue
from kaj.serialization import ast_from_json, ast_to_json


def compiled(source: str):  # type: ignore[no-untyped-def]
    result = compile_source(source)
    assert result.diagnostics == ()
    assert result.resolution is not None and result.types is not None
    return result


def runtime_for(source: str, store=None) -> TaskRuntime:  # type: ignore[no-untyped-def]
    result = compiled(source)
    return TaskRuntime(result.program, result.resolution, result.types, store=store)


def test_start_await_format_ast_and_completed_child() -> None:
    source = """task Parent() -> Int {
    let child: TaskHandle<Int> = start Child(21)
    return await child
}

task Child(value: Int) -> Int {
    return value * 2
}
"""
    parsed = parse_source(source)
    assert parsed.diagnostics == ()
    assert format_program(parsed.program) == source
    encoded = ast_to_json(parsed.program)
    assert ast_from_json(encoded) == parsed.program
    runtime = runtime_for(source)
    parent = runtime.start_task("Parent")
    assert parent.result == 42
    assert len(parent.child_task_ids) == 1
    child = runtime.task(parent.child_task_ids[0])
    assert child is not None and child.parent_task_id == parent.id
    assert child.id != parent.id


@pytest.mark.parametrize(
    ("source", "code"),
    [
        (
            "fn f() -> Int { return 1 } task P() -> None { let h = start f() return none }",
            "TASK_START_TARGET_NOT_TASK",
        ),
        ("task P() -> None { let h = start Missing() return none }", "TASK_START_UNKNOWN_TASK"),
        (
            'task C(v: Int) -> Int { return v } task P() -> None { let h = start C("x") return none }',
            "TASK_START_ARGUMENT_MISMATCH",
        ),
        ("task P() -> Int { return await 1 }", "TASK_AWAIT_EXPECTED_HANDLE"),
        (
            "task C() -> Int { return 1 } fn f() -> TaskHandle<Int> { return start C() }",
            "TASK_COMPOSITION_NOT_ALLOWED_IN_FUNCTION",
        ),
        (
            "task C() -> Int { return 1 } task P() -> None { require { await start C() == 1 } return none }",
            "TASK_COMPOSITION_NOT_ALLOWED_IN_CONTRACT",
        ),
    ],
)
def test_composition_diagnostics(source: str, code: str) -> None:
    assert code in [item.code for item in compile_source(source).diagnostics]


def test_parent_waits_for_human_child_then_wakes() -> None:
    source = """task Parent() -> Int { let child = start Child() return await child }
task Child() -> Int { return ask<Int>("value?") }
"""
    runtime = runtime_for(source)
    parent = runtime.start_task("Parent")
    assert parent.state is TaskState.WAITING_FOR_TASK
    assert parent.waiting_on_task_id is not None
    child = runtime.task(parent.waiting_on_task_id)
    assert child is not None and child.state is TaskState.WAITING_FOR_HUMAN
    interaction = child.pending_interaction
    assert interaction is not None
    runtime.respond_to_interaction(child.id, interaction.id, 42)
    assert child.state.value == TaskState.COMPLETED.value
    assert parent.state.value == TaskState.COMPLETED.value and parent.result == 42


def test_child_failure_and_cancellation_fail_awaiting_parent() -> None:
    failed_source = """task P() -> Decimal { let h = start C() return await h }
task C() -> Decimal { return 1 / 0 }
"""
    failed = runtime_for(failed_source).start_task("P")
    assert failed.state is TaskState.FAILED
    assert failed.failure is not None and failed.failure.code == "TASK_CHILD_FAILED"

    cancelled_source = """task P() -> Int { let h = start C() return await h }
task C() -> Int { return ask<Int>("x") }
"""
    runtime = runtime_for(cancelled_source)
    parent = runtime.start_task("P")
    assert parent.waiting_on_task_id is not None
    child = runtime.task(parent.waiting_on_task_id)
    assert child is not None
    runtime.cancel_task(child)
    assert parent.state is TaskState.FAILED
    assert parent.failure is not None and parent.failure.code == "TASK_CHILD_CANCELLED"


def test_parent_cancellation_propagates_but_completion_does_not() -> None:
    source = """task P() -> None { let h = start C() return none }
task C() -> Int { return ask<Int>("x") }
"""
    runtime = runtime_for(source)
    completed_parent = runtime.start_task("P")
    live_child = runtime.task(completed_parent.child_task_ids[0])
    assert completed_parent.state is TaskState.COMPLETED
    assert live_child is not None and live_child.state is TaskState.WAITING_FOR_HUMAN

    waiting_source = """task P() -> Int { let h = start C() return await h }
task C() -> Int { return ask<Int>("x") }
"""
    runtime2 = runtime_for(waiting_source)
    parent = runtime2.start_task("P")
    assert parent.waiting_on_task_id is not None
    child = runtime2.task(parent.waiting_on_task_id)
    runtime2.cancel_task(parent)
    assert child is not None and child.state is TaskState.CANCELLED


def test_waiting_relationship_and_handle_persist_restore() -> None:
    source = """task P() -> Int { let h = start C() return await h }
task C() -> Int { return ask<Int>("x") }
"""
    store = InMemoryTaskStore()
    first = runtime_for(source, store)
    parent = first.start_task("P")
    child_id = parent.waiting_on_task_id
    assert child_id is not None
    snapshot = store.load(str(parent.id))
    assert snapshot.waiting_on_task_id == str(child_id)
    assert snapshot.child_task_ids == (str(child_id),)

    second = runtime_for(source, store)
    restored_parent = second.restore_task(parent.id)
    assert restored_parent.state is TaskState.WAITING_FOR_TASK
    assert second.resume_task(restored_parent).state is TaskState.WAITING_FOR_TASK
    restored_child = second.task(child_id)
    assert restored_child is not None
    interaction = restored_child.pending_interaction
    assert interaction is not None
    second.respond_to_interaction(restored_child.id, interaction.id, 42)
    assert restored_parent.result == 42


def test_missing_child_restore_rejected() -> None:
    source = """task P() -> Int { let h = start C() return await h }
task C() -> Int { return ask<Int>("x") }
"""
    store = InMemoryTaskStore()
    first = runtime_for(source, store)
    parent = first.start_task("P")
    store.delete(str(parent.waiting_on_task_id))
    second = runtime_for(source, store)
    restored = second.restore_task(parent.id)
    with pytest.raises(TaskStartError) as failure:
        second.resume_task(restored)
    assert failure.value.code == "TASK_CHILD_NOT_FOUND"


class ChildAdapter(CapabilityAdapter):
    @property
    def capability_identity(self) -> CapabilityIdentity:
        return CapabilityIdentity("<entry>", "Counter", 1)

    @property
    def capability_type(self) -> str:
        return "Counter"

    @property
    def host_binding_id(self) -> str:
        return "child-counter"

    @property
    def supported_operations(self) -> frozenset[str]:
        return frozenset({"read"})

    def invoke(
        self,
        request_id: CapabilityRequestId,
        operation: str,
        arguments: tuple[RuntimeValue, ...],
    ) -> CapabilityAdapterResult:
        del request_id, operation, arguments
        return CapabilityAdapterResult.immediate(42)


def test_child_capabilities_are_bound_independently() -> None:
    source = """capability Counter { fn read() -> Int }
task P() -> Int { let h = start C() return await h }
task C() -> Int { use Counter as counter return counter.read() }
"""
    result = compiled(source)
    without_binding = TaskRuntime(result.program, result.resolution, result.types)
    parent = without_binding.start_task("P")
    assert parent.failure is not None and parent.failure.code == "TASK_CHILD_FAILED"

    def bind_child(runtime: TaskRuntime, child) -> None:  # type: ignore[no-untyped-def]
        runtime.bind_capability(child, "counter", ChildAdapter())

    with_binding = TaskRuntime(
        result.program,
        result.resolution,
        result.types,
        child_capability_binder=bind_child,
    )
    complete = with_binding.start_task("P")
    assert complete.result == 42
