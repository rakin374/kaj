import json
from collections.abc import Callable
from pathlib import Path

import jsonschema
import pytest

from kaj.ast import Program
from kaj.serialization import ast_to_json_value

SCHEMA_PATH = Path(__file__).parents[2] / "schemas" / "ast" / "v1.json"


@pytest.fixture(scope="module")
def schema() -> object:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_is_valid_draft_2020_12(schema: object) -> None:
    jsonschema.Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize(
    "source",
    [
        "let x = 10",
        "let x = -2 ** 2",
        "let missing = none",
        "var price: Decimal = 19.99",
        'let data = [foo().bar[0], {"x": true}]',
        "x += 1",
        "send(message, priority: 2)",
        "if ready { run() } else if waiting { wait() }",
        "while ready { break continue }",
        "for item in items { print(item) }",
        "fn noop() -> None { return }",
        "fn add(var a: Int, b: List<Int>) -> Int { return a + b[0] }",
        'type User { name: String age: Int } let user = User { name: "A", age: 1 }',
    ],
)
def test_emitted_documents_validate_against_schema(
    schema: object, parse_program: Callable[[str], Program], source: str
) -> None:
    jsonschema.validate(ast_to_json_value(parse_program(source)), schema)


def test_known_invalid_document_fails_schema(schema: object) -> None:
    invalid = {"format": "kaj-ast", "version": 1, "program": {"kind": "program"}}

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(invalid, schema)
