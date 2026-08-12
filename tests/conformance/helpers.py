from __future__ import annotations

from dataclasses import dataclass

from kaj.ast import Program
from kaj.diagnostics import Diagnostic
from kaj.formatting import format_program
from kaj.pipeline import compile_source, parse_source
from kaj.runtime import ExecutionResult, Interpreter
from kaj.serialization import ast_from_json_value, ast_to_json_value


def diagnostic_codes(diagnostics: tuple[Diagnostic, ...]) -> tuple[str, ...]:
    return tuple(item.code for item in diagnostics)


def assert_diagnostic_codes(
    diagnostics: tuple[Diagnostic, ...], expected: tuple[str, ...]
) -> None:
    assert diagnostic_codes(diagnostics) == expected


def parse_ok(source: str) -> Program:
    result = parse_source(source, "conformance.kaj")
    assert_diagnostic_codes(result.diagnostics, ())
    return result.program


def compile_error_codes(source: str) -> tuple[str, ...]:
    return diagnostic_codes(compile_source(source, "conformance.kaj").diagnostics)


@dataclass(frozen=True)
class CapturedExecution:
    result: ExecutionResult

    @property
    def stdout(self) -> str:
        return self.result.output


def run_ok(source: str) -> CapturedExecution:
    compiled = compile_source(source, "conformance.kaj")
    assert_diagnostic_codes(compiled.diagnostics, ())
    assert compiled.resolution is not None and compiled.types is not None
    execution = Interpreter(compiled.resolution, compiled.types).interpret(compiled.program)
    assert execution.runtime_error is None
    return CapturedExecution(execution)


def format_ok(source: str) -> str:
    return format_program(parse_ok(source))


def ast_json_ok(source: str) -> dict[str, object]:
    program = parse_ok(source)
    document = ast_to_json_value(program)
    assert ast_from_json_value(document) == program
    return document
