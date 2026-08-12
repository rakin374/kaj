from collections.abc import Callable

from kaj.ast import Program
from kaj.semantic import PrimitiveType, Resolver, TypeChecker, TypeCheckResult
from kaj.serialization import ast_from_json, ast_to_json


def test_shadowed_symbols_have_independent_types(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source('let x = 1\nif true { let x = "hello" }')
    x_types = [typed.type for typed in result.symbols if typed.symbol.name == "x"]

    assert x_types == [PrimitiveType.INT, PrimitiveType.STRING]
    assert result.diagnostics == ()


def test_resolver_error_does_not_cascade(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("let x = missing\nlet y = x + 1")

    assert [diagnostic.code for diagnostic in result.resolution.diagnostics] == [
        "RESOLVE_UNKNOWN_NAME"
    ]
    assert result.diagnostics == ()


def test_multiple_type_errors_are_collected_in_order(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source('let a = "x" + 1\nif 2 {}\nlet b: Int = 2.5')

    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "TYPE_MISMATCH",
        "TYPE_CONDITION_NOT_BOOL",
        "TYPE_MISMATCH",
    ]


def test_ast_json_round_trip_has_equivalent_types(
    parse_program: Callable[[str], Program],
) -> None:
    program = parse_program("let x = 10 + 2.5\nlet y = x == 12.5")
    restored = ast_from_json(ast_to_json(program))

    def check(candidate: Program) -> TypeCheckResult:
        resolution = Resolver().resolve(candidate)
        return TypeChecker(resolution).check(candidate)

    original = check(program)
    round_tripped = check(restored)
    assert [typed.type for typed in original.symbols] == [
        typed.type for typed in round_tripped.symbols
    ]
    assert original.diagnostics == round_tripped.diagnostics
