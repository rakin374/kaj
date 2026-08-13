from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

from kaj.capabilities import CapabilityIdentity, HostBindingId
from kaj.runtime.values import RuntimeValue

@dataclass(frozen=True)
class CapabilityRequestId:
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class CapabilityAdapterResult:
    is_pending: bool
    value: RuntimeValue = None
    retry_safe: bool = False

    @classmethod
    def immediate(cls, value: RuntimeValue) -> CapabilityAdapterResult:
        return cls(False, value)

    @classmethod
    def pending(cls, *, retry_safe: bool = False) -> CapabilityAdapterResult:
        return cls(True, retry_safe=retry_safe)


class CapabilityAdapter(ABC):
    @property
    @abstractmethod
    def capability_identity(self) -> CapabilityIdentity: ...

    @property
    def capability_type(self) -> str:
        return self.capability_identity.capability_name

    @property
    @abstractmethod
    def host_binding_id(self) -> str: ...

    @property
    @abstractmethod
    def supported_operations(self) -> frozenset[str]: ...

    @abstractmethod
    def invoke(
        self,
        request_id: CapabilityRequestId,
        operation: str,
        arguments: tuple[RuntimeValue, ...],
    ) -> CapabilityAdapterResult: ...


CapabilityAdapterFactory = Callable[[CapabilityIdentity, HostBindingId], CapabilityAdapter | None]


class CapabilityRegistryError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class CapabilityBindingDescriptor:
    capability_identity: CapabilityIdentity
    alias: str
    host_binding_id: HostBindingId
    granted_operations: frozenset[str]

    @property
    def capability_type(self) -> str:
        return self.capability_identity.capability_name


@dataclass(frozen=True)
class CapabilityBinding:
    task_id: str
    descriptor: CapabilityBindingDescriptor
    adapter: CapabilityAdapter


class TaskCapabilityBindings:
    def __init__(self) -> None:
        self._bindings: dict[tuple[str, str], CapabilityBinding] = {}

    def bind(
        self,
        task_id: str,
        descriptor: CapabilityBindingDescriptor,
        adapter: CapabilityAdapter,
    ) -> CapabilityBinding:
        binding = CapabilityBinding(task_id, descriptor, adapter)
        self._bindings[(task_id, descriptor.alias)] = binding
        return binding

    def resolve(self, task_id: str, alias: str) -> CapabilityBinding | None:
        return self._bindings.get((task_id, alias))

    def resolve_for_host_binding(
        self, task_id: str, host_binding_id: HostBindingId
    ) -> CapabilityBinding | None:
        for (bound_task_id, _), binding in self._bindings.items():
            if bound_task_id == task_id and binding.descriptor.host_binding_id == host_binding_id:
                return binding
        return None


