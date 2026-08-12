from kaj.ast import BindingDeclaration, NoneLiteral
from kaj.lexer import Lexer
from kaj.parser import Parser
from kaj.semantic import OptionalType, PrimitiveType, Resolver, ResultType, TypeChecker


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


def test_nested_standard_tagged_types_and_invalid_arities() -> None:
    assert (
        codes(
            "let x: Optional<Result<Int, String>> = none "
            "let y: Result<Optional<Int>, String> = ok(none)"
        )
        == []
    )
    assert codes("let x: Optional = none let y: Result<Int> = ok(1)") == [
        "TYPE_INVALID_TYPE_ARGUMENTS",
        "TYPE_INVALID_TYPE_ARGUMENTS",
    ]


def test_primitive_none_and_contextual_optional_none_have_distinct_types() -> None:
    program, _, checked = check("let primitive = none let optional: Optional<Int> = none")
    first, second = program.statements
    assert isinstance(first, BindingDeclaration) and isinstance(first.initializer, NoneLiteral)
    assert isinstance(second, BindingDeclaration) and isinstance(second.initializer, NoneLiteral)
    assert checked.type_of_expression(first.initializer) is PrimitiveType.NONE
    assert checked.type_of_expression(second.initializer) == OptionalType(PrimitiveType.INT)


def test_some_inference_context_and_invariance() -> None:
    program, resolution, checked = check(
        "let inferred = some(10) let promoted: Optional<Decimal> = some(10)"
    )
    assert not resolution.diagnostics and not checked.diagnostics
    inferred = program.statements[0]
    assert isinstance(inferred, BindingDeclaration)
    symbol = resolution.symbol_for_declaration(inferred)
    assert symbol is not None
    assert checked.type_of_symbol(symbol) == OptionalType(PrimitiveType.INT)
    assert codes("let a = some(1) let b: Optional<Decimal> = a") == ["TYPE_MISMATCH"]


def test_result_requires_context_and_is_invariant() -> None:
    assert codes('let a = ok(1) let b = err("bad")') == [
        "TYPE_CANNOT_INFER_RESULT_TYPE",
        "TYPE_CANNOT_INFER_RESULT_TYPE",
    ]
    program, resolution, checked = check(
        "let a: Result<Decimal, String> = ok(1) let b: Result<Int, Decimal> = err(2)"
    )
    assert not resolution.diagnostics and not checked.diagnostics
    a = program.statements[0]
    assert isinstance(a, BindingDeclaration)
    symbol = resolution.symbol_for_declaration(a)
    assert symbol is not None
    assert checked.type_of_symbol(symbol) == ResultType(PrimitiveType.DECIMAL, PrimitiveType.STRING)
    assert codes("let a: Result<Int, String> = ok(1) let b: Result<Decimal, String> = a") == [
        "TYPE_MISMATCH"
    ]


def test_context_propagates_through_returns_calls_records_and_lists() -> None:
    source = """type Box { value: Optional<Int> result: Result<Int, String> }
fn use(value: Optional<Int>) -> None {}
fn handle(value: Result<Int, String>) -> None {}
fn find() -> Optional<Int> { return none }
fn parse() -> Result<Int, String> { return ok(10) }
let box = Box { value: none, result: err("bad") }
let values: List<Optional<Int>> = [some(1), none]
let results: List<Result<Int, String>> = [ok(1), err("bad")]
use(none)
handle(ok(10))
"""
    assert codes(source) == []


def test_optional_and_result_match_diagnostics_and_definite_return() -> None:
    assert codes("let x: Optional<Int> = none match x { some(v) => print(v) }") == [
        "NON_EXHAUSTIVE_MATCH"
    ]
    assert (
        codes("let x: Result<Int, String> = ok(1) match x { ok(v) => print(v) err(e) => print(e) }")
        == []
    )
    assert (
        codes(
            "fn unwrap(x: Optional<Int>) -> Int { match x { some(v) => return v none => return 0 } }"
        )
        == []
    )
