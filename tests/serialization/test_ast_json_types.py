from kaj.ast import GenericType, NamedType, Program
from kaj.serialization import ast_from_json_value, ast_to_json_value
from kaj.source import SourceSpan


def test_nested_types_round_trip_as_explicit_nodes(span: SourceSpan) -> None:
    nested = GenericType(
        span=span,
        base=NamedType(span=span, name="Map"),
        arguments=(
            NamedType(span=span, name="String"),
            GenericType(
                span=span,
                base=NamedType(span=span, name="List"),
                arguments=(NamedType(span=span, name="Int"),),
            ),
        ),
    )
    from kaj.ast import BindingDeclaration, BindingKind, NoneLiteral

    program = Program(
        span=span,
        statements=(
            BindingDeclaration(
                span=span,
                name="value",
                kind=BindingKind.LET,
                annotation=nested,
                initializer=NoneLiteral(span=span),
            ),
        ),
    )

    assert ast_from_json_value(ast_to_json_value(program)) == program
