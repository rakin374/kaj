from __future__ import annotations

from dataclasses import dataclass

from kaj.ast import Program
from kaj.diagnostics import Diagnostic
from kaj.lexer import Lexer
from kaj.parser import Parser
from kaj.semantic import ResolutionResult, Resolver, TypeChecker, TypeCheckResult


@dataclass(frozen=True)
class ParseSourceResult:
    program: Program
    diagnostics: tuple[Diagnostic, ...]


@dataclass(frozen=True)
class CompileSourceResult:
    program: Program
    resolution: ResolutionResult | None
    types: TypeCheckResult | None
    diagnostics: tuple[Diagnostic, ...]


def parse_source(source: str, source_name: str = "<source>") -> ParseSourceResult:
    lexed = Lexer(source, filename=source_name).tokenize()
    parsed = Parser(lexed.tokens, filename=source_name).parse()
    return ParseSourceResult(parsed.program, (*lexed.diagnostics, *parsed.diagnostics))


def compile_source(source: str, source_name: str = "<source>") -> CompileSourceResult:
    parsed = parse_source(source, source_name)
    if parsed.diagnostics:
        return CompileSourceResult(parsed.program, None, None, parsed.diagnostics)
    resolution = Resolver(include_builtins=True).resolve(parsed.program)
    types = TypeChecker(resolution).check(parsed.program)
    diagnostics = (*resolution.diagnostics, *types.diagnostics)
    return CompileSourceResult(parsed.program, resolution, types, diagnostics)
