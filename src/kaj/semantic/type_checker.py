from __future__ import annotations

from dataclasses import dataclass

from kaj.ast import (
    AssignmentOperator,
    AssignmentStatement,
    BinaryExpression,
    BinaryOperator,
    BindingDeclaration,
    Block,
    BooleanLiteral,
    BreakStatement,
    CallArgument,
    CallExpression,
    ContinueStatement,
    DecimalLiteral,
    Expression,
    ExpressionStatement,
    ForStatement,
    FunctionDeclaration,
    GenericType,
    Identifier,
    IfStatement,
    IndexExpression,
    IntegerLiteral,
    ListLiteral,
    MapLiteral,
    MemberAccessExpression,
    NamedType,
    NoneLiteral,
    Parameter,
    Program,
    ReturnStatement,
    Statement,
    StringLiteral,
    TypeExpression,
    UnaryExpression,
    UnaryOperator,
    WhileStatement,
)
from kaj.diagnostics import Diagnostic
from kaj.semantic.resolver import ResolutionResult
from kaj.semantic.symbols import Symbol, SymbolKind
from kaj.semantic.types import (
    PRIMITIVE_TYPES_BY_NAME,
    BuiltinFunctionType,
    FunctionParameterType,
    FunctionType,
    PrimitiveType,
    SemanticType,
    format_type,
    is_assignable,
)
from kaj.source import SourceSpan


@dataclass(frozen=True)
class TypedExpression:
    expression: Expression
    type: SemanticType


@dataclass(frozen=True)
class TypedSymbol:
    symbol: Symbol
    type: SemanticType


@dataclass(frozen=True)
class MappedArgument:
    argument: CallArgument
    parameter: FunctionParameterType
    parameter_index: int


@dataclass(frozen=True)
class TypeCheckResult:
    resolution: ResolutionResult
    expressions: tuple[TypedExpression, ...]
    symbols: tuple[TypedSymbol, ...]
    arguments: tuple[MappedArgument, ...]
    diagnostics: tuple[Diagnostic, ...]

    def type_of_expression(self, expression: Expression) -> SemanticType | None:
        for typed in self.expressions:
            if typed.expression is expression:
                return typed.type
        return None

    def type_of_symbol(self, symbol: Symbol) -> SemanticType | None:
        for typed in self.symbols:
            if typed.symbol is symbol:
                return typed.type
        return None

    def parameter_for_argument(self, argument: CallArgument) -> FunctionParameterType | None:
        for mapped in self.arguments:
            if mapped.argument is argument:
                return mapped.parameter
        return None

    def mapping_for_argument(self, argument: CallArgument) -> MappedArgument | None:
        for mapped in self.arguments:
            if mapped.argument is argument:
                return mapped
        return None


