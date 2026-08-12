from collections.abc import Callable

import pytest

from kaj.ast import Program, RecordConstructionExpression, RecordDeclaration
from kaj.serialization import ASTJSONError, ast_from_json_value, ast_to_json_value


def test_record_nodes_round_trip(parse_program: Callable[[str], Program]) -> None:
    program = parse_program(
        'type User { name: String age: Int }\nlet user = User { name: "A", age: 1 }'
    )
    restored = ast_from_json_value(ast_to_json_value(program))

    assert restored == program
    assert isinstance(restored.statements[0], RecordDeclaration)
    construction = restored.statements[1].initializer  # type: ignore[union-attr]
    assert isinstance(construction, RecordConstructionExpression)


def test_record_json_rejects_malformed_field_node(
    parse_program: Callable[[str], Program],
) -> None:
    value = ast_to_json_value(parse_program("type User { name: String }"))
    declaration = value["program"]["statements"][0]  # type: ignore[index]
    declaration["fields"][0]["kind"] = "identifier"  # type: ignore[index]

    with pytest.raises(ASTJSONError) as caught:
        ast_from_json_value(value)
    assert caught.value.code == "ASTJSON_INVALID_FIELD"
