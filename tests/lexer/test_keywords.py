import pytest

from kaj.lexer import Lexer, TokenKind

KEYWORDS = {
    "let": TokenKind.LET,
    "var": TokenKind.VAR,
    "fn": TokenKind.FN,
    "return": TokenKind.RETURN,
    "if": TokenKind.IF,
    "else": TokenKind.ELSE,
    "while": TokenKind.WHILE,
    "for": TokenKind.FOR,
    "in": TokenKind.IN,
    "break": TokenKind.BREAK,
    "continue": TokenKind.CONTINUE,
    "true": TokenKind.TRUE,
    "false": TokenKind.FALSE,
    "none": TokenKind.NONE,
    "and": TokenKind.AND,
    "or": TokenKind.OR,
    "not": TokenKind.NOT,
    "type": TokenKind.TYPE,
    "enum": TokenKind.ENUM,
    "newtype": TokenKind.NEWTYPE,
    "match": TokenKind.MATCH,
    "import": TokenKind.IMPORT,
}


@pytest.mark.parametrize(("source", "kind"), KEYWORDS.items())
def test_every_keyword(source: str, kind: TokenKind) -> None:
    result = Lexer(source).tokenize()

    assert result.tokens[0].kind is kind


@pytest.mark.parametrize("source", ["Let", "LET", "Return", "IMPORT"])
def test_keywords_are_case_sensitive(source: str) -> None:
    result = Lexer(source).tokenize()

    assert result.tokens[0].kind is TokenKind.IDENTIFIER


@pytest.mark.parametrize(
    "source",
    [
        "task",
        "step",
        "goal",
        "success",
        "require",
        "verify",
        "observe",
        "ask",
        "use",
    ],
)
def test_deferred_agent_words_are_identifiers(source: str) -> None:
    result = Lexer(source).tokenize()

    assert result.tokens[0].kind is TokenKind.IDENTIFIER
