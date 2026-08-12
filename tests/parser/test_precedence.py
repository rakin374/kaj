from collections.abc import Callable

import pytest

from kaj.ast import (
    BinaryExpression,
    BinaryOperator,
    Expression,
    ExpressionStatement,
    UnaryExpression,
    UnaryOperator,
)
from kaj.parser import ParserResult


def parsed_expression(parse: Callable[[str], ParserResult], source: str) -> Expression:
    statement = parse(source).program.statements[0]
    assert isinstance(statement, ExpressionStatement)
    return statement.expression


@pytest.mark.parametrize(
    ("source", "root", "nested_side", "nested"),
    [
        ("1 + 2 * 3", BinaryOperator.ADD, "right", BinaryOperator.MULTIPLY),
        ("1 * 2 + 3", BinaryOperator.ADD, "left", BinaryOperator.MULTIPLY),
        ("a or b and c", BinaryOperator.OR, "right", BinaryOperator.AND),
        ("a == b < c", BinaryOperator.EQUAL, "right", BinaryOperator.LESS),
    ],
)
def test_precedence(
    parse: Callable[[str], ParserResult],
    source: str,
    root: BinaryOperator,
    nested_side: str,
    nested: BinaryOperator,
) -> None:
    expression = parsed_expression(parse, source)

    assert isinstance(expression, BinaryExpression)
    assert expression.operator is root
    child = expression.left if nested_side == "left" else expression.right
    assert isinstance(child, BinaryExpression)
    assert child.operator is nested


def test_ordinary_binary_operators_are_left_associative(
    parse: Callable[[str], ParserResult],
) -> None:
    expression = parsed_expression(parse, "10 - 3 - 2")

    assert isinstance(expression, BinaryExpression)
    assert expression.operator is BinaryOperator.SUBTRACT
    assert isinstance(expression.left, BinaryExpression)
    assert expression.left.operator is BinaryOperator.SUBTRACT


def test_power_is_right_associative(parse: Callable[[str], ParserResult]) -> None:
    expression = parsed_expression(parse, "2 ** 3 ** 2")

    assert isinstance(expression, BinaryExpression)
    assert expression.operator is BinaryOperator.POWER
    assert isinstance(expression.right, BinaryExpression)
    assert expression.right.operator is BinaryOperator.POWER


def test_power_binds_more_tightly_than_unary_minus(
    parse: Callable[[str], ParserResult],
) -> None:
    expression = parsed_expression(parse, "-2 ** 2")

    assert isinstance(expression, UnaryExpression)
    assert expression.operator is UnaryOperator.NEGATE
    assert isinstance(expression.operand, BinaryExpression)
    assert expression.operand.operator is BinaryOperator.POWER


def test_grouping_places_unary_minus_left_of_power(
    parse: Callable[[str], ParserResult],
) -> None:
    expression = parsed_expression(parse, "(-2) ** 2")

    assert isinstance(expression, BinaryExpression)
    assert expression.operator is BinaryOperator.POWER
    assert isinstance(expression.left, UnaryExpression)
