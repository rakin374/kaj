from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, DecimalException, localcontext
from typing import Never, cast

from kaj.ast import (
    AssignmentOperator,
    AssignmentStatement,
    BinaryExpression,
    BinaryOperator,
    BindingDeclaration,
    BindingKind,
    Block,
    BooleanLiteral,
    BreakStatement,
    CallExpression,
    ContinueStatement,
    DecimalLiteral,
    Expression,
    ExpressionStatement,
    ForStatement,
    FunctionDeclaration,
    Identifier,
    IfStatement,
    IndexExpression,
    IntegerLiteral,
    ListLiteral,
    MapLiteral,
    MemberAccessExpression,
    NoneLiteral,
    Program,
    ReturnStatement,
    Statement,
    StringLiteral,
    UnaryExpression,
    UnaryOperator,
    WhileStatement,
)
from kaj.runtime.environment import Environment
from kaj.runtime.errors import RuntimeErrorInfo, RuntimeFailure
from kaj.runtime.output import BufferOutput, RuntimeOutput
from kaj.runtime.values import BuiltinFunction, KajFunction, RuntimeValue
from kaj.semantic import (
    FunctionType,
    PrimitiveType,
    ResolutionResult,
    SemanticType,
    Symbol,
    SymbolKind,
    TypeCheckResult,
)
from kaj.source import SourceSpan


@dataclass(frozen=True)
class ExecutionResult:
    value: RuntimeValue
    output: str
    runtime_error: RuntimeErrorInfo | None


class _ReturnSignal(Exception):
    def __init__(self, value: RuntimeValue, source_type: SemanticType) -> None:
        self.value = value
        self.source_type = source_type


class Interpreter:
    def __init__(
        self,
        resolution: ResolutionResult,
        types: TypeCheckResult,
        *,
        output: RuntimeOutput | None = None,
    ) -> None:
        self._resolution = resolution
        self._types = types
        self._output = BufferOutput() if output is None else output
        self._captured_lines: list[str] = []

    def interpret(self, program: Program) -> ExecutionResult:
        self._captured_lines = []
        builtin_environment = Environment()
        module_environment = Environment(builtin_environment)
        try:
            self._install_builtins(builtin_environment)
            self._install_functions(program, module_environment)
            for statement in program.statements:
                if not isinstance(statement, FunctionDeclaration):
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
        return ExecutionResult(None, self._captured_output(), None)

    def _captured_output(self) -> str:
        return "".join(line + "\n" for line in self._captured_lines)

    def _emit(self, text: str) -> None:
        self._captured_lines.append(text)
        self._output.write_line(text)

    def _install_builtins(self, environment: Environment) -> None:
        for symbol in self._resolution.symbols:
            if symbol.kind is SymbolKind.BUILTIN_FUNCTION and symbol.name == "print":
                environment.define(symbol, BuiltinFunction.PRINT, mutable=False)

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
                KajFunction(statement, symbol, signature, environment),
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
                self._execute_block(statement.body, Environment(environment))
        elif isinstance(statement, ReturnStatement):
            if statement.value is None:
                raise _ReturnSignal(None, PrimitiveType.NONE)
            raise _ReturnSignal(
                self._evaluate(statement.value, environment),
                self._expression_type(statement.value),
            )
        elif isinstance(statement, Block):
            self._execute_block(statement, Environment(environment))
        elif isinstance(statement, FunctionDeclaration):
            return
        elif isinstance(statement, (ForStatement, BreakStatement, ContinueStatement)):
            self._fail(
                "RUNTIME_INVALID_OPERATION",
                f"{type(statement).__name__} is not executable in Checkpoint 8.",
                statement.span,
            )
        else:
            self._fail(
                "RUNTIME_INVALID_OPERATION",
                f"Unsupported statement {type(statement).__name__}.",
                statement.span,
            )

    def _execute_block(self, block: Block, environment: Environment) -> None:
        for statement in block.statements:
            self._execute_statement(statement, environment)

    def _execute_assignment(
        self, statement: AssignmentStatement, environment: Environment
    ) -> None:
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
        value = self._coerce(
            value, value_type, self._symbol_type(symbol), statement.value.span
        )
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
        if isinstance(expression, NoneLiteral):
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
            return self._evaluate_call(expression, environment)
        if isinstance(
            expression,
            (ListLiteral, MapLiteral, MemberAccessExpression, IndexExpression),
        ):
            self._fail(
                "RUNTIME_INVALID_OPERATION",
                f"{type(expression).__name__} is not executable in Checkpoint 8.",
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
                    return left == right
                if operator is BinaryOperator.NOT_EQUAL:
                    return left != right
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

    def _evaluate_call(
        self, expression: CallExpression, environment: Environment
    ) -> RuntimeValue:
        callee = self._evaluate(expression.callee, environment)
        values = [self._evaluate(argument.value, environment) for argument in expression.arguments]
        if callee is BuiltinFunction.PRINT:
            if len(values) != 1:
                self._fail(
                    "RUNTIME_INVALID_OPERATION", "print expects one argument.", expression.span
                )
            self._emit(self._format_value(values[0]))
            return None
        if not isinstance(callee, KajFunction):
            self._fail("RUNTIME_INVALID_OPERATION", "Value is not callable.", expression.span)
        call_environment = Environment(callee.environment)
        for argument, value in zip(expression.arguments, values, strict=True):
            mapping = self._types.mapping_for_argument(argument)
            if mapping is None:
                self._fail(
                    "RUNTIME_INTERNAL_ERROR", "Call argument has no parameter mapping.", argument.span
                )
            parameter = callee.declaration.parameters[mapping.parameter_index]
            symbol = self._resolution.symbol_for_declaration(parameter)
            if symbol is None:
                self._fail(
                    "RUNTIME_INTERNAL_ERROR", "Function parameter has no symbol.", parameter.span
                )
            value = self._coerce(
                value,
                self._expression_type(argument.value),
                mapping.parameter.type,
                argument.span,
            )
            call_environment.define(symbol, value, mutable=mapping.parameter.mutable)
        try:
            self._execute_block(callee.declaration.body, call_environment)
        except _ReturnSignal as signal:
            return self._coerce(
                signal.value,
                signal.source_type,
                callee.signature.return_type,
                callee.declaration.span,
            )
        return None

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

    def _expression_type(self, expression: Expression) -> SemanticType:
        semantic_type = self._types.type_of_expression(expression)
        if semantic_type is None:
            self._fail("RUNTIME_INTERNAL_ERROR", "Expression has no static type.", expression.span)
        return semantic_type

    def _symbol_type(self, symbol: Symbol) -> SemanticType:
        semantic_type = self._types.type_of_symbol(symbol)
        if semantic_type is None:
            self._fail("RUNTIME_INTERNAL_ERROR", "Symbol has no static type.", symbol.declaration_span)
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
            return repr(value)
        return f"<{type(value).__name__}>"

    def _fail(self, code: str, message: str, span: SourceSpan) -> Never:
        raise RuntimeFailure(RuntimeErrorInfo(code, message, span))
