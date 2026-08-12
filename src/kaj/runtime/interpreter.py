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
    EnumConstructionExpression,
    EnumDeclaration,
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
    MatchStatement,
    MemberAccessExpression,
    NoneLiteral,
    Program,
    RecordConstructionExpression,
    RecordDeclaration,
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
from kaj.runtime.values import (
    BuiltinFunction,
    KajEnumValue,
    KajFunction,
    KajList,
    KajRecord,
    RuntimeValue,
)
from kaj.semantic import (
    EnumType,
    FunctionType,
    ListType,
    PrimitiveType,
    RecordType,
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
                if not isinstance(
                    statement, (FunctionDeclaration, RecordDeclaration, EnumDeclaration)
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
        elif isinstance(statement, ForStatement):
            iterable = self._evaluate(statement.iterable, environment)
            if not isinstance(iterable, KajList):
                self._fail(
                    "RUNTIME_INVALID_OPERATION",
                    "For iterable is not a Kaj List.",
                    statement.iterable.span,
                )
            symbol = self._resolution.symbol_for_declaration(statement)
            if symbol is None:
                self._fail("RUNTIME_INTERNAL_ERROR", "Loop variable has no symbol.", statement.span)
            for element in iterable.elements:
                iteration_environment = Environment(environment)
                iteration_environment.define(symbol, element, mutable=False)
                self._execute_block(statement.body, iteration_environment)
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
        elif isinstance(statement, (FunctionDeclaration, RecordDeclaration, EnumDeclaration)):
            return
        elif isinstance(statement, (BreakStatement, ContinueStatement)):
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
        if isinstance(expression, IndexExpression):
            object_value = self._evaluate(expression.object, environment)
            index_value = self._evaluate(expression.index, environment)
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
        if isinstance(expression, MapLiteral):
            self._fail(
                "RUNTIME_INVALID_OPERATION",
                f"{type(expression).__name__} is not executable in Checkpoint 9.",
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

    def _evaluate_call(self, expression: CallExpression, environment: Environment) -> RuntimeValue:
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
                    "RUNTIME_INTERNAL_ERROR",
                    "Call argument has no parameter mapping.",
                    argument.span,
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
            return repr(value)
        return f"<{type(value).__name__}>"

    def _fail(self, code: str, message: str, span: SourceSpan) -> Never:
        raise RuntimeFailure(RuntimeErrorInfo(code, message, span))
