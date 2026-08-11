import pytest

from kaj.ast import (
    AssignmentOperator,
    AssignmentStatement,
    BindingDeclaration,
    BindingKind,
    Block,
    BooleanLiteral,
    BreakStatement,
    ContinueStatement,
    ExpressionStatement,
    ForStatement,
    Identifier,
    IfStatement,
    IntegerLiteral,
    NamedType,
    ReturnStatement,
    WhileStatement,
)
from kaj.source import SourceSpan


def test_typed_and_untyped_bindings_preserve_let_var_distinction(span: SourceSpan) -> None:
    value = IntegerLiteral(span=span, value=10)
    immutable = BindingDeclaration(
        span=span,
        name="x",
        kind=BindingKind.LET,
        annotation=None,
        initializer=value,
    )
    mutable = BindingDeclaration(
        span=span,
        name="y",
        kind=BindingKind.VAR,
        annotation=NamedType(span=span, name="Int"),
        initializer=value,
    )

    assert immutable.kind is BindingKind.LET
    assert immutable.annotation is None
    assert mutable.kind is BindingKind.VAR
    assert mutable.annotation == NamedType(span=span, name="Int")


@pytest.mark.parametrize("operator", list(AssignmentOperator))
def test_every_assignment_operator_is_representable(
    span: SourceSpan, operator: AssignmentOperator
) -> None:
    statement = AssignmentStatement(
        span=span,
        target=Identifier(span=span, name="x"),
        operator=operator,
        value=IntegerLiteral(span=span, value=1),
    )

    assert statement.operator is operator


def test_expression_and_control_flow_statements(span: SourceSpan) -> None:
    condition = BooleanLiteral(span=span, value=True)
    expression_statement = ExpressionStatement(
        span=span,
        expression=Identifier(span=span, name="work"),
    )
    body = Block(span=span, statements=(expression_statement,))
    nested_if = IfStatement(
        span=span,
        condition=condition,
        then_branch=body,
        else_branch=None,
    )
    if_statement = IfStatement(
        span=span,
        condition=condition,
        then_branch=body,
        else_branch=nested_if,
    )
    while_statement = WhileStatement(span=span, condition=condition, body=body)
    for_statement = ForStatement(
        span=span,
        name="item",
        iterable=Identifier(span=span, name="items"),
        body=body,
    )

    assert if_statement.else_branch == nested_if
    assert while_statement.body == body
    assert for_statement.name == "item"


def test_control_transfer_statements(span: SourceSpan) -> None:
    break_statement = BreakStatement(span=span)
    continue_statement = ContinueStatement(span=span)
    bare_return = ReturnStatement(span=span, value=None)
    value_return = ReturnStatement(
        span=span,
        value=IntegerLiteral(span=span, value=1),
    )

    assert break_statement.span == span
    assert continue_statement.span == span
    assert bare_return.value is None
    assert value_return.value == IntegerLiteral(span=span, value=1)
