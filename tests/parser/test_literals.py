from collections.abc import Callable
from decimal import Decimal

import pytest

from kaj.ast import (
    BooleanLiteral,
    DecimalLiteral,
    ExpressionStatement,
    IntegerLiteral,
    NoneLiteral,
    StringLiteral,
)
from kaj.parser import ParserResult


@pytest.mark.parametrize(
    ("source", "node_type", "value"),
    [
        ("42", IntegerLiteral, 42),
        ("19.99", DecimalLiteral, Decimal("19.99")),
        ('"Kaj"', StringLiteral, "Kaj"),
        ("true", BooleanLiteral, True),
        ("false", BooleanLiteral, False),
    ],
)
def test_value_literals(
    parse: Callable[[str], ParserResult], source: str, node_type: type[object], value: object
) -> None:
    result = parse(source)
    statement = result.program.statements[0]

    assert result.diagnostics == ()
    assert isinstance(statement, ExpressionStatement)
    assert isinstance(statement.expression, node_type)
    assert statement.expression.value == value


def test_none_literal(parse: Callable[[str], ParserResult]) -> None:
    statement = parse("none").program.statements[0]

    assert isinstance(statement, ExpressionStatement)
    assert isinstance(statement.expression, NoneLiteral)
