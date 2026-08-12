from collections.abc import Callable

import pytest

from kaj.semantic import ListType, PrimitiveType, SemanticType, TypeCheckResult


def binding_type(result: TypeCheckResult, name: str) -> SemanticType | None:
    symbol = result.resolution.module_scope.lookup_local(name)
    assert symbol is not None
    return result.type_of_symbol(symbol)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("let values = [1, 2, 3]", ListType(PrimitiveType.INT)),
        ("let values = [1, 2.5, 3]", ListType(PrimitiveType.DECIMAL)),
        ('let values = ["a", "b"]', ListType(PrimitiveType.STRING)),
        (
            "let values = [[1, 2], [3, 4]]",
            ListType(ListType(PrimitiveType.INT)),
        ),
    ],
)
def test_list_literal_inference(
    check_source: Callable[[str], TypeCheckResult], source: str, expected: ListType
) -> None:
    result = check_source(source)

    assert binding_type(result, "values") == expected
    assert result.diagnostics == ()


def test_heterogeneous_list_is_rejected(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source('let values = ["a", 1]')
    assert [item.code for item in result.diagnostics] == ["TYPE_MISMATCH"]


def test_empty_list_requires_context(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("let values = []")
    assert [item.code for item in result.diagnostics] == [
        "TYPE_CANNOT_INFER_LIST_ELEMENT"
    ]


def test_annotated_empty_and_nested_lists(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source(
        "let empty: List<Int> = []\nlet nested: List<List<String>> = [[]]"
    )

    assert binding_type(result, "empty") == ListType(PrimitiveType.INT)
    assert binding_type(result, "nested") == ListType(ListType(PrimitiveType.STRING))
    assert result.diagnostics == ()


def test_contextual_element_promotion(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("let values: List<Decimal> = [1, 2, 3]")
    assert binding_type(result, "values") == ListType(PrimitiveType.DECIMAL)
    assert result.diagnostics == ()


def test_contextual_element_narrowing_is_rejected(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source("let values: List<Int> = [1, 2.5]")
    assert [item.code for item in result.diagnostics] == ["TYPE_MISMATCH"]


def test_existing_lists_are_invariant(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source(
        "let ints: List<Int> = [1, 2]\nlet decimals: List<Decimal> = ints"
    )
    assert [item.code for item in result.diagnostics] == ["TYPE_MISMATCH"]


@pytest.mark.parametrize("annotation", ["List", "List<Int, String>"])
def test_list_annotation_requires_one_argument(
    check_source: Callable[[str], TypeCheckResult], annotation: str
) -> None:
    result = check_source(f"let values: {annotation} = [1]")
    assert result.diagnostics[0].code == "TYPE_INVALID_TYPE_ARGUMENTS"


def test_list_arithmetic_equality_truthiness_and_print_remain_unsupported(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source("let values = [1]\nlet x = values + values\nlet y = values == values\nif values {}")
    assert [item.code for item in result.diagnostics] == [
        "TYPE_MISMATCH",
        "TYPE_MISMATCH",
        "TYPE_CONDITION_NOT_BOOL",
    ]
