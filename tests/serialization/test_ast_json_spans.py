from copy import deepcopy

import pytest

from kaj.ast import Program
from kaj.serialization import ASTJSONError, ast_from_json_value, ast_to_json_value
from kaj.source import SourceLocation, SourceSpan


def test_spans_round_trip_exactly(span: SourceSpan) -> None:
    program = Program(span=span, statements=())

    assert ast_from_json_value(ast_to_json_value(program)).span == span


@pytest.mark.parametrize(
    ("field_path", "value"),
    [
        (("start", "offset"), -1),
        (("start", "line"), 0),
        (("start", "column"), 0),
        (("end", "offset"), -1),
    ],
)
def test_invalid_location_values_are_rejected(
    span: SourceSpan, field_path: tuple[str, str], value: int
) -> None:
    document = deepcopy(ast_to_json_value(Program(span=span, statements=())))
    location = document["program"]["span"]  # type: ignore[index]
    location[field_path[0]][field_path[1]] = value  # type: ignore[index]

    with pytest.raises(ASTJSONError) as raised:
        ast_from_json_value(document)
    assert raised.value.code == "ASTJSON_INVALID_FIELD"


def test_end_offset_cannot_precede_start() -> None:
    span = SourceSpan(SourceLocation(5, 1, 6), SourceLocation(6, 1, 7))
    document = deepcopy(ast_to_json_value(Program(span=span, statements=())))
    document["program"]["span"]["end"]["offset"] = 4  # type: ignore[index]

    with pytest.raises(ASTJSONError) as raised:
        ast_from_json_value(document)
    assert raised.value.path_string == "$.program.span.end.offset"
