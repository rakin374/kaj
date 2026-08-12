from kaj.ast import Block, FunctionDeclaration, NamedType, Parameter, Program, ReturnStatement
from kaj.serialization import ast_from_json_value, ast_to_json_value
from kaj.source import SourceSpan


def test_function_and_parameter_round_trip(span: SourceSpan) -> None:
    type_expression = NamedType(span=span, name="Decimal")
    parameter = Parameter(
        span=span,
        name="value",
        type_annotation=type_expression,
        mutable=True,
    )
    function = FunctionDeclaration(
        span=span,
        name="normalize",
        parameters=(parameter,),
        return_type=type_expression,
        body=Block(span=span, statements=(ReturnStatement(span=span, value=None),)),
    )
    program = Program(span=span, statements=(function,))
    value = ast_to_json_value(program)
    encoded = value["program"]["statements"][0]  # type: ignore[index]

    assert encoded["kind"] == "function_declaration"  # type: ignore[index]
    assert encoded["parameters"][0]["mutable"] is True  # type: ignore[index]
    assert ast_from_json_value(value) == program
