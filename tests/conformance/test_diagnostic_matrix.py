from __future__ import annotations

from pathlib import Path

import pytest

from kaj.lexer import Lexer
from kaj.pipeline import compile_source, parse_source
from kaj.runtime import Interpreter
from kaj.serialization import ASTJSONError, ast_from_json, ast_from_json_value

from .helpers import assert_diagnostic_codes, compile_error_codes


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ("@", "LEX_INVALID_CHARACTER"),
        ('"unterminated', "LEX_UNTERMINATED_STRING"),
        ('"bad\\q"', "LEX_INVALID_ESCAPE"),
        ("1.", "LEX_INVALID_NUMBER"),
        ("/* unterminated", "LEX_UNTERMINATED_COMMENT"),
    ],
)
def test_lexical_invalid_constructs_have_one_exact_code(source: str, code: str) -> None:
    assert_diagnostic_codes(Lexer(source).tokenize().diagnostics, (code,))


@pytest.mark.parametrize(
    ("source", "codes"),
    [
        ("let x =", ("PARSE_EXPECTED_EXPRESSION",)),
        ("let = 1", ("PARSE_EXPECTED_IDENTIFIER",)),
        ("if true print(1)", ("PARSE_EXPECTED_TOKEN",)),
        ("let x:", ("PARSE_EXPECTED_TYPE",)),
        ("1 = 2", ("PARSE_INVALID_ASSIGNMENT_TARGET",)),
        ("f(a: 1, 2)", ("PARSE_POSITIONAL_AFTER_NAMED_ARGUMENT",)),
    ],
)
def test_parser_invalid_constructs_have_exact_ordered_codes(
    source: str, codes: tuple[str, ...]
) -> None:
    assert_diagnostic_codes(parse_source(source).diagnostics, codes)


@pytest.mark.parametrize(
    ("source", "codes"),
    [
        ("let x = missing", ("RESOLVE_UNKNOWN_NAME",)),
        ("let x = 1 let x = 2", ("RESOLVE_DUPLICATE_NAME",)),
        ('let x: Int = "x"', ("TYPE_MISMATCH",)),
        ("let x = -true", ("TYPE_INVALID_OPERATOR",)),
        ("if 1 {}", ("TYPE_CONDITION_NOT_BOOL",)),
        ("let x: Missing = 1", ("TYPE_UNKNOWN_TYPE",)),
        ("let x = 1 x = 2", ("ASSIGN_TO_IMMUTABLE",)),
        ("let x = 1 x()", ("TYPE_NOT_CALLABLE",)),
        (
            "fn f(x: Int) -> None {} f(nope: 1)",
            ("TYPE_UNKNOWN_NAMED_ARGUMENT", "TYPE_MISSING_ARGUMENT"),
        ),
        ("fn f(x: Int) -> None {} f(1, x: 2)", ("TYPE_DUPLICATE_ARGUMENT",)),
        ("fn f(x: Int) -> None {} f()", ("TYPE_MISSING_ARGUMENT",)),
        ("fn f() -> None {} f(1)", ("TYPE_TOO_MANY_ARGUMENTS",)),
        ("fn f() -> Int {}", ("TYPE_MISSING_RETURN",)),
        ("return", ("TYPE_RETURN_OUTSIDE_FUNCTION",)),
        ("let xs = []", ("TYPE_CANNOT_INFER_LIST_ELEMENT",)),
        (
            "let xs: List<Int, String> = []",
            ("TYPE_INVALID_TYPE_ARGUMENTS", "TYPE_CANNOT_INFER_LIST_ELEMENT"),
        ),
        ("let xs = [1] print(xs.nope)", ("TYPE_UNKNOWN_MEMBER",)),
        ("for x in 1 {}", ("TYPE_NOT_ITERABLE",)),
        ("type A {} type A {}", ("TYPE_DUPLICATE_TYPE_NAME",)),
        ("type A { x: Int x: Int }", ("TYPE_DUPLICATE_FIELD",)),
        ("type A { x: Int } let a = A {}", ("TYPE_MISSING_FIELD",)),
        ("type A {} let a = A { x: 1 }", ("TYPE_UNKNOWN_FIELD",)),
        ("enum E { a a }", ("TYPE_DUPLICATE_VARIANT",)),
        ("enum E { a } let x = E.b", ("TYPE_UNKNOWN_VARIANT",)),
        ("enum E { a(x: Int) } let x = E.a", ("TYPE_INVALID_VARIANT_CONSTRUCTION",)),
        ("enum E { a(x: Int) } let x = E.a(x: 1) match x { a => {} }", ("TYPE_PATTERN_ARITY_MISMATCH",)),
        ("enum E { a } let x = E.a match x { a => {} a => {} }", ("TYPE_DUPLICATE_MATCH_CASE",)),
        ("match 1 { nope => {} }", ("TYPE_MATCH_REQUIRES_ENUM",)),
        ("enum E { a b } let x = E.a match x { a => {} }", ("NON_EXHAUSTIVE_MATCH",)),
        ("let x = ok(1)", ("TYPE_CANNOT_INFER_RESULT_TYPE",)),
        ("let x = {}", ("TYPE_CANNOT_INFER_MAP_TYPE",)),
        ("let x: Map<List<Int>, Int> = {}", ("TYPE_INVALID_MAP_KEY_TYPE",)),
        ("newtype A = A", ("TYPE_RECURSIVE_NEWTYPE",)),
    ],
)
def test_semantic_invalid_constructs_have_exact_ordered_codes(
    source: str, codes: tuple[str, ...]
) -> None:
    assert compile_error_codes(source) == codes


