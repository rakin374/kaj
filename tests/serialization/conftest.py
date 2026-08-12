from collections.abc import Callable

import pytest

from kaj.ast import Program
from kaj.lexer import Lexer
from kaj.parser import Parser
from kaj.source import SourceLocation, SourceSpan


@pytest.fixture
def span() -> SourceSpan:
    return SourceSpan(SourceLocation(0, 1, 1), SourceLocation(1, 1, 2))


@pytest.fixture
def parse_program() -> Callable[[str], Program]:
    def parse(source: str) -> Program:
        lexer_result = Lexer(source, filename="test.kaj").tokenize()
        assert lexer_result.diagnostics == []
        parser_result = Parser(lexer_result.tokens, filename="test.kaj").parse()
        assert parser_result.diagnostics == ()
        return parser_result.program

    return parse
