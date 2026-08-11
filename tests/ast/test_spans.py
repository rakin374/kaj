from dataclasses import FrozenInstanceError

import pytest

from kaj.ast import CallArgument, Identifier, IntegerLiteral, MapEntry, NamedType, Parameter
from kaj.source import SourceLocation, SourceSpan


def test_concrete_nodes_and_helper_nodes_preserve_spans(span: SourceSpan) -> None:
    expression = IntegerLiteral(span=span, value=1)
    argument = CallArgument(span=span, name=None, value=expression)
    entry = MapEntry(span=span, key=expression, value=expression)
    parameter = Parameter(
        span=span,
        name="value",
        type_annotation=NamedType(span=span, name="Int"),
        mutable=False,
    )

    assert expression.span == span
    assert argument.span == span
    assert entry.span == span
    assert parameter.span == span


def test_ast_nodes_are_frozen(span: SourceSpan) -> None:
    identifier = Identifier(span=span, name="before")

    with pytest.raises(FrozenInstanceError):
        identifier.name = "after"  # type: ignore[misc]


def test_equality_includes_source_span(span: SourceSpan) -> None:
    other_span = SourceSpan(SourceLocation(1, 1, 2), SourceLocation(2, 1, 3))

    assert Identifier(span=span, name="x") != Identifier(span=other_span, name="x")
