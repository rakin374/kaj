from collections.abc import Callable

import pytest

from kaj.semantic import PrimitiveType, TypeCheckResult


def inferred_x(result: TypeCheckResult) -> PrimitiveType:
    symbol = result.resolution.module_scope.lookup_local("x")
    assert symbol is not None
    semantic_type = result.type_of_symbol(symbol)
    assert semantic_type is not None
    return semantic_type


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("10 + 2", PrimitiveType.INT),
        ("10 + 2.5", PrimitiveType.DECIMAL),
        ("2.5 + 10", PrimitiveType.DECIMAL),
        ("10 - 2.5", PrimitiveType.DECIMAL),
        ("2 * 3", PrimitiveType.INT),
        ("5 % 2.0", PrimitiveType.DECIMAL),
        ("2 ** 3", PrimitiveType.INT),
        ("2 ** 3.0", PrimitiveType.DECIMAL),
        ("5 / 2", PrimitiveType.DECIMAL),
        ('"hello" + " world"', PrimitiveType.STRING),
    ],
)
def test_arithmetic_tables(
    check_source: Callable[[str], TypeCheckResult],
    expression: str,
    expected: PrimitiveType,
) -> None:
    result = check_source(f"let x = {expression}")

    assert inferred_x(result) is expected
    assert result.diagnostics == ()


@pytest.mark.parametrize("expression", ['"10" + 2', "10 == \"10\"", '"a" < "b"'])
def test_incompatible_binary_operands_are_type_mismatches(
    check_source: Callable[[str], TypeCheckResult], expression: str
) -> None:
    result = check_source(f"let x = {expression}")

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["TYPE_MISMATCH"]


@pytest.mark.parametrize(
    "expression",
    ["1 == 2", "1 != 2.0", '"a" == "b"', "none == none", "1 < 2.0", "2 >= 1"],
)
def test_valid_comparisons_infer_bool(
    check_source: Callable[[str], TypeCheckResult], expression: str
) -> None:
    result = check_source(f"let x = {expression}")

    assert inferred_x(result) is PrimitiveType.BOOL
    assert result.diagnostics == ()


def test_boolean_operators(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("let x = true and false\nlet y = true or false\nlet z = not true")

    assert [typed.type for typed in result.symbols] == [
        PrimitiveType.BOOL,
        PrimitiveType.BOOL,
        PrimitiveType.BOOL,
    ]
    assert result.diagnostics == ()


@pytest.mark.parametrize("expression", ["not 1", '-"hello"', "+true"])
def test_invalid_unary_operators(
    check_source: Callable[[str], TypeCheckResult], expression: str
) -> None:
    result = check_source(f"let x = {expression}")

    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "TYPE_INVALID_OPERATOR"
    ]
