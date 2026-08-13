from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, fields, is_dataclass, replace
from decimal import Decimal
from enum import Enum
from hashlib import sha256
from typing import cast
from uuid import uuid4

from kaj.ast import (
    CallExpression,
    Expression,
    GoalClause,
    HumanInteractionExpression,
    InvariantClause,
    PlanRegion,
    Program,
    RequireClause,
    StartTaskExpression,
    StepStatement,
    SuccessClause,
    TaskDeclaration,
    UseCapabilityDeclaration,
)
from kaj.formatting import format_program
from kaj.pipeline import compile_source
from kaj.runtime.capabilities import (
    CapabilityAdapter,
    CapabilityBindingDescriptor,
    CapabilityRegistry,
    CapabilityRequestId,
)
from kaj.runtime.environment import RuntimeSlot
from kaj.runtime.errors import RuntimeErrorInfo, RuntimeFailure
from kaj.runtime.interpreter import (
    CapabilityInvocation,
    CapabilityInvocationResult,
    CapabilitySuspension,
    InteractionRequest,
    Interpreter,
    TaskExecutionContext,
)
from kaj.runtime.output import RuntimeOutput
from kaj.runtime.persistence import (
    InMemoryTaskStore,
    JSONValue,
    KajValueCodec,
    TaskPersistenceError,
    TaskSnapshot,
    TaskStore,
    task_definition_fingerprint,
)
from kaj.runtime.planner import (
    PlannerAdapter,
    PlannerProposal,
    PlannerRequest,
    PlanningAttempt,
    PlanningAttemptId,
    PlanPatch,
)
from kaj.runtime.values import (
    KajEnumValue,
    KajList,
    KajMap,
    KajModuleValue,
    KajNewtypeValue,
    KajRecord,
    KajTaskHandle,
    RuntimeValue,
)
from kaj.semantic import (
    CapabilityType,
    EnumType,
    ListType,
    MapType,
    NewtypeType,
    OptionalType,
    PrimitiveType,
    RecordType,
    ResolutionResult,
    ResultType,
    TaskType,
    TypeCheckResult,
    ValueType,
)
from kaj.serialization import ast_from_json, ast_to_json

AGENTIC_CONFORMANCE_VERSION = "Agentic Kaj Conformance 1"


@dataclass(frozen=True)
class TaskId:
    """Opaque identity for one task execution."""

    _value: str

    @classmethod
    def create(cls) -> TaskId:
        return cls(str(uuid4()))

    def __str__(self) -> str:
        return self._value


class TaskState(Enum):
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_FOR_HUMAN = "waiting_for_human"
    WAITING_FOR_CAPABILITY = "waiting_for_capability"
    WAITING_FOR_TASK = "waiting_for_task"
    WAITING_FOR_PLANNER = "waiting_for_planner"


class StepState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ContractFailureKind(Enum):
    REQUIREMENT_VIOLATION = "requirement_violation"
    INVARIANT_VIOLATION = "invariant_violation"
    SUCCESS_NOT_SATISFIED = "success_not_satisfied"
    EVALUATION_FAILURE = "evaluation_failure"


@dataclass(frozen=True)
class InteractionId:
    _value: str

    @classmethod
    def create(cls) -> InteractionId:
        return cls(str(uuid4()))

    def __str__(self) -> str:
        return self._value


class InteractionKind(Enum):
    ASK = "ask"
    CHOOSE = "choose"
    CONFIRM = "confirm"
    HANDOFF = "handoff"
    INFORM = "inform"


class InteractionStatus(Enum):
    PENDING = "pending"
    ANSWERED = "answered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class CapabilityRequestStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INDETERMINATE = "indeterminate"


@dataclass
class CapabilityRequest:
    id: CapabilityRequestId
    task_id: TaskId
    alias: str
    capability_type: str
    operation: str
    arguments: tuple[RuntimeValue, ...]
    expected_type: ValueType
    status: CapabilityRequestStatus = CapabilityRequestStatus.PENDING
    retry_safe: bool = False
    _suspension: CapabilitySuspension | None = field(default=None, repr=False)


@dataclass
class HumanInteraction:
    id: InteractionId
    task_id: TaskId
    kind: InteractionKind
    prompt: str
    expected_type: ValueType
    options: tuple[RuntimeValue, ...] = ()
    status: InteractionStatus = InteractionStatus.PENDING
    response: RuntimeValue = None
    _request: InteractionRequest | None = field(default=None, repr=False)


@dataclass(frozen=True)
class ContractFailure:
    kind: ContractFailureKind
    clause: GoalClause | RequireClause | InvariantClause | SuccessClause
    underlying_error: RuntimeErrorInfo | None = None


@dataclass(frozen=True)
class TaskFailure:
    code: str
    message: str
    runtime_error: RuntimeErrorInfo
    contract_failure: ContractFailure | None = None


@dataclass(frozen=True)
class TaskDefinition:
    declaration: TaskDeclaration
    signature: TaskType
    goal: GoalClause | None = None
    requirements: tuple[RequireClause, ...] = ()
    invariants: tuple[InvariantClause, ...] = ()
    success: SuccessClause | None = None

    @property
    def name(self) -> str:
        return self.declaration.name


@dataclass(frozen=True)
class StepDefinition:
    statement: StepStatement

    @property
    def name(self) -> str:
        return self.statement.name


@dataclass
class StepExecution:
    definition: StepDefinition
    state: StepState = StepState.PENDING
    _observer: Callable[[str, str], None] | None = field(default=None, repr=False)

    def _transition(self, target: StepState) -> None:
        allowed = {
            StepState.PENDING: {StepState.RUNNING},
            StepState.RUNNING: {StepState.COMPLETED, StepState.FAILED},
            StepState.COMPLETED: set(),
            StepState.FAILED: set(),
        }
        if target not in allowed[self.state]:
            raise TaskStartError(
                "TASK_INVALID_STEP_STATE_TRANSITION",
                f"Cannot transition step '{self.definition.name}' from "
                f"{self.state.value} to {target.value}.",
            )
        previous = self.state
        self.state = target
        if self._observer is not None:
            self._observer(previous.value, target.value)


@dataclass(frozen=True)
class RuntimeEvent:
    """Deterministic host-observability event; never part of Kaj source semantics."""

    sequence: int
    kind: str
    task_id: str
    details: tuple[tuple[str, str], ...] = ()


@dataclass
class TaskInstance:
    id: TaskId
    definition: TaskDefinition
    arguments: tuple[RuntimeValue, ...]
    state: TaskState = TaskState.CREATED
    result: RuntimeValue = None
    failure: TaskFailure | None = None
    goal: str | None = None
    step_executions: tuple[StepExecution, ...] = ()
    pause_requested: bool = False
    cancel_requested: bool = False
    pending_interaction: HumanInteraction | None = None
    interactions: list[HumanInteraction] = field(default_factory=list)
    inform_events: list[str] = field(default_factory=list)
    capability_bindings: dict[str, CapabilityBindingDescriptor] = field(default_factory=dict)
    pending_capability_request: CapabilityRequest | None = None
    capability_requests: list[CapabilityRequest] = field(default_factory=list)
    parent_task_id: TaskId | None = None
    child_task_ids: list[TaskId] = field(default_factory=list)
    waiting_on_task_id: TaskId | None = None
    planning_attempt: PlanningAttempt | None = None
    planning_attempts: list[PlanningAttempt] = field(default_factory=list)
    accepted_plan: PlanRegion | None = None
    accepted_plan_fingerprint: str | None = None
    plan_revision: int = 0
    _interpreter: Interpreter | None = field(default=None, repr=False)
    _context: TaskExecutionContext | None = field(default=None, repr=False)
    _observer: Callable[[TaskState, TaskState], None] | None = field(
        default=None, repr=False
    )

    def _transition(self, target: TaskState) -> None:
        allowed = {
            TaskState.CREATED: {
                TaskState.READY,
                TaskState.FAILED,
                TaskState.CANCELLED,
            },
            TaskState.READY: {
                TaskState.RUNNING,
                TaskState.FAILED,
                TaskState.CANCELLED,
            },
            TaskState.RUNNING: {
                TaskState.PAUSED,
                TaskState.COMPLETED,
                TaskState.FAILED,
                TaskState.CANCELLED,
                TaskState.WAITING_FOR_HUMAN,
                TaskState.WAITING_FOR_CAPABILITY,
                TaskState.WAITING_FOR_TASK,
                TaskState.WAITING_FOR_PLANNER,
            },
            TaskState.PAUSED: {
                TaskState.RUNNING,
                TaskState.FAILED,
                TaskState.CANCELLED,
                TaskState.WAITING_FOR_PLANNER,
            },
            TaskState.COMPLETED: set(),
            TaskState.FAILED: set(),
            TaskState.CANCELLED: set(),
            TaskState.WAITING_FOR_HUMAN: {
                TaskState.RUNNING,
                TaskState.CANCELLED,
                TaskState.FAILED,
            },
            TaskState.WAITING_FOR_CAPABILITY: {
                TaskState.RUNNING,
                TaskState.CANCELLED,
                TaskState.FAILED,
            },
            TaskState.WAITING_FOR_TASK: {
                TaskState.RUNNING,
                TaskState.CANCELLED,
                TaskState.FAILED,
            },
            TaskState.WAITING_FOR_PLANNER: {
                TaskState.RUNNING,
                TaskState.PAUSED,
                TaskState.CANCELLED,
                TaskState.FAILED,
            },
        }
        if target not in allowed[self.state]:
            raise TaskStartError(
                "TASK_INVALID_STATE_TRANSITION",
                f"Cannot transition task from {self.state.value} to {target.value}.",
            )
        previous = self.state
        self.state = target
        if self._observer is not None:
            self._observer(previous, target)

    def step(self, name: str) -> StepExecution | None:
        return next((item for item in self.step_executions if item.definition.name == name), None)


