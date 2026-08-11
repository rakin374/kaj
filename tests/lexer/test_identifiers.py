from kaj.lexer import Lexer, TokenKind


def test_ascii_identifiers() -> None:
    result = Lexer("foo _user foo2 ParserState").tokenize()

    assert [token.kind for token in result.tokens] == [
        TokenKind.IDENTIFIER,
        TokenKind.IDENTIFIER,
        TokenKind.IDENTIFIER,
        TokenKind.IDENTIFIER,
        TokenKind.EOF,
    ]
    assert [token.lexeme for token in result.tokens[:-1]] == [
        "foo",
        "_user",
        "foo2",
        "ParserState",
    ]


def test_keyword_prefixes_remain_identifiers() -> None:
    result = Lexer("let letter returnValue matching").tokenize()

    assert [token.kind for token in result.tokens] == [
        TokenKind.LET,
        TokenKind.IDENTIFIER,
        TokenKind.IDENTIFIER,
        TokenKind.IDENTIFIER,
        TokenKind.EOF,
    ]


def test_unicode_identifier_characters_are_invalid() -> None:
    result = Lexer("café").tokenize()

    assert [token.lexeme for token in result.tokens[:-1]] == ["caf"]
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["LEX_INVALID_CHARACTER"]
