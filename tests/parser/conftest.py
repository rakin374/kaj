from collections.abc import Callable

import pytest

from kaj.lexer import Lexer
from kaj.parser import Parser, ParserResult


@pytest.fixture
def parse() -> Callable[[str], ParserResult]:
    def parse_source(source: str) -> ParserResult:
        lexer_result = Lexer(source, filename="test.kaj").tokenize()
        assert lexer_result.diagnostics == []
        return Parser(lexer_result.tokens, filename="test.kaj").parse()

    return parse_source
