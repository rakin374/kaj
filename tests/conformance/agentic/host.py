from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass

from kaj.capabilities import CapabilityIdentity
from kaj.pipeline import compile_source
from kaj.runtime import (
    BufferOutput,
    CapabilityAdapter,
    CapabilityAdapterResult,
    CapabilityRegistry,
    InMemoryTaskStore,
    PlannerAdapter,
    PlannerAdapterResult,
    PlannerProposal,
    RuntimeEvent,
    TaskRuntime,
)
from kaj.runtime.values import RuntimeValue


class DeterministicCapability(CapabilityAdapter):
    """Queue-backed capability adapter with no external services or native leaks."""

    def __init__(
        self,
        capability_type: str,
        binding_id: str,
        results: Iterable[RuntimeValue],
        *,
        module_name: str = "<entry>",
        major_version: int = 1,
        supported_operations: frozenset[str] | None = None,
    ) -> None:
        self._capability_type = capability_type
        self._binding_id = binding_id
        self._identity = CapabilityIdentity(module_name, capability_type, major_version)
        self.results = deque(results)
        self.calls: list[tuple[str, tuple[object, ...]]] = []
        self._supported_operations = (
            frozenset({"read"}) if supported_operations is None else supported_operations
        )

    @property
    def capability_identity(self) -> CapabilityIdentity:
        return self._identity

    @property
    def capability_type(self) -> str:
        return self._capability_type

    @property
    def host_binding_id(self) -> str:
        return self._binding_id

    @property
    def supported_operations(self) -> frozenset[str]:
        return self._supported_operations

    def invoke(self, request_id, operation, arguments):  # type: ignore[no-untyped-def]
        del request_id
        self.calls.append((operation, tuple(arguments)))
        return CapabilityAdapterResult.immediate(self.results.popleft())


class DeterministicPlanner(PlannerAdapter):
    def __init__(self, proposals: Iterable[PlannerProposal] = ()) -> None:
        self.proposals = deque(proposals)
        self.requests = []  # type: ignore[var-annotated]

    def request_plan(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        if not self.proposals:
            return PlannerAdapterResult.pending_result()
        return PlannerAdapterResult.immediate(self.proposals.popleft())


@dataclass
class DeterministicTestHost:
    source: str
    planner: PlannerAdapter | None = None

    def __post_init__(self) -> None:
        compiled = compile_source(self.source)
        assert compiled.diagnostics == ()
        assert compiled.resolution is not None and compiled.types is not None
        self.store = InMemoryTaskStore()
        self.registry = CapabilityRegistry()
        self.output = BufferOutput()
        self.recorded_events: list[RuntimeEvent] = []
        self.runtime = TaskRuntime(
            compiled.program,
            compiled.resolution,
            compiled.types,
            store=self.store,
            output=self.output,
            capability_registry=self.registry,
            planner_adapter=self.planner,
            event_sink=self.recorded_events.append,
        )

    def event_kinds(self) -> tuple[str, ...]:
        return tuple(event.kind for event in self.recorded_events)
