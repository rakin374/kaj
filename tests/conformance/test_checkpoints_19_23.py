from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from kaj.formatting import format_program
from kaj.pipeline import compile_source, parse_source
from kaj.runtime import KajRange, decode_utf8
from kaj.semantic import PrimitiveType, ResultType
from kaj.serialization import ast_from_json_value, ast_to_json_value

from .helpers import compile_error_codes, run_ok


def test_break_and_continue_execute_in_for_and_while() -> None:
    result = run_ok(
        """for value in [1, 2, 3, 4, 5] {
    if value == 3 { continue }
    if value == 5 { break }
    print(value)
}
var n = 0
while n < 5 {
    n += 1
    if n == 2 { continue }
    if n == 4 { break }
    print(n)
}
"""
    )
    assert result.stdout == "1\n2\n4\n1\n3\n"


def test_nested_loop_control_targets_nearest_loop_and_return_still_escapes() -> None:
    result = run_ok(
        """fn find() -> Int {
    for outer in range(0, 3) {
        for inner in range(0, 4) {
            if inner == 1 { continue }
            if inner == 2 { break }
            print(outer)
        }
    }
    while false { return 8 }
    return 9
}
print(find())
"""
    )
    assert result.stdout == "0\n1\n2\n9\n"


def test_mixed_nested_loop_shapes_consume_only_their_own_signals() -> None:
    result = run_ok(
        """var outer = 0
while outer < 2 {
    outer += 1
    var inner = 0
    while inner < 3 {
        inner += 1
        if inner == 2 { break }
        print("w{outer}{inner}")
    }
}
for a in range(0, 2) {
    var b = 0
    while b < 3 { b += 1 if b == 2 { continue } print("f{a}{b}") }
}
var c = 0
while c < 2 {
    c += 1
    for d in range(0, 3) { if d == 1 { break } print("m{c}{d}") }
}
"""
    )
    assert result.stdout == "w11\nw21\nf01\nf03\nf11\nf13\nm10\nm20\n"


def test_loop_control_outside_loop_has_exact_diagnostics() -> None:
    assert compile_error_codes("break") == ("CONTROL_BREAK_OUTSIDE_LOOP",)
    assert compile_error_codes("continue") == ("CONTROL_CONTINUE_OUTSIDE_LOOP",)


def test_range_is_lazy_end_exclusive_and_empty_when_descending() -> None:
    assert KajRange(0, 1_000_000_000).end == 1_000_000_000
    result = run_ok(
        """for value in range(3, 7) { print(value) }
for value in range(5, 2) { print(value) }
"""
    )
    assert result.stdout == "3\n4\n5\n6\n"
    assert compile_error_codes("for value in range(0.0, 2) {}") == ("TYPE_MISMATCH",)
    assert compile_error_codes("range(0)") == ("TYPE_MISSING_ARGUMENT",)
    assert compile_error_codes("range(0, 1, 2)") == ("TYPE_TOO_MANY_ARGUMENTS",)


def test_interpolation_conversion_and_utf8_round_trip() -> None:
    result = run_ok(
        """let name = "Alice"
let count = 2
print("{name} has {count + 1} items and {{braces}}")
print(String(true))
print(String(2.50))
let encoded: Bytes = utf8_encode("café")
match utf8_decode(encoded) {
    ok(text) => print(text)
    err(message) => print(message)
}
"""
    )
    assert result.stdout == "Alice has 3 items and {braces}\ntrue\n2.50\ncafé\n"
    assert compile_error_codes("let x: String = 1") == ("TYPE_MISMATCH",)
    assert compile_error_codes("utf8_encode(1)") == ("TYPE_MISMATCH",)


def test_invalid_utf8_is_a_typed_result_without_replacement() -> None:
    result_type = ResultType(PrimitiveType.STRING, PrimitiveType.STRING)
    decoded = decode_utf8(b"\xff", result_type)
    assert decoded.type == result_type
    assert decoded.variant == "err"
    assert decoded.payload == ("invalid UTF-8",)


