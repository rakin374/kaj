import pytest

from kaj.lexer import Lexer, TokenKind


@pytest.mark.parametrize("source", ["", " \t\r\n", "// only", "/* only */"])
def test_trivia_only_source_has_exactly_one_eof(source: str) -> None:
    result = Lexer(source).tokenize()

    assert [token.kind for token in result.tokens] == [TokenKind.EOF]
    assert result.diagnostics == []


def test_repeated_tokenization_still_has_exactly_one_eof() -> None:
    lexer = Lexer("let")

    first = lexer.tokenize()
    second = lexer.tokenize()

    assert [token.kind for token in first.tokens] == [TokenKind.LET, TokenKind.EOF]
    assert [token.kind for token in second.tokens] == [TokenKind.LET, TokenKind.EOF]


def test_binding_acceptance_example() -> None:
    result = Lexer("let x = 10").tokenize()

    assert [token.kind for token in result.tokens] == [
        TokenKind.LET,
        TokenKind.IDENTIFIER,
        TokenKind.EQUAL,
        TokenKind.INTEGER,
        TokenKind.EOF,
    ]


def test_realistic_function_source() -> None:
    source = """fn add(a: Int, b: Int) -> Int {
    return a + b
}
"""
    result = Lexer(source, filename="add.kaj").tokenize()

    assert result.diagnostics == []
    assert result.tokens[0].kind is TokenKind.FN
    assert result.tokens[-2].kind is TokenKind.RIGHT_BRACE
    assert result.tokens[-1].kind is TokenKind.EOF
    assert sum(token.kind is TokenKind.EOF for token in result.tokens) == 1


def test_condition_acceptance_example() -> None:
    result = Lexer('if x >= 10 and x != 20 { print("hello") }').tokenize()
    kinds = [token.kind for token in result.tokens]

    assert TokenKind.IF in kinds
    assert TokenKind.GREATER_EQUAL in kinds
    assert TokenKind.AND in kinds
    assert TokenKind.BANG_EQUAL in kinds
    assert TokenKind.STRING in kinds