class TypeChecker:
    def __init__(self, resolution: ResolutionResult) -> None:
        self._resolution = resolution
        self._expression_types: dict[int, TypedExpression] = {}
        self._symbol_types: dict[int, TypedSymbol] = {}
        self._mutable_symbols: dict[int, bool] = {}
        self._function_types: dict[int, FunctionType] = {}
        self._mapped_arguments: list[MappedArgument] = []
        self._diagnostics: list[Diagnostic] = []
        self._current_return_type: PrimitiveType | None = None

    def check(self, program: Program) -> TypeCheckResult:
        self._expression_types = {}
        self._symbol_types = {}
        self._mutable_symbols = {}
        self._function_types = {}
        self._mapped_arguments = []
        self._diagnostics = []
        self._current_return_type = None
        for symbol in self._resolution.symbols:
            if symbol.kind is SymbolKind.BUILTIN_FUNCTION and symbol.name == "print":
                self._record_symbol(symbol, BuiltinFunctionType.PRINT)
        for statement in program.statements:
            if isinstance(statement, FunctionDeclaration):
                self._declare_function_signature(statement)
        for statement in program.statements:
            self._check_statement(statement)
        return TypeCheckResult(
            resolution=self._resolution,
            expressions=tuple(self._expression_types.values()),
            symbols=tuple(self._symbol_types.values()),
            arguments=tuple(self._mapped_arguments),
            diagnostics=tuple(self._diagnostics),
        )

    def _record_expression(
        self, expression: Expression, semantic_type: SemanticType
    ) -> SemanticType:
        self._expression_types[id(expression)] = TypedExpression(expression, semantic_type)
        return semantic_type

    def _record_symbol(self, symbol: Symbol, semantic_type: SemanticType) -> None:
        self._symbol_types[symbol.id] = TypedSymbol(symbol, semantic_type)

    def _symbol_type(self, symbol: Symbol | None) -> SemanticType:
        if symbol is None:
            return PrimitiveType.ERROR
        typed = self._symbol_types.get(symbol.id)
        return PrimitiveType.ERROR if typed is None else typed.type

    def _declare_function_signature(self, declaration: FunctionDeclaration) -> None:
        parameters = tuple(
            FunctionParameterType(
                name=parameter.name,
                type=self._resolve_annotation(parameter.type_annotation),
                mutable=parameter.mutable,
            )
            for parameter in declaration.parameters
        )
        signature = FunctionType(
            parameters=parameters,
            return_type=self._resolve_annotation(declaration.return_type),
        )
        self._function_types[id(declaration)] = signature
        symbol = self._resolution.symbol_for_declaration(declaration)
        if symbol is not None:
            self._record_symbol(symbol, signature)

    def _diagnose(self, code: str, message: str, span: SourceSpan) -> None:
        self._diagnostics.append(Diagnostic(code=code, message=message, span=span))

    def _resolve_annotation(self, annotation: TypeExpression) -> PrimitiveType:
        if isinstance(annotation, NamedType):
            primitive = PRIMITIVE_TYPES_BY_NAME.get(annotation.name)
            if primitive is not None:
                return primitive
        elif not isinstance(annotation, GenericType):
            raise TypeError(f"Unsupported type expression: {type(annotation).__name__}")
        self._diagnose(
            "TYPE_UNKNOWN_TYPE",
            "Type annotation is not a known primitive type.",
            annotation.span,
        )
        return PrimitiveType.ERROR

    def _check_binding(self, declaration: BindingDeclaration) -> None:
        declared_type = (
            self._resolve_annotation(declaration.annotation)
            if declaration.annotation is not None
            else None
        )
        initializer_type = self._infer(declaration.initializer)
        symbol = self._resolution.symbol_for_declaration(declaration)
        static_type = initializer_type if declared_type is None else declared_type
        if declared_type is not None and not is_assignable(initializer_type, declared_type):
            self._diagnose(
                "TYPE_MISMATCH",
                f"Cannot assign {format_type(initializer_type)} to {format_type(declared_type)}.",
                declaration.initializer.span,
            )
        if symbol is not None:
            self._record_symbol(symbol, static_type)
            self._mutable_symbols[symbol.id] = symbol.kind is SymbolKind.VAR_BINDING

    def _check_parameter(self, parameter: Parameter, semantic_type: PrimitiveType) -> None:
        symbol = self._resolution.symbol_for_declaration(parameter)
        if symbol is not None:
            self._record_symbol(symbol, semantic_type)
            self._mutable_symbols[symbol.id] = parameter.mutable

    def _check_statement(self, statement: Statement) -> None:
        if isinstance(statement, BindingDeclaration):
            self._check_binding(statement)
        elif isinstance(statement, AssignmentStatement):
            self._check_assignment(statement)
        elif isinstance(statement, ExpressionStatement):
            self._infer(statement.expression)
        elif isinstance(statement, IfStatement):
            self._check_condition(statement.condition)
            self._check_block(statement.then_branch)
            if isinstance(statement.else_branch, Block):
                self._check_block(statement.else_branch)
            elif statement.else_branch is not None:
                self._check_statement(statement.else_branch)
        elif isinstance(statement, WhileStatement):
            self._check_condition(statement.condition)
            self._check_block(statement.body)
        elif isinstance(statement, ForStatement):
            self._infer(statement.iterable)
            symbol = self._resolution.symbol_for_declaration(statement)
            if symbol is not None:
                self._record_symbol(symbol, PrimitiveType.ERROR)
            self._check_block(statement.body)
        elif isinstance(statement, FunctionDeclaration):
            signature = self._function_types.get(id(statement))
            if signature is None:
                # Named functions are module-level only in Kaj v0. The parser's
                # general Statement shape can still represent an unsupported nested one.
                return
            for parameter, descriptor in zip(
                statement.parameters, signature.parameters, strict=True
            ):
                self._check_parameter(parameter, descriptor.type)
            previous_return_type = self._current_return_type
            self._current_return_type = signature.return_type
            self._check_block(statement.body)
            self._current_return_type = previous_return_type
            if (
                signature.return_type not in (PrimitiveType.NONE, PrimitiveType.ERROR)
                and not self._block_definitely_returns(statement.body)
            ):
                self._diagnose(
                    "TYPE_MISSING_RETURN",
                    f"Function '{statement.name}' may reach its end without returning.",
                    statement.span,
                )
        elif isinstance(statement, ReturnStatement):
            self._check_return(statement)
        elif isinstance(statement, Block):
            self._check_block(statement)
        elif isinstance(statement, (BreakStatement, ContinueStatement)):
            return
        else:
            raise TypeError(f"Unsupported statement node: {type(statement).__name__}")

    def _check_block(self, block: Block) -> None:
        for statement in block.statements:
            self._check_statement(statement)

    def _check_condition(self, condition: Expression) -> None:
        condition_type = self._infer(condition)
        if condition_type not in (PrimitiveType.BOOL, PrimitiveType.ERROR):
            self._diagnose(
                "TYPE_CONDITION_NOT_BOOL",
                f"Condition must be Bool, not {format_type(condition_type)}.",
                condition.span,
            )

    def _check_assignment(self, statement: AssignmentStatement) -> None:
        target_type = self._infer(statement.target)
        value_type = self._infer(statement.value)
        symbol = (
            self._resolution.symbol_for(statement.target)
            if isinstance(statement.target, Identifier)
            else None
        )
        if symbol is not None and self._mutable_symbols.get(symbol.id) is False:
            self._diagnose(
                "ASSIGN_TO_IMMUTABLE",
                f"Cannot assign to immutable name '{symbol.name}'.",
                statement.target.span,
            )

        result_type = value_type
        if statement.operator is not AssignmentOperator.ASSIGN:
            operator = {
                AssignmentOperator.ADD_ASSIGN: BinaryOperator.ADD,
                AssignmentOperator.SUBTRACT_ASSIGN: BinaryOperator.SUBTRACT,
                AssignmentOperator.MULTIPLY_ASSIGN: BinaryOperator.MULTIPLY,
                AssignmentOperator.DIVIDE_ASSIGN: BinaryOperator.DIVIDE,
            }[statement.operator]
            result_type = self._infer_binary_types(
                operator, target_type, value_type, statement.span
            )
        if not is_assignable(result_type, target_type):
            self._diagnose(
                "TYPE_MISMATCH",
                f"Cannot assign {format_type(result_type)} to {format_type(target_type)}.",
                statement.value.span,
            )

    def _infer(self, expression: Expression) -> SemanticType:
        result: SemanticType
        if isinstance(expression, BooleanLiteral):
            result = PrimitiveType.BOOL
        elif isinstance(expression, IntegerLiteral):
            result = PrimitiveType.INT
        elif isinstance(expression, DecimalLiteral):
            result = PrimitiveType.DECIMAL
        elif isinstance(expression, StringLiteral):
            result = PrimitiveType.STRING
        elif isinstance(expression, NoneLiteral):
            result = PrimitiveType.NONE
        elif isinstance(expression, Identifier):
            result = self._symbol_type(self._resolution.symbol_for(expression))
        elif isinstance(expression, UnaryExpression):
            result = self._infer_unary(expression)
        elif isinstance(expression, BinaryExpression):
            left = self._infer(expression.left)
            right = self._infer(expression.right)
            result = self._infer_binary_types(expression.operator, left, right, expression.span)
        elif isinstance(expression, CallExpression):
            result = self._infer_call(expression)
        elif isinstance(expression, MemberAccessExpression):
            self._infer(expression.object)
            result = PrimitiveType.ERROR
        elif isinstance(expression, IndexExpression):
            self._infer(expression.object)
            self._infer(expression.index)
            result = PrimitiveType.ERROR
        elif isinstance(expression, ListLiteral):
            for element in expression.elements:
                self._infer(element)
            result = PrimitiveType.ERROR
        elif isinstance(expression, MapLiteral):
            for entry in expression.entries:
                self._infer(entry.key)
                self._infer(entry.value)
            result = PrimitiveType.ERROR
        else:
            raise TypeError(f"Unsupported expression node: {type(expression).__name__}")
        return self._record_expression(expression, result)

    def _infer_unary(self, expression: UnaryExpression) -> PrimitiveType:
        operand = self._infer(expression.operand)
        if operand is PrimitiveType.ERROR:
            return PrimitiveType.ERROR
        if expression.operator in (UnaryOperator.POSITIVE, UnaryOperator.NEGATE):
            if operand in (PrimitiveType.INT, PrimitiveType.DECIMAL):
                return operand
        elif expression.operator is UnaryOperator.NOT and operand is PrimitiveType.BOOL:
            return PrimitiveType.BOOL
        self._diagnose(
            "TYPE_INVALID_OPERATOR",
            f"Operator {expression.operator.name} is invalid for {format_type(operand)}.",
            expression.span,
        )
        return PrimitiveType.ERROR

    def _infer_binary_types(
        self,
        operator: BinaryOperator,
        left: SemanticType,
        right: SemanticType,
        span: SourceSpan,
    ) -> PrimitiveType:
        if PrimitiveType.ERROR in (left, right):
            return PrimitiveType.ERROR
        numeric = (PrimitiveType.INT, PrimitiveType.DECIMAL)
        both_numeric = left in numeric and right in numeric

        if operator in (BinaryOperator.AND, BinaryOperator.OR):
            if left is right is PrimitiveType.BOOL:
                return PrimitiveType.BOOL
        elif operator in (BinaryOperator.EQUAL, BinaryOperator.NOT_EQUAL):
            if left is right or both_numeric:
                return PrimitiveType.BOOL
        elif operator in (
            BinaryOperator.LESS,
            BinaryOperator.LESS_EQUAL,
            BinaryOperator.GREATER,
            BinaryOperator.GREATER_EQUAL,
        ):
            if both_numeric:
                return PrimitiveType.BOOL
        elif operator is BinaryOperator.ADD and left is right is PrimitiveType.STRING:
            return PrimitiveType.STRING
        elif operator in (
            BinaryOperator.ADD,
            BinaryOperator.SUBTRACT,
            BinaryOperator.MULTIPLY,
            BinaryOperator.MODULO,
            BinaryOperator.POWER,
        ):
            if both_numeric:
                if left is right is PrimitiveType.INT:
                    return PrimitiveType.INT
                return PrimitiveType.DECIMAL
        elif operator is BinaryOperator.DIVIDE and both_numeric:
            return PrimitiveType.DECIMAL

        self._diagnose(
            "TYPE_MISMATCH",
            f"Operator {operator.name} cannot combine {format_type(left)} and {format_type(right)}.",
            span,
        )
        return PrimitiveType.ERROR

    def _infer_call(self, expression: CallExpression) -> SemanticType:
        callee_type = self._infer(expression.callee)
        argument_types = [self._infer(argument.value) for argument in expression.arguments]
        if callee_type is PrimitiveType.ERROR:
            return PrimitiveType.ERROR
        if callee_type is BuiltinFunctionType.PRINT:
            return self._infer_print_call(expression, argument_types)
        if not isinstance(callee_type, FunctionType):
            self._diagnose(
                "TYPE_NOT_CALLABLE",
                f"Value of type {format_type(callee_type)} is not callable.",
                expression.callee.span,
            )
            return PrimitiveType.ERROR

        assigned: set[int] = set()
        next_positional = 0
        for argument, argument_type in zip(
            expression.arguments, argument_types, strict=True
        ):
            parameter_index: int | None
            if argument.name is None:
                parameter_index = next_positional
                next_positional += 1
                if parameter_index >= len(callee_type.parameters):
                    self._diagnose(
                        "TYPE_TOO_MANY_ARGUMENTS",
                        "Call has too many positional arguments.",
                        argument.span,
                    )
                    continue
            else:
                parameter_index = next(
                    (
                        index
                        for index, parameter in enumerate(callee_type.parameters)
                        if parameter.name == argument.name
                    ),
                    None,
                )
                if parameter_index is None:
                    self._diagnose(
                        "TYPE_UNKNOWN_NAMED_ARGUMENT",
                        f"Unknown named argument '{argument.name}'.",
                        argument.span,
                    )
                    continue
            if parameter_index in assigned:
                self._diagnose(
                    "TYPE_DUPLICATE_ARGUMENT",
                    f"Parameter '{callee_type.parameters[parameter_index].name}' is provided twice.",
                    argument.span,
                )
                continue
            assigned.add(parameter_index)
            parameter = callee_type.parameters[parameter_index]
            self._mapped_arguments.append(
                MappedArgument(argument, parameter, parameter_index)
            )
            if not is_assignable(argument_type, parameter.type):
                self._diagnose(
                    "TYPE_MISMATCH",
                    f"Cannot pass {format_type(argument_type)} to parameter "
                    f"'{parameter.name}' of type {parameter.type.value}.",
                    argument.value.span,
                )

        missing = [
            parameter.name
            for index, parameter in enumerate(callee_type.parameters)
            if index not in assigned
        ]
        if missing:
            self._diagnose(
                "TYPE_MISSING_ARGUMENT",
                f"Missing required argument(s): {', '.join(missing)}.",
                expression.span,
            )
        return callee_type.return_type

    def _infer_print_call(
        self, expression: CallExpression, argument_types: list[SemanticType]
    ) -> PrimitiveType:
        if any(argument.name is not None for argument in expression.arguments):
            for argument in expression.arguments:
                if argument.name is not None:
                    self._diagnose(
                        "TYPE_UNKNOWN_NAMED_ARGUMENT",
                        "Builtin 'print' does not accept named arguments.",
                        argument.span,
                    )
        if len(expression.arguments) == 0:
            self._diagnose(
                "TYPE_MISSING_ARGUMENT",
                "Builtin 'print' requires one argument.",
                expression.span,
            )
        elif len(expression.arguments) > 1:
            self._diagnose(
                "TYPE_TOO_MANY_ARGUMENTS",
                "Builtin 'print' accepts exactly one argument.",
                expression.span,
            )
        if argument_types:
            printable = {
                PrimitiveType.BOOL,
                PrimitiveType.INT,
                PrimitiveType.DECIMAL,
                PrimitiveType.STRING,
                PrimitiveType.BYTES,
                PrimitiveType.NONE,
                PrimitiveType.ERROR,
            }
            if argument_types[0] not in printable:
                self._diagnose(
                    "TYPE_MISMATCH",
                    f"Builtin 'print' cannot print {format_type(argument_types[0])}.",
                    expression.arguments[0].value.span,
                )
        return PrimitiveType.NONE

    def _check_return(self, statement: ReturnStatement) -> None:
        if self._current_return_type is None:
            if statement.value is not None:
                self._infer(statement.value)
            self._diagnose(
                "TYPE_RETURN_OUTSIDE_FUNCTION",
                "Return statement is outside a function.",
                statement.span,
            )
            return
        actual = (
            PrimitiveType.NONE
            if statement.value is None
            else self._infer(statement.value)
        )
        if not is_assignable(actual, self._current_return_type):
            span = statement.span if statement.value is None else statement.value.span
            self._diagnose(
                "TYPE_MISMATCH",
                f"Cannot return {format_type(actual)} from a function returning "
                f"{self._current_return_type.value}.",
                span,
            )

    def _block_definitely_returns(self, block: Block) -> bool:
        return any(self._statement_definitely_returns(statement) for statement in block.statements)

    def _statement_definitely_returns(self, statement: Statement) -> bool:
        if isinstance(statement, ReturnStatement):
            return True
        if isinstance(statement, Block):
            return self._block_definitely_returns(statement)
        if isinstance(statement, IfStatement):
            if statement.else_branch is None:
                return False
            then_returns = self._block_definitely_returns(statement.then_branch)
            else_returns = (
                self._block_definitely_returns(statement.else_branch)
                if isinstance(statement.else_branch, Block)
                else self._statement_definitely_returns(statement.else_branch)
            )
            return then_returns and else_returns
        return False
