from collections.abc import Callable

import pytest

from kaj.parser import ParserResult


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ("let = 1", "PARSE_EXPECTED_IDENTIFIER"),
        ("let x =", "PARSE_EXPECTED_EXPRESSION"),
        ("foo(1", "PARSE_EXPECTED_TOKEN"),
        ("items[0", "PARSE_EXPECTED_TOKEN"),
        ("if ready { run()", "PARSE_EXPECTED_TOKEN"),
        ("fn f(x Int) -> Int {}", "PARSE_EXPECTED_TOKEN"),
        ("fn f() Int {}", "PARSE_EXPECTED_TOKEN"),
        ("fn f() -> {}", "PARSE_EXPECTED_TYPE"),
        ("type User", "PARSE_EXPECTED_TOKEN"),
        ("1 = 2", "PARSE_INVALID_ASSIGNMENT_TARGET"),
        ("f(a: 1, b)", "PARSE_POSITIONAL_AFTER_NAMED_ARGUMENT"),
    ],
)
def test_required_diagnostics(parse: Callable[[str], ParserResult], source: str, code: str) -> None:
    result = parse(source)

    assert result.diagnostics[0].code == code
    assert result.diagnostics[0].span.start.offset <= result.diagnostics[0].span.end.offset


def test_missing_expression_recovers_at_next_statement(
    parse: Callable[[str], ParserResult],
) -> None:
    result = parse("let x = let y = 20")

    assert result.diagnostics[0].code == "PARSE_EXPECTED_EXPRESSION"
    assert len(result.program.statements) == 1
    assert result.program.statements[0].name == "y"  # type: ignore[attr-defined]
