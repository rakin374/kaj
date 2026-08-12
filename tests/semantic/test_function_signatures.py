from collections.abc import Callable

from kaj.semantic import FunctionType, PrimitiveType, TypeCheckResult


def function_type(result: TypeCheckResult, name: str) -> FunctionType:
    symbol = result.resolution.module_scope.lookup_local(name)
    assert symbol is not None
    signature = result.type_of_symbol(symbol)
    assert isinstance(signature, FunctionType)
    return signature


def test_signature_preserves_parameter_contract(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source("fn add(a: Int, var b: Decimal) -> String { return \"ok\" }")
    signature = function_type(result, "add")

    assert [(item.name, item.type, item.mutable) for item in signature.parameters] == [
        ("a", PrimitiveType.INT, False),
        ("b", PrimitiveType.DECIMAL, True),
    ]
    assert signature.return_type is PrimitiveType.STRING
    assert result.diagnostics == ()


def test_unknown_signature_types_are_diagnosed_once_each(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source("fn f(x: Missing) -> AlsoMissing { return x }")

    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "TYPE_UNKNOWN_TYPE",
        "TYPE_UNKNOWN_TYPE",
    ]


def test_parameter_symbol_types_are_available_in_body(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source("fn add(a: Int, b: Decimal) -> Decimal { return a + b }")
    parameter_types = [
        typed.type for typed in result.symbols if typed.symbol.name in {"a", "b"}
    ]

    assert parameter_types == [PrimitiveType.INT, PrimitiveType.DECIMAL]
    assert result.diagnostics == ()
