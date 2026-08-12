from collections.abc import Callable

from kaj.semantic import ResolutionResult, ScopeKind, SymbolKind


def test_forward_function_reference_recursion_and_mutual_recursion(
    resolve_source: Callable[[str], ResolutionResult],
) -> None:
    result = resolve_source("fn a() -> None { b() a() }\nfn b() -> None { a() }")

    assert result.diagnostics == ()
    assert [reference.symbol.name for reference in result.references] == ["b", "a", "a"]
    assert all(reference.symbol.kind is SymbolKind.FUNCTION for reference in result.references)


def test_parameters_and_direct_locals_share_function_scope(
    resolve_source: Callable[[str], ResolutionResult],
) -> None:
    result = resolve_source("fn f(x: Int) -> Int { let x = 1 return x }")

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["RESOLVE_DUPLICATE_NAME"]
    assert result.references[0].symbol.kind is SymbolKind.PARAMETER
    function_scope = result.module_scope.children[0]
    assert function_scope.kind is ScopeKind.FUNCTION
    assert function_scope.lookup_local("x") is result.references[0].symbol


def test_duplicate_parameters_keep_original_active(
    resolve_source: Callable[[str], ResolutionResult],
) -> None:
    result = resolve_source("fn f(x: Int, x: Int) -> Int { return x }")

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["RESOLVE_DUPLICATE_NAME"]
    assert result.references[0].symbol is result.module_scope.children[0].lookup_local("x")


def test_function_sees_only_earlier_module_bindings(
    resolve_source: Callable[[str], ResolutionResult],
) -> None:
    result = resolve_source(
        "let earlier = 1\n"
        "fn f() -> Int { return earlier }\n"
        "fn g() -> Int { return later }\n"
        "let later = 2"
    )

    assert [reference.symbol.name for reference in result.references] == ["earlier"]
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["RESOLVE_UNKNOWN_NAME"]


def test_type_names_are_not_value_references(
    resolve_source: Callable[[str], ResolutionResult],
) -> None:
    result = resolve_source("fn f(x: Mystery) -> UnknownType { return x }")

    assert result.diagnostics == ()
    assert [reference.symbol.name for reference in result.references] == ["x"]
