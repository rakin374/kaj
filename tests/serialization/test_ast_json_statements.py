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
    Program,
    ReturnStatement,
    WhileStatement,
)
from kaj.serialization import ast_from_json_value, ast_to_json_value
from kaj.source import SourceSpan


def test_every_statement_shape_round_trips(span: SourceSpan) -> None:
    identifier = Identifier(span=span, name="x")
    empty = Block(span=span, statements=())
    nested_if = IfStatement(
        span=span,
        condition=BooleanLiteral(span=span, value=False),
        then_branch=empty,
        else_branch=None,
    )
    statements = (
        empty,
        BindingDeclaration(
            span=span,
            name="x",
            kind=BindingKind.VAR,
            annotation=NamedType(span=span, name="Int"),
            initializer=IntegerLiteral(span=span, value=1),
        ),
        AssignmentStatement(
            span=span,
            target=identifier,
            operator=AssignmentOperator.ADD_ASSIGN,
            value=IntegerLiteral(span=span, value=1),
        ),
        ExpressionStatement(span=span, expression=identifier),
        IfStatement(
            span=span,
            condition=BooleanLiteral(span=span, value=True),
            then_branch=empty,
            else_branch=nested_if,
        ),
        WhileStatement(span=span, condition=identifier, body=empty),
        ForStatement(span=span, name="item", iterable=identifier, body=empty),
        BreakStatement(span=span),
        ContinueStatement(span=span),
        ReturnStatement(span=span, value=None),
        ReturnStatement(span=span, value=identifier),
    )
    program = Program(span=span, statements=statements)

    assert ast_from_json_value(ast_to_json_value(program)) == program


def test_all_binding_and_assignment_enum_values_are_stable(span: SourceSpan) -> None:
    identifier = Identifier(span=span, name="x")
    integer = IntegerLiteral(span=span, value=1)
    assignment_expected = {
        AssignmentOperator.ASSIGN: "assign",
        AssignmentOperator.ADD_ASSIGN: "add_assign",
        AssignmentOperator.SUBTRACT_ASSIGN: "subtract_assign",
        AssignmentOperator.MULTIPLY_ASSIGN: "multiply_assign",
        AssignmentOperator.DIVIDE_ASSIGN: "divide_assign",
    }

    for kind, external in [(BindingKind.LET, "let"), (BindingKind.VAR, "var")]:
        binding = BindingDeclaration(
            span=span,
            name="x",
            kind=kind,
            annotation=None,
            initializer=integer,
        )
        encoded = ast_to_json_value(Program(span=span, statements=(binding,)))
        assert encoded["program"]["statements"][0]["binding_kind"] == external  # type: ignore[index]

    for operator, external in assignment_expected.items():
        assignment = AssignmentStatement(
            span=span,
            target=identifier,
            operator=operator,
            value=integer,
        )
        encoded = ast_to_json_value(Program(span=span, statements=(assignment,)))
        assert encoded["program"]["statements"][0]["operator"] == external  # type: ignore[index]
