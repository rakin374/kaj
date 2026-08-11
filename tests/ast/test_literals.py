from decimal import Decimal

from kaj.ast import (
    BooleanLiteral,
    DecimalLiteral,
    IntegerLiteral,
    NoneLiteral,
    StringLiteral,
)
from kaj.source import SourceSpan


def test_literal_nodes_preserve_values_and_spans(span: SourceSpan) -> None:
    integer = IntegerLiteral(span=span, value=42)
    decimal = DecimalLiteral(span=span, value=Decimal("19.99"))
    string = StringLiteral(span=span, value="Kaj")
    boolean = BooleanLiteral(span=span, value=True)
    none = NoneLiteral(span=span)

    assert integer.value == 42
    assert integer.span == span
    assert decimal.value == Decimal("19.99")
    assert isinstance(decimal.value, Decimal)
    assert string.value == "Kaj"
    assert boolean.value is True
    assert none.span == span


def test_literals_have_structural_equality(span: SourceSpan) -> None:
    assert IntegerLiteral(span=span, value=10) == IntegerLiteral(span=span, value=10)
    assert IntegerLiteral(span=span, value=10) != IntegerLiteral(span=span, value=11)
