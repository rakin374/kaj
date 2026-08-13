from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from decimal import Decimal, DecimalException, localcontext
from typing import Never, cast

from kaj.ast import (
    AssignmentOperator,
    AssignmentStatement,
    AwaitTaskExpression,
    BinaryExpression,
    BinaryOperator,
    BindingDeclaration,
    BindingKind,
    Block,
    BooleanLiteral,
    BreakStatement,
    CallExpression,
    CapabilityDeclaration,
    ContinueStatement,
    DecimalLiteral,
    EnumConstructionExpression,
    EnumDeclaration,
    Expression,
    ExpressionStatement,
    ForStatement,
    FunctionDeclaration,
    GoalClause,
    HumanInteractionExpression,
    Identifier,
    IfStatement,
    ImportDeclaration,
    IndexExpression,
    IntegerLiteral,
    InterpolatedString,
    InvariantClause,
    ListLiteral,
    MapLiteral,
    MatchStatement,
    MemberAccessExpression,
    NewtypeDeclaration,
    NoneLiteral,
    PlanRegion,
    Program,
    RecordConstructionExpression,
    RecordDeclaration,
    RequireClause,
    ReturnStatement,
    StartTaskExpression,
    Statement,
    StepStatement,
    StringLiteral,
    SuccessClause,
    SuccessParameter,
    TaskDeclaration,
    UnaryExpression,
    UnaryOperator,
    UseCapabilityDeclaration,
    WhileStatement,
)
from kaj.runtime.environment import Environment
from kaj.runtime.errors import RuntimeErrorInfo, RuntimeFailure
from kaj.runtime.output import BufferOutput, RuntimeOutput
from kaj.runtime.values import (
    BuiltinFunction,
    KajEnumValue,
    KajFunction,
    KajList,
    KajMap,
    KajMapEntry,
    KajMapKey,
    KajModuleValue,
    KajNewtypeValue,
    KajRange,
    KajRecord,
    KajTaskHandle,
    RuntimeValue,
    decode_utf8,
)
from kaj.semantic import (
    EnumType,
    FunctionType,
    ListType,
    MapType,
    NewtypeType,
    OptionalType,
    PrimitiveType,
    RecordType,
    ResolutionResult,
    ResultType,
    SemanticType,
    Symbol,
    SymbolKind,
    TaskType,
    TypeCheckResult,
    ValueType,
)
from kaj.source import SourceSpan


@dataclass(frozen=True)
class ExecutionResult:
    value: RuntimeValue
    output: str
    runtime_error: RuntimeErrorInfo | None
    exports: tuple[tuple[str, RuntimeValue], ...] = ()


@dataclass
class TaskExecutionContext:
    declaration: TaskDeclaration
    signature: TaskType
    environment: Environment
    statements: tuple[Statement, ...]
    next_statement: int = 0


@dataclass(frozen=True)
class TaskExecutionOutcome:
    statement: Statement | None
    returned: bool
    value: RuntimeValue
    runtime_error: RuntimeErrorInfo | None
    interaction: InteractionRequest | None = None
    capability: CapabilitySuspension | None = None
    task_await: TaskAwaitSuspension | None = None


@dataclass(frozen=True)
class InteractionRequest:
    expression: HumanInteractionExpression
    prompt: str
    expected_type: ValueType
    options: tuple[RuntimeValue, ...] = ()


@dataclass(frozen=True)
class CapabilityInvocation:
    expression: CallExpression
    alias: str
    operation: str
    arguments: tuple[RuntimeValue, ...]
    expected_type: ValueType


@dataclass(frozen=True)
class CapabilityInvocationResult:
    pending: bool
    value: RuntimeValue = None
    request_id: str | None = None
    retry_safe: bool = False


@dataclass(frozen=True)
class CapabilitySuspension:
    invocation: CapabilityInvocation
    result: CapabilityInvocationResult


@dataclass(frozen=True)
class TaskAwaitSuspension:
    expression: AwaitTaskExpression
    handle: KajTaskHandle


class _HumanInteractionSignal(Exception):
    def __init__(self, request: InteractionRequest) -> None:
        self.request = request


class _CapabilitySignal(Exception):
    def __init__(self, suspension: CapabilitySuspension) -> None:
        self.suspension = suspension


class _TaskAwaitSignal(Exception):
    def __init__(self, suspension: TaskAwaitSuspension) -> None:
        self.suspension = suspension


class _ReturnSignal(Exception):
    def __init__(self, value: RuntimeValue, source_type: SemanticType) -> None:
        self.value = value
        self.source_type = source_type


class _BreakSignal(Exception):
    pass


class _ContinueSignal(Exception):
    pass


_NO_INTERACTION_RESPONSE = object()


