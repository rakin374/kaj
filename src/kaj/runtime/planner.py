from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import uuid4

from kaj.ast import Block


@dataclass(frozen=True)
class PlanningAttemptId:
    value: str

    @classmethod
    def create(cls) -> PlanningAttemptId:
        return cls(str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PlannerRequest:
    task_id: str
    attempt_id: PlanningAttemptId
    task_name: str
    task_inputs: tuple[object, ...]
    goal: str | None
    requirement_count: int
    invariant_count: int
    has_success: bool
    capability_grants: tuple[tuple[str, tuple[str, ...]], ...]
    completed_steps: tuple[str, ...]
    purpose: str = "initial_plan"
    current_plan_revision: int = 0
    current_plan_fingerprint: str | None = None
    replan_reason: str | None = None
    pending_steps: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlannerProposal:
    plan: Block
    metadata: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class PlanPatch:
    base_plan_revision: int
    base_plan_fingerprint: str
    replacement_pending_plan: Block
    metadata: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class PlannerAdapterResult:
    pending: bool
    proposal: PlannerProposal | None = None

    @classmethod
    def immediate(cls, proposal: PlannerProposal) -> PlannerAdapterResult:
        return cls(False, proposal)

    @classmethod
    def pending_result(cls) -> PlannerAdapterResult:
        return cls(True)


class PlannerAdapter(ABC):
    @abstractmethod
    def request_plan(self, request: PlannerRequest) -> PlannerAdapterResult: ...


@dataclass
class PlanningAttempt:
    id: PlanningAttemptId
    request: PlannerRequest
    status: str = "pending"
    diagnostics: tuple[object, ...] = ()
    purpose: str = "initial_plan"
    base_revision: int = 0
    base_fingerprint: str | None = None
    reason: str | None = None
    resulting_revision: int | None = None
    resulting_fingerprint: str | None = None
