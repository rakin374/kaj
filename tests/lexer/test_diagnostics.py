import pytest

from kaj.lexer import Lexer


@pytest.mark.parametrize(
    ("source", "code", "start", "end"),
    [
        ("@", "LEX_INVALID_CHARACTER", 0, 1),
        ("!", "LEX_INVALID_CHARACTER", 0, 1),
        (r'"\q"', "LEX_INVALID_ESCAPE", 1, 3),
        ('"x', "LEX_UNTERMINATED_STRING", 0, 2),
        ("1.", "LEX_INVALID_NUMBER", 0, 2),
        ("/* x", "LEX_UNTERMINATED_COMMENT", 0, 4),
    ],
)
def test_stable_diagnostic_codes_and_spans(source: str, code: str, start: int, end: int) -> None:
    diagnostic = Lexer(source).tokenize().diagnostics[0]

    assert diagnostic.code == code
    assert diagnostic.span.start.offset == start
    assert diagnostic.span.end.offset == end


def test_multiple_errors_are_collected() -> None:
    result = Lexer('let x = @\nlet y = "\\q"').tokenize()

    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "LEX_INVALID_CHARACTER",
        "LEX_INVALID_ESCAPE",
    ]