class Interpreter:
    def __init__(
        self,
        resolution: ResolutionResult,
        types: TypeCheckResult,
        *,
        output: RuntimeOutput | None = None,
        imported_modules: dict[int, KajModuleValue] | None = None,
        capability_invoker: Callable[[CapabilityInvocation], CapabilityInvocationResult]
        | None = None,
        task_starter: Callable[[StartTaskExpression, tuple[RuntimeValue, ...]], KajTaskHandle]
        | None = None,
        task_awaiter: Callable[[KajTaskHandle], tuple[bool, RuntimeValue]] | None = None,
    ) -> None:
        self._resolution = resolution
        self._types = types
        self._output = BufferOutput() if output is None else output
        self._captured_lines: list[str] = []
        self._imported_modules = {} if imported_modules is None else imported_modules
        self._interaction_responses: dict[str, RuntimeValue] = {}
        self.inform_events: list[str] = []
        self._transaction_lines: list[str] | None = None
        self._capability_invoker = capability_invoker
        self._capability_responses: dict[str, RuntimeValue] = {}
        self._task_starter = task_starter
        self._task_awaiter = task_awaiter
        self._composition_values: dict[str, RuntimeValue] = {}

    def interpret(self, program: Program) -> ExecutionResult:
        self._captured_lines = []
        builtin_environment = Environment()
        module_environment = Environment(builtin_environment)
        try:
            self._install_builtins(builtin_environment)
            for statement in program.statements:
                if isinstance(statement, ImportDeclaration):
                    symbol = self._resolution.symbol_for_declaration(statement)
                    value = self._imported_modules.get(id(statement))
                    if symbol is not None and value is not None:
                        module_environment.define(symbol, value, mutable=False)
            self._install_functions(program, module_environment)
            for statement in program.statements:
                if not isinstance(
                    statement,
                    (
                        FunctionDeclaration,
                        TaskDeclaration,
                        RecordDeclaration,
                        EnumDeclaration,
                        NewtypeDeclaration,
                        ImportDeclaration,
                    ),
                ):
                    self._execute_statement(statement, module_environment)
        except RuntimeFailure as failure:
            return ExecutionResult(None, self._captured_output(), failure.error)
        except (KeyError, PermissionError, TypeError, ValueError, ArithmeticError) as error:
            return ExecutionResult(
                None,
                self._captured_output(),
                RuntimeErrorInfo(
                    "RUNTIME_INTERNAL_ERROR",
                    f"Invalid interpreter state: {error}",
                    program.span,
                ),
            )
        exports: list[tuple[str, RuntimeValue]] = []
        for name, symbol in self._resolution.module_scope.symbols.items():
            if symbol.kind in {
                SymbolKind.FUNCTION,
                SymbolKind.LET_BINDING,
                SymbolKind.VAR_BINDING,
            }:
                try:
                    exports.append((name, module_environment.read(symbol)))
                except KeyError:
                    pass
        return ExecutionResult(None, self._captured_output(), None, tuple(exports))

    def execute_task(
        self,
        program: Program,
        declaration: TaskDeclaration,
        arguments: tuple[RuntimeValue, ...],
    ) -> ExecutionResult:
        """Initialize a module and synchronously execute one host-selected task."""
        context, error = self.prepare_task(program, declaration, arguments)
        if error is not None:
            return ExecutionResult(None, self._captured_output(), error)
        if context is None:
            raise RuntimeError("task preparation omitted context without an error")
        while True:
            outcome = self.execute_task_next(context)
            if outcome.runtime_error is not None:
                return ExecutionResult(None, self._captured_output(), outcome.runtime_error)
            if outcome.returned:
                return ExecutionResult(outcome.value, self._captured_output(), None)

    def prepare_task(
        self,
        program: Program,
        declaration: TaskDeclaration,
        arguments: tuple[RuntimeValue, ...],
    ) -> tuple[TaskExecutionContext | None, RuntimeErrorInfo | None]:
        self._captured_lines = []
        builtin_environment = Environment()
        module_environment = Environment(builtin_environment)
        try:
            self._install_builtins(builtin_environment)
            for statement in program.statements:
                if isinstance(statement, ImportDeclaration):
                    symbol = self._resolution.symbol_for_declaration(statement)
                    value = self._imported_modules.get(id(statement))
                    if symbol is not None and value is not None:
                        module_environment.define(symbol, value, mutable=False)
            self._install_functions(program, module_environment)
            for statement in program.statements:
                if not isinstance(
                    statement,
                    (
                        FunctionDeclaration,
                        TaskDeclaration,
                        RecordDeclaration,
                        EnumDeclaration,
                        NewtypeDeclaration,
                        ImportDeclaration,
                    ),
                ):
                    self._execute_statement(statement, module_environment)

            symbol = self._resolution.symbol_for_declaration(declaration)
            signature = None if symbol is None else self._types.type_of_symbol(symbol)
            if not isinstance(signature, TaskType):
                self._fail("RUNTIME_INTERNAL_ERROR", "Task has no signature.", declaration.span)
            task_environment = Environment(module_environment)
            for parameter, descriptor, argument_value in zip(
                declaration.parameters, signature.parameters, arguments, strict=True
            ):
                parameter_symbol = self._resolution.symbol_for_declaration(parameter)
                if parameter_symbol is None:
                    self._fail(
                        "RUNTIME_INTERNAL_ERROR", "Task parameter has no symbol.", parameter.span
                    )
                task_environment.define(
                    parameter_symbol, argument_value, mutable=descriptor.mutable
                )
            executable_statements: list[Statement] = []
            normal_execution_started = False
            for statement in declaration.body.statements:
                if isinstance(
                    statement, (GoalClause, RequireClause, InvariantClause, SuccessClause)
                ):
                    continue
                if (
                    not normal_execution_started
                    and isinstance(statement, BindingDeclaration)
                    and not isinstance(statement.initializer, HumanInteractionExpression)
                ):
                    self._execute_statement(statement, task_environment)
                    continue
                normal_execution_started = True
                executable_statements.append(statement)
            return (
                TaskExecutionContext(
                    declaration,
                    signature,
                    task_environment,
                    tuple(executable_statements),
                ),
                None,
            )
        except RuntimeFailure as failure:
            return None, failure.error
        except (KeyError, PermissionError, TypeError, ValueError, ArithmeticError) as error:
            return None, RuntimeErrorInfo(
                "RUNTIME_INTERNAL_ERROR",
                f"Invalid interpreter state: {error}",
                declaration.span,
            )

    def execute_task_next(self, context: TaskExecutionContext) -> TaskExecutionOutcome:
        statements = context.statements
        if context.next_statement >= len(statements):
            return TaskExecutionOutcome(None, True, None, None)
        statement = statements[context.next_statement]
        context.next_statement += 1
        environment_snapshot = context.environment.snapshot()
        inform_count = len(self.inform_events)
        self._transaction_lines = []
        try:
            self._execute_statement(statement, context.environment)
            self._commit_transaction()
            return TaskExecutionOutcome(statement, False, None, None)
        except _ReturnSignal as returned:
            self._commit_transaction()
            try:
                result_value = self._coerce(
                    returned.value,
                    returned.source_type,
                    context.signature.return_type,
                    context.declaration.span,
                )
            except RuntimeFailure as failure:
                return TaskExecutionOutcome(statement, False, None, failure.error)
            return TaskExecutionOutcome(statement, True, result_value, None)
        except RuntimeFailure as failure:
            self._commit_transaction()
            return TaskExecutionOutcome(statement, False, None, failure.error)
        except _HumanInteractionSignal as signal:
            context.next_statement -= 1
            Environment.restore(environment_snapshot)
            del self.inform_events[inform_count:]
            self._transaction_lines = None
            return TaskExecutionOutcome(statement, False, None, None, signal.request)
        except _CapabilitySignal as signal:
            context.next_statement -= 1
            Environment.restore(environment_snapshot)
            del self.inform_events[inform_count:]
            self._transaction_lines = None
            return TaskExecutionOutcome(
                statement,
                False,
                None,
                None,
                capability=signal.suspension,
            )
        except _TaskAwaitSignal as signal:
            context.next_statement -= 1
            Environment.restore(environment_snapshot)
            del self.inform_events[inform_count:]
            self._transaction_lines = None
            return TaskExecutionOutcome(statement, False, None, None, task_await=signal.suspension)
        except (KeyError, PermissionError, TypeError, ValueError, ArithmeticError) as error:
            self._commit_transaction()
            return TaskExecutionOutcome(
                statement,
                False,
                None,
                RuntimeErrorInfo(
                    "RUNTIME_INTERNAL_ERROR",
                    f"Invalid interpreter state: {error}",
                    statement.span,
                ),
            )

    def supply_interaction_response(
        self, expression: HumanInteractionExpression, value: RuntimeValue
    ) -> None:
        self._interaction_responses[self.interaction_key(expression)] = value

    @staticmethod
    def interaction_key(expression: HumanInteractionExpression) -> str:
        span = expression.span
        return f"{span.start.offset}:{span.end.offset}:{expression.kind}"

    def interaction_responses(self) -> tuple[tuple[str, RuntimeValue], ...]:
        return tuple(sorted(self._interaction_responses.items()))

    def restore_interaction_responses(
        self, responses: tuple[tuple[str, RuntimeValue], ...]
    ) -> None:
        self._interaction_responses = dict(responses)

    @staticmethod
    def capability_key(expression: CallExpression) -> str:
        span = expression.span
        return f"{span.start.offset}:{span.end.offset}:capability"

    def supply_capability_response(self, expression: CallExpression, value: RuntimeValue) -> None:
        self._capability_responses[self.capability_key(expression)] = value

    def capability_responses(self) -> tuple[tuple[str, RuntimeValue], ...]:
        return tuple(sorted(self._capability_responses.items()))

    def restore_capability_responses(self, responses: tuple[tuple[str, RuntimeValue], ...]) -> None:
        self._capability_responses = dict(responses)

    @staticmethod
    def composition_key(expression: Expression) -> str:
        return f"{expression.span.start.offset}:{expression.span.end.offset}:composition"

    def composition_values(self) -> tuple[tuple[str, RuntimeValue], ...]:
        return tuple(sorted(self._composition_values.items()))

    def restore_composition_values(self, values: tuple[tuple[str, RuntimeValue], ...]) -> None:
        self._composition_values = dict(values)

    def evaluate_contract(
        self,
        context: TaskExecutionContext,
        expression: Expression,
        *,
        parameter: SuccessParameter | None = None,
        value: RuntimeValue = None,
    ) -> tuple[RuntimeValue, RuntimeErrorInfo | None]:
        environment = context.environment
        try:
            if parameter is not None:
                environment = Environment(environment)
                symbol = self._resolution.symbol_for_declaration(parameter)
                if symbol is None:
                    self._fail(
                        "RUNTIME_INTERNAL_ERROR",
                        "Success parameter has no symbol.",
                        parameter.span,
                    )
                environment.define(symbol, value, mutable=False)
            return self._evaluate(expression, environment), None
        except RuntimeFailure as failure:
            return None, failure.error
        except (KeyError, PermissionError, TypeError, ValueError, ArithmeticError) as error:
            return None, RuntimeErrorInfo(
                "RUNTIME_INTERNAL_ERROR",
                f"Invalid contract evaluation state: {error}",
                expression.span,
            )

    def _captured_output(self) -> str:
        return "".join(line + "\n" for line in self._captured_lines)

    def _emit(self, text: str) -> None:
        if self._transaction_lines is not None:
            self._transaction_lines.append(text)
            return
        self._captured_lines.append(text)
        self._output.write_line(text)

    def _commit_transaction(self) -> None:
        lines = self._transaction_lines
        self._transaction_lines = None
        if lines is None:
            return
        for line in lines:
            self._captured_lines.append(line)
            self._output.write_line(line)

    def _install_builtins(self, environment: Environment) -> None:
        builtins = {
            "print": BuiltinFunction.PRINT,
            "range": BuiltinFunction.RANGE,
            "String": BuiltinFunction.STRING,
            "utf8_encode": BuiltinFunction.UTF8_ENCODE,
            "utf8_decode": BuiltinFunction.UTF8_DECODE,
        }
        for symbol in self._resolution.symbols:
            if symbol.kind is SymbolKind.BUILTIN_FUNCTION and symbol.name in builtins:
                environment.define(symbol, builtins[symbol.name], mutable=False)

    def _install_functions(self, program: Program, environment: Environment) -> None:
        for statement in program.statements:
            if not isinstance(statement, FunctionDeclaration):
                continue
            symbol = self._resolution.symbol_for_declaration(statement)
            if symbol is None:
                continue
            signature = self._types.type_of_symbol(symbol)
            if not isinstance(signature, FunctionType):
                self._fail("RUNTIME_INTERNAL_ERROR", "Function has no signature.", statement.span)
            environment.define(
                symbol,
                KajFunction(
                    statement,
                    symbol,
                    signature,
                    environment,
                    self._resolution,
                    self._types,
                ),
                mutable=False,
            )

    def _execute_statement(self, statement: Statement, environment: Environment) -> None:
        if isinstance(statement, BindingDeclaration):
            value = self._evaluate(statement.initializer, environment)
            symbol = self._resolution.symbol_for_declaration(statement)
            if symbol is None:
                self._fail("RUNTIME_INTERNAL_ERROR", "Binding has no symbol.", statement.span)
            value = self._coerce(
                value,
                self._expression_type(statement.initializer),
                self._symbol_type(symbol),
                statement.span,
            )
            environment.define(
                symbol,
                value,
                mutable=statement.kind is BindingKind.VAR,
            )
        elif isinstance(statement, AssignmentStatement):
            self._execute_assignment(statement, environment)
        elif isinstance(statement, ExpressionStatement):
            self._evaluate(statement.expression, environment)
        elif isinstance(statement, IfStatement):
            condition = self._evaluate(statement.condition, environment)
            self._require_bool(condition, statement.condition.span)
            if condition is True:
                self._execute_block(statement.then_branch, Environment(environment))
            elif isinstance(statement.else_branch, Block):
                self._execute_block(statement.else_branch, Environment(environment))
            elif statement.else_branch is not None:
                self._execute_statement(statement.else_branch, environment)
        elif isinstance(statement, WhileStatement):
            while True:
                condition = self._evaluate(statement.condition, environment)
                self._require_bool(condition, statement.condition.span)
                if condition is False:
                    break
                try:
                    self._execute_block(statement.body, Environment(environment))
                except _ContinueSignal:
                    continue
                except _BreakSignal:
                    break
        elif isinstance(statement, ForStatement):
            iterable = self._evaluate(statement.iterable, environment)
            elements: Iterable[RuntimeValue]
            if isinstance(iterable, KajList):
                elements = iterable.elements
            elif isinstance(iterable, KajRange):
                elements = range(iterable.start, iterable.end)
            elif isinstance(iterable, KajMap):
                elements = tuple(
                    KajMapEntry(self._map_key_value(key), value) for key, value in iterable.entries
                )
            else:
                self._fail(
                    "RUNTIME_INVALID_OPERATION",
                    "For value is not iterable.",
                    statement.iterable.span,
                )
            symbol = self._resolution.symbol_for_declaration(statement)
            if symbol is None:
                self._fail("RUNTIME_INTERNAL_ERROR", "Loop variable has no symbol.", statement.span)
            for element in elements:
                iteration_environment = Environment(environment)
                iteration_environment.define(symbol, element, mutable=False)
                try:
                    self._execute_block(statement.body, iteration_environment)
                except _ContinueSignal:
                    continue
                except _BreakSignal:
                    break
        elif isinstance(statement, ReturnStatement):
            if statement.value is None:
                raise _ReturnSignal(None, PrimitiveType.NONE)
            raise _ReturnSignal(
                self._evaluate(statement.value, environment),
                self._expression_type(statement.value),
            )
        elif isinstance(statement, MatchStatement):
            value = self._evaluate(statement.scrutinee, environment)
            if not isinstance(value, KajEnumValue):
                self._fail(
                    "RUNTIME_INTERNAL_ERROR",
                    "Match scrutinee is not an enum value.",
                    statement.scrutinee.span,
                )
            selected = next(
                (case for case in statement.cases if case.pattern.variant_name == value.variant),
                None,
            )
            if selected is None:
                self._fail(
                    "RUNTIME_INTERNAL_ERROR",
                    f"No match case for variant '{value.variant}'.",
                    statement.span,
                )
            mapping = self._types.mapping_for_match_case(selected)
            if mapping is None or mapping.enum_type != value.type:
                self._fail(
                    "RUNTIME_INTERNAL_ERROR", "Match case metadata is inconsistent.", selected.span
                )
            branch_environment = Environment(environment)
            if len(selected.pattern.bindings) != len(value.payload):
                self._fail(
                    "RUNTIME_INTERNAL_ERROR",
                    "Enum payload arity is inconsistent.",
                    selected.pattern.span,
                )
            for binding, payload in zip(selected.pattern.bindings, value.payload, strict=True):
                symbol = self._resolution.symbol_for_declaration(binding)
                if symbol is None:
                    self._fail(
                        "RUNTIME_INTERNAL_ERROR", "Pattern binding has no symbol.", binding.span
                    )
                branch_environment.define(symbol, payload, mutable=False)
            if isinstance(selected.body, Block):
                self._execute_block(selected.body, branch_environment)
            else:
                self._execute_statement(selected.body, branch_environment)
        elif isinstance(statement, Block):
            self._execute_block(statement, Environment(environment))
        elif isinstance(statement, StepStatement):
            self._execute_block(statement.body, Environment(environment))
        elif isinstance(statement, PlanRegion):
            self._execute_block(statement.body, environment)
        elif isinstance(
            statement,
            (
                GoalClause,
                RequireClause,
                InvariantClause,
                SuccessClause,
                FunctionDeclaration,
                TaskDeclaration,
                RecordDeclaration,
                EnumDeclaration,
                NewtypeDeclaration,
                ImportDeclaration,
                CapabilityDeclaration,
                UseCapabilityDeclaration,
            ),
        ):
            return
        elif isinstance(statement, BreakStatement):
            raise _BreakSignal
        elif isinstance(statement, ContinueStatement):
            raise _ContinueSignal
        else:
            self._fail(
                "RUNTIME_INVALID_OPERATION",
                f"Unsupported statement {type(statement).__name__}.",
                statement.span,
            )

    def _execute_block(self, block: Block, environment: Environment) -> None:
        for statement in block.statements:
            self._execute_statement(statement, environment)

    def _execute_assignment(self, statement: AssignmentStatement, environment: Environment) -> None:
        if not isinstance(statement.target, Identifier):
            self._fail(
                "RUNTIME_INVALID_OPERATION",
                "Only identifier assignment is executable in Checkpoint 8.",
                statement.target.span,
            )
        symbol = self._resolution.symbol_for(statement.target)
        if symbol is None:
            self._fail("RUNTIME_INTERNAL_ERROR", "Assignment target is unresolved.", statement.span)
        rhs = self._evaluate(statement.value, environment)
        rhs_type = self._expression_type(statement.value)
        value = rhs
        value_type = rhs_type
        if statement.operator is not AssignmentOperator.ASSIGN:
            operator = {
                AssignmentOperator.ADD_ASSIGN: BinaryOperator.ADD,
                AssignmentOperator.SUBTRACT_ASSIGN: BinaryOperator.SUBTRACT,
                AssignmentOperator.MULTIPLY_ASSIGN: BinaryOperator.MULTIPLY,
                AssignmentOperator.DIVIDE_ASSIGN: BinaryOperator.DIVIDE,
            }[statement.operator]
            target_type = self._symbol_type(symbol)
            value = self._apply_binary(
                operator,
                environment.read(symbol),
                rhs,
                target_type,
                rhs_type,
                statement.span,
            )
            value_type = self._binary_result_type(operator, target_type, rhs_type)
        value = self._coerce(value, value_type, self._symbol_type(symbol), statement.value.span)
        try:
            environment.assign(symbol, value)
        except PermissionError:
            self._fail(
                "RUNTIME_INVALID_OPERATION",
                f"Cannot mutate immutable binding '{symbol.name}'.",
                statement.target.span,
            )

    def _evaluate(self, expression: Expression, environment: Environment) -> RuntimeValue:
        if isinstance(expression, BooleanLiteral):
            return expression.value
        if isinstance(expression, IntegerLiteral):
            return expression.value
        if isinstance(expression, DecimalLiteral):
            return expression.value
        if isinstance(expression, StringLiteral):
            return expression.value
        if isinstance(expression, InterpolatedString):
            return "".join(
                part
                if isinstance(part, str)
                else self._format_value(self._evaluate(part, environment))
                for part in expression.parts
            )
        if isinstance(expression, NoneLiteral):
            semantic_type = self._expression_type(expression)
            if isinstance(semantic_type, OptionalType):
                return KajEnumValue(semantic_type, "none", ())
            return None
        if isinstance(expression, Identifier):
            symbol = self._resolution.symbol_for(expression)
            if symbol is None:
                self._fail("RUNTIME_INTERNAL_ERROR", "Identifier is unresolved.", expression.span)
            try:
                return environment.read(symbol)
            except KeyError:
                self._fail(
                    "RUNTIME_INTERNAL_ERROR",
                    f"No runtime value exists for '{symbol.name}'.",
                    expression.span,
                )
        if isinstance(expression, UnaryExpression):
            return self._evaluate_unary(expression, environment)
        if isinstance(expression, BinaryExpression):
            return self._evaluate_binary(expression, environment)
        if isinstance(expression, CallExpression):
            if self._is_capability_call(expression):
                return self._capability_call(expression, environment)
            return self._evaluate_call(expression, environment)
        if isinstance(expression, HumanInteractionExpression):
            return self._evaluate_human_interaction(expression, environment)
        if isinstance(expression, StartTaskExpression):
            composition_cache_key = self.composition_key(expression)
            cached = self._composition_values.get(composition_cache_key)
            if isinstance(cached, KajTaskHandle):
                return cached
            if self._task_starter is None:
                self._fail(
                    "TASK_COMPOSITION_RUNTIME_UNAVAILABLE",
                    "No task scheduler is available.",
                    expression.span,
                )
            arguments = tuple(
                self._evaluate(argument.value, environment) for argument in expression.arguments
            )
            handle = self._task_starter(expression, arguments)
            self._composition_values[composition_cache_key] = handle
            return handle
        if isinstance(expression, AwaitTaskExpression):
            composition_cache_key = self.composition_key(expression)
            if composition_cache_key in self._composition_values:
                return self._composition_values[composition_cache_key]
            awaited_handle = self._evaluate(expression.operand, environment)
            if not isinstance(awaited_handle, KajTaskHandle) or self._task_awaiter is None:
                self._fail(
                    "TASK_AWAIT_EXPECTED_HANDLE",
                    "await requires a task handle.",
                    expression.span,
                )
            ready, value = self._task_awaiter(awaited_handle)
            if not ready:
                raise _TaskAwaitSignal(TaskAwaitSuspension(expression, awaited_handle))
            self._composition_values[composition_cache_key] = value
            return value
        if isinstance(expression, RecordConstructionExpression):
            record_type = self._expression_type(expression)
            if not isinstance(record_type, RecordType):
                self._fail(
                    "RUNTIME_INTERNAL_ERROR",
                    "Record construction has no static record type.",
                    expression.span,
                )
            fields: list[tuple[str, RuntimeValue]] = []
            for initializer in expression.fields:
                field = self._types.field_for_initializer(initializer)
                if field is None:
                    self._fail(
                        "RUNTIME_INTERNAL_ERROR",
                        "Record initializer has no field mapping.",
                        initializer.span,
                    )
                value = self._coerce(
                    self._evaluate(initializer.value, environment),
                    self._expression_type(initializer.value),
                    field.type,
                    initializer.span,
                )
                fields.append((field.name, value))
            return KajRecord(record_type, tuple(fields))
        if isinstance(expression, EnumConstructionExpression):
            enum_type = self._expression_type(expression)
            if not isinstance(enum_type, EnumType):
                self._fail(
                    "RUNTIME_INTERNAL_ERROR",
                    "Enum construction has no static enum type.",
                    expression.span,
                )
            values_by_name: dict[str, RuntimeValue] = {}
            for argument in () if expression.arguments is None else expression.arguments:
                enum_field = self._types.field_for_enum_argument(argument)
                if enum_field is None:
                    self._fail(
                        "RUNTIME_INTERNAL_ERROR",
                        "Enum argument has no field mapping.",
                        argument.span,
                    )
                values_by_name[enum_field.name] = self._coerce(
                    self._evaluate(argument.value, environment),
                    self._expression_type(argument.value),
                    enum_field.type,
                    argument.span,
                )
            definition = self._types.enum_definition(enum_type)
            if definition is None:
                self._fail(
                    "RUNTIME_INTERNAL_ERROR",
                    "Enum construction has no definition.",
                    expression.span,
                )
            variant = next(
                (item for item in definition.variants if item.name == expression.variant_name), None
            )
            if variant is None:
                self._fail(
                    "RUNTIME_INTERNAL_ERROR",
                    "Enum construction has no variant definition.",
                    expression.span,
                )
            return KajEnumValue(
                enum_type,
                expression.variant_name,
                tuple(values_by_name[field.name] for field in variant.payload),
            )
        if isinstance(expression, ListLiteral):
            list_type = self._expression_type(expression)
            if not isinstance(list_type, ListType):
                self._fail(
                    "RUNTIME_INTERNAL_ERROR", "List has no static List type.", expression.span
                )
            elements = tuple(
                self._coerce(
                    self._evaluate(element, environment),
                    self._expression_type(element),
                    list_type.element_type,
                    element.span,
                )
                for element in expression.elements
            )
            return KajList(elements)
        if isinstance(expression, MapLiteral):
            map_type = self._expression_type(expression)
            if not isinstance(map_type, MapType):
                self._fail("RUNTIME_INTERNAL_ERROR", "Map has no static Map type.", expression.span)
            entries: list[tuple[KajMapKey, RuntimeValue]] = []
            seen: set[KajMapKey] = set()
            for entry in expression.entries:
                key_value = self._coerce(
                    self._evaluate(entry.key, environment),
                    self._expression_type(entry.key),
                    map_type.key_type,
                    entry.key.span,
                )
                value = self._coerce(
                    self._evaluate(entry.value, environment),
                    self._expression_type(entry.value),
                    map_type.value_type,
                    entry.value.span,
                )
                key = self._map_key(key_value, map_type, entry.key.span)
                if key in seen:
                    self._fail(
                        "RUNTIME_DUPLICATE_MAP_KEY",
                        "Map literal contains duplicate evaluated keys.",
                        entry.key.span,
                    )
                seen.add(key)
                entries.append((key, value))
            return KajMap(map_type, tuple(entries))
        if isinstance(expression, IndexExpression):
            object_value = self._evaluate(expression.object, environment)
            index_value = self._evaluate(expression.index, environment)
            if isinstance(object_value, KajMap):
                coerced_key = self._coerce(
                    index_value,
                    self._expression_type(expression.index),
                    object_value.type.key_type,
                    expression.index.span,
                )
                key = self._map_key(coerced_key, object_value.type, expression.index.span)
                optional_type = OptionalType(object_value.type.value_type)
                try:
                    return KajEnumValue(optional_type, "some", (object_value.read(key),))
                except KeyError:
                    return KajEnumValue(optional_type, "none", ())
            if not isinstance(object_value, KajList) or type(index_value) is not int:
                self._fail(
                    "RUNTIME_INVALID_OPERATION",
                    "Index access requires a Kaj List and Int index.",
                    expression.span,
                )
            if index_value < 0 or index_value >= len(object_value.elements):
                self._fail(
                    "RUNTIME_INDEX_OUT_OF_BOUNDS",
                    f"List index {index_value} is out of bounds.",
                    expression.index.span,
                )
            return object_value.elements[index_value]
        if isinstance(expression, MemberAccessExpression):
            object_value = self._evaluate(expression.object, environment)
            if isinstance(object_value, KajList) and expression.member == "count":
                return len(object_value.elements)
            if isinstance(object_value, KajList) and expression.member in {"first", "last"}:
                edge_type = self._expression_type(expression)
                if not isinstance(edge_type, OptionalType):
                    self._fail(
                        "RUNTIME_INTERNAL_ERROR", "List edge has invalid type.", expression.span
                    )
                if not object_value.elements:
                    return KajEnumValue(edge_type, "none", ())
                index = 0 if expression.member == "first" else -1
                return KajEnumValue(edge_type, "some", (object_value.elements[index],))
            if isinstance(object_value, KajMap) and expression.member == "count":
                return len(object_value.entries)
            if isinstance(object_value, KajNewtypeValue) and expression.member == "value":
                return object_value.value
            if isinstance(object_value, KajMapEntry):
                if expression.member == "key":
                    return object_value.key
                if expression.member == "value":
                    return object_value.value
            if isinstance(object_value, KajModuleValue):
                try:
                    return object_value.read(expression.member)
                except KeyError:
                    self._fail(
                        "RUNTIME_INTERNAL_ERROR",
                        f"Module member '{expression.member}' is absent at runtime.",
                        expression.span,
                    )
            if isinstance(object_value, KajRecord):
                try:
                    return object_value.read(expression.member)
                except KeyError:
                    self._fail(
                        "RUNTIME_INTERNAL_ERROR",
                        f"Record field '{expression.member}' is absent at runtime.",
                        expression.span,
                    )
            self._fail(
                "RUNTIME_INVALID_OPERATION",
                f"Unsupported runtime member '{expression.member}'.",
                expression.span,
            )
        self._fail(
            "RUNTIME_INVALID_OPERATION",
            f"Unsupported expression {type(expression).__name__}.",
            expression.span,
        )

    def _evaluate_unary(
        self, expression: UnaryExpression, environment: Environment
    ) -> RuntimeValue:
        value = self._evaluate(expression.operand, environment)
        if expression.operator is UnaryOperator.NOT:
            self._require_bool(value, expression.span)
            return not value
        if expression.operator is UnaryOperator.POSITIVE:
            return +value  # type: ignore[operator]
        if expression.operator is UnaryOperator.NEGATE:
            return -value  # type: ignore[operator]
        self._fail("RUNTIME_INVALID_OPERATION", "Unknown unary operator.", expression.span)

    def _evaluate_binary(
        self, expression: BinaryExpression, environment: Environment
    ) -> RuntimeValue:
        left = self._evaluate(expression.left, environment)
        if expression.operator is BinaryOperator.AND:
            self._require_bool(left, expression.left.span)
            if left is False:
                return False
        elif expression.operator is BinaryOperator.OR:
            self._require_bool(left, expression.left.span)
            if left is True:
                return True
        right = self._evaluate(expression.right, environment)
        return self._apply_binary(
            expression.operator,
            left,
            right,
            self._expression_type(expression.left),
            self._expression_type(expression.right),
            expression.span,
        )

    def _apply_binary(
        self,
        operator: BinaryOperator,
        left: RuntimeValue,
        right: RuntimeValue,
        left_type: SemanticType,
        right_type: SemanticType,
        span: SourceSpan,
    ) -> RuntimeValue:
        if operator in (BinaryOperator.AND, BinaryOperator.OR):
            self._require_bool(left, span)
            self._require_bool(right, span)
            return right
        if (
            left_type in (PrimitiveType.INT, PrimitiveType.DECIMAL)
            and right_type in (PrimitiveType.INT, PrimitiveType.DECIMAL)
            and (
                PrimitiveType.DECIMAL in (left_type, right_type)
                or operator is BinaryOperator.DIVIDE
            )
        ):
            left = self._to_decimal(left, span)
            right = self._to_decimal(right, span)
        if operator in (BinaryOperator.DIVIDE, BinaryOperator.MODULO) and right == 0:
            self._fail("RUNTIME_DIVISION_BY_ZERO", "Division by zero.", span)
        if (
            operator is BinaryOperator.POWER
            and left_type is PrimitiveType.INT
            and right_type is PrimitiveType.INT
            and type(right) is int
            and right < 0
        ):
            self._fail(
                "RUNTIME_INVALID_OPERATION",
                "Negative Int exponents cannot produce an exact Int result.",
                span,
            )
        try:
            with localcontext() as context:
                context.prec = 34
                if operator is BinaryOperator.ADD:
                    return left + right  # type: ignore[operator]
                if operator is BinaryOperator.SUBTRACT:
                    return left - right  # type: ignore[operator]
                if operator is BinaryOperator.MULTIPLY:
                    return left * right  # type: ignore[operator]
                if operator is BinaryOperator.DIVIDE:
                    return cast(RuntimeValue, left / right)  # type: ignore[operator]
                if operator is BinaryOperator.MODULO:
                    return left % right  # type: ignore[operator]
                if operator is BinaryOperator.POWER:
                    return left**right  # type: ignore[operator]
                if operator is BinaryOperator.EQUAL:
                    return self._kaj_equal(left, right)
                if operator is BinaryOperator.NOT_EQUAL:
                    return not self._kaj_equal(left, right)
                if operator is BinaryOperator.LESS:
                    return left < right  # type: ignore[operator]
                if operator is BinaryOperator.LESS_EQUAL:
                    return left <= right  # type: ignore[operator]
                if operator is BinaryOperator.GREATER:
                    return left > right  # type: ignore[operator]
                if operator is BinaryOperator.GREATER_EQUAL:
                    return left >= right  # type: ignore[operator]
        except (ZeroDivisionError, DecimalException):
            if operator in (BinaryOperator.DIVIDE, BinaryOperator.MODULO):
                self._fail("RUNTIME_DIVISION_BY_ZERO", "Division by zero.", span)
            self._fail(
                "RUNTIME_INVALID_OPERATION",
                "Decimal operation cannot be represented exactly by this runtime.",
                span,
            )
        self._fail("RUNTIME_INVALID_OPERATION", "Unknown binary operator.", span)

    def _evaluate_human_interaction(
        self, expression: HumanInteractionExpression, environment: Environment
    ) -> RuntimeValue:
        cached = self._interaction_responses.get(
            self.interaction_key(expression), _NO_INTERACTION_RESPONSE
        )
        if cached is not _NO_INTERACTION_RESPONSE:
            return cast(RuntimeValue, cached)
        values = [self._evaluate(argument.value, environment) for argument in expression.arguments]
        if not values or not isinstance(values[0], str):
            self._fail(
                "RUNTIME_INTERNAL_ERROR",
                "Human interaction prompt is not String.",
                expression.span,
            )
        prompt = values[0]
        if expression.kind == "inform":
            self.inform_events.append(prompt)
            return None
        expected_type = self._expression_type(expression)
        if not isinstance(
            expected_type,
            (
                PrimitiveType,
                ListType,
                MapType,
                RecordType,
                EnumType,
                NewtypeType,
                OptionalType,
                ResultType,
            ),
        ):
            self._fail(
                "RUNTIME_INTERNAL_ERROR",
                "Human interaction has no value type.",
                expression.span,
            )
        options: tuple[RuntimeValue, ...] = ()
        if expression.kind == "choose":
            if len(values) != 2 or not isinstance(values[1], KajList):
                self._fail(
                    "TASK_CHOOSE_OPTIONS_INVALID",
                    "choose options must be a non-empty List.",
                    expression.span,
                )
            options = values[1].elements
            if not options:
                self._fail(
                    "TASK_CHOOSE_EMPTY_OPTIONS",
                    "choose options must not be empty.",
                    expression.span,
                )
        raise _HumanInteractionSignal(
            InteractionRequest(expression, prompt, expected_type, options)
        )

    def _capability_call(
        self, expression: CallExpression, environment: Environment
    ) -> RuntimeValue:
        callee = expression.callee
        if not isinstance(callee, MemberAccessExpression) or not isinstance(
            callee.object, Identifier
        ):
            raise TypeError("capability call shape changed after detection")
        symbol = self._resolution.symbol_for(callee.object)
        if symbol is None or symbol.kind is not SymbolKind.CAPABILITY_ALIAS:
            raise RuntimeError("capability alias changed after detection")
        key = self.capability_key(expression)
        cached = self._capability_responses.get(key, _NO_INTERACTION_RESPONSE)
        if cached is not _NO_INTERACTION_RESPONSE:
            return cast(RuntimeValue, cached)
        expected = self._expression_type(expression)
        if not isinstance(
            expected,
            (
                PrimitiveType,
                ListType,
                MapType,
                RecordType,
                EnumType,
                NewtypeType,
                OptionalType,
                ResultType,
            ),
        ):
            self._fail(
                "RUNTIME_INTERNAL_ERROR",
                "Capability call has no value return type.",
                expression.span,
            )
        arguments = tuple(
            self._evaluate(argument.value, environment) for argument in expression.arguments
        )
        if self._capability_invoker is None:
            self._fail(
                "CAPABILITY_NOT_PROVIDED",
                f"Capability alias '{callee.object.name}' is not bound.",
                expression.span,
            )
        invocation = CapabilityInvocation(
            expression, callee.object.name, callee.member, arguments, expected
        )
        result = self._capability_invoker(invocation)
        if result.pending:
            raise _CapabilitySignal(CapabilitySuspension(invocation, result))
        return result.value

    def _is_capability_call(self, expression: CallExpression) -> bool:
        callee = expression.callee
        if not isinstance(callee, MemberAccessExpression) or not isinstance(
            callee.object, Identifier
        ):
            return False
        symbol = self._resolution.symbol_for(callee.object)
        return symbol is not None and symbol.kind is SymbolKind.CAPABILITY_ALIAS

    def _evaluate_call(self, expression: CallExpression, environment: Environment) -> RuntimeValue:
        expression_type = self._expression_type(expression)
        if isinstance(expression_type, NewtypeType):
            if len(expression.arguments) != 1:
                self._fail(
                    "RUNTIME_INTERNAL_ERROR",
                    "Newtype constructor has invalid arity.",
                    expression.span,
                )
            definition = self._types.newtype_definition(expression_type)
            if definition is None:
                self._fail(
                    "RUNTIME_INTERNAL_ERROR",
                    "Newtype constructor has no semantic definition.",
                    expression.span,
                )
            argument = expression.arguments[0]
            value = self._coerce(
                self._evaluate(argument.value, environment),
                self._expression_type(argument.value),
                definition.underlying_type,
                argument.span,
            )
            return KajNewtypeValue(expression_type, value)
        if isinstance(expression.callee, Identifier) and expression.callee.name in {
            "some",
            "ok",
            "err",
        }:
            return self._evaluate_standard_constructor(
                expression, expression.callee.name, environment
            )
        callee = self._evaluate(expression.callee, environment)
        values = [self._evaluate(argument.value, environment) for argument in expression.arguments]
        argument_types = [self._expression_type(item.value) for item in expression.arguments]
        if callee is BuiltinFunction.PRINT:
            if len(values) != 1:
                self._fail(
                    "RUNTIME_INVALID_OPERATION", "print expects one argument.", expression.span
                )
            self._emit(self._format_value(values[0]))
            return None
        if callee is BuiltinFunction.RANGE:
            if len(values) != 2 or any(type(value) is not int for value in values):
                self._fail(
                    "RUNTIME_INTERNAL_ERROR", "range received invalid arguments.", expression.span
                )
            return KajRange(cast(int, values[0]), cast(int, values[1]))
        if callee is BuiltinFunction.STRING:
            if len(values) != 1:
                self._fail(
                    "RUNTIME_INTERNAL_ERROR", "String received invalid arity.", expression.span
                )
            return self._format_value(values[0])
        if callee is BuiltinFunction.UTF8_ENCODE:
            if len(values) != 1 or not isinstance(values[0], str):
                self._fail(
                    "RUNTIME_INTERNAL_ERROR", "utf8_encode received invalid input.", expression.span
                )
            return values[0].encode("utf-8")
        if callee is BuiltinFunction.UTF8_DECODE:
            if len(values) != 1 or not isinstance(values[0], bytes):
                self._fail(
                    "RUNTIME_INTERNAL_ERROR", "utf8_decode received invalid input.", expression.span
                )
            result_type = self._expression_type(expression)
            if not isinstance(result_type, ResultType):
                self._fail(
                    "RUNTIME_INTERNAL_ERROR", "utf8_decode has invalid type.", expression.span
                )
            return decode_utf8(values[0], result_type)
        if not isinstance(callee, KajFunction):
            self._fail("RUNTIME_INVALID_OPERATION", "Value is not callable.", expression.span)
        call_environment = Environment(callee.environment)
        caller_types = self._types
        for argument, value, source_type in zip(
            expression.arguments, values, argument_types, strict=True
        ):
            mapping = caller_types.mapping_for_argument(argument)
            if mapping is None:
                self._fail(
                    "RUNTIME_INTERNAL_ERROR",
                    "Call argument has no parameter mapping.",
                    argument.span,
                )
            parameter = callee.declaration.parameters[mapping.parameter_index]
            symbol = callee.resolution.symbol_for_declaration(parameter)
            if symbol is None:
                self._fail(
                    "RUNTIME_INTERNAL_ERROR", "Function parameter has no symbol.", parameter.span
                )
            value = self._coerce(
                value,
                source_type,
                mapping.parameter.type,
                argument.span,
            )
            call_environment.define(symbol, value, mutable=mapping.parameter.mutable)
        caller_resolution = self._resolution
        self._resolution = callee.resolution
        self._types = callee.types
        try:
            try:
                self._execute_block(callee.declaration.body, call_environment)
            except _ReturnSignal as signal:
                return self._coerce(
                    signal.value,
                    signal.source_type,
                    callee.signature.return_type,
                    callee.declaration.span,
                )
        finally:
            self._resolution = caller_resolution
            self._types = caller_types
        return None

    def _evaluate_standard_constructor(
        self, expression: CallExpression, name: str, environment: Environment
    ) -> RuntimeValue:
        if len(expression.arguments) != 1:
            self._fail(
                "RUNTIME_INTERNAL_ERROR",
                f"Standard constructor '{name}' has invalid arity.",
                expression.span,
            )
        tagged_type = self._expression_type(expression)
        if name == "some" and isinstance(tagged_type, OptionalType):
            payload_type = tagged_type.value_type
            variant = "some"
        elif name in {"ok", "err"} and isinstance(tagged_type, ResultType):
            payload_type = tagged_type.ok_type if name == "ok" else tagged_type.err_type
            variant = name
        else:
            self._fail(
                "RUNTIME_INTERNAL_ERROR",
                f"Standard constructor '{name}' has invalid static type.",
                expression.span,
            )
        argument = expression.arguments[0]
        value = self._coerce(
            self._evaluate(argument.value, environment),
            self._expression_type(argument.value),
            payload_type,
            argument.span,
        )
        return KajEnumValue(tagged_type, variant, (value,))

    def _coerce(
        self,
        value: RuntimeValue,
        source_type: SemanticType,
        target_type: SemanticType,
        span: SourceSpan,
    ) -> RuntimeValue:
        if source_type is PrimitiveType.INT and target_type is PrimitiveType.DECIMAL:
            return self._to_decimal(value, span)
        return value

    def _to_decimal(self, value: RuntimeValue, span: SourceSpan) -> Decimal:
        if type(value) is int:
            return Decimal(value)
        if isinstance(value, Decimal):
            return value
        self._fail("RUNTIME_INTERNAL_ERROR", "Expected numeric value for promotion.", span)

    def _map_key(self, value: RuntimeValue, map_type: MapType, span: SourceSpan) -> KajMapKey:
        return self._canonical_map_key(value, map_type.key_type, span)

    def _canonical_map_key(
        self, value: RuntimeValue, key_type: SemanticType, span: SourceSpan
    ) -> KajMapKey:
        if isinstance(key_type, NewtypeType):
            if not isinstance(value, KajNewtypeValue) or value.type != key_type:
                self._fail("RUNTIME_INTERNAL_ERROR", "Map newtype key has invalid identity.", span)
            definition = self._types.newtype_definition(key_type)
            if definition is None:
                self._fail("RUNTIME_INTERNAL_ERROR", "Map newtype key has no definition.", span)
            return KajMapKey(
                key_type,
                self._canonical_map_key(value.value, definition.underlying_type, span),
            )
        if not isinstance(key_type, PrimitiveType) or key_type in {
            PrimitiveType.NONE,
            PrimitiveType.ERROR,
        }:
            self._fail("RUNTIME_INTERNAL_ERROR", "Map has an invalid key type.", span)
        if (
            (key_type is PrimitiveType.BOOL and type(value) is not bool)
            or (key_type is PrimitiveType.INT and type(value) is not int)
            or (key_type is PrimitiveType.DECIMAL and not isinstance(value, Decimal))
            or (key_type is PrimitiveType.STRING and not isinstance(value, str))
            or (key_type is PrimitiveType.BYTES and not isinstance(value, bytes))
        ):
            self._fail("RUNTIME_INTERNAL_ERROR", "Map key does not match its static type.", span)
        return KajMapKey(key_type, cast(bool | int | Decimal | str | bytes, value))

    def _map_key_value(self, key: KajMapKey) -> RuntimeValue:
        if isinstance(key.type, NewtypeType):
            nested = key.value
            if not isinstance(nested, KajMapKey):
                self._fail(
                    "RUNTIME_INTERNAL_ERROR",
                    "Newtype map key has invalid representation.",
                    key.type.symbol.declaration_span,
                )
            return KajNewtypeValue(key.type, self._map_key_value(nested))
        return cast(RuntimeValue, key.value)

    def _expression_type(self, expression: Expression) -> SemanticType:
        semantic_type = self._types.type_of_expression(expression)
        if semantic_type is None:
            self._fail("RUNTIME_INTERNAL_ERROR", "Expression has no static type.", expression.span)
        return semantic_type

    def _symbol_type(self, symbol: Symbol) -> SemanticType:
        semantic_type = self._types.type_of_symbol(symbol)
        if semantic_type is None:
            self._fail(
                "RUNTIME_INTERNAL_ERROR", "Symbol has no static type.", symbol.declaration_span
            )
        return semantic_type

    def _binary_result_type(
        self, operator: BinaryOperator, left: SemanticType, right: SemanticType
    ) -> SemanticType:
        if operator is BinaryOperator.DIVIDE:
            return PrimitiveType.DECIMAL
        if PrimitiveType.DECIMAL in (left, right):
            return PrimitiveType.DECIMAL
        return left

    def _require_bool(self, value: RuntimeValue, span: SourceSpan) -> None:
        if type(value) is not bool:
            self._fail("RUNTIME_INTERNAL_ERROR", "Expected Bool runtime value.", span)

    def _format_value(self, value: RuntimeValue) -> str:
        if value is None:
            return "none"
        if type(value) is bool:
            return "true" if value else "false"
        if type(value) is int:
            return str(value)
        if isinstance(value, Decimal):
            return format(value, "f")
        if isinstance(value, str):
            return value
        if isinstance(value, bytes):
            return f'bytes("{value.hex()}")'
        if isinstance(value, KajList):
            return "[" + ", ".join(self._format_nested(item) for item in value.elements) + "]"
        if isinstance(value, KajMap):
            return (
                "{"
                + ", ".join(
                    f"{self._format_nested(self._map_key_value(key))}: {self._format_nested(item)}"
                    for key, item in value.entries
                )
                + "}"
            )
        if isinstance(value, KajEnumValue):
            if isinstance(value.type, (OptionalType, ResultType)):
                name = value.variant
            else:
                name = f"{value.type.symbol.name}.{value.variant}"
            if not value.payload:
                return name
            if isinstance(value.type, EnumType):
                definition = self._types.enum_definition(value.type)
                variant = (
                    None
                    if definition is None
                    else next(
                        (item for item in definition.variants if item.name == value.variant), None
                    )
                )
                if variant is not None:
                    payload = ", ".join(
                        f"{field.name}: {self._format_nested(item)}"
                        for field, item in zip(variant.payload, value.payload, strict=True)
                    )
                    return name + "(" + payload + ")"
            return name + "(" + ", ".join(self._format_nested(item) for item in value.payload) + ")"
        if isinstance(value, KajNewtypeValue):
            return f"{value.type.symbol.name}({self._format_nested(value.value)})"
        if isinstance(value, KajRecord):
            fields = ", ".join(
                f"{name}: {self._format_nested(item)}" for name, item in value.fields
            )
            return f"{value.type.symbol.name} {{ {fields} }}"
        if isinstance(value, KajRange):
            return f"range({value.start}, {value.end})"
        if isinstance(value, KajMapEntry):
            return (
                f"MapEntry {{ key: {self._format_nested(value.key)}, "
                f"value: {self._format_nested(value.value)} }}"
            )
        return f"<{type(value).__name__}>"

    def _format_nested(self, value: RuntimeValue) -> str:
        if isinstance(value, str):
            escaped = (
                value.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t")
            )
            return f'"{escaped}"'
        return self._format_value(value)

    def _kaj_equal(self, left: RuntimeValue, right: RuntimeValue) -> bool:
        if type(left) is not type(right):
            if (
                isinstance(left, (int, Decimal))
                and not isinstance(left, bool)
                and isinstance(right, (int, Decimal))
                and not isinstance(right, bool)
            ):
                return Decimal(left) == Decimal(right)
            return False
        if isinstance(left, KajEnumValue) and isinstance(right, KajEnumValue):
            return (
                left.type == right.type
                and left.variant == right.variant
                and len(left.payload) == len(right.payload)
                and all(
                    self._kaj_equal(a, b) for a, b in zip(left.payload, right.payload, strict=True)
                )
            )
        if isinstance(left, KajNewtypeValue) and isinstance(right, KajNewtypeValue):
            return left.type == right.type and self._kaj_equal(left.value, right.value)
        return left == right

    def _fail(self, code: str, message: str, span: SourceSpan) -> Never:
        raise RuntimeFailure(RuntimeErrorInfo(code, message, span))
