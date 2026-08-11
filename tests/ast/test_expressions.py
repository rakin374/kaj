from kaj.ast import (
    BinaryExpression,
    BinaryOperator,
    CallArgument,
    CallExpression,
    Identifier,
    IndexExpression,
    IntegerLiteral,
    ListLiteral,
    MapEntry,
    MapLiteral,
    MemberAccessExpression,
    StringLiteral,
    UnaryExpression,
    UnaryOperator,
)
from kaj.source import SourceSpan


def test_operator_enums_cover_the_checkpoint_inventory() -> None:
    assert {operator.name for operator in UnaryOperator} == {"POSITIVE", "NEGATE", "NOT"}
    assert {operator.name for operator in BinaryOperator} == {
        "ADD",
        "SUBTRACT",
        "MULTIPLY",
        "DIVIDE",
        "MODULO",
        "POWER",
        "EQUAL",
        "NOT_EQUAL",
        "LESS",
        "LESS_EQUAL",
        "GREATER",
        "GREATER_EQUAL",
        "AND",
        "OR",
    }


def test_identifier_and_operator_expressions(span: SourceSpan) -> None:
    identifier = Identifier(span=span, name="value")
    unary = UnaryExpression(span=span, operator=UnaryOperator.NOT, operand=identifier)
    binary = BinaryExpression(
        span=span,
        left=identifier,
        operator=BinaryOperator.ADD,
        right=IntegerLiteral(span=span, value=1),
    )

    assert identifier.name == "value"
    assert unary.operator is UnaryOperator.NOT
    assert binary.operator is BinaryOperator.ADD
    assert binary.left is identifier


def test_negative_number_is_representable_as_unary_negation(span: SourceSpan) -> None:
    magnitude = IntegerLiteral(span=span, value=42)
    expression = UnaryExpression(
        span=span,
        operator=UnaryOperator.NEGATE,
        operand=magnitude,
    )

    assert expression.operator is UnaryOperator.NEGATE
    assert expression.operand == magnitude
    assert magnitude.value == 42


def test_calls_support_positional_and_named_arguments(span: SourceSpan) -> None:
    positional = CallArgument(
        span=span,
        name=None,
        value=StringLiteral(span=span, value="hello"),
    )
    named = CallArgument(
        span=span,
        name="priority",
        value=IntegerLiteral(span=span, value=2),
    )
    call = CallExpression(
        span=span,
        callee=Identifier(span=span, name="send"),
        arguments=(positional, named),
    )

    assert call.arguments == (positional, named)
    assert call.arguments[0].name is None
    assert call.arguments[1].name == "priority"


def test_member_and_index_expressions(span: SourceSpan) -> None:
    user = Identifier(span=span, name="user")
    member = MemberAccessExpression(span=span, object=user, member="name")
    index = IndexExpression(
        span=span,
        object=Identifier(span=span, name="items"),
        index=IntegerLiteral(span=span, value=0),
    )

    assert member.object == user
    assert member.member == "name"
    assert index.index == IntegerLiteral(span=span, value=0)


def test_list_and_map_children_are_ordered_tuples(span: SourceSpan) -> None:
    one = IntegerLiteral(span=span, value=1)
    two = IntegerLiteral(span=span, value=2)
    items = ListLiteral(span=span, elements=(one, two))
    entry = MapEntry(
        span=span,
        key=StringLiteral(span=span, value="Alice"),
        value=IntegerLiteral(span=span, value=30),
    )
    mapping = MapLiteral(span=span, entries=(entry,))

    assert items.elements == (one, two)
    assert isinstance(items.elements, tuple)
    assert mapping.entries == (entry,)
