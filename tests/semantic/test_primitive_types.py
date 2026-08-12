from collections.abc import Callable

from kaj.semantic import PrimitiveType, TypeCheckResult, is_assignable


def symbol_types(result: TypeCheckResult) -> dict[str, PrimitiveType]:
    return {typed.symbol.name: typed.type for typed in result.symbols}


def test_primitive_literal_inference(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source(
        "let bool_value = true\nlet int_value = 10\nlet decimal_value = 19.99\n"
        'let string_value = "hello"\nlet none_value = none'
    )

    assert symbol_types(result) == {
        "bool_value": PrimitiveType.BOOL,
        "int_value": PrimitiveType.INT,
        "decimal_value": PrimitiveType.DECIMAL,
        "string_value": PrimitiveType.STRING,
        "none_value": PrimitiveType.NONE,
    }
    assert result.diagnostics == ()


def test_bytes_exists_and_primitive_assignability_is_frozen() -> None:
    assert PrimitiveType.BYTES.value == "Bytes"
    assert is_assignable(PrimitiveType.INT, PrimitiveType.DECIMAL)
    assert not is_assignable(PrimitiveType.DECIMAL, PrimitiveType.INT)
    assert not is_assignable(PrimitiveType.STRING, PrimitiveType.BYTES)


def test_annotations_and_numeric_widening(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("let x: Int = 10\nlet y: Decimal = 10\nlet z: Bytes = missing")

    assert symbol_types(result) == {
        "x": PrimitiveType.INT,
        "y": PrimitiveType.DECIMAL,
        "z": PrimitiveType.BYTES,
    }
    assert result.diagnostics == ()
    assert [diagnostic.code for diagnostic in result.resolution.diagnostics] == [
        "RESOLVE_UNKNOWN_NAME"
    ]


def test_annotation_mismatch_preserves_declared_type(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source("let x: Int = 10.5\nlet y = x + 1")

    assert symbol_types(result) == {"x": PrimitiveType.INT, "y": PrimitiveType.INT}
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["TYPE_MISMATCH"]


def test_unknown_and_generic_annotations_are_diagnosed(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source("let x: Foo = 1\nlet y: Map<Int> = 2")

    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "TYPE_UNKNOWN_TYPE",
        "TYPE_INVALID_TYPE_ARGUMENTS",
    ]
