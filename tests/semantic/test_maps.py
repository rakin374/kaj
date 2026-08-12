from kaj.ast import BindingDeclaration, IndexExpression, MatchStatement
from kaj.lexer import Lexer
from kaj.parser import Parser
from kaj.semantic import (
    MapType,
    OptionalType,
    PrimitiveType,
    Resolver,
    TypeChecker,
)


def check(source: str):
    lexed = Lexer(source).tokenize()
    parsed = Parser(lexed.tokens).parse()
    assert not lexed.diagnostics and not parsed.diagnostics
    resolved = Resolver(include_builtins=True).resolve(parsed.program)
    checked = TypeChecker(resolved).check(parsed.program)
    return parsed.program, resolved, checked


def codes(source: str) -> list[str]:
    _, resolved, checked = check(source)
    return [item.code for item in (*resolved.diagnostics, *checked.diagnostics)]


def test_map_annotation_arity_nesting_and_key_restrictions() -> None:
    assert (
        codes(
            "let a: Map<String, Optional<Int>> = {} let b: Optional<Map<String, List<Int>>> = none"
        )
        == []
    )
    assert codes("let a: Map = {} let b: Map<String> = {}") == [
        "TYPE_INVALID_TYPE_ARGUMENTS",
        "TYPE_INVALID_TYPE_ARGUMENTS",
    ]
    assert codes("let bad: Map<List<Int>, String> = {}") == ["TYPE_INVALID_MAP_KEY_TYPE"]


def test_map_literal_inference_and_numeric_common_types() -> None:
    program, resolution, checked = check(
        'let plain = {"a": 1, "b": 2} let values = {"a": 1, "b": 2.5} let keys = {1: "a", 2.5: "b"}'
    )
    assert not resolution.diagnostics and not checked.diagnostics
    expected = (
        MapType(PrimitiveType.STRING, PrimitiveType.INT),
        MapType(PrimitiveType.STRING, PrimitiveType.DECIMAL),
        MapType(PrimitiveType.DECIMAL, PrimitiveType.STRING),
    )
    for statement, semantic_type in zip(program.statements, expected, strict=True):
        assert isinstance(statement, BindingDeclaration)
        symbol = resolution.symbol_for_declaration(statement)
        assert symbol is not None
        assert checked.type_of_symbol(symbol) == semantic_type


def test_empty_context_mismatch_and_invariance() -> None:
    assert codes("let empty = {}") == ["TYPE_CANNOT_INFER_MAP_TYPE"]
    assert codes('let bad = {"a": 1, 2: 2}') == ["TYPE_MISMATCH"]
    assert codes('let bad = {"a": 1, "b": "two"}') == ["TYPE_MISMATCH"]
    assert codes('let a = {"a": 1} let b: Map<String, Decimal> = a') == ["TYPE_MISMATCH"]


def test_lookup_returns_optional_and_checks_key() -> None:
    program, resolution, checked = check(
        'let values: Map<String, Int> = {"a": 1} '
        'match values["a"] { some(value) => print(value) none => print("missing") }'
    )
    assert not resolution.diagnostics and not checked.diagnostics
    match = program.statements[1]
    assert isinstance(match, MatchStatement) and isinstance(match.scrutinee, IndexExpression)
    assert checked.type_of_expression(match.scrutinee) == OptionalType(PrimitiveType.INT)
    assert codes("let values: Map<String, Int> = {} let x = values[1]") == ["TYPE_MISMATCH"]
    assert codes("let values: Map<Decimal, Int> = {} let x = values[1]") == []


def test_map_count_functions_and_no_iteration_or_mutation() -> None:
    assert (
        codes(
            "fn find(values: Map<String, Int>, key: String) -> Optional<Int> { return values[key] }"
        )
        == []
    )
    assert codes('let values = {"a": 1} let n = values.count') == []
    assert codes('let values = {"a": 1} let n = values.keys') == ["TYPE_UNKNOWN_MEMBER"]
    assert "TYPE_NOT_ITERABLE" in codes('let values = {"a": 1} for item in values { break }')
    assert "TYPE_MISMATCH" in codes('let values = {"a": 1} values["a"] = 2')
