from collections.abc import Callable

import pytest

from kaj.ast import Program
from kaj.serialization import ast_from_json, ast_to_json


@pytest.mark.parametrize(
    "source",
    [
        "let x = 10",
        "var price: Decimal = 19.99",
        "let x = -42",
        "let items = [1, 2, 3]",
        'let ages = {"Alice": 30}',
        "if ready { run() } else { wait() }",
        "while ready { run() }",
        "for item in items { print(item) }",
        "fn add(a: Int, b: Int) -> Int { return a + b }",
        "fn normalize(var value: Decimal) -> Decimal { return value }",
        "foo().bar[0](x, priority: 2)",
    ],
)
def test_source_ast_json_ast_round_trip(
    parse_program: Callable[[str], Program], source: str
) -> None:
    program = parse_program(source)

    assert ast_from_json(ast_to_json(program)) == program


def test_output_is_deterministic(parse_program: Callable[[str], Program]) -> None:
    program = parse_program("let x = 10")

    assert ast_to_json(program, indent=2) == ast_to_json(program, indent=2)
