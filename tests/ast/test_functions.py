from kaj.ast import (
    BinaryExpression,
    BinaryOperator,
    Block,
    FunctionDeclaration,
    Identifier,
    NamedType,
    Parameter,
    Program,
    ReturnStatement,
)
from kaj.source import SourceSpan


def test_parameter_preserves_type_and_local_mutability(span: SourceSpan) -> None:
    parameter = Parameter(
        span=span,
        name="value",
        type_annotation=NamedType(span=span, name="Decimal"),
        mutable=True,
    )

    assert parameter.name == "value"
    assert parameter.type_annotation.name == "Decimal"
    assert parameter.mutable is True


def test_function_and_program_preserve_structure(span: SourceSpan) -> None:
    int_type = NamedType(span=span, name="Int")
    left = Parameter(span=span, name="a", type_annotation=int_type, mutable=False)
    right = Parameter(span=span, name="b", type_annotation=int_type, mutable=False)
    addition = BinaryExpression(
        span=span,
        left=Identifier(span=span, name="a"),
        operator=BinaryOperator.ADD,
        right=Identifier(span=span, name="b"),
    )
    body = Block(
        span=span,
        statements=(ReturnStatement(span=span, value=addition),),
    )
    function = FunctionDeclaration(
        span=span,
        name="add",
        parameters=(left, right),
        return_type=int_type,
        body=body,
    )
    program = Program(span=span, statements=(function,))

    assert function.parameters == (left, right)
    assert function.return_type == int_type
    assert function.body == body
    assert program.statements == (function,)