@pytest.mark.parametrize(
    ("operation", "code"),
    [
        (lambda: ast_from_json("{"), "ASTJSON_INVALID_JSON"),
        (lambda: ast_from_json_value([]), "ASTJSON_INVALID_DOCUMENT"),
        (
            lambda: ast_from_json_value({"format": "kaj-ast", "version": 2, "program": {}}),
            "ASTJSON_UNSUPPORTED_VERSION",
        ),
        (
            lambda: ast_from_json_value(
                {"format": "kaj-ast", "version": 1, "program": {"kind": "mystery"}}
            ),
            "ASTJSON_UNKNOWN_NODE_KIND",
        ),
    ],
)
def test_ast_json_invalid_documents_have_exact_codes(operation, code: str) -> None:
    with pytest.raises(ASTJSONError) as caught:
        operation()
    assert caught.value.code == code


def test_inconsistent_interpreter_inputs_report_internal_error_without_python_exception() -> None:
    compiled = compile_source("let x = 1")
    different = parse_source("let y = 2")
    assert compiled.resolution is not None and compiled.types is not None
    execution = Interpreter(compiled.resolution, compiled.types).interpret(different.program)
    assert execution.runtime_error is not None
    assert execution.runtime_error.code == "RUNTIME_INTERNAL_ERROR"


def test_every_implementation_diagnostic_code_is_named_by_a_behavior_test() -> None:
    root = Path(__file__).parents[2]
    implementation = "\n".join(path.read_text() for path in (root / "src" / "kaj").rglob("*.py"))
    tests = "\n".join(path.read_text() for path in (root / "tests").rglob("*.py"))
    prefixes = ("LEX_", "PARSE_", "ASTJSON_", "RESOLVE_", "TYPE_", "ASSIGN_", "RUNTIME_", "IMPORT_")
    import re

    codes = set(re.findall(r'"([A-Z][A-Z0-9_]+)"', implementation))
    stable = {code for code in codes if code.startswith(prefixes)}
    # Defensive-only guards that valid Kaj tokens/module names cannot currently reach.
    # They remain inventoried here so adding a reachable path cannot silently lose them.
    defensive_only = {"IMPORT_OUTSIDE_PROJECT", "PARSE_UNEXPECTED_TOKEN"}
    assert defensive_only <= stable
    tests += '\n"IMPORT_OUTSIDE_PROJECT"\n"PARSE_UNEXPECTED_TOKEN"'
    missing = sorted(code for code in stable if f'"{code}"' not in tests)
    assert missing == []
