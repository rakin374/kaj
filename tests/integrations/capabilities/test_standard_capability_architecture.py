from __future__ import annotations

from pathlib import Path

import pytest

from kaj.capabilities import CapabilityIdentity, HostBindingId
from kaj.modules import compile_module_graph, resolve_stdlib_module, stdlib_root
from kaj.modules.names import ModuleName
from kaj.pipeline import compile_source
from kaj.runtime import (
    CapabilityBindingDescriptor,
    CapabilityRegistry,
    CapabilityRegistryError,
    CapabilityRequestId,
    InMemoryTaskStore,
    TaskPersistenceError,
    TaskRuntime,
    TaskState,
    decode_binding_descriptor,
    encode_binding_descriptor,
)
from kaj.runtime.capabilities import CapabilityAdapter, CapabilityAdapterResult
from kaj.runtime.values import RuntimeValue

LOCAL_COUNTER_IDENTITY = CapabilityIdentity("<entry>", "Counter", 1)
STANDARD_COUNTER_IDENTITY = CapabilityIdentity("std.capabilities.counter", "Counter", 1)

LOCAL_TASK_SOURCE = """capability Counter {
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


class MockCounterAdapter(CapabilityAdapter):
    def __init__(
        self,
        binding_id: str = "counter-1",
        *,
        identity: CapabilityIdentity = LOCAL_COUNTER_IDENTITY,
        asynchronous: bool = False,
    ) -> None:
        self._binding_id = binding_id
        self._identity = identity
        self.asynchronous = asynchronous
        self.value = 0
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    @property
    def capability_identity(self) -> CapabilityIdentity:
        return self._identity

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
        del request_id
        self.calls.append((operation, arguments))
        if self.asynchronous:
            return CapabilityAdapterResult.pending()
        if operation == "add":
            amount = arguments[0]
            assert type(amount) is int
            self.value += amount
            return CapabilityAdapterResult.immediate(self.value)
        return CapabilityAdapterResult.immediate(self.value)


def runtime_for(source: str, **kwargs):  # type: ignore[no-untyped-def]
    result = compile_source(source)
    assert result.diagnostics == ()
    assert result.resolution is not None and result.types is not None
    registry = kwargs.pop("registry", None)
    if registry is not None:
        kwargs["capability_registry"] = registry
    return TaskRuntime(result.program, result.resolution, result.types, **kwargs)


def test_capability_identity_equality_and_canonical_form() -> None:
    first = CapabilityIdentity("std.capabilities.counter", "Counter", 1)
    second = CapabilityIdentity("std.capabilities.counter", "Counter", 1)
    assert first == second
    assert first.canonical == "std.capabilities.counter.Counter@1"
    assert first != CapabilityIdentity("std.capabilities.other", "Counter", 1)
    assert first != CapabilityIdentity("std.capabilities.counter", "Other", 1)
    assert first != CapabilityIdentity("std.capabilities.counter", "Counter", 2)
    assert not first.is_compatible_with(CapabilityIdentity("std.capabilities.counter", "Counter", 2))


def test_registry_register_resolve_and_conflict() -> None:
    registry = CapabilityRegistry()
    adapter = MockCounterAdapter("binding-a", identity=STANDARD_COUNTER_IDENTITY)
    registry.register(adapter)
    resolved = registry.resolve_adapter(
        STANDARD_COUNTER_IDENTITY,
        HostBindingId("binding-a"),
    )
    assert resolved is adapter

    replacement = MockCounterAdapter("binding-a", identity=STANDARD_COUNTER_IDENTITY)
    with pytest.raises(CapabilityRegistryError) as conflict:
        registry.register(replacement)
    assert conflict.value.code == "CAPABILITY_REGISTRATION_CONFLICT"

    wrong_identity = MockCounterAdapter("binding-a", identity=LOCAL_COUNTER_IDENTITY)
    with pytest.raises(CapabilityRegistryError) as mismatch:
        registry.bind_task(
            "task-1",
            CapabilityBindingDescriptor(
                STANDARD_COUNTER_IDENTITY,
                "counter",
                HostBindingId("binding-a"),
                frozenset({"read"}),
            ),
            wrong_identity,
        )
    assert mismatch.value.code == "CAPABILITY_VERSION_MISMATCH"


def test_registration_is_not_grant_and_tasks_are_isolated() -> None:
    registry = CapabilityRegistry()
    registry.register(MockCounterAdapter("shared-binding"))

    runtime = runtime_for(LOCAL_TASK_SOURCE, registry=registry)
    missing = runtime.create_task("Count")
    runtime.run_task(missing)
    assert missing.failure is not None
    assert missing.failure.code == "CAPABILITY_NOT_PROVIDED"

    first = runtime.create_task("Count")
    second = runtime.create_task("Count")
    one = MockCounterAdapter("one")
    two = MockCounterAdapter("two")
    runtime.bind_capability(first, "counter", one)
    runtime.bind_capability(second, "counter", two)
    assert registry.resolve_task_binding(str(first.id), "counter").adapter is one  # type: ignore[union-attr]
    assert registry.resolve_task_binding(str(second.id), "counter").adapter is two  # type: ignore[union-attr]


def test_host_binding_id_alone_does_not_grant_access() -> None:
    registry = CapabilityRegistry()
    registry.register(MockCounterAdapter("secret-binding"))
    runtime = runtime_for(LOCAL_TASK_SOURCE, registry=registry)
    instance = runtime.create_task("Count")
    assert registry.task_bindings.resolve_for_host_binding(
        str(instance.id), HostBindingId("secret-binding")
    ) is None


def test_binding_descriptor_round_trip_excludes_adapter() -> None:
    descriptor = CapabilityBindingDescriptor(
        STANDARD_COUNTER_IDENTITY,
        "counter",
        HostBindingId("binding-1"),
        frozenset({"read", "add"}),
    )
    encoded = encode_binding_descriptor(descriptor)
    assert "adapter" not in encoded
    restored = decode_binding_descriptor(encoded)
    assert restored == descriptor


def test_restore_rebind_and_failure_cases() -> None:
    store = InMemoryTaskStore()
    registry = CapabilityRegistry()
    first = runtime_for(LOCAL_TASK_SOURCE, store=store, registry=registry)
    instance = first.create_task("Count")
    first.bind_capability(instance, "counter", MockCounterAdapter("counter-1"))

    second = runtime_for(LOCAL_TASK_SOURCE, store=store, registry=CapabilityRegistry())
    with pytest.raises(TaskPersistenceError) as missing_adapter:
        second.restore_task(instance.id)
    assert missing_adapter.value.code == "CAPABILITY_REBIND_FAILED"

    third = runtime_for(LOCAL_TASK_SOURCE, store=store, registry=registry)
    restored = third.restore_task(instance.id)
    assert restored.capability_bindings["counter"].capability_identity == LOCAL_COUNTER_IDENTITY

    bad_registry = CapabilityRegistry()
    bad_registry.register(
        MockCounterAdapter("counter-1", identity=CapabilityIdentity("<entry>", "Counter", 2))
    )
    fourth = runtime_for(LOCAL_TASK_SOURCE, store=store, registry=bad_registry)
    with pytest.raises(TaskPersistenceError) as version_mismatch:
        fourth.restore_task(instance.id)
    assert version_mismatch.value.code == "CAPABILITY_REBIND_FAILED"


def test_std_capability_module_resolution_and_imports(tmp_path: Path) -> None:
    assert resolve_stdlib_module(ModuleName(("std", "capabilities", "counter"))) is not None
    assert resolve_stdlib_module(ModuleName(("std", "capabilities", "missing"))) is None
    assert stdlib_root().is_dir()

    entry = tmp_path / "main.kaj"
    entry.write_text("import std.capabilities.counter\n", encoding="utf-8")
    graph = compile_module_graph(entry, entry.read_text(encoding="utf-8"))
    assert graph.diagnostics == ()
    assert graph.entry is not None
    imported = graph.entry.imported_namespaces[0][1]
    assert imported.name == "std"
    counter_module = next(module for name, module in imported.modules if name == "capabilities")
    nested = next(module for name, module in counter_module.modules if name == "counter")
    assert nested.name == "std.capabilities.counter"
    assert any(name == "Counter" for name, _ in nested.values)
    assert any(name == "CounterId" for name, _ in nested.types)


def test_qualified_std_capability_use_compiles(tmp_path: Path) -> None:
    entry = tmp_path / "task.kaj"
    entry.write_text(
        """import std.capabilities.counter

task Count() -> Int {
    use std.capabilities.counter.Counter as counter
    return counter.read()
}
""",
        encoding="utf-8",
    )
    graph = compile_module_graph(entry, entry.read_text(encoding="utf-8"))
    assert graph.diagnostics == ()


def test_local_imports_still_work() -> None:
    root = stdlib_root().parent / "examples" / "modules"
    graph = compile_module_graph(root / "main.kaj", (root / "main.kaj").read_text(encoding="utf-8"))
    assert graph.diagnostics == ()