class TaskStartError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class TaskRuntime:
    """Synchronous, cooperatively pausable in-memory Kaj task runtime."""

    def __init__(
        self,
        program: Program,
        resolution: ResolutionResult,
        types: TypeCheckResult,
        *,
        output: RuntimeOutput | None = None,
        imported_modules: dict[int, KajModuleValue] | None = None,
        store: TaskStore | None = None,
        module_identity: str = "main",
        capability_registry: CapabilityRegistry | None = None,
        child_capability_binder: Callable[[TaskRuntime, TaskInstance], None] | None = None,
        planner_adapter: PlannerAdapter | None = None,
        event_sink: Callable[[RuntimeEvent], None] | None = None,
    ) -> None:
        self._program = program
        self._resolution = resolution
        self._types = types
        self._output = output
        self._imported_modules = imported_modules
        self._store = InMemoryTaskStore() if store is None else store
        self._module_identity = module_identity
        self._codec = KajValueCodec(types)
        self._capability_registry = (
            CapabilityRegistry() if capability_registry is None else capability_registry
        )
        self._child_capability_binder = child_capability_binder
        self._planner_adapter = planner_adapter
        self._event_sink = event_sink
        self._events: list[RuntimeEvent] = []
        definitions: dict[str, TaskDefinition] = {}
        for statement in program.statements:
            if not isinstance(statement, TaskDeclaration):
                continue
            symbol = resolution.symbol_for_declaration(statement)
            signature = None if symbol is None else types.type_of_symbol(symbol)
            if isinstance(signature, TaskType):
                goal = next(
                    (item for item in statement.body.statements if isinstance(item, GoalClause)),
                    None,
                )
                requirements = tuple(
                    item for item in statement.body.statements if isinstance(item, RequireClause)
                )
                invariants = tuple(
                    item for item in statement.body.statements if isinstance(item, InvariantClause)
                )
                success = next(
                    (item for item in statement.body.statements if isinstance(item, SuccessClause)),
                    None,
                )
                definitions[statement.name] = TaskDefinition(
                    statement, signature, goal, requirements, invariants, success
                )
        self._definitions = definitions
        self._instances: dict[str, TaskInstance] = {}

    @property
    def store(self) -> TaskStore:
        return self._store

    @property
    def events(self) -> tuple[RuntimeEvent, ...]:
        return tuple(self._events)

    def _emit(self, kind: str, instance: TaskInstance, **details: str) -> None:
        event = RuntimeEvent(
            len(self._events) + 1,
            kind,
            str(instance.id),
            tuple(sorted(details.items())),
        )
        self._events.append(event)
        if self._event_sink is not None:
            self._event_sink(event)

    def _observe_instance(self, instance: TaskInstance) -> None:
        instance._observer = lambda previous, current: self._state_changed(
            instance, previous, current
        )
        for step in instance.step_executions:
            self._observe_step(instance, step)

    def _observe_step(self, instance: TaskInstance, step: StepExecution) -> None:
        step._observer = lambda previous, current: self._step_changed(
            instance, step, previous, current
        )

    def _state_changed(
        self, instance: TaskInstance, previous: TaskState, current: TaskState
    ) -> None:
        self._emit(
            "task_state_changed",
            instance,
            previous=previous.value,
            current=current.value,
        )
        terminal_event = {
            TaskState.COMPLETED: "task_completed",
            TaskState.FAILED: "task_failed",
            TaskState.CANCELLED: "task_cancelled",
        }.get(current)
        if terminal_event is not None:
            self._emit(terminal_event, instance)

    def _step_changed(
        self, instance: TaskInstance, step: StepExecution, previous: str, current: str
    ) -> None:
        del previous
        event = {
            StepState.RUNNING.value: "step_started",
            StepState.COMPLETED.value: "step_completed",
            StepState.FAILED.value: "step_failed",
        }.get(current)
        if event is not None:
            self._emit(event, instance, step=step.definition.name)

    def definition(self, name: str) -> TaskDefinition | None:
        return self._definitions.get(name)

    def bind_capability(
        self,
        instance: TaskInstance,
        alias: str,
        adapter: CapabilityAdapter,
        *,
        granted_operations: frozenset[str] | set[str] | None = None,
    ) -> CapabilityBindingDescriptor:
        declaration = next(
            (
                item
                for item in instance.definition.declaration.body.statements
                if isinstance(item, UseCapabilityDeclaration) and item.alias == alias
            ),
            None,
        )
        if declaration is None:
            raise TaskStartError(
                "CAPABILITY_UNKNOWN_ALIAS", f"Task has no capability alias '{alias}'."
            )
        if adapter.capability_type != declaration.capability_name:
            raise TaskStartError(
                "CAPABILITY_BINDING_MISMATCH",
                f"Adapter type '{adapter.capability_type}' cannot bind '{declaration.capability_name}'.",
            )
        capability_symbol = self._resolution.symbol_for_declaration(declaration)
        capability_type = (
            None if capability_symbol is None else self._types.type_of_symbol(capability_symbol)
        )
        if not isinstance(capability_type, CapabilityType):
            raise TaskStartError(
                "CAPABILITY_UNKNOWN_TYPE", "Capability requirement has no static type."
            )
        declared = frozenset(item.name for item in capability_type.operations)
        grants = declared if granted_operations is None else frozenset(granted_operations)
        if not grants <= declared:
            raise TaskStartError(
                "CAPABILITY_BINDING_MISMATCH",
                "Capability grant contains an undeclared operation.",
            )
        descriptor = CapabilityBindingDescriptor(
            declaration.capability_name,
            alias,
            adapter.host_binding_id,
            grants,
        )
        self._capability_registry.bind(str(instance.id), descriptor, adapter)
        instance.capability_bindings[alias] = descriptor
        self._save_snapshot(instance)
        return descriptor

    def start_task(
        self, name: str, arguments: tuple[RuntimeValue, ...] | list[RuntimeValue] = ()
    ) -> TaskInstance:
        instance = self.create_task(name, arguments)
        return self.run_task(instance)

    def create_task(
        self, name: str, arguments: tuple[RuntimeValue, ...] | list[RuntimeValue] = ()
    ) -> TaskInstance:
        definition = self.definition(name)
        if definition is None:
            raise TaskStartError("TASK_NOT_FOUND", f"Task '{name}' was not found.")
        supplied = tuple(arguments)
        parameters = definition.signature.parameters
        if len(supplied) != len(parameters):
            raise TaskStartError(
                "TASK_ARGUMENT_COUNT_MISMATCH",
                f"Task '{name}' expects {len(parameters)} arguments but received {len(supplied)}.",
            )
        coerced: list[RuntimeValue] = []
        for index, (value, parameter) in enumerate(zip(supplied, parameters, strict=True)):
            converted = _validate_argument(value, parameter.type)
            if converted is _INVALID:
                raise TaskStartError(
                    "TASK_ARGUMENT_TYPE_MISMATCH",
                    f"Argument {index + 1} for task '{name}' does not match {parameter.type!s}.",
                )
            coerced.append(cast(RuntimeValue, converted))

        steps = tuple(
            StepExecution(StepDefinition(statement))
            for statement in definition.declaration.body.statements
            if isinstance(statement, StepStatement)
        )
        instance = TaskInstance(TaskId.create(), definition, tuple(coerced), step_executions=steps)
        self._observe_instance(instance)
        self._instances[str(instance.id)] = instance
        self._emit("task_created", instance)
        self._save_snapshot(instance)
        return instance

    def ready_task(self, instance: TaskInstance) -> TaskInstance:
        for capability_requirement in self._capability_requirements(instance):
            if (
                self._capability_registry.resolve(str(instance.id), capability_requirement.alias)
                is None
            ):
                capability_error = RuntimeErrorInfo(
                    "CAPABILITY_NOT_PROVIDED",
                    f"Required capability '{capability_requirement.capability_name}' as "
                    f"'{capability_requirement.alias}' was not provided.",
                    capability_requirement.span,
                )
                instance.failure = TaskFailure(
                    capability_error.code, capability_error.message, capability_error
                )
                instance._transition(TaskState.FAILED)
                self._save_snapshot(instance)
                return instance
        self._prepare_instance(instance)
        if instance.state is TaskState.FAILED:
            return instance
        definition = instance.definition
        interpreter = instance._interpreter
        context = instance._context
        if interpreter is None or context is None:
            raise RuntimeError("prepared task has no execution context")
        if definition.goal is not None:
            goal, goal_error = interpreter.evaluate_contract(context, definition.goal.expression)
            if goal_error is not None:
                self._fail_contract_evaluation(instance, definition.goal, goal_error)
                return instance
            if not isinstance(goal, str):
                self._fail_contract_evaluation(
                    instance,
                    definition.goal,
                    RuntimeErrorInfo(
                        "RUNTIME_INTERNAL_ERROR",
                        "Goal did not evaluate to String.",
                        definition.goal.span,
                    ),
                )
                return instance
            instance.goal = goal
        for contract_requirement in definition.requirements:
            passed = self._evaluate_bool_contract(
                instance, contract_requirement, contract_requirement.condition
            )
            if passed is None:
                return instance
            if not passed:
                self._fail_contract(
                    instance,
                    "TASK_REQUIREMENT_VIOLATED",
                    "Task requirement evaluated to false.",
                    ContractFailureKind.REQUIREMENT_VIOLATION,
                    contract_requirement,
                )
                return instance
        instance._transition(TaskState.READY)
        self._save_snapshot(instance)
        return instance

    def run_task(self, instance: TaskInstance) -> TaskInstance:
        if instance.state is TaskState.CREATED:
            self.ready_task(instance)
        if instance.state is TaskState.FAILED:
            return instance
        if not self._evaluate_invariants(instance):
            return instance
        instance._transition(TaskState.RUNNING)
        return self._continue_task(instance)

    def resume_task(self, instance: TaskInstance | TaskId | str) -> TaskInstance:
        if not isinstance(instance, TaskInstance):
            instance = self.restore_task(instance)
        if instance.state in {TaskState.CREATED, TaskState.READY}:
            return self.run_task(instance)
        if instance.state is TaskState.WAITING_FOR_HUMAN:
            return instance
        if instance.state is TaskState.WAITING_FOR_CAPABILITY:
            return instance
        if instance.state is TaskState.WAITING_FOR_TASK:
            child_id = instance.waiting_on_task_id
            if child_id is None:
                raise TaskStartError("TASK_CHILD_NOT_FOUND", "Waiting task has no child identity.")
            child = self._instances.get(str(child_id))
            if child is None:
                try:
                    child = self.restore_task(child_id)
                except TaskPersistenceError as error:
                    raise TaskStartError("TASK_CHILD_NOT_FOUND", error.message) from None
            if child.state not in {
                TaskState.COMPLETED,
                TaskState.FAILED,
                TaskState.CANCELLED,
            }:
                return instance
            instance.waiting_on_task_id = None
            instance._transition(TaskState.RUNNING)
            return self._continue_task(instance)
        if instance.state in {TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED}:
            raise TaskStartError(
                "TASK_INVALID_STATE_TRANSITION",
                f"Cannot resume terminal task in state {instance.state.value}.",
            )
        instance.pause_requested = False
        if not self._evaluate_invariants(instance):
            return instance
        instance._transition(TaskState.RUNNING)
        return self._continue_task(instance)

    def request_pause(self, instance: TaskInstance) -> None:
        if instance.state is not TaskState.RUNNING:
            raise TaskStartError(
                "TASK_INVALID_STATE_TRANSITION",
                f"Cannot request pause while task is {instance.state.value}.",
            )
        instance.pause_requested = True

    def cancel_task(self, instance: TaskInstance) -> TaskInstance:
        if instance.state is TaskState.RUNNING:
            instance.cancel_requested = True
            return instance
        if instance.state is TaskState.WAITING_FOR_HUMAN:
            interaction = instance.pending_interaction
            if interaction is not None:
                interaction.status = InteractionStatus.CANCELLED
                instance.pending_interaction = None
        if instance.state is TaskState.WAITING_FOR_CAPABILITY:
            request = instance.pending_capability_request
            if request is not None:
                request.status = CapabilityRequestStatus.CANCELLED
                instance.pending_capability_request = None
        if (
            instance.state is TaskState.WAITING_FOR_PLANNER
            and instance.planning_attempt is not None
        ):
            instance.planning_attempt.status = "cancelled"
            instance.planning_attempt = None
        instance._transition(TaskState.CANCELLED)
        self._save_snapshot(instance)
        self._cancel_descendants(instance)
        self._wake_parent(instance)
        return instance

    def get_pending_interaction(self, task_id: TaskId | str) -> HumanInteraction | None:
        instance = self._instances.get(str(task_id))
        return None if instance is None else instance.pending_interaction

    def respond_to_interaction(
        self,
        task_id: TaskId | str,
        interaction_id: InteractionId | str,
        value: object,
    ) -> TaskInstance:
        instance, interaction = self._active_interaction(task_id, interaction_id)
        if interaction.kind is InteractionKind.HANDOFF:
            raise TaskStartError(
                "TASK_INTERACTION_RESPONSE_TYPE_MISMATCH",
                "Use complete_handoff for a handoff interaction.",
            )
        converted = _validate_argument(value, interaction.expected_type)
        if converted is _INVALID:
            raise TaskStartError(
                "TASK_INTERACTION_RESPONSE_TYPE_MISMATCH",
                "Human response does not match the expected Kaj type.",
            )
        canonical = cast(RuntimeValue, converted)
        if interaction.kind is InteractionKind.CHOOSE and not any(
            canonical == option for option in interaction.options
        ):
            raise TaskStartError(
                "TASK_CHOOSE_RESPONSE_INVALID",
                "Human response is not one of the available choices.",
            )
        return self._complete_interaction(instance, interaction, canonical)

    def complete_handoff(
        self, task_id: TaskId | str, interaction_id: InteractionId | str
    ) -> TaskInstance:
        instance, interaction = self._active_interaction(task_id, interaction_id)
        if interaction.kind is not InteractionKind.HANDOFF:
            raise TaskStartError(
                "TASK_INTERACTION_RESPONSE_TYPE_MISMATCH",
                "Only handoff interactions accept a completion signal.",
            )
        return self._complete_interaction(instance, interaction, None)

    def cancel_interaction(
        self, task_id: TaskId | str, interaction_id: InteractionId | str
    ) -> TaskInstance:
        instance, interaction = self._active_interaction(task_id, interaction_id)
        interaction.status = InteractionStatus.CANCELLED
        instance.pending_interaction = None
        instance._transition(TaskState.CANCELLED)
        self._save_snapshot(instance)
        return instance

    def _active_interaction(
        self, task_id: TaskId | str, interaction_id: InteractionId | str
    ) -> tuple[TaskInstance, HumanInteraction]:
        instance = self._instances.get(str(task_id))
        if instance is None:
            raise TaskStartError("TASK_INTERACTION_NOT_FOUND", "Task or interaction was not found.")
        interaction = instance.pending_interaction
        if interaction is None:
            known = next(
                (item for item in instance.interactions if str(item.id) == str(interaction_id)),
                None,
            )
            code = (
                "TASK_INTERACTION_ALREADY_COMPLETED"
                if known is not None
                else "TASK_INTERACTION_NOT_FOUND"
            )
            raise TaskStartError(code, "Interaction is not active.")
        if str(interaction.id) != str(interaction_id):
            raise TaskStartError(
                "TASK_INTERACTION_STALE", "Interaction ID is not the active interaction."
            )
        return instance, interaction

    def _complete_interaction(
        self,
        instance: TaskInstance,
        interaction: HumanInteraction,
        value: RuntimeValue,
    ) -> TaskInstance:
        request = interaction._request
        interpreter = instance._interpreter
        if request is None or interpreter is None:
            raise RuntimeError("pending interaction has no interpreter request")
        interaction.response = value
        interaction.status = InteractionStatus.COMPLETED
        interpreter.supply_interaction_response(request.expression, value)
        instance.pending_interaction = None
        self._emit(
            "interaction_resolved",
            instance,
            interaction_id=str(interaction.id),
            interaction_kind=interaction.kind.value,
        )
        instance._transition(TaskState.RUNNING)
        resumed = self._continue_task(instance)
        return resumed

    def _continue_task(self, instance: TaskInstance) -> TaskInstance:
        interpreter = instance._interpreter
        context = instance._context
        if interpreter is None or context is None:
            raise RuntimeError("running task has no execution context")
        while instance.state is TaskState.RUNNING:
            next_statement = (
                context.statements[context.next_statement]
                if context.next_statement < len(context.statements)
                else None
            )
            step_execution = (
                instance.step(next_statement.name)
                if isinstance(next_statement, StepStatement)
                else None
            )
            if isinstance(next_statement, PlanRegion) and instance.accepted_plan is None:
                if self._request_plan(instance) is False:
                    return instance
                continue
            if step_execution is not None and step_execution.state is StepState.PENDING:
                step_execution._transition(StepState.RUNNING)
                # This pre-step image is the committed recovery point if the process
                # dies before the completion snapshot is atomically saved.
                self._save_snapshot(instance)
            outcome = interpreter.execute_task_next(context)
            instance.inform_events = list(interpreter.inform_events)
            if outcome.interaction is not None:
                if instance.pending_interaction is not None:
                    raise TaskStartError(
                        "TASK_MULTIPLE_PENDING_INTERACTIONS",
                        "A task may have only one pending blocking interaction.",
                    )
                request = outcome.interaction
                interaction = HumanInteraction(
                    InteractionId.create(),
                    instance.id,
                    InteractionKind(request.expression.kind),
                    request.prompt,
                    request.expected_type,
                    request.options,
                    _request=request,
                )
                instance.interactions.append(interaction)
                instance.pending_interaction = interaction
                self._emit(
                    "interaction_requested",
                    instance,
                    interaction_id=str(interaction.id),
                    interaction_kind=interaction.kind.value,
                )
                instance._transition(TaskState.WAITING_FOR_HUMAN)
                self._save_snapshot(instance)
                return instance
            if outcome.capability is not None:
                suspension = outcome.capability
                request_id = suspension.result.request_id
                if request_id is None:
                    raise TaskStartError(
                        "CAPABILITY_REQUEST_NOT_FOUND",
                        "Pending capability invocation has no request identity.",
                    )
                binding = instance.capability_bindings[suspension.invocation.alias]
                capability_request = CapabilityRequest(
                    CapabilityRequestId(request_id),
                    instance.id,
                    suspension.invocation.alias,
                    binding.capability_type,
                    suspension.invocation.operation,
                    suspension.invocation.arguments,
                    suspension.invocation.expected_type,
                    retry_safe=suspension.result.retry_safe,
                    _suspension=suspension,
                )
                instance.capability_requests.append(capability_request)
                instance.pending_capability_request = capability_request
                self._emit(
                    "capability_requested",
                    instance,
                    request_id=str(capability_request.id),
                    operation=capability_request.operation,
                )
                instance._transition(TaskState.WAITING_FOR_CAPABILITY)
                self._save_snapshot(instance)
                return instance
            if outcome.task_await is not None:
                instance.waiting_on_task_id = TaskId(outcome.task_await.handle.task_id)
                instance._transition(TaskState.WAITING_FOR_TASK)
                self._save_snapshot(instance)
                return instance
            if outcome.runtime_error is not None:
                if step_execution is not None:
                    step_execution._transition(StepState.FAILED)
                error = outcome.runtime_error
                instance.failure = TaskFailure(error.code, error.message, error)
                instance._transition(TaskState.FAILED)
                self._save_snapshot(instance)
                self._cancel_descendants(instance)
                self._wake_parent(instance)
                return instance
            if step_execution is not None:
                step_execution._transition(StepState.COMPLETED)
                if not self._evaluate_invariants(instance):
                    return instance
                self._save_snapshot(instance)
            if outcome.returned:
                instance.result = outcome.value
                if not self._evaluate_invariants(instance):
                    return instance
                if not self._evaluate_success(instance, outcome.value):
                    return instance
                instance._transition(TaskState.COMPLETED)
                self._save_snapshot(instance)
                self._wake_parent(instance)
                return instance
            if step_execution is not None:
                if instance.cancel_requested:
                    instance._transition(TaskState.CANCELLED)
                    self._save_snapshot(instance)
                    self._cancel_descendants(instance)
                    self._wake_parent(instance)
                    return instance
                if instance.pause_requested:
                    instance._transition(TaskState.PAUSED)
                    self._save_snapshot(instance)
                    return instance
        return instance

    def get_planner_request(self, task_id: TaskId | str) -> PlannerRequest | None:
        instance = self._instances.get(str(task_id))
        attempt = None if instance is None else instance.planning_attempt
        return None if attempt is None else attempt.request

    def request_replan(self, task_id: TaskId | str, reason: str) -> PlannerRequest:
        instance = self._instances.get(str(task_id))
        if instance is None or instance.accepted_plan is None or instance.plan_revision < 1:
            raise TaskStartError(
                "PLANNER_REPLAN_NOT_ALLOWED", "Task has no accepted plan to revise."
            )
        if instance.state is not TaskState.PAUSED:
            raise TaskStartError(
                "PLANNER_REPLAN_UNSAFE_BOUNDARY",
                f"Replanning requires a paused step boundary, not {instance.state.value}.",
            )
        if any(step.state is StepState.RUNNING for step in instance.step_executions):
            raise TaskStartError(
                "PLANNER_REPLAN_UNSAFE_BOUNDARY", "A running step cannot be replaced."
            )
        attempt_id = PlanningAttemptId.create()
        completed = tuple(
            step.definition.name
            for step in instance.step_executions
            if step.state is StepState.COMPLETED
        )
        pending = tuple(
            step.definition.name
            for step in instance.step_executions
            if step.state is StepState.PENDING
        )
        request = PlannerRequest(
            str(instance.id), attempt_id, instance.definition.name,
            tuple(instance.arguments), instance.goal,
            len(instance.definition.requirements), len(instance.definition.invariants),
            instance.definition.success is not None,
            tuple((alias, tuple(sorted(binding.granted_operations))) for alias, binding in sorted(instance.capability_bindings.items())),
            completed,
            "replan", instance.plan_revision, instance.accepted_plan_fingerprint,
            reason, pending,
        )
        attempt = PlanningAttempt(
            attempt_id, request, purpose="replan",
            base_revision=instance.plan_revision,
            base_fingerprint=instance.accepted_plan_fingerprint,
            reason=reason,
        )
        instance.planning_attempt = attempt
        instance.planning_attempts.append(attempt)
        self._emit(
            "planner_requested",
            instance,
            attempt_id=str(attempt.id),
            purpose="replan",
        )
        instance._transition(TaskState.WAITING_FOR_PLANNER)
        self._save_snapshot(instance)
        return request

    def complete_replan_request(
        self,
        task_id: TaskId | str,
        attempt_id: PlanningAttemptId | str,
        patch: PlanPatch,
    ) -> TaskInstance:
        instance = self._instances.get(str(task_id))
        if instance is None:
            raise TaskStartError("PLANNER_RESPONSE_TASK_MISMATCH", "Task was not found.")
        if instance.planning_attempt is None:
            known = next(
                (
                    item
                    for item in instance.planning_attempts
                    if str(item.id) == str(attempt_id)
                ),
                None,
            )
            raise TaskStartError(
                "PLANNER_RESPONSE_DUPLICATE"
                if known is not None
                else "PLANNER_ATTEMPT_NOT_FOUND",
                "Replan attempt is not active.",
            )
        attempt = instance.planning_attempt
        if str(attempt.id) != str(attempt_id):
            raise TaskStartError("PLANNER_ATTEMPT_STALE", "Replan attempt is stale.")
        if attempt.purpose != "replan":
            raise TaskStartError(
                "PLANNER_ATTEMPT_PURPOSE_MISMATCH", "Attempt is not a replan."
            )
        if patch.base_plan_revision != instance.plan_revision:
            raise TaskStartError(
                "PLANNER_PLAN_REVISION_STALE", "Patch targets a stale plan revision."
            )
        if patch.base_plan_fingerprint != instance.accepted_plan_fingerprint:
            raise TaskStartError(
                "PLANNER_PLAN_FINGERPRINT_MISMATCH", "Patch targets a different plan."
            )
        old_plan = instance.accepted_plan
        assert old_plan is not None
        completed_names = {
            step.definition.name
            for step in instance.step_executions
            if step.state is StepState.COMPLETED
        }
        completed_prefix = tuple(
            statement
            for statement in old_plan.body.statements
            if isinstance(statement, StepStatement) and statement.name in completed_names
        )
        replacement = replace(
            patch.replacement_pending_plan,
            statements=completed_prefix + patch.replacement_pending_plan.statements,
        )
        old_revision = instance.plan_revision
        old_fingerprint = instance.accepted_plan_fingerprint
        old_steps = instance.step_executions
        old_context_statements = (
            () if instance._context is None else instance._context.statements
        )
        old_resolution = (
            None if instance._interpreter is None else instance._interpreter._resolution
        )
        old_types = None if instance._interpreter is None else instance._interpreter._types
        diagnostics = self._validate_and_install_plan(
            instance, PlannerProposal(replacement, patch.metadata), is_replan=True
        )
        if diagnostics:
            attempt.status = "rejected"
            attempt.diagnostics = diagnostics
            self._emit(
                "planner_proposal_rejected",
                instance,
                attempt_id=str(attempt.id),
                purpose="replan",
            )
            instance.planning_attempt = None
            instance._transition(TaskState.PAUSED)
            self._save_snapshot(instance)
            self.request_replan(str(instance.id), attempt.reason or "")
            return instance
        instance.plan_revision = old_revision + 1
        attempt.status = "accepted"
        attempt.resulting_revision = instance.plan_revision
        attempt.resulting_fingerprint = instance.accepted_plan_fingerprint
        instance.planning_attempt = None
        try:
            self._save_snapshot(instance)
        except TaskPersistenceError:
            instance.accepted_plan = old_plan
            instance.accepted_plan_fingerprint = old_fingerprint
            instance.plan_revision = old_revision
            instance.step_executions = old_steps
            if instance._context is not None:
                instance._context.statements = old_context_statements
            if instance._interpreter is not None:
                assert old_resolution is not None and old_types is not None
                instance._interpreter._resolution = old_resolution
                instance._interpreter._types = old_types
            instance.planning_attempt = attempt
            attempt.status = "pending"
            attempt.resulting_revision = None
            attempt.resulting_fingerprint = None
            raise
        self._emit(
            "replan_accepted",
            instance,
            attempt_id=str(attempt.id),
            revision=str(instance.plan_revision),
        )
        instance.pause_requested = False
        instance._transition(TaskState.RUNNING)
        return self._continue_task(instance)

    def complete_planner_request(
        self,
        task_id: TaskId | str,
        attempt_id: PlanningAttemptId | str,
        proposal: PlannerProposal,
    ) -> TaskInstance:
        instance = self._instances.get(str(task_id))
        if instance is None:
            raise TaskStartError("PLANNER_RESPONSE_TASK_MISMATCH", "Task was not found.")
        attempt = instance.planning_attempt
        owner = next(
            (
                item
                for item in self._instances.values()
                if item.planning_attempt is not None
                and str(item.planning_attempt.id) == str(attempt_id)
            ),
            None,
        )
        if owner is not None and owner is not instance:
            raise TaskStartError(
                "PLANNER_RESPONSE_TASK_MISMATCH",
                "Planning attempt belongs to a different task.",
            )
        if attempt is None:
            known = next(
                (item for item in instance.planning_attempts if str(item.id) == str(attempt_id)),
                None,
            )
            raise TaskStartError(
                "PLANNER_RESPONSE_DUPLICATE" if known is not None else "PLANNER_ATTEMPT_NOT_FOUND",
                "Planning attempt is not active.",
            )
        if str(attempt.id) != str(attempt_id):
            raise TaskStartError("PLANNER_ATTEMPT_STALE", "Planning attempt is stale.")
        diagnostics = self._validate_and_install_plan(instance, proposal)
        if diagnostics:
            attempt.status = "rejected"
            attempt.diagnostics = diagnostics
            self._emit(
                "planner_proposal_rejected",
                instance,
                attempt_id=str(attempt.id),
                purpose="initial_plan",
            )
            instance.planning_attempt = None
            instance._transition(TaskState.RUNNING)
            self._request_plan(instance)
            return instance
        attempt.status = "accepted"
        attempt.resulting_revision = instance.plan_revision
        attempt.resulting_fingerprint = instance.accepted_plan_fingerprint
        self._emit(
            "plan_accepted",
            instance,
            attempt_id=str(attempt.id),
            revision=str(instance.plan_revision),
        )
        instance.planning_attempt = None
        instance._transition(TaskState.RUNNING)
        return self._continue_task(instance)

    def fail_planner_request(
        self, task_id: TaskId | str, attempt_id: PlanningAttemptId | str, message: str
    ) -> TaskInstance:
        instance = self._instances.get(str(task_id))
        if instance is None or instance.planning_attempt is None:
            raise TaskStartError("PLANNER_ATTEMPT_NOT_FOUND", "Planning attempt not found.")
        if str(instance.planning_attempt.id) != str(attempt_id):
            raise TaskStartError("PLANNER_ATTEMPT_STALE", "Planning attempt is stale.")
        error = RuntimeErrorInfo(
            "PLANNER_RUNTIME_FAILED", message, instance.definition.declaration.span
        )
        instance.failure = TaskFailure(error.code, error.message, error)
        instance.planning_attempt.status = "failed"
        instance.planning_attempt = None
        instance._transition(TaskState.FAILED)
        self._save_snapshot(instance)
        return instance

    def _request_plan(self, instance: TaskInstance) -> bool:
        attempt_id = PlanningAttemptId.create()
        request = PlannerRequest(
            str(instance.id),
            attempt_id,
            instance.definition.name,
            tuple(instance.arguments),
            instance.goal,
            len(instance.definition.requirements),
            len(instance.definition.invariants),
            instance.definition.success is not None,
            tuple(
                (alias, tuple(sorted(binding.granted_operations)))
                for alias, binding in sorted(instance.capability_bindings.items())
            ),
            tuple(
                step.definition.name
                for step in instance.step_executions
                if step.state is StepState.COMPLETED
            ),
        )
        attempt = PlanningAttempt(attempt_id, request)
        instance.planning_attempt = attempt
        instance.planning_attempts.append(attempt)
        self._emit(
            "planner_requested",
            instance,
            attempt_id=str(attempt.id),
            purpose="initial_plan",
        )
        if self._planner_adapter is not None:
            result = self._planner_adapter.request_plan(request)
            if not result.pending and result.proposal is not None:
                diagnostics = self._validate_and_install_plan(instance, result.proposal)
                attempt.status = "rejected" if diagnostics else "accepted"
                attempt.diagnostics = diagnostics
                if not diagnostics:
                    attempt.resulting_revision = instance.plan_revision
                    attempt.resulting_fingerprint = instance.accepted_plan_fingerprint
                    self._emit(
                        "plan_accepted",
                        instance,
                        attempt_id=str(attempt.id),
                        revision=str(instance.plan_revision),
                    )
                else:
                    self._emit(
                        "planner_proposal_rejected",
                        instance,
                        attempt_id=str(attempt.id),
                        purpose="initial_plan",
                    )
                instance.planning_attempt = None
                if not diagnostics:
                    return True
        instance._transition(TaskState.WAITING_FOR_PLANNER)
        self._save_snapshot(instance)
        return False

    def _validate_and_install_plan(
        self, instance: TaskInstance, proposal: PlannerProposal, *, is_replan: bool = False
    ) -> tuple[object, ...]:
        forbidden = (
            UseCapabilityDeclaration,
            GoalClause,
            RequireClause,
            InvariantClause,
            SuccessClause,
            PlanRegion,
        )
        if any(isinstance(item, forbidden) for item in proposal.plan.statements):
            return ("PLANNER_PROTECTED_REGION_MODIFIED",)
        statements = []
        for statement in self._program.statements:
            if statement is instance.definition.declaration:
                body = tuple(
                    replace(item, body=proposal.plan) if isinstance(item, PlanRegion) else item
                    for item in statement.body.statements
                )
                statement = replace(statement, body=replace(statement.body, statements=body))
            statements.append(statement)
        effective = replace(self._program, statements=tuple(statements))
        checked = compile_source(format_program(effective))
        if checked.diagnostics:
            return checked.diagnostics
        if checked.resolution is None or checked.types is None:
            return ("PLANNER_PROPOSAL_INVALID",)
        for node in _walk_nodes(proposal.plan):
            if isinstance(node, CallExpression) and hasattr(node.callee, "object"):
                callee = node.callee
                obj = getattr(callee, "object", None)
                alias_value = getattr(obj, "name", None)
                operation = getattr(callee, "member", None)
                binding = (
                    instance.capability_bindings.get(alias_value)
                    if isinstance(alias_value, str)
                    else None
                )
                if binding is not None and operation not in binding.granted_operations:
                    return ("PLANNER_CAPABILITY_OPERATION_DENIED",)
        compiled_task = next(
            item
            for item in checked.program.statements
            if isinstance(item, TaskDeclaration) and item.name == instance.definition.name
        )
        instance.accepted_plan = next(
            item for item in compiled_task.body.statements if isinstance(item, PlanRegion)
        )
        canonical = format_program(Program(proposal.plan.span, proposal.plan.statements))
        instance.accepted_plan_fingerprint = sha256(canonical.encode()).hexdigest()
        context = instance._context
        if context is not None:
            index = context.next_statement
            validation_interpreter = Interpreter(checked.resolution, checked.types)
            compiled_context, preparation_error = validation_interpreter.prepare_task(
                checked.program, compiled_task, instance.arguments
            )
            if preparation_error is not None or compiled_context is None:
                return ("PLANNER_PROPOSAL_INVALID",)
            context.statements = tuple(
                nested
                for statement in compiled_context.statements
                for nested in (
                    statement.body.statements
                    if isinstance(statement, PlanRegion)
                    else (statement,)
                )
            )
            context.next_statement = index
        if instance._interpreter is not None:
            instance._interpreter._resolution = checked.resolution
            instance._interpreter._types = checked.types
        completed_executions = tuple(
            item for item in instance.step_executions if item.state is StepState.COMPLETED
        )
        planned_executions = tuple(
            StepExecution(StepDefinition(item))
            for item in instance.accepted_plan.body.statements
            if isinstance(item, StepStatement)
            and item.name not in {step.definition.name for step in completed_executions}
        )
        instance.step_executions = completed_executions + planned_executions
        for step in instance.step_executions:
            self._observe_step(instance, step)
        if not is_replan:
            instance.plan_revision = 1
            self._save_snapshot(instance)
        return ()

    def snapshot(self, instance: TaskInstance) -> TaskSnapshot:
        context = instance._context
        environment: list[dict[str, JSONValue]] = []
        position = 0
        responses: tuple[tuple[str, JSONValue], ...] = ()
        capability_responses: tuple[tuple[str, JSONValue], ...] = ()
        composition_values: tuple[tuple[str, JSONValue], ...] = ()
        if context is not None:
            position = context.next_statement
            for slot in context.environment.local_slots():
                environment.append(
                    {
                        "symbol_id": slot.symbol.id,
                        "mutable": slot.mutable,
                        "value": self._codec.encode(slot.value),
                    }
                )
        if instance._interpreter is not None:
            responses = tuple(
                (key, self._codec.encode(value))
                for key, value in instance._interpreter.interaction_responses()
            )
            capability_responses = tuple(
                (key, self._codec.encode(value))
                for key, value in instance._interpreter.capability_responses()
            )
            composition_values = tuple(
                (key, self._codec.encode(value))
                for key, value in instance._interpreter.composition_values()
            )
        pending: dict[str, JSONValue] | None = None
        interaction_history: list[dict[str, JSONValue]] = []
        for interaction in instance.interactions:
            has_response = (
                interaction.kind is not InteractionKind.HANDOFF
                and interaction.status in {InteractionStatus.ANSWERED, InteractionStatus.COMPLETED}
            )
            interaction_history.append(
                {
                    "id": str(interaction.id),
                    "kind": interaction.kind.value,
                    "prompt": interaction.prompt,
                    "expected_type": self._codec.encode_type(interaction.expected_type),
                    "options": [self._codec.encode(item) for item in interaction.options],
                    "status": interaction.status.value,
                    "has_response": has_response,
                    "response": self._codec.encode(interaction.response) if has_response else None,
                }
            )
        if instance.pending_interaction is not None:
            interaction = instance.pending_interaction
            request = interaction._request
            if request is None:
                raise TaskPersistenceError(
                    "TASK_PERSISTENCE_INVALID_STATE",
                    "Pending interaction has no durable continuation.",
                )
            pending = {
                "id": str(interaction.id),
                "kind": interaction.kind.value,
                "prompt": interaction.prompt,
                "expected_type": self._codec.encode_type(interaction.expected_type),
                "options": [self._codec.encode(item) for item in interaction.options],
                "status": interaction.status.value,
                "expression_key": Interpreter.interaction_key(request.expression),
            }
        capability_bindings: tuple[dict[str, JSONValue], ...] = tuple(
            cast(
                dict[str, JSONValue],
                {
                    "capability_type": descriptor.capability_type,
                    "alias": descriptor.alias,
                    "host_binding_id": descriptor.host_binding_id,
                    "granted_operations": sorted(descriptor.granted_operations),
                },
            )
            for _, descriptor in sorted(instance.capability_bindings.items())
        )
        capability_history: list[dict[str, JSONValue]] = []
        for capability_request in instance.capability_requests:
            capability_history.append(
                {
                    "id": str(capability_request.id),
                    "alias": capability_request.alias,
                    "capability_type": capability_request.capability_type,
                    "operation": capability_request.operation,
                    "arguments": [
                        self._codec.encode(value) for value in capability_request.arguments
                    ],
                    "expected_type": self._codec.encode_type(capability_request.expected_type),
                    "status": capability_request.status.value,
                    "retry_safe": capability_request.retry_safe,
                }
            )
        pending_capability: dict[str, JSONValue] | None = None
        if instance.pending_capability_request is not None:
            capability_request = instance.pending_capability_request
            suspension = capability_request._suspension
            if suspension is None:
                raise TaskPersistenceError(
                    "TASK_PERSISTENCE_INVALID_STATE",
                    "Pending capability request has no continuation.",
                )
            pending_capability = {
                "id": str(capability_request.id),
                "alias": capability_request.alias,
                "capability_type": capability_request.capability_type,
                "operation": capability_request.operation,
                "arguments": [self._codec.encode(value) for value in capability_request.arguments],
                "expected_type": self._codec.encode_type(capability_request.expected_type),
                "status": capability_request.status.value,
                "retry_safe": capability_request.retry_safe,
                "expression_key": Interpreter.capability_key(suspension.invocation.expression),
            }
        failure: dict[str, JSONValue] | None = None
        if instance.failure is not None:
            error = instance.failure.runtime_error
            failure = {
                "code": instance.failure.code,
                "message": instance.failure.message,
                "span": {
                    "start": error.span.start.offset,
                    "end": error.span.end.offset,
                },
            }
        snapshot = TaskSnapshot(
            1,
            str(instance.id),
            self._module_identity,
            instance.definition.name,
            task_definition_fingerprint(self._program, instance.definition.name),
            instance.state.value,
            tuple(self._codec.encode(value) for value in instance.arguments),
            position,
            tuple(environment),
            tuple((step.definition.name, step.state.value) for step in instance.step_executions),
            responses,
            tuple(interaction_history),
            capability_bindings,
            capability_responses,
            tuple(capability_history),
            pending,
            pending_capability,
            self._codec.encode(instance.result) if instance.state is TaskState.COMPLETED else None,
            failure,
            instance.goal,
        )
        return TaskSnapshot(
            **{
                **snapshot.__dict__,
                "parent_task_id": None
                if instance.parent_task_id is None
                else str(instance.parent_task_id),
                "child_task_ids": tuple(str(item) for item in instance.child_task_ids),
                "waiting_on_task_id": None
                if instance.waiting_on_task_id is None
                else str(instance.waiting_on_task_id),
                "composition_values": composition_values,
                "planning_attempt": (
                    None
                    if instance.planning_attempt is None
                    else {
                        "id": str(instance.planning_attempt.id),
                        "status": instance.planning_attempt.status,
                        "purpose": instance.planning_attempt.purpose,
                        "base_revision": instance.planning_attempt.base_revision,
                        "base_fingerprint": instance.planning_attempt.base_fingerprint,
                        "reason": instance.planning_attempt.reason,
                        "resulting_revision": instance.planning_attempt.resulting_revision,
                        "resulting_fingerprint": (
                            instance.planning_attempt.resulting_fingerprint
                        ),
                        "diagnostics": [
                            getattr(item, "code", str(item))
                            for item in instance.planning_attempt.diagnostics
                        ],
                    }
                ),
                "accepted_plan_json": (
                    None
                    if instance.accepted_plan is None
                    else ast_to_json(
                        Program(
                            instance.accepted_plan.body.span,
                            instance.accepted_plan.body.statements,
                        )
                    )
                ),
                "accepted_plan_fingerprint": instance.accepted_plan_fingerprint,
                "plan_revision": instance.plan_revision,
                "planning_attempts": tuple(
                    {
                        "id": str(attempt.id),
                        "status": attempt.status,
                        "purpose": attempt.purpose,
                        "base_revision": attempt.base_revision,
                        "base_fingerprint": attempt.base_fingerprint,
                        "reason": attempt.reason,
                        "resulting_revision": attempt.resulting_revision,
                        "resulting_fingerprint": attempt.resulting_fingerprint,
                        "diagnostics": [
                            getattr(item, "code", str(item)) for item in attempt.diagnostics
                        ],
                    }
                    for attempt in instance.planning_attempts
                ),
            }
        )

    def restore_task(self, task_id: TaskId | str) -> TaskInstance:
        snapshot = self._store.load(str(task_id))
        definition = self.definition(snapshot.task_name)
        fingerprint = task_definition_fingerprint(self._program, snapshot.task_name)
        if (
            definition is None
            or snapshot.module_identity != self._module_identity
            or snapshot.task_definition_fingerprint != fingerprint
        ):
            raise TaskPersistenceError(
                "TASK_DEFINITION_MISMATCH",
                "Persisted task definition does not match the current program.",
            )
        try:
            arguments = tuple(self._codec.decode(value) for value in snapshot.inputs)
            steps_by_name = dict(snapshot.step_states)
            steps = tuple(
                StepExecution(
                    StepDefinition(statement),
                    StepState(steps_by_name.get(statement.name, StepState.PENDING.value)),
                )
                for statement in definition.declaration.body.statements
                if isinstance(statement, StepStatement)
            )
            restored_state = TaskState(snapshot.task_state)
            if restored_state is TaskState.RUNNING:
                restored_state = TaskState.READY
                for step in steps:
                    if step.state is StepState.RUNNING:
                        step.state = StepState.PENDING
            binding_descriptors: dict[str, CapabilityBindingDescriptor] = {}
            for data in snapshot.capability_bindings:
                descriptor = CapabilityBindingDescriptor(
                    str(data.get("capability_type")),
                    str(data.get("alias")),
                    str(data.get("host_binding_id")),
                    frozenset(
                        str(item)
                        for item in cast(list[JSONValue], data.get("granted_operations", []))
                    ),
                )
                if self._capability_registry.rebind(snapshot.task_id, descriptor) is None:
                    raise TaskPersistenceError(
                        "CAPABILITY_REBIND_FAILED",
                        f"Capability '{descriptor.alias}' could not be rebound.",
                    )
                binding_descriptors[descriptor.alias] = descriptor
            instance = TaskInstance(
                TaskId(snapshot.task_id),
                definition,
                arguments,
                state=restored_state,
                result=(
                    self._codec.decode(snapshot.result)
                    if restored_state is TaskState.COMPLETED
                    else None
                ),
                goal=snapshot.goal,
                step_executions=steps,
                capability_bindings=binding_descriptors,
                parent_task_id=(
                    None if snapshot.parent_task_id is None else TaskId(snapshot.parent_task_id)
                ),
                child_task_ids=[TaskId(item) for item in snapshot.child_task_ids],
                waiting_on_task_id=(
                    None
                    if snapshot.waiting_on_task_id is None
                    else TaskId(snapshot.waiting_on_task_id)
                ),
                plan_revision=snapshot.plan_revision,
            )
            self._observe_instance(instance)
            if snapshot.planning_attempt is not None:
                attempt_id = PlanningAttemptId(str(snapshot.planning_attempt.get("id")))
                restored_planner_request = PlannerRequest(
                    str(instance.id),
                    attempt_id,
                    definition.name,
                    tuple(arguments),
                    instance.goal,
                    len(definition.requirements),
                    len(definition.invariants),
                    definition.success is not None,
                    tuple(
                        (alias, tuple(sorted(binding.granted_operations)))
                        for alias, binding in sorted(binding_descriptors.items())
                    ),
                    tuple(name for name, state in snapshot.step_states if state == "completed"),
                    str(snapshot.planning_attempt.get("purpose", "initial_plan")),
                    cast(int, snapshot.planning_attempt.get("base_revision", 0)),
                    cast(str | None, snapshot.planning_attempt.get("base_fingerprint")),
                    cast(str | None, snapshot.planning_attempt.get("reason")),
                    tuple(name for name, state in snapshot.step_states if state == "pending"),
                )
                attempt = PlanningAttempt(
                    attempt_id,
                    restored_planner_request,
                    str(snapshot.planning_attempt.get("status")),
                    purpose=str(snapshot.planning_attempt.get("purpose", "initial_plan")),
                    base_revision=cast(
                        int, snapshot.planning_attempt.get("base_revision", 0)
                    ),
                    base_fingerprint=cast(
                        str | None, snapshot.planning_attempt.get("base_fingerprint")
                    ),
                    reason=cast(str | None, snapshot.planning_attempt.get("reason")),
                    resulting_revision=cast(
                        int | None, snapshot.planning_attempt.get("resulting_revision")
                    ),
                    resulting_fingerprint=cast(
                        str | None,
                        snapshot.planning_attempt.get("resulting_fingerprint"),
                    ),
                    diagnostics=tuple(
                        cast(list[object], snapshot.planning_attempt.get("diagnostics", []))
                    ),
                )
                instance.planning_attempt = attempt
            if snapshot.accepted_plan_json is not None:
                plan_program = ast_from_json(snapshot.accepted_plan_json)
                region = next(
                    item
                    for item in definition.declaration.body.statements
                    if isinstance(item, PlanRegion)
                )
                instance.accepted_plan = replace(
                    region, body=replace(region.body, statements=plan_program.statements)
                )
                instance.accepted_plan_fingerprint = snapshot.accepted_plan_fingerprint
                instance.step_executions = tuple(
                    StepExecution(
                        StepDefinition(statement),
                        StepState(steps_by_name.get(statement.name, StepState.PENDING.value)),
                    )
                    for statement in instance.accepted_plan.body.statements
                    if isinstance(statement, StepStatement)
                )
                for step in instance.step_executions:
                    self._observe_step(instance, step)
            attempts_by_id: dict[str, PlanningAttempt] = {}
            for data in snapshot.planning_attempts:
                saved_id = str(data.get("id"))
                saved_attempt = PlanningAttempt(
                    PlanningAttemptId(saved_id),
                    (
                        instance.planning_attempt.request
                        if instance.planning_attempt is not None
                        and str(instance.planning_attempt.id) == saved_id
                        else PlannerRequest(
                            str(instance.id),
                            PlanningAttemptId(saved_id),
                            definition.name,
                            tuple(arguments),
                            instance.goal,
                            len(definition.requirements),
                            len(definition.invariants),
                            definition.success is not None,
                            (),
                            (),
                            str(data.get("purpose", "initial_plan")),
                            cast(int, data.get("base_revision", 0)),
                            cast(str | None, data.get("base_fingerprint")),
                            cast(str | None, data.get("reason")),
                            (),
                        )
                    ),
                    str(data.get("status", "pending")),
                    purpose=str(data.get("purpose", "initial_plan")),
                    base_revision=cast(int, data.get("base_revision", 0)),
                    base_fingerprint=cast(str | None, data.get("base_fingerprint")),
                    reason=cast(str | None, data.get("reason")),
                    resulting_revision=cast(int | None, data.get("resulting_revision")),
                    resulting_fingerprint=cast(
                        str | None, data.get("resulting_fingerprint")
                    ),
                    diagnostics=tuple(cast(list[object], data.get("diagnostics", []))),
                )
                attempts_by_id[saved_id] = saved_attempt
            instance.planning_attempts = list(attempts_by_id.values())
            if instance.planning_attempt is not None:
                active_id = str(instance.planning_attempt.id)
                if active_id in attempts_by_id:
                    instance.planning_attempt = attempts_by_id[active_id]
                else:
                    instance.planning_attempts.append(instance.planning_attempt)
            self._prepare_instance(instance)
            context = instance._context
            interpreter = instance._interpreter
            if context is None or interpreter is None:
                raise ValueError("task could not be reconstructed")
            if instance.accepted_plan is not None:
                context.statements = tuple(
                    nested
                    for statement in context.statements
                    for nested in (
                        instance.accepted_plan.body.statements
                        if isinstance(statement, PlanRegion)
                        else (statement,)
                    )
                )
            symbol_by_id = {symbol.id: symbol for symbol in self._resolution.symbols}
            slots: list[RuntimeSlot] = []
            for encoded in snapshot.environment:
                symbol_id = encoded.get("symbol_id")
                mutable = encoded.get("mutable")
                if type(symbol_id) is not int or type(mutable) is not bool:
                    raise ValueError("invalid environment slot")
                symbol = symbol_by_id.get(symbol_id)
                if symbol is None:
                    raise ValueError(f"unknown environment symbol {symbol_id}")
                slots.append(
                    RuntimeSlot(
                        symbol,
                        self._codec.decode(encoded.get("value")),
                        mutable,
                    )
                )
            if snapshot.task_state != TaskState.CREATED.value:
                context.environment.replace_local_slots(tuple(slots))
            context.next_statement = snapshot.execution_position
            interpreter.restore_interaction_responses(
                tuple(
                    (key, self._codec.decode(value))
                    for key, value in snapshot.interaction_responses
                )
            )
            interpreter.restore_capability_responses(
                tuple(
                    (key, self._codec.decode(value)) for key, value in snapshot.capability_responses
                )
            )
            interpreter.restore_composition_values(
                tuple(
                    (key, self._codec.decode(value)) for key, value in snapshot.composition_values
                )
            )
            interactions_by_id: dict[str, HumanInteraction] = {}
            for data in snapshot.interactions:
                expected = self._codec.decode_type(data.get("expected_type"))
                options = tuple(
                    self._codec.decode(value)
                    for value in cast(list[JSONValue], data.get("options", []))
                )
                response: RuntimeValue = None
                if data.get("has_response") is True:
                    response = self._codec.decode(data.get("response"))
                interaction = HumanInteraction(
                    InteractionId(str(data.get("id"))),
                    instance.id,
                    InteractionKind(str(data.get("kind"))),
                    str(data.get("prompt")),
                    expected,
                    options,
                    InteractionStatus(str(data.get("status"))),
                    response,
                )
                instance.interactions.append(interaction)
                interactions_by_id[str(interaction.id)] = interaction
            if snapshot.failure is not None:
                code = str(snapshot.failure.get("code"))
                message = str(snapshot.failure.get("message"))
                instance.failure = TaskFailure(
                    code,
                    message,
                    RuntimeErrorInfo(code, message, definition.declaration.span),
                )
            if snapshot.pending_interaction is not None:
                data = snapshot.pending_interaction
                expression_key = str(data.get("expression_key"))
                expression = _find_interaction_expression(
                    context.statements[context.next_statement], expression_key
                )
                if expression is None:
                    raise ValueError("interaction continuation was not found")
                expected = self._codec.decode_type(data.get("expected_type"))
                options = tuple(
                    self._codec.decode(value)
                    for value in cast(list[JSONValue], data.get("options", []))
                )
                request = InteractionRequest(expression, str(data.get("prompt")), expected, options)
                pending_interaction = interactions_by_id.get(str(data.get("id")))
                if pending_interaction is None:
                    pending_interaction = HumanInteraction(
                        InteractionId(str(data.get("id"))),
                        instance.id,
                        InteractionKind(str(data.get("kind"))),
                        request.prompt,
                        expected,
                        options,
                        InteractionStatus(str(data.get("status"))),
                    )
                    instance.interactions.append(pending_interaction)
                pending_interaction._request = request
                instance.pending_interaction = pending_interaction
            capability_requests_by_id: dict[str, CapabilityRequest] = {}
            for data in snapshot.capability_requests:
                capability_request = CapabilityRequest(
                    CapabilityRequestId(str(data.get("id"))),
                    instance.id,
                    str(data.get("alias")),
                    str(data.get("capability_type")),
                    str(data.get("operation")),
                    tuple(
                        self._codec.decode(value)
                        for value in cast(list[JSONValue], data.get("arguments", []))
                    ),
                    self._codec.decode_type(data.get("expected_type")),
                    CapabilityRequestStatus(str(data.get("status"))),
                    data.get("retry_safe") is True,
                )
                instance.capability_requests.append(capability_request)
                capability_requests_by_id[str(capability_request.id)] = capability_request
            if snapshot.pending_capability_request is not None:
                data = snapshot.pending_capability_request
                expression_key = str(data.get("expression_key"))
                capability_expression = _find_capability_expression(
                    context.statements[context.next_statement], expression_key
                )
                if capability_expression is None:
                    raise ValueError("capability continuation was not found")
                expected = self._codec.decode_type(data.get("expected_type"))
                arguments = tuple(
                    self._codec.decode(value)
                    for value in cast(list[JSONValue], data.get("arguments", []))
                )
                invocation = CapabilityInvocation(
                    capability_expression,
                    str(data.get("alias")),
                    str(data.get("operation")),
                    arguments,
                    expected,
                )
                suspension = CapabilitySuspension(
                    invocation,
                    CapabilityInvocationResult(
                        True,
                        request_id=str(data.get("id")),
                        retry_safe=data.get("retry_safe") is True,
                    ),
                )
                restored_pending = capability_requests_by_id.get(str(data.get("id")))
                if restored_pending is None:
                    restored_pending = CapabilityRequest(
                        CapabilityRequestId(str(data.get("id"))),
                        instance.id,
                        invocation.alias,
                        str(data.get("capability_type")),
                        invocation.operation,
                        arguments,
                        expected,
                        retry_safe=suspension.result.retry_safe,
                    )
                    instance.capability_requests.append(restored_pending)
                restored_pending.status = CapabilityRequestStatus.INDETERMINATE
                restored_pending._suspension = suspension
                instance.pending_capability_request = restored_pending
            self._instances[str(instance.id)] = instance
            return instance
        except TaskPersistenceError:
            raise
        except (KeyError, ValueError, TypeError, IndexError) as error:
            raise TaskPersistenceError(
                "TASK_PERSISTENCE_INVALID_STATE",
                f"Task snapshot cannot be restored: {error}.",
            ) from None

    def _save_snapshot(self, instance: TaskInstance) -> None:
        self._store.save(self.snapshot(instance))

    def _prepare_instance(self, instance: TaskInstance) -> None:
        if instance._interpreter is not None:
            return
        instance._interpreter = Interpreter(
            self._resolution,
            self._types,
            output=self._output,
            imported_modules=self._imported_modules,
            capability_invoker=lambda invocation: self._invoke_capability(instance, invocation),
            task_starter=lambda expression, arguments: self._start_child(
                instance, expression, arguments
            ),
            task_awaiter=lambda handle: self._await_child(instance, handle),
        )
        context, error = instance._interpreter.prepare_task(
            self._program, instance.definition.declaration, instance.arguments
        )
        if error is not None:
            instance.failure = TaskFailure(error.code, error.message, error)
            instance._transition(TaskState.FAILED)
            return
        if context is None:
            raise RuntimeError("task preparation omitted context without an error")
        instance._context = context

    def get_pending_capability_request(self, task_id: TaskId | str) -> CapabilityRequest | None:
        instance = self._instances.get(str(task_id))
        return None if instance is None else instance.pending_capability_request

    def complete_capability_request(
        self,
        task_id: TaskId | str,
        request_id: CapabilityRequestId | str,
        result: object,
    ) -> TaskInstance:
        instance, request = self._active_capability_request(task_id, request_id)
        if request.status is CapabilityRequestStatus.INDETERMINATE:
            raise TaskStartError(
                "CAPABILITY_REQUEST_INDETERMINATE",
                "Crash-time capability outcome must be explicitly reconciled.",
            )
        converted = _validate_argument(result, request.expected_type)
        if converted is _INVALID:
            raise TaskStartError(
                "CAPABILITY_RETURN_MISMATCH",
                "Capability result does not match the declared return type.",
            )
        interpreter = instance._interpreter
        suspension = request._suspension
        if interpreter is None or suspension is None:
            raise TaskStartError(
                "CAPABILITY_REQUEST_INDETERMINATE",
                "Capability continuation is indeterminate and requires reconciliation.",
            )
        canonical = cast(RuntimeValue, converted)
        interpreter.supply_capability_response(suspension.invocation.expression, canonical)
        request.status = CapabilityRequestStatus.COMPLETED
        instance.pending_capability_request = None
        self._emit(
            "capability_completed",
            instance,
            request_id=str(request.id),
            operation=request.operation,
        )
        instance._transition(TaskState.RUNNING)
        return self._continue_task(instance)

    def reconcile_capability_request(
        self,
        task_id: TaskId | str,
        request_id: CapabilityRequestId | str,
        result: object,
    ) -> TaskInstance:
        _, request = self._active_capability_request(task_id, request_id)
        if request.status is not CapabilityRequestStatus.INDETERMINATE:
            raise TaskStartError(
                "CAPABILITY_REQUEST_STALE",
                "Only an indeterminate request may be reconciled.",
            )
        request.status = CapabilityRequestStatus.PENDING
        return self.complete_capability_request(task_id, request_id, result)

    def fail_capability_request(
        self,
        task_id: TaskId | str,
        request_id: CapabilityRequestId | str,
        message: str,
    ) -> TaskInstance:
        instance, request = self._active_capability_request(task_id, request_id)
        request.status = CapabilityRequestStatus.FAILED
        instance.pending_capability_request = None
        error = RuntimeErrorInfo(
            "CAPABILITY_HOST_FAILURE", message, instance.definition.declaration.span
        )
        instance.failure = TaskFailure(error.code, error.message, error)
        instance._transition(TaskState.FAILED)
        self._save_snapshot(instance)
        self._cancel_descendants(instance)
        self._wake_parent(instance)
        return instance

    def _active_capability_request(
        self,
        task_id: TaskId | str,
        request_id: CapabilityRequestId | str,
    ) -> tuple[TaskInstance, CapabilityRequest]:
        instance = self._instances.get(str(task_id))
        if instance is None:
            raise TaskStartError(
                "CAPABILITY_REQUEST_NOT_FOUND", "Capability request was not found."
            )
        request = instance.pending_capability_request
        if request is None:
            known = next(
                (item for item in instance.capability_requests if str(item.id) == str(request_id)),
                None,
            )
            code = (
                "CAPABILITY_REQUEST_ALREADY_COMPLETED"
                if known is not None
                else "CAPABILITY_REQUEST_NOT_FOUND"
            )
            raise TaskStartError(code, "Capability request is not active.")
        if str(request.id) != str(request_id):
            raise TaskStartError("CAPABILITY_REQUEST_STALE", "Capability request ID is stale.")
        return instance, request

    def _invoke_capability(
        self, instance: TaskInstance, invocation: CapabilityInvocation
    ) -> CapabilityInvocationResult:
        binding = self._capability_registry.resolve(str(instance.id), invocation.alias)
        if binding is None:
            raise RuntimeFailure(
                RuntimeErrorInfo(
                    "CAPABILITY_NOT_PROVIDED",
                    f"Capability alias '{invocation.alias}' is not bound.",
                    invocation.expression.span,
                )
            )
        if invocation.operation not in binding.descriptor.granted_operations:
            raise RuntimeFailure(
                RuntimeErrorInfo(
                    "CAPABILITY_OPERATION_DENIED",
                    f"Operation '{invocation.operation}' is not granted.",
                    invocation.expression.span,
                )
            )
        request_id = CapabilityRequestId(str(uuid4()))
        try:
            result = binding.adapter.invoke(request_id, invocation.operation, invocation.arguments)
        except (RuntimeError, ValueError, TypeError, OSError) as error:
            raise RuntimeFailure(
                RuntimeErrorInfo(
                    "CAPABILITY_HOST_FAILURE",
                    f"Capability adapter failed: {error}",
                    invocation.expression.span,
                )
            ) from None
        if result.is_pending:
            return CapabilityInvocationResult(
                True, request_id=str(request_id), retry_safe=result.retry_safe
            )
        converted = _validate_argument(result.value, invocation.expected_type)
        if converted is _INVALID:
            raise RuntimeFailure(
                RuntimeErrorInfo(
                    "CAPABILITY_RETURN_MISMATCH",
                    "Capability result does not match the declared return type.",
                    invocation.expression.span,
                )
            )
        return CapabilityInvocationResult(False, cast(RuntimeValue, converted))

    def _capability_requirements(
        self, instance: TaskInstance
    ) -> tuple[UseCapabilityDeclaration, ...]:
        return tuple(
            item
            for item in instance.definition.declaration.body.statements
            if isinstance(item, UseCapabilityDeclaration)
        )

    def task(self, task_id: TaskId | str) -> TaskInstance | None:
        return self._instances.get(str(task_id))

    def _start_child(
        self,
        parent: TaskInstance,
        expression: StartTaskExpression,
        arguments: tuple[RuntimeValue, ...],
    ) -> KajTaskHandle:
        child = self.create_task(expression.task_name, arguments)
        child.parent_task_id = parent.id
        parent.child_task_ids.append(child.id)
        self._emit("child_started", parent, child_task_id=str(child.id))
        if self._child_capability_binder is not None:
            self._child_capability_binder(self, child)
        self._save_snapshot(parent)
        self.run_task(child)
        return KajTaskHandle(str(child.id), child.definition.signature.return_type)

    def _await_child(
        self, parent: TaskInstance, handle: KajTaskHandle
    ) -> tuple[bool, RuntimeValue]:
        child = self._instances.get(handle.task_id)
        if child is None or child.parent_task_id != parent.id:
            raise RuntimeFailure(
                RuntimeErrorInfo(
                    "TASK_CHILD_NOT_FOUND",
                    f"Child task '{handle.task_id}' was not found.",
                    parent.definition.declaration.span,
                )
            )
        if child.state is TaskState.COMPLETED:
            return True, child.result
        if child.state is TaskState.FAILED:
            raise RuntimeFailure(
                RuntimeErrorInfo(
                    "TASK_CHILD_FAILED",
                    f"Child task '{child.definition.name}' failed: "
                    f"{child.failure.message if child.failure else 'unknown failure'}",
                    parent.definition.declaration.span,
                )
            )
        if child.state is TaskState.CANCELLED:
            raise RuntimeFailure(
                RuntimeErrorInfo(
                    "TASK_CHILD_CANCELLED",
                    f"Child task '{child.definition.name}' was cancelled.",
                    parent.definition.declaration.span,
                )
            )
        return False, None

    def _wake_parent(self, child: TaskInstance) -> None:
        if child.parent_task_id is None:
            return
        parent = self._instances.get(str(child.parent_task_id))
        if (
            parent is None
            or parent.state is not TaskState.WAITING_FOR_TASK
            or parent.waiting_on_task_id != child.id
        ):
            return
        parent.waiting_on_task_id = None
        parent._transition(TaskState.RUNNING)
        self._continue_task(parent)

    def _cancel_descendants(self, instance: TaskInstance) -> None:
        for child_id in instance.child_task_ids:
            child = self._instances.get(str(child_id))
            if child is None or child.state in {
                TaskState.COMPLETED,
                TaskState.FAILED,
                TaskState.CANCELLED,
            }:
                continue
            self._cancel_descendants(child)
            child.state = TaskState.CANCELLED
            self._save_snapshot(child)

    def _evaluate_bool_contract(
        self,
        instance: TaskInstance,
        clause: RequireClause | InvariantClause | SuccessClause,
        expression: Expression,
        *,
        result: RuntimeValue = None,
    ) -> bool | None:
        interpreter = instance._interpreter
        context = instance._context
        if interpreter is None or context is None:
            raise RuntimeError("contract evaluation requires a prepared task")
        if isinstance(clause, SuccessClause):
            value, error = interpreter.evaluate_contract(
                context,
                clause.condition,
                parameter=clause.parameter,
                value=result,
            )
        else:
            value, error = interpreter.evaluate_contract(context, clause.condition)
        if error is not None:
            self._fail_contract_evaluation(instance, clause, error)
            return None
        if type(value) is not bool:
            self._fail_contract_evaluation(
                instance,
                clause,
                RuntimeErrorInfo(
                    "RUNTIME_INTERNAL_ERROR",
                    "Contract condition did not evaluate to Bool.",
                    clause.span,
                ),
            )
            return None
        return value

    def _evaluate_invariants(self, instance: TaskInstance) -> bool:
        for invariant in instance.definition.invariants:
            passed = self._evaluate_bool_contract(instance, invariant, invariant.condition)
            if passed is None:
                return False
            if not passed:
                self._fail_contract(
                    instance,
                    "TASK_INVARIANT_VIOLATED",
                    "Task invariant evaluated to false.",
                    ContractFailureKind.INVARIANT_VIOLATION,
                    invariant,
                )
                return False
        return True

    def _evaluate_success(self, instance: TaskInstance, result: RuntimeValue) -> bool:
        success = instance.definition.success
        if success is None:
            return True
        passed = self._evaluate_bool_contract(instance, success, success.condition, result=result)
        if passed is None:
            return False
        if not passed:
            self._fail_contract(
                instance,
                "TASK_SUCCESS_NOT_SATISFIED",
                "Task success condition evaluated to false.",
                ContractFailureKind.SUCCESS_NOT_SATISFIED,
                success,
            )
            return False
        return True

    def _fail_contract_evaluation(
        self,
        instance: TaskInstance,
        clause: GoalClause | RequireClause | InvariantClause | SuccessClause,
        underlying: RuntimeErrorInfo,
    ) -> None:
        self._fail_contract(
            instance,
            "TASK_CONTRACT_EVALUATION_FAILED",
            f"Contract evaluation failed: {underlying.message}",
            ContractFailureKind.EVALUATION_FAILURE,
            clause,
            underlying,
        )

    def _fail_contract(
        self,
        instance: TaskInstance,
        code: str,
        message: str,
        kind: ContractFailureKind,
        clause: GoalClause | RequireClause | InvariantClause | SuccessClause,
        underlying: RuntimeErrorInfo | None = None,
    ) -> None:
        error = RuntimeErrorInfo(code, message, clause.span)
        instance.failure = TaskFailure(
            code,
            message,
            error,
            ContractFailure(kind, clause, underlying),
        )
        instance._transition(TaskState.FAILED)
        self._save_snapshot(instance)


