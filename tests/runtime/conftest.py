from collections.abc import Callable
from dataclasses import dataclass

import pytest

from kaj.lexer import Lexer
from kaj.parser import Parser
from kaj.runtime import ExecutionResult, Interpreter
from kaj.semantic import ResolutionResult, Resolver, TypeChecker, TypeCheckResult


@dataclass(frozen=True)
class PipelineResult:
    resolution: ResolutionResult
    types: TypeCheckResult
    execution: ExecutionResult | None


@pytest.fixture
def run_source() -> Callable[[str], PipelineResult]:
    def run(source: str) -> PipelineResult:
        lexed = Lexer(source, filename="test.kaj").tokenize()
        assert not lexed.diagnostics
        parsed = Parser(lexed.tokens, filename="test.kaj").parse()
        assert not parsed.diagnostics
        resolution = Resolver(include_builtins=True).resolve(parsed.program)
        types = TypeChecker(resolution).check(parsed.program)
        if resolution.diagnostics or types.diagnostics:
            return PipelineResult(resolution, types, None)
        execution = Interpreter(resolution, types).interpret(parsed.program)
        return PipelineResult(resolution, types, execution)

    return run
