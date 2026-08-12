from copy import deepcopy

import pytest

from kaj.ast import Program
from kaj.serialization import ASTJSONError, ast_from_json, ast_from_json_value, ast_to_json_value
from kaj.source import SourceLocation, SourceSpan

SPAN = SourceSpan(SourceLocation(0, 1, 1), SourceLocation(0, 1, 1))


def empty_document() -> dict[str, object]:
    return ast_to_json_value(Program(span=SPAN, statements=()))


def assert_error(value: object, code: str, path: str | None = None) -> None:
    with pytest.raises(ASTJSONError) as raised:
        ast_from_json_value(value)
    assert raised.value.code == code
    if path is not None:
        assert raised.value.path_string == path


def test_invalid_json_has_structured_error() -> None:
    with pytest.raises(ASTJSONError) as raised:
        ast_from_json("{")

    assert raised.value.code == "ASTJSON_INVALID_JSON"
    assert raised.value.path_string == "$"


@pytest.mark.parametrize("field", ["format", "version", "program"])
def test_missing_envelope_fields(field: str) -> None:
    document = empty_document()
    del document[field]

    assert_error(document, "ASTJSON_MISSING_FIELD", f"$.{field}")


def test_wrong_format_and_unsupported_version() -> None:
    wrong_format = empty_document()
    wrong_format["format"] = "other"
    assert_error(wrong_format, "ASTJSON_INVALID_DOCUMENT", "$.format")

    wrong_version = empty_document()
    wrong_version["version"] = 2
    assert_error(wrong_version, "ASTJSON_UNSUPPORTED_VERSION", "$.version")


def test_unknown_kind_missing_field_and_extra_field() -> None:
    unknown = empty_document()
    unknown["program"]["kind"] = "future_program"  # type: ignore[index]
    assert_error(unknown, "ASTJSON_UNKNOWN_NODE_KIND", "$.program.kind")

    missing = empty_document()
    del missing["program"]["statements"]  # type: ignore[index]
    assert_error(missing, "ASTJSON_MISSING_FIELD", "$.program.statements")

    extra = empty_document()
    extra["program"]["extra"] = True  # type: ignore[index]
    assert_error(extra, "ASTJSON_INVALID_FIELD", "$.program.extra")


def test_wrong_field_type_and_wrong_program_category() -> None:
    wrong_type = empty_document()
    wrong_type["program"]["statements"] = "not-an-array"  # type: ignore[index]
    assert_error(wrong_type, "ASTJSON_INVALID_FIELD", "$.program.statements")

    wrong_category = empty_document()
    wrong_category["program"] = {
        "kind": "identifier",
        "name": "x",
        "span": deepcopy(wrong_category["program"]["span"]),  # type: ignore[index]
    }
    assert_error(wrong_category, "ASTJSON_INVALID_FIELD", "$.program")


@pytest.mark.parametrize(
    ("kind", "value"),
    [("integer_literal", "ten"), ("decimal_literal", "abc")],
)
def test_invalid_numeric_strings(kind: str, value: str) -> None:
    document = empty_document()
    node = {"kind": kind, "value": value, "span": deepcopy(document["program"]["span"])}  # type: ignore[index]
    document["program"]["statements"] = [  # type: ignore[index]
        {"kind": "expression_statement", "expression": node, "span": node["span"]}
    ]

    assert_error(document, "ASTJSON_INVALID_FIELD")


def test_numeric_json_numbers_are_not_coerced() -> None:
    document = empty_document()
    node = {"kind": "integer_literal", "value": 10, "span": deepcopy(document["program"]["span"])}  # type: ignore[index]
    document["program"]["statements"] = [  # type: ignore[index]
        {"kind": "expression_statement", "expression": node, "span": node["span"]}
    ]

    assert_error(document, "ASTJSON_INVALID_FIELD")


def test_invalid_enum_and_child_category() -> None:
    document = empty_document()
    span = deepcopy(document["program"]["span"])  # type: ignore[index]
    literal = {"kind": "integer_literal", "value": "1", "span": span}
    binary = {
        "kind": "binary_expression",
        "operator": "times",
        "left": literal,
        "right": literal,
        "span": span,
    }
    document["program"]["statements"] = [  # type: ignore[index]
        {"kind": "expression_statement", "expression": binary, "span": span}
    ]
    assert_error(document, "ASTJSON_INVALID_ENUM_VALUE")

    wrong_child = deepcopy(empty_document())
    wrong_child["program"]["statements"] = [literal]  # type: ignore[index]
    assert_error(wrong_child, "ASTJSON_INVALID_FIELD", "$.program.statements[0]")
