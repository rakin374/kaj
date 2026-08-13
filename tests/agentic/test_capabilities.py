from __future__ import annotations

import json

import pytest

from kaj.capabilities import CapabilityIdentity
from kaj.formatting import format_program
from kaj.pipeline import compile_source, parse_source
from kaj.runtime import (
    CapabilityAdapter,
    CapabilityAdapterResult,
    CapabilityRegistry,
    CapabilityRequestId,
    CapabilityRequestStatus,
    InMemoryTaskStore,
    StepState,
    TaskPersistenceError,
    TaskRuntime,
    TaskStartError,
    TaskState,
)
from kaj.runtime.values import RuntimeValue
from kaj.serialization import ast_from_json, ast_to_json

SOURCE = """capability Counter {
    fn read() -> Int
    fn add(amount: Int) -> Int
}

task Count() -> Int {
    use Counter as counter
    step update {
        let value = counter.add(41)
    }
    return counter.read()
}
"""


def compiled(source: str = SOURCE):  # type: ignore[no-untyped-def]
    result = compile_source(source)
    assert result.diagnostics == ()
    assert result.resolution is not None
    assert result.types is not None
    return result


LOCAL_COUNTER_IDENTITY = CapabilityIdentity("<entry>", "Counter", 1)


class MockCounter(CapabilityAdapter):
    def __init__(self, binding_id: str = "counter-1", *, asynchronous: bool = False) -> None:
        self._binding_id = binding_id
        self.asynchronous = asynchronous
        self.value = 0
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    @property
    def capability_identity(self) -> CapabilityIdentity:
        return LOCAL_COUNTER_IDENTITY

    @property
    def capability_type(self) -> str:
        return "Counter"

    @property
    def host_binding_id(self) -> str:
        return self._binding_id

    @property
    def supported_operations(self) -> frozenset[str]:
        return frozenset({"read", "add"})

    def invoke(
        self,
        request_id: CapabilityRequestId,
        operation: str,
        arguments: tuple[RuntimeValue, ...],
    ) -> CapabilityAdapterResult:
        self.calls.append((operation, arguments))
        if self.asynchronous:
            return CapabilityAdapterResult.pending()
        if operation == "add":
            amount = arguments[0]
            assert type(amount) is int
            self.value += amount
            return CapabilityAdapterResult.immediate(self.value)
        return CapabilityAdapterResult.immediate(self.value)


def runtime_for(  # type: ignore[no-untyped-def]
    source: str = SOURCE, *, store=None, registry=None
) -> TaskRuntime:
    result = compiled(source)
    return TaskRuntime(
        result.program,
        result.resolution,
        result.types,
        store=store,
        capability_registry=registry,
    )


def test_capability_syntax_format_ast_json_and_schema() -> None:
    parsed = parse_source(SOURCE)
    assert parsed.diagnostics == ()
    assert format_program(parsed.program) == SOURCE
    encoded = ast_to_json(parsed.program)
    document = json.loads(encoded)
    assert document["program"]["statements"][0]["kind"] == "capability_declaration"
    use = document["program"]["statements"][1]["body"]["statements"][0]
    assert use["kind"] == "use_capability_declaration"
    assert ast_from_json(encoded) == parsed.program


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ("fn Bad() -> None { use Counter as c return none }", "CAPABILITY_USE_OUTSIDE_TASK"),
        (
            "task Bad() -> None { step x { use Counter as c } return none }",
            "CAPABILITY_USE_OUTSIDE_TASK",
        ),
        (
            "capability C { fn x() -> Int { return 1 } }",
            "CAPABILITY_OPERATION_BODY_NOT_ALLOWED",
        ),
        (
            "capability C { fn x() -> Int fn x() -> Int }",
            "CAPABILITY_DUPLICATE_OPERATION",
        ),
        (
            "task Bad() -> None { use Missing as c return none }",
            "CAPABILITY_UNKNOWN_TYPE",
        ),
        (
            "capability C { fn x() -> Int } task Bad() -> Int { use C as c return c.nope() }",
            "CAPABILITY_UNKNOWN_OPERATION",
        ),
        (
            'capability C { fn x(v: Int) -> Int } task Bad() -> Int { use C as c return c.x("bad") }',
            "TYPE_MISMATCH",
        ),
    ],
)
def test_capability_diagnostics(source: str, code: str) -> None:
    result = compile_source(source)
    assert code in [item.code for item in result.diagnostics]


