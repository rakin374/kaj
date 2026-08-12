from collections.abc import Callable

from kaj.semantic import ListType, PrimitiveType, SymbolKind, TypeCheckResult


def test_index_and_count_types(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("let values = [10, 20]\nlet item = values[0]\nlet size = values.count")
    item = result.resolution.module_scope.lookup_local("item")
    size = result.resolution.module_scope.lookup_local("size")
    assert item is not None and size is not None

    assert result.type_of_symbol(item) is PrimitiveType.INT
    assert result.type_of_symbol(size) is PrimitiveType.INT
    assert result.diagnostics == ()


def test_index_requires_int(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("let values = [1]\nlet item = values[0.5]")
    assert [item.code for item in result.diagnostics] == ["TYPE_MISMATCH"]


def test_unknown_list_member(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("let values = [1]\nvalues.foo")
    assert [item.code for item in result.diagnostics] == ["TYPE_UNKNOWN_MEMBER"]


def test_for_assigns_immutable_element_type(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source("let values = [1, 2]\nfor value in values { value = 3 }")
    loop_symbols = [
        typed for typed in result.symbols if typed.symbol.kind is SymbolKind.LOOP_VARIABLE
    ]

    assert [typed.type for typed in loop_symbols] == [PrimitiveType.INT]
    assert [item.code for item in result.diagnostics] == ["ASSIGN_TO_IMMUTABLE"]


def test_for_requires_list(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("for value in 10 {}")
    assert [item.code for item in result.diagnostics] == ["TYPE_NOT_ITERABLE"]


def test_list_function_annotations_and_contextual_call(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source(
        "fn first(values: List<Decimal>) -> Decimal { return values[0] }\nlet x = first([1, 2])"
    )
    x = result.resolution.module_scope.lookup_local("x")
    assert x is not None

    assert result.type_of_symbol(x) is PrimitiveType.DECIMAL
    assert result.diagnostics == ()


def test_wrong_list_call_argument(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source('fn first(values: List<Int>) -> Int { return values[0] }\nfirst(["x"])')
    assert [item.code for item in result.diagnostics] == ["TYPE_MISMATCH"]


def test_list_index_assignment_is_deferred(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source("var values = [1, 2]\nvalues[0] = 3")
    assert [item.code for item in result.diagnostics] == ["TYPE_MISMATCH"]


def test_list_type_equality_is_recursive() -> None:
    assert ListType(ListType(PrimitiveType.INT)) == ListType(ListType(PrimitiveType.INT))
    assert ListType(PrimitiveType.INT) != ListType(PrimitiveType.DECIMAL)
