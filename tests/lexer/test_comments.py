import pytest

from kaj.lexer import Lexer, TokenKind


@pytest.mark.parametrize(
    "source",
    [
        "// comment\nlet",
        "let // comment\n",
        "let // comment",
        "/* comment */ let",
        "/* multi\nline */ let",
        "var /* between */ value",
    ],
)
def test_comments_are_skipped(source: str) -> None:
    result = Lexer(source).tokenize()

    assert all(token.kind is not TokenKind.SLASH for token in result.tokens)
    assert result.diagnostics == []


def test_unterminated_block_comment_is_diagnosed() -> None:
    result = Lexer("let /* comment").tokenize()

    assert [token.kind for token in result.tokens] == [TokenKind.LET, TokenKind.EOF]
    assert result.diagnostics[0].code == "LEX_UNTERMINATED_COMMENT"
    assert result.diagnostics[0].span.start.offset == 4
    assert result.diagnostics[0].span.end.offset == len("let /* comment")


def test_block_comments_are_not_nested() -> None:
    result = Lexer("/* outer /* inner */ value").tokenize()

    assert [token.kind for token in result.tokens] == [TokenKind.IDENTIFIER, TokenKind.EOF]
    assert result.tokens[0].lexeme == "value"
