from kaj.lexer import Lexer
from kaj.parser import Parser
from kaj.semantic import Resolver, TypeChecker


def diagnostics(source: str) -> list[str]:
    lexed = Lexer(source).tokenize()
    parsed = Parser(lexed.tokens).parse()
    assert not lexed.diagnostics and not parsed.diagnostics
    resolved = Resolver(include_builtins=True).resolve(parsed.program)
    checked = TypeChecker(resolved).check(parsed.program)
    return [item.code for item in (*resolved.diagnostics, *checked.diagnostics)]


def test_enum_diagnostics_and_exhaustiveness() -> None:
    source = """enum Status { pending complete }
let status = Status.pending
match status { pending => print("pending") }
"""
    assert diagnostics(source) == ["NON_EXHAUSTIVE_MATCH"]


def test_payload_and_pattern_diagnostics() -> None:
    source = """enum Message { text(value: String) text(other: Int) }
let message = Message.text(value: 1)
match message { text(a, b) => print(a) missing => print("x") }
"""
    codes = diagnostics(source)
    assert "TYPE_DUPLICATE_VARIANT" in codes
    assert "TYPE_MISMATCH" in codes
    assert "TYPE_PATTERN_ARITY_MISMATCH" in codes
    assert "TYPE_UNKNOWN_VARIANT" in codes


def test_enum_type_namespace_and_forward_references() -> None:
    assert diagnostics("enum A { next(value: B) } enum B { back(value: A) }") == []
    assert diagnostics("type Status { value: Int } enum Status { pending }") == [
        "TYPE_DUPLICATE_TYPE_NAME"
    ]


def test_exhaustive_match_counts_as_definite_return() -> None:
    source = """enum Status { pending complete }
fn code(status: Status) -> Int {
  match status { pending => return 0 complete => return 1 }
}
"""
    assert diagnostics(source) == []
