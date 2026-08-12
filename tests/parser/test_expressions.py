from collections.abc import Callable

from kaj.ast import (
    BinaryExpression,
    BinaryOperator,
    ExpressionStatement,
    Identifier,
    UnaryExpression,
    UnaryOperator,
)
from kaj.parser import ParserResult


def expression(result: ParserResult) -> object:
    statement = result.program.statements[0]
    assert isinstance(statement, ExpressionStatement)
    return statement.expression


def test_identifier_and_grouping(parse: Callable[[str], ParserResult]) -> None:
    identifier = expression(parse("value"))
    grouped = expression(parse("(1 + 2)"))

    assert isinstance(identifier, Identifier)
    assert identifier.name == "value"
    assert isinstance(grouped, BinaryExpression)
    assert grouped.operator is BinaryOperator.ADD
    assert grouped.span.start.offset == 0
    assert grouped.span.end.offset == 7


def test_unary_operators_and_nesting(parse: Callable[[str], ParserResult]) -> None:
    positive = expression(parse("+value"))
    negative = expression(parse("-42"))
    nested = expression(parse("not not ready"))

    assert isinstance(positive, UnaryExpression)
    assert positive.operator is UnaryOperator.POSITIVE
    assert isinstance(negative, UnaryExpression)
    assert negative.operator is UnaryOperator.NEGATE
    assert isinstance(nested, UnaryExpression)
    assert nested.operator is UnaryOperator.NOT
    assert isinstance(nested.operand, UnaryExpression)