_INVALID = object()


def _find_interaction_expression(value: object, key: str) -> HumanInteractionExpression | None:
    if isinstance(value, HumanInteractionExpression) and Interpreter.interaction_key(value) == key:
        return value
    if isinstance(value, (tuple, list)):
        for item in value:
            found = _find_interaction_expression(item, key)
            if found is not None:
                return found
    elif is_dataclass(value) and not isinstance(value, type):
        for descriptor in fields(value):
            found = _find_interaction_expression(getattr(value, descriptor.name), key)
            if found is not None:
                return found
    return None


def _find_capability_expression(value: object, key: str) -> CallExpression | None:
    if isinstance(value, CallExpression) and Interpreter.capability_key(value) == key:
        return value
    if isinstance(value, (tuple, list)):
        for item in value:
            found = _find_capability_expression(item, key)
            if found is not None:
                return found
    elif is_dataclass(value) and not isinstance(value, type):
        for descriptor in fields(value):
            found = _find_capability_expression(getattr(value, descriptor.name), key)
            if found is not None:
                return found
    return None


def _walk_nodes(value: object) -> tuple[object, ...]:
    result: list[object] = [value]
    if isinstance(value, (tuple, list)):
        for item in value:
            result.extend(_walk_nodes(item))
    elif is_dataclass(value) and not isinstance(value, type):
        for descriptor in fields(value):
            if descriptor.name != "span":
                result.extend(_walk_nodes(getattr(value, descriptor.name)))
    return tuple(result)


