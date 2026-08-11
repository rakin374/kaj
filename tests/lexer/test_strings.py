import pytest

from kaj.lexer import Lexer, TokenKind


@pytest.mark.parametrize(
    ("source", "value"),
    [
        ('""', ""),
        ('"hello"', "hello"),
        ('"বাংলা 你好 👋"', "বাংলা 你好 👋"),
        (r'"say \"hi\""', 'say "hi"'),
        (r'"a\\b"', "a\\b"),
        (r'"a\nb"', "a\nb"),
        (r'"a\rb"', "a\rb"),
        (r'"a\tb"', "a\tb"),
        ('"Hello, {name}"', "Hello, {name}"),
    ],
)
def test_string_lexeme_and_decoded_value(source: str, value: str) -> None:
    result = Lexer(source).tokenize()
    token = result.tokens[0]

    assert token.kind is TokenKind.STRING
    assert token.lexeme == source
    assert token.value == value
    assert result.diagnostics == []


def test_invalid_escape_is_diagnosed_but_string_scanning_continues() -> None:
    result = Lexer(r'"a\qz" let').tokenize()

    assert [token.kind for token in result.tokens] == [
        TokenKind.STRING,
        TokenKind.LET,
        TokenKind.EOF,
    ]
    assert result.tokens[0].value == "aqz"
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["LEX_INVALID_ESCAPE"]
    assert result.diagnostics[0].span.start.offset == 2
    assert result.diagnostics[0].span.end.offset == 4


@pytest.mark.parametrize("source", ['"hello', '"hello\nlet'])
def test_unterminated_strings_are_diagnosed(source: str) -> None:
    result = Lexer(source).tokenize()

    assert result.diagnostics[0].code == "LEX_UNTERMINATED_STRING"
    assert result.diagnostics[0].span.start.offset == 0
