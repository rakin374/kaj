from collections.abc import Callable

import pytest

from kaj.ast import BindingDeclaration, BindingKind, GenericType, ListLiteral, NamedType
from kaj.parser import ParserResult


@pytest.mark.parametrize(
    ("source", "kind"),
    [("let x = 10", BindingKind.LET), ("var y = 20", BindingKind.VAR)],
)
def test_untyped_bindings(
    parse: Callable[[str], ParserResult], source: str, kind: BindingKind
) -> None:
    statement = parse(source).program.statements[0]

    assert isinstance(statement, BindingDeclaration)
    assert statement.kind is kind
    assert statement.annotation is None


def test_typed_binding_with_generic_and_list(parse: Callable[[str], ParserResult]) -> None:
    statement = parse("var items: List<Int> = [1, 2]").program.statements[0]

    assert isinstance(statement, BindingDeclaration)
    assert isinstance(statement.annotation, GenericType)
    assert statement.annotation.base == NamedType(
        span=statement.annotation.base.span,
        name="List",
    )
    assert isinstance(statement.initializer, ListLiteral)


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ("let = 10", "PARSE_EXPECTED_IDENTIFIER"),
        ("let x", "PARSE_EXPECTED_TOKEN"),
        ("let x: = 10", "PARSE_EXPECTED_TYPE"),
    ],
)
def test_malformed_bindings(parse: Callable[[str], ParserResult], source: str, code: str) -> None:
    result = parse(source)

    assert result.diagnostics[0].code == code
