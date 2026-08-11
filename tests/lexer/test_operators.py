from kaj.lexer import Lexer, TokenKind


def test_all_punctuation_and_operators() -> None:
    source = "( ) { } [ ] , : . + - * / % ** = == != < <= > >= += -= *= /= -> =>"
    result = Lexer(source).tokenize()

    assert [token.kind for token in result.tokens] == [
        TokenKind.LEFT_PAREN,
        TokenKind.RIGHT_PAREN,
        TokenKind.LEFT_BRACE,
        TokenKind.RIGHT_BRACE,
        TokenKind.LEFT_BRACKET,
        TokenKind.RIGHT_BRACKET,
        TokenKind.COMMA,
        TokenKind.COLON,
        TokenKind.DOT,
        TokenKind.PLUS,
        TokenKind.MINUS,
        TokenKind.STAR,
        TokenKind.SLASH,
        TokenKind.PERCENT,
        TokenKind.STAR_STAR,
        TokenKind.EQUAL,
        TokenKind.EQUAL_EQUAL,
        TokenKind.BANG_EQUAL,
        TokenKind.LESS,
        TokenKind.LESS_EQUAL,
        TokenKind.GREATER,
        TokenKind.GREATER_EQUAL,
        TokenKind.PLUS_EQUAL,
        TokenKind.MINUS_EQUAL,
        TokenKind.STAR_EQUAL,
        TokenKind.SLASH_EQUAL,
        TokenKind.ARROW,
        TokenKind.FAT_ARROW,
        TokenKind.EOF,
    ]
    assert result.diagnostics == []


def test_longest_match_operators_are_single_tokens() -> None:
    result = Lexer("** == != <= >= += -= *= /= -> =>").tokenize()

    assert all(len(token.lexeme) == 2 for token in result.tokens[:-1])


def test_unsupported_symbolic_boolean_operators_are_invalid() -> None:
    result = Lexer("! && ||").tokenize()

    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "LEX_INVALID_CHARACTER",
        "LEX_INVALID_CHARACTER",
        "LEX_INVALID_CHARACTER",
        "LEX_INVALID_CHARACTER",
        "LEX_INVALID_CHARACTER",
    ]