def _validate_argument(value: object, expected: ValueType) -> RuntimeValue | object:
    if expected is PrimitiveType.BOOL:
        return value if type(value) is bool else _INVALID
    if expected is PrimitiveType.INT:
        return value if type(value) is int else _INVALID
    if expected is PrimitiveType.DECIMAL:
        if type(value) is int:
            return Decimal(value)
        return value if isinstance(value, Decimal) else _INVALID
    if expected is PrimitiveType.STRING:
        return value if isinstance(value, str) else _INVALID
    if expected is PrimitiveType.BYTES:
        return value if isinstance(value, bytes) else _INVALID
    if expected is PrimitiveType.NONE:
        return value if value is None else _INVALID
    if expected is PrimitiveType.ERROR:
        return _INVALID
    if isinstance(expected, ListType):
        elements = (
            value.elements
            if isinstance(value, KajList)
            else tuple(value)
            if isinstance(value, (list, tuple))
            else None
        )
        if elements is None:
            return _INVALID
        converted = tuple(_validate_argument(item, expected.element_type) for item in elements)
        if any(item is _INVALID for item in converted):
            return _INVALID
        return KajList(tuple(cast(RuntimeValue, item) for item in converted))
    if isinstance(expected, MapType):
        return value if isinstance(value, KajMap) and value.type == expected else _INVALID
    if isinstance(expected, RecordType):
        return value if isinstance(value, KajRecord) and value.type == expected else _INVALID
    if isinstance(expected, NewtypeType):
        return value if isinstance(value, KajNewtypeValue) and value.type == expected else _INVALID
    if isinstance(expected, (EnumType, OptionalType, ResultType)):
        return value if isinstance(value, KajEnumValue) and value.type == expected else _INVALID
    return _INVALID