def test_interpolation_ast_json_schema_and_formatter_are_deterministic() -> None:
    parsed = parse_source('let x="value={1+2}, {{ok}}"')
    assert parsed.diagnostics == ()
    encoded = ast_to_json_value(parsed.program)
    assert ast_from_json_value(encoded) == parsed.program
    schema = json.loads((Path(__file__).parents[2] / "schemas/ast/v1.json").read_text())
    jsonschema.validate(encoded, schema)
    formatted = format_program(parsed.program)
    assert formatted == 'let x = "value={1 + 2}, {{ok}}"\n'
    reparsed = parse_source(formatted)
    assert reparsed.diagnostics == ()
    assert format_program(reparsed.program) == formatted

    escaped_only = parse_source('print("{{literal}}")')
    assert escaped_only.diagnostics == ()
    escaped_formatted = format_program(escaped_only.program)
    assert escaped_formatted == 'print("{{literal}}")\n'

    unknown = compile_source('print("before {missing} after")')
    assert tuple(item.code for item in unknown.diagnostics) == ("RESOLVE_UNKNOWN_NAME",)
    assert unknown.diagnostics[0].span.start.offset == 6
    assert unknown.diagnostics[0].span.end.offset == len('print("before {missing} after"')


def test_list_first_last_and_map_iteration_are_safe_and_ordered() -> None:
    result = run_ok(
        """let empty: List<Int> = []
match empty.first { some(value) => print(value) none => print("empty") }
let values = [1, 2, 3]
match values.first { some(value) => print(value) none => print(0) }
match values.last { some(value) => print(value) none => print(0) }
let entries = {"b": 2, "a": 1, "c": 3}
for entry in entries {
    if entry.key == "a" { continue }
    print(entry.key)
    if entry.key == "c" { break }
}
"""
    )
    assert result.stdout == "empty\n1\n3\nb\nc\n"


def test_tagged_enum_and_newtype_equality_preserve_nominal_identity() -> None:
    result = run_ok(
        """newtype UserId = String
enum State { ready blocked(reason: String) }
let a: Optional<Int> = some(1)
let b: Optional<Int> = none
let ok_a: Result<Int, String> = ok(1)
let ok_b: Result<Int, String> = ok(1)
print(a == some(1))
print(a == b)
print(ok_a == ok_b)
print(State.ready == State.ready)
print(State.blocked(reason: "x") == State.blocked(reason: "x"))
print(UserId("a") == UserId("a"))
"""
    )
    assert result.stdout == "true\nfalse\ntrue\ntrue\ntrue\ntrue\n"
    assert compile_error_codes(
        'newtype A = String newtype B = String let x = A("a") == B("a")'
    ) == ("TYPE_MISMATCH",)
    assert compile_error_codes("let x = [1] == [1]") == ("TYPE_MISMATCH",)
    assert compile_error_codes(
        "let a: Optional<List<Int>> = some([1]) "
        "let b: Optional<List<Int>> = some([1]) let same = a == b"
    ) == ("TYPE_MISMATCH",)


def test_structured_display_is_kaj_defined_and_deterministic() -> None:
    result = run_ok(
        """newtype UserId = String
enum State { ready blocked(reason: String) }
type User { id: UserId name: String }
let optional: Optional<Int> = some(10)
let outcome: Result<Int, String> = err("bad")
print([1, 2, 3])
print({"Alice": 30, "Bob": 40})
print(optional)
print(outcome)
print(State.blocked(reason: "review"))
print(UserId("abc"))
print(User { id: UserId("u1"), name: "Alice" })
"""
    )
    assert result.stdout == (
        "[1, 2, 3]\n"
        '{"Alice": 30, "Bob": 40}\n'
        "some(10)\n"
        'err("bad")\n'
        'State.blocked(reason: "review")\n'
        'UserId("abc")\n'
        'User { id: UserId("u1"), name: "Alice" }\n'
    )


def test_all_new_programs_compile_without_unexpected_diagnostics() -> None:
    compiled = compile_source("for value in range(0, 2) { print(\"{value}\") }")
    assert tuple(item.code for item in compiled.diagnostics) == ()
