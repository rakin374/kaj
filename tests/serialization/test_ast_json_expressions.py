from decimal import Decimal

from kaj.ast import (
    BinaryExpression,
    BinaryOperator,
    BooleanLiteral,
    CallArgument,
    CallExpression,
    DecimalLiteral,
    ExpressionStatement,
    Identifier,
    IndexExpression,
    IntegerLiteral,
    ListLiteral,
    MapEntry,
    MapLiteral,
    MemberAccessExpression,
    NoneLiteral,
    Program,
    StringLiteral,
    UnaryExpression,
    UnaryOperator,
)
from kaj.serialization import ast_from_json_value, ast_to_json_value
from kaj.source import SourceSpan


def test_every_expression_and_helper_node_round_trips(span: SourceSpan) -> None:
    integer = IntegerLiteral(span=span, value=42)
    identifier = Identifier(span=span, name="items")
    call = CallExpression(
        span=span,
        callee=Identifier(span=span, name="send"),
        arguments=(
            CallArgument(span=span, name=None, value=StringLiteral(span=span, value="hello")),
            CallArgument(span=span, name="priority", value=integer),
        ),
    )
    expressions = (
        integer,
        DecimalLiteral(span=span, value=Decimal("19.99")),
        StringLiteral(span=span, value="Kaj"),
        BooleanLiteral(span=span, value=True),
        NoneLiteral(span=span),
        identifier,
        UnaryExpression(span=span, operator=UnaryOperator.NEGATE, operand=integer),
        BinaryExpression(
            span=span,
            left=integer,
            operator=BinaryOperator.POWER,
            right=integer,
        ),
        call,
        MemberAccessExpression(span=span, object=identifier, member="count"),
        IndexExpression(span=span, object=identifier, index=integer),
        ListLiteral(span=span, elements=(integer,)),
        MapLiteral(
            span=span,
            entries=(MapEntry(span=span, key=StringLiteral(span=span, value="x"), value=integer),),
        ),
    )
    program = Program(
        span=span,
        statements=tuple(ExpressionStatement(span=span, expression=item) for item in expressions),
    )

    assert ast_from_json_value(ast_to_json_value(program)) == program


def test_stable_expression_kinds_and_enum_strings(span: SourceSpan) -> None:
    expression = BinaryExpression(
        span=span,
        left=IntegerLiteral(span=span, value=1),
        operator=BinaryOperator.NOT_EQUAL,
        right=IntegerLiteral(span=span, value=2),
    )
    program = Program(
        span=span, statements=(ExpressionStatement(span=span, expression=expression),)
    )
    value = ast_to_json_value(program)
    encoded = value["program"]["statements"][0]["expression"]  # type: ignore[index]

    assert encoded["kind"] == "binary_expression"  # type: ignore[index]
    assert encoded["operator"] == "not_equal"  # type: ignore[index]


def test_all_operator_values_use_the_frozen_external_strings(span: SourceSpan) -> None:
    integer = IntegerLiteral(span=span, value=1)
    unary_expected = {
        UnaryOperator.POSITIVE: "positive",
        UnaryOperator.NEGATE: "negate",
        UnaryOperator.NOT: "not",
    }
    binary_expected = {
        BinaryOperator.ADD: "add",
        BinaryOperator.SUBTRACT: "subtract",
        BinaryOperator.MULTIPLY: "multiply",
        BinaryOperator.DIVIDE: "divide",
        BinaryOperator.MODULO: "modulo",
        BinaryOperator.POWER: "power",
        BinaryOperator.EQUAL: "equal",
        BinaryOperator.NOT_EQUAL: "not_equal",
        BinaryOperator.LESS: "less",
        BinaryOperator.LESS_EQUAL: "less_equal",
        BinaryOperator.GREATER: "greater",
        BinaryOperator.GREATER_EQUAL: "greater_equal",
        BinaryOperator.AND: "and",
        BinaryOperator.OR: "or",
    }

    for operator, external in unary_expected.items():
        expression = UnaryExpression(span=span, operator=operator, operand=integer)
        program = Program(
            span=span,
            statements=(ExpressionStatement(span=span, expression=expression),),
        )
        encoded = ast_to_json_value(program)["program"]["statements"][0]["expression"]  # type: ignore[index]
        assert encoded["operator"] == external  # type: ignore[index]

    for operator, external in binary_expected.items():
        expression = BinaryExpression(
            span=span,
            left=integer,
            operator=operator,
            right=integer,
        )
        program = Program(
            span=span,
            statements=(ExpressionStatement(span=span, expression=expression),),
        )
        encoded = ast_to_json_value(program)["program"]["statements"][0]["expression"]  # type: ignore[index]
        assert encoded["operator"] == external  # type: ignore[index]
