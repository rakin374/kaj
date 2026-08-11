from kaj.ast import GenericType, NamedType
from kaj.source import SourceSpan


def test_named_type_preserves_syntax_name(span: SourceSpan) -> None:
    type_expression = NamedType(span=span, name="User")

    assert type_expression.name == "User"
    assert type_expression.span == span


def test_nested_generic_type_is_representable(span: SourceSpan) -> None:
    int_type = NamedType(span=span, name="Int")
    list_type = GenericType(
        span=span,
        base=NamedType(span=span, name="List"),
        arguments=(int_type,),
    )
    map_type = GenericType(
        span=span,
        base=NamedType(span=span, name="Map"),
        arguments=(NamedType(span=span, name="String"), list_type),
    )

    assert map_type.base.name == "Map"
    assert map_type.arguments[1] == list_type
    assert isinstance(map_type.arguments, tuple)
