from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

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
    def capability_type(self) -> str: ...

    @property
    @abstractmethod
    def host_binding_id(self) -> str: ...

    @abstractmethod
    def invoke(
        self,
        request_id: CapabilityRequestId,
        operation: str,
        arguments: tuple[RuntimeValue, ...],
    ) -> CapabilityAdapterResult: ...


@dataclass(frozen=True)
class CapabilityBindingDescriptor:
    capability_type: str
    alias: str
    host_binding_id: str
    granted_operations: frozenset[str]


@dataclass(frozen=True)
class CapabilityBinding:
    task_id: str
    descriptor: CapabilityBindingDescriptor
    adapter: CapabilityAdapter


class CapabilityRegistry:
    def __init__(self) -> None:
        self._adapters: dict[tuple[str, str], CapabilityAdapter] = {}
        self._bindings: dict[tuple[str, str], CapabilityBinding] = {}

    def register(self, adapter: CapabilityAdapter) -> None:
        self._adapters[(adapter.capability_type, adapter.host_binding_id)] = adapter

    def bind(
        self,
        task_id: str,
        descriptor: CapabilityBindingDescriptor,
        adapter: CapabilityAdapter,
    ) -> CapabilityBinding:
        if (
            adapter.capability_type != descriptor.capability_type
            or adapter.host_binding_id != descriptor.host_binding_id
        ):
            raise ValueError("CAPABILITY_BINDING_MISMATCH")
        self.register(adapter)
        binding = CapabilityBinding(task_id, descriptor, adapter)
        self._bindings[(task_id, descriptor.alias)] = binding
        return binding

    def resolve(self, task_id: str, alias: str) -> CapabilityBinding | None:
        return self._bindings.get((task_id, alias))

    def rebind(
        self, task_id: str, descriptor: CapabilityBindingDescriptor
    ) -> CapabilityBinding | None:
        adapter = self._adapters.get((descriptor.capability_type, descriptor.host_binding_id))
        if adapter is None:
            return None
        return self.bind(task_id, descriptor, adapter)
