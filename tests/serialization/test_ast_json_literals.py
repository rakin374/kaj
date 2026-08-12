from collections.abc import Callable
from decimal import Decimal

from kaj.ast import BindingDeclaration, DecimalLiteral, IntegerLiteral, Program, StringLiteral
from kaj.serialization import ast_from_json, ast_to_json, ast_to_json_value


def test_large_integer_is_a_string_and_round_trips(
    parse_program: Callable[[str], Program],
) -> None:
    program = parse_program("let x = 999999999999999999999999999999999999")
    value = ast_to_json_value(program)
    statement = value["program"]["statements"][0]  # type: ignore[index]
    literal = statement["initializer"]  # type: ignore[index]

    assert literal["value"] == "999999999999999999999999999999999999"  # type: ignore[index]
    decoded = ast_from_json(ast_to_json(program))
    assert decoded == program
    binding = decoded.statements[0]
    assert isinstance(binding, BindingDeclaration)
    assert isinstance(binding.initializer, IntegerLiteral)


def test_decimals_are_exact_strings(parse_program: Callable[[str], Program]) -> None:
    for source, expected in [("let x = 0.1", "0.1"), ("let x = 19.99", "19.99")]:
        program = parse_program(source)
        value = ast_to_json_value(program)
        literal = value["program"]["statements"][0]["initializer"]  # type: ignore[index]

        assert literal["value"] == expected  # type: ignore[index]
        decoded = ast_from_json(ast_to_json(program))
        binding = decoded.statements[0]
        assert isinstance(binding, BindingDeclaration)
        assert isinstance(binding.initializer, DecimalLiteral)
        assert binding.initializer.value == Decimal(expected)
        assert decoded == program


def test_unicode_is_readable_and_round_trips(parse_program: Callable[[str], Program]) -> None:
    program = parse_program('let greeting = "বাংলা 你好 👋"')
    text = ast_to_json(program)

    assert "বাংলা 你好 👋" in text
    assert "\\u" not in text
    decoded = ast_from_json(text)
    binding = decoded.statements[0]
    assert isinstance(binding, BindingDeclaration)
    assert isinstance(binding.initializer, StringLiteral)
    assert binding.initializer.value == "বাংলা 你好 👋"
