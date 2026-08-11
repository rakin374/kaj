from decimal import Decimal

import pytest

from kaj.lexer import Lexer, TokenKind


@pytest.mark.parametrize("source", ["0", "1", "42", "999999999999999999999999999999"])
def test_integer_values_are_arbitrary_precision(source: str) -> None:
    token = Lexer(source).tokenize().tokens[0]

    assert token.kind is TokenKind.INTEGER
    assert token.lexeme == source
    assert token.value == int(source)


@pytest.mark.parametrize("source", ["0.0", "0.5", "3.14", "10.0"])
def test_decimal_values_are_exact(source: str) -> None:
    token = Lexer(source).tokenize().tokens[0]

    assert token.kind is TokenKind.DECIMAL
    assert token.lexeme == source
    assert token.value == Decimal(source)
    assert isinstance(token.value, Decimal)


@pytest.mark.parametrize(
    ("source", "number_kind"),
    [("-42", TokenKind.INTEGER), ("-3.14", TokenKind.DECIMAL)],
)
def test_negative_numbers_have_a_separate_minus(source: str, number_kind: TokenKind) -> None:
    result = Lexer(source).tokenize()

    assert [token.kind for token in result.tokens] == [
        TokenKind.MINUS,
        number_kind,
        TokenKind.EOF,
    ]


@pytest.mark.parametrize("source", ["1.", ".5", "1.2.3"])
def test_malformed_numbers_have_one_diagnostic_and_no_number_token(source: str) -> None:
    result = Lexer(source).tokenize()

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["LEX_INVALID_NUMBER"]
    assert result.diagnostics[0].span.start.offset == 0
    assert result.diagnostics[0].span.end.offset == len(source)
    assert [token.kind for token in result.tokens] == [TokenKind.EOF]


def test_invalid_number_recovery_continues_after_numeric_sequence() -> None:
    result = Lexer("1. let").tokenize()

    assert [token.kind for token in result.tokens] == [TokenKind.LET, TokenKind.EOF]