class CapabilityRegistry:
    """Host-known capability implementations and restore-time adapter resolution."""

    def __init__(self) -> None:
        self._adapters: dict[tuple[str, str], CapabilityAdapter] = {}
        self._factories: list[CapabilityAdapterFactory] = []
        self._task_bindings = TaskCapabilityBindings()

    @property
    def task_bindings(self) -> TaskCapabilityBindings:
        return self._task_bindings

    def register(self, adapter: CapabilityAdapter) -> None:
        self._validate_adapter_metadata(adapter)
        key = self._adapter_key(adapter.capability_identity, HostBindingId(adapter.host_binding_id))
        existing = self._adapters.get(key)
        if existing is not None and existing is not adapter:
            raise CapabilityRegistryError(
                "CAPABILITY_REGISTRATION_CONFLICT",
                f"Adapter already registered for {adapter.capability_identity.canonical} "
                f"and host binding '{adapter.host_binding_id}'.",
            )
        self._adapters[key] = adapter

    def register_factory(self, factory: CapabilityAdapterFactory) -> None:
        self._factories.append(factory)

    def resolve_adapter(
        self,
        identity: CapabilityIdentity,
        host_binding_id: HostBindingId,
    ) -> CapabilityAdapter | None:
        adapter = self._adapters.get(self._adapter_key(identity, host_binding_id))
        if adapter is not None:
            return adapter
        for factory in self._factories:
            resolved = factory(identity, host_binding_id)
            if resolved is not None:
                self._validate_adapter_metadata(resolved, expected_identity=identity)
                if resolved.host_binding_id != host_binding_id.value:
                    raise CapabilityRegistryError(
                        "CAPABILITY_BINDING_MISMATCH",
                        "Resolved adapter host binding does not match the requested binding.",
                    )
                self.register(resolved)
                return resolved
        return None

    def bind_task(
        self,
        task_id: str,
        descriptor: CapabilityBindingDescriptor,
        adapter: CapabilityAdapter,
    ) -> CapabilityBinding:
        self._validate_binding(descriptor, adapter)
        self.register(adapter)
        return self._task_bindings.bind(task_id, descriptor, adapter)

    def resolve_task_binding(self, task_id: str, alias: str) -> CapabilityBinding | None:
        return self._task_bindings.resolve(task_id, alias)

    def rebind_task(
        self, task_id: str, descriptor: CapabilityBindingDescriptor
    ) -> CapabilityBinding | None:
        adapter = self.resolve_adapter(descriptor.capability_identity, descriptor.host_binding_id)
        if adapter is None:
            return None
        try:
            self._validate_binding(descriptor, adapter)
        except CapabilityRegistryError:
            return None
        return self.bind_task(task_id, descriptor, adapter)

    def _adapter_key(
        self, identity: CapabilityIdentity, host_binding_id: HostBindingId
    ) -> tuple[str, str]:
        return (identity.canonical, host_binding_id.value)

    def _validate_adapter_metadata(
        self,
        adapter: CapabilityAdapter,
        *,
        expected_identity: CapabilityIdentity | None = None,
    ) -> None:
        identity = adapter.capability_identity
        if expected_identity is not None and not identity.is_compatible_with(expected_identity):
            raise CapabilityRegistryError(
                "CAPABILITY_VERSION_MISMATCH",
                f"Adapter identity {identity.canonical} is incompatible with "
                f"{expected_identity.canonical}.",
            )
        if not adapter.host_binding_id:
            raise CapabilityRegistryError(
                "CAPABILITY_BINDING_MISMATCH",
                "Capability adapter requires a host binding identifier.",
            )
        if not adapter.supported_operations:
            raise CapabilityRegistryError(
                "CAPABILITY_ADAPTER_INCOMPATIBLE",
                "Capability adapter must declare supported operations.",
            )

    def _validate_binding(
        self,
        descriptor: CapabilityBindingDescriptor,
        adapter: CapabilityAdapter,
    ) -> None:
        self._validate_adapter_metadata(
            adapter,
            expected_identity=descriptor.capability_identity,
        )
        if adapter.host_binding_id != descriptor.host_binding_id.value:
            raise CapabilityRegistryError(
                "CAPABILITY_BINDING_MISMATCH",
                "Adapter host binding does not match the binding descriptor.",
            )
        if not descriptor.granted_operations <= adapter.supported_operations:
            raise CapabilityRegistryError(
                "CAPABILITY_ADAPTER_INCOMPATIBLE",
                "Adapter does not support all granted capability operations.",
            )

    # Backward-compatible aliases used by earlier Agentic Kaj code.
    def bind(
        self,
        task_id: str,
        descriptor: CapabilityBindingDescriptor,
        adapter: CapabilityAdapter,
    ) -> CapabilityBinding:
        return self.bind_task(task_id, descriptor, adapter)

    def resolve(self, task_id: str, alias: str) -> CapabilityBinding | None:
        return self.resolve_task_binding(task_id, alias)

    def rebind(
        self, task_id: str, descriptor: CapabilityBindingDescriptor
    ) -> CapabilityBinding | None:
        return self.rebind_task(task_id, descriptor)


JSONValue = None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]


def encode_binding_descriptor(descriptor: CapabilityBindingDescriptor) -> dict[str, JSONValue]:
    return {
        "capability_identity": {
            "module": descriptor.capability_identity.module_name,
            "name": descriptor.capability_identity.capability_name,
            "major_version": descriptor.capability_identity.major_version,
        },
        "alias": descriptor.alias,
        "host_binding_id": descriptor.host_binding_id.value,
        "granted_operations": sorted(descriptor.granted_operations),
    }


def decode_binding_descriptor(data: dict[str, JSONValue]) -> CapabilityBindingDescriptor:
    identity_data = data.get("capability_identity")
    if not isinstance(identity_data, dict):
        raise ValueError("capability_identity must be an object")
    major_version = identity_data.get("major_version")
    if type(major_version) is not int:
        raise ValueError("capability_identity.major_version must be an integer")
    identity = CapabilityIdentity(
        str(identity_data.get("module")),
        str(identity_data.get("name")),
        major_version,
    )
    granted = data.get("granted_operations", [])
    if not isinstance(granted, list):
        raise ValueError("granted_operations must be an array")
    return CapabilityBindingDescriptor(
        identity,
        str(data.get("alias")),
        HostBindingId(str(data.get("host_binding_id"))),
        frozenset(str(item) for item in granted),
    )
