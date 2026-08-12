from collections.abc import Callable

import pytest

from kaj.ast import ExpressionStatement, ListLiteral, MapLiteral
from kaj.parser import ParserResult


@pytest.mark.parametrize(("source", "length"), [("[]", 0), ("[1]", 1), ("[1, 2, 3]", 3)])
def test_list_literals(parse: Callable[[str], ParserResult], source: str, length: int) -> None:
    statement = parse(source).program.statements[0]

    assert isinstance(statement, ExpressionStatement)
    assert isinstance(statement.expression, ListLiteral)
    assert len(statement.expression.elements) == length


@pytest.mark.parametrize(
    ("source", "length"),
    [("{}", 0), ('{"a": 1}', 1), ('{"a": 1, "b": 2}', 2)],
)
def test_map_literals(parse: Callable[[str], ParserResult], source: str, length: int) -> None:
    statement = parse(source).program.statements[0]

    assert isinstance(statement, ExpressionStatement)
    assert isinstance(statement.expression, MapLiteral)
    assert len(statement.expression.entries) == length
