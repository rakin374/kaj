from collections.abc import Callable

from kaj.ast import (
    BindingDeclaration,
    MapLiteral,
    RecordConstructionExpression,
    RecordDeclaration,
)
from kaj.parser import ParserResult


def test_record_declaration_preserves_order_and_spans(
    parse: Callable[[str], ParserResult],
) -> None:
    declaration = parse("type User { name: String age: Int }").program.statements[0]
    assert isinstance(declaration, RecordDeclaration)

    assert declaration.name == "User"
    assert [field.name for field in declaration.fields] == ["name", "age"]
    assert declaration.span.start.offset == 0
    assert declaration.span.end.offset == 35


def test_record_construction_is_explicit_expression(
    parse: Callable[[str], ParserResult],
) -> None:
    statement = parse('let user = User { age: 30, name: "Alice" }').program.statements[0]
    assert isinstance(statement, BindingDeclaration)
    construction = statement.initializer
    assert isinstance(construction, RecordConstructionExpression)

    assert construction.type_name == "User"
    assert [field.name for field in construction.fields] == ["age", "name"]


def test_blocks_maps_and_records_remain_disambiguated(
    parse: Callable[[str], ParserResult],
) -> None:
    result = parse('if ready {}\nlet map = {"x": 1}\nlet empty = Empty {}')

    map_binding = result.program.statements[1]
    record_binding = result.program.statements[2]
    assert isinstance(map_binding, BindingDeclaration)
    assert isinstance(map_binding.initializer, MapLiteral)
    assert isinstance(record_binding, BindingDeclaration)
    assert isinstance(record_binding.initializer, RecordConstructionExpression)
