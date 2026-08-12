from collections.abc import Callable

from kaj.ast import Program
from kaj.semantic import Resolver, TypeChecker
from kaj.serialization import ast_from_json, ast_to_json


def test_ast_json_round_trip_has_equivalent_function_typing(
    parse_program: Callable[[str], Program],
) -> None:
    program = parse_program(
        "fn add(a: Int, b: Decimal) -> Decimal { return a + b }\nlet result = add(1, b: 2.5)"
    )
    restored = ast_from_json(ast_to_json(program))

    def check(candidate: Program):  # type: ignore[no-untyped-def]
        resolution = Resolver().resolve(candidate)
        return TypeChecker(resolution).check(candidate)

    original = check(program)
    round_tripped = check(restored)
    assert [typed.type for typed in original.symbols] == [
        typed.type for typed in round_tripped.symbols
    ]
    assert original.diagnostics == round_tripped.diagnostics
