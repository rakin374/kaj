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
from kaj.semantic.types import PRIMITIVE_TYPES_BY_NAME, PrimitiveType, is_assignable
from kaj.source import SourceSpan


@dataclass(frozen=True)
class TypedExpression:
    expression: Expression
    type: PrimitiveType


@dataclass(frozen=True)
class TypedSymbol:
    symbol: Symbol
    type: PrimitiveType


@dataclass(frozen=True)
class TypeCheckResult:
    resolution: ResolutionResult
    expressions: tuple[TypedExpression, ...]
    symbols: tuple[TypedSymbol, ...]
    diagnostics: tuple[Diagnostic, ...]

    def type_of_expression(self, expression: Expression) -> PrimitiveType | None:
        for typed in self.expressions:
            if typed.expression is expression:
                return typed.type
        return None

    def type_of_symbol(self, symbol: Symbol) -> PrimitiveType | None:
        for typed in self.symbols:
            if typed.symbol is symbol:
                return typed.type
        return None


class TypeChecker:
    def __init__(self, resolution: ResolutionResult) -> None:
        self._resolution = resolution
        self._expression_types: dict[int, TypedExpression] = {}
        self._symbol_types: dict[int, TypedSymbol] = {}
        self._mutable_symbols: dict[int, bool] = {}
        self._diagnostics: list[Diagnostic] = []

    def check(self, program: Program) -> TypeCheckResult:
        self._expression_types = {}
        self._symbol_types = {}
        self._mutable_symbols = {}
        self._diagnostics = []
        for statement in program.statements:
            self._check_statement(statement)
        return TypeCheckResult(
            resolution=self._resolution,
            expressions=tuple(self._expression_types.values()),
            symbols=tuple(self._symbol_types.values()),
            diagnostics=tuple(self._diagnostics),
        )

    def _record_expression(
        self, expression: Expression, semantic_type: PrimitiveType
    ) -> PrimitiveType:
        self._expression_types[id(expression)] = TypedExpression(expression, semantic_type)
        return semantic_type

    def _record_symbol(self, symbol: Symbol, semantic_type: PrimitiveType) -> None:
        self._symbol_types[symbol.id] = TypedSymbol(symbol, semantic_type)

    def _symbol_type(self, symbol: Symbol | None) -> PrimitiveType:
        if symbol is None:
            return PrimitiveType.ERROR
        typed = self._symbol_types.get(symbol.id)
        return PrimitiveType.ERROR if typed is None else typed.type

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
                f"Cannot assign {initializer_type.value} to {declared_type.value}.",
                declaration.initializer.span,
            )
        if symbol is not None:
            self._record_symbol(symbol, static_type)
            self._mutable_symbols[symbol.id] = symbol.kind is SymbolKind.VAR_BINDING

    def _check_parameter(self, parameter: Parameter) -> None:
        semantic_type = self._resolve_annotation(parameter.type_annotation)
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
            for parameter in statement.parameters:
                self._check_parameter(parameter)
            self._check_block(statement.body)
        elif isinstance(statement, ReturnStatement):
            if statement.value is not None:
                self._infer(statement.value)
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
                f"Condition must be Bool, not {condition_type.value}.",
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
                f"Cannot assign {result_type.value} to {target_type.value}.",
                statement.value.span,
            )

    def _infer(self, expression: Expression) -> PrimitiveType:
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
            self._infer(expression.callee)
            for argument in expression.arguments:
                self._infer(argument.value)
            result = PrimitiveType.ERROR
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
            f"Operator {expression.operator.name} is invalid for {operand.value}.",
            expression.span,
        )
        return PrimitiveType.ERROR

    def _infer_binary_types(
        self,
        operator: BinaryOperator,
        left: PrimitiveType,
        right: PrimitiveType,
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
            f"Operator {operator.name} cannot combine {left.value} and {right.value}.",
            span,
        )
        return PrimitiveType.ERROR
