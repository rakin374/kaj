from collections.abc import Callable

import pytest

from kaj.ast import BindingDeclaration, GenericType, NamedType, TypeExpression
from kaj.parser import ParserResult


@pytest.mark.parametrize("source", ["Int", "User"])
def test_named_types(parse: Callable[[str], ParserResult], source: str) -> None:
    binding = parse(f"let x: {source} = none").program.statements[0]

    assert isinstance(binding, BindingDeclaration)
    assert isinstance(binding.annotation, NamedType)
    assert binding.annotation.name == source


@pytest.mark.parametrize(
    "source",
    [
        "List<Int>",
        "Map<String, Int>",
        "Optional<User>",
        "Result<Value, Error>",
        "Map<String, List<Int>>",
    ],
)
def test_generic_types(parse: Callable[[str], ParserResult], source: str) -> None:
    binding = parse(f"let x: {source} = none").program.statements[0]

    assert isinstance(binding, BindingDeclaration)
    annotation: TypeExpression | None = binding.annotation
    assert isinstance(annotation, GenericType)
