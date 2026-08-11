from kaj.lexer import Lexer, TokenKind
from kaj.source import SourceLocation


def test_first_token_and_exclusive_end_location() -> None:
    token = Lexer("let").tokenize().tokens[0]

    assert token.span.start == SourceLocation(0, 1, 1)
    assert token.span.end == SourceLocation(3, 1, 4)


def test_spaces_tabs_and_newlines_update_locations() -> None:
    result = Lexer(" \tlet\n  var").tokenize()

    assert result.tokens[0].span.start == SourceLocation(2, 1, 3)
    assert result.tokens[1].span.start == SourceLocation(8, 2, 3)


def test_multiline_comment_updates_locations() -> None:
    token = Lexer("/* one\ntwo */let").tokenize().tokens[0]

    assert token.kind is TokenKind.LET
    assert token.span.start == SourceLocation(13, 2, 7)


def test_lf_cr_and_crlf_are_each_one_logical_line_break() -> None:
    result = Lexer("let\rvar\r\nfn\nreturn").tokenize()

    assert [(token.span.start.line, token.span.start.column) for token in result.tokens[:-1]] == [
        (1, 1),
        (2, 1),
        (3, 1),
        (4, 1),
    ]
    assert [token.span.start.offset for token in result.tokens[:-1]] == [0, 4, 9, 12]


def test_eof_is_zero_width_at_end_of_source() -> None:
    eof = Lexer("let\r\n").tokenize().tokens[-1]

    assert eof.kind is TokenKind.EOF
    assert eof.span.start == SourceLocation(5, 2, 1)
    assert eof.span.end == eof.span.start
