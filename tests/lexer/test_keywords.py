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
        "verify",
        "observe",
        "use",
    ],
)
def test_deferred_agent_words_are_identifiers(source: str) -> None:
    result = Lexer(source).tokenize()

    assert result.tokens[0].kind is TokenKind.IDENTIFIER


def test_task_is_a_reserved_keyword() -> None:
    result = Lexer("task").tokenize()

    assert result.tokens[0].kind is TokenKind.TASK


def test_step_is_a_reserved_keyword() -> None:
    result = Lexer("step").tokenize()

    assert result.tokens[0].kind is TokenKind.STEP


@pytest.mark.parametrize(
    ("source", "kind"),
    [
        ("goal", TokenKind.GOAL),
        ("require", TokenKind.REQUIRE),
        ("invariant", TokenKind.INVARIANT),
        ("success", TokenKind.SUCCESS),
    ],
)
def test_task_contract_words_are_reserved(source: str, kind: TokenKind) -> None:
    result = Lexer(source).tokenize()

    assert result.tokens[0].kind is kind


@pytest.mark.parametrize(
    ("source", "kind"),
    [
        ("ask", TokenKind.ASK),
        ("choose", TokenKind.CHOOSE),
        ("confirm", TokenKind.CONFIRM),
        ("inform", TokenKind.INFORM),
        ("handoff", TokenKind.HANDOFF),
    ],
)
def test_human_interaction_words_are_reserved(source: str, kind: TokenKind) -> None:
    result = Lexer(source).tokenize()

    assert result.tokens[0].kind is kind