def test_sync_binding_and_operation_grants() -> None:
    runtime = runtime_for()
    instance = runtime.create_task("Count")
    adapter = MockCounter()
    runtime.bind_capability(instance, "counter", adapter)
    runtime.run_task(instance)
    assert instance.state is TaskState.COMPLETED
    assert instance.result == 41
    assert [call[0] for call in adapter.calls] == ["add", "read"]

    denied_runtime = runtime_for()
    denied = denied_runtime.create_task("Count")
    denied_adapter = MockCounter()
    denied_runtime.bind_capability(denied, "counter", denied_adapter, granted_operations={"read"})
    denied_runtime.run_task(denied)
    assert denied.state is TaskState.FAILED
    assert denied.failure is not None
    assert denied.failure.code == "CAPABILITY_OPERATION_DENIED"
    assert denied_adapter.calls == []


def test_missing_binding_blocks_start_and_task_bindings_are_isolated() -> None:
    registry = CapabilityRegistry()
    runtime = runtime_for(registry=registry)
    missing = runtime.create_task("Count")
    runtime.run_task(missing)
    assert missing.failure is not None
    assert missing.failure.code == "CAPABILITY_NOT_PROVIDED"

    first = runtime.create_task("Count")
    second = runtime.create_task("Count")
    one = MockCounter("one")
    two = MockCounter("two")
    runtime.bind_capability(first, "counter", one)
    runtime.bind_capability(second, "counter", two)
    assert registry.resolve(str(first.id), "counter").adapter is one  # type: ignore[union-attr]
    assert registry.resolve(str(second.id), "counter").adapter is two  # type: ignore[union-attr]


def test_async_suspension_completion_validation_and_duplicates() -> None:
    source = """capability Counter { fn add(amount: Int) -> Int }
task Count() -> Int { use Counter as counter step work { return counter.add(1) } return 0 }
"""
    runtime = runtime_for(source)
    instance = runtime.create_task("Count")
    adapter = MockCounter(asynchronous=True)
    runtime.bind_capability(instance, "counter", adapter)
    runtime.run_task(instance)
    request = instance.pending_capability_request
    assert request is not None
    assert instance.state is TaskState.WAITING_FOR_CAPABILITY
    assert instance.step("work").state is StepState.RUNNING  # type: ignore[union-attr]
    with pytest.raises(TaskStartError) as mismatch:
        runtime.complete_capability_request(instance.id, request.id, "wrong")
    assert mismatch.value.code == "CAPABILITY_RETURN_MISMATCH"
    runtime.complete_capability_request(instance.id, request.id, 42)
    assert instance.result == 42
    assert len(adapter.calls) == 1
    with pytest.raises(TaskStartError) as duplicate:
        runtime.complete_capability_request(instance.id, request.id, 43)
    assert duplicate.value.code == "CAPABILITY_REQUEST_ALREADY_COMPLETED"


def test_binding_and_pending_request_persist_then_restore_indeterminate() -> None:
    source = """capability Counter { fn add(amount: Int) -> Int }
task Count() -> Int { use Counter as counter return counter.add(1) }
"""
    store = InMemoryTaskStore()
    registry = CapabilityRegistry()
    adapter = MockCounter(asynchronous=True)
    first = runtime_for(source, store=store, registry=registry)
    instance = first.create_task("Count")
    first.bind_capability(instance, "counter", adapter)
    first.run_task(instance)
    original = instance.pending_capability_request
    assert original is not None
    snapshot = store.load(str(instance.id))
    assert snapshot.capability_bindings[0]["host_binding_id"] == "counter-1"
    assert snapshot.capability_bindings[0]["capability_identity"]["module"] == "<entry>"
    assert snapshot.pending_capability_request["id"] == str(original.id)  # type: ignore[index]

    second = runtime_for(source, store=store, registry=registry)
    restored = second.restore_task(instance.id)
    pending = restored.pending_capability_request
    assert pending is not None
    assert pending.id == original.id
    assert pending.status is CapabilityRequestStatus.INDETERMINATE
    assert len(adapter.calls) == 1
    with pytest.raises(TaskStartError) as blocked:
        second.complete_capability_request(restored.id, pending.id, 42)
    assert blocked.value.code == "CAPABILITY_REQUEST_INDETERMINATE"
    second.reconcile_capability_request(restored.id, pending.id, 42)
    assert restored.result == 42
    assert len(adapter.calls) == 1


def test_restore_requires_exact_capability_rebinding() -> None:
    store = InMemoryTaskStore()
    first_registry = CapabilityRegistry()
    first = runtime_for(store=store, registry=first_registry)
    instance = first.create_task("Count")
    first.bind_capability(instance, "counter", MockCounter())

    second = runtime_for(store=store, registry=CapabilityRegistry())
    with pytest.raises(TaskPersistenceError) as failure:
        second.restore_task(instance.id)
    assert failure.value.code == "CAPABILITY_REBIND_FAILED"
