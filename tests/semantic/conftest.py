from collections.abc import Callable

import pytest

from kaj.ast import Program
from kaj.lexer import Lexer
from kaj.parser import Parser
from kaj.semantic import ResolutionResult, Resolver


@pytest.fixture
def parse_program() -> Callable[[str], Program]:
    def parse(source: str) -> Program:
        lexed = Lexer(source, filename="test.kaj").tokenize()
        assert not lexed.diagnostics
        parsed = Parser(lexed.tokens, filename="test.kaj").parse()
        assert not parsed.diagnostics
        return parsed.program

    return parse


@pytest.fixture
def resolve_source(parse_program: Callable[[str], Program]) -> Callable[[str], ResolutionResult]:
    def resolve(source: str) -> ResolutionResult:
        return Resolver().resolve(parse_program(source))

    return resolve
