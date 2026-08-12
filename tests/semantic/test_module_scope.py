from collections.abc import Callable

from kaj.semantic import ResolutionResult, ScopeKind, SymbolKind


def test_module_binding_is_visible_after_declaration(
    resolve_source: Callable[[str], ResolutionResult],
) -> None:
    result = resolve_source("let x = 1\nlet y = x")

    assert result.diagnostics == ()
    assert result.references[0].symbol is result.module_scope.lookup_local("x")


def test_module_binding_is_not_forward_visible(
    resolve_source: Callable[[str], ResolutionResult],
) -> None:
    result = resolve_source("let y = x\nlet x = 1")

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["RESOLVE_UNKNOWN_NAME"]


def test_symbol_and_scope_models(resolve_source: Callable[[str], ResolutionResult]) -> None:
    result = resolve_source("let x = 1\nvar y = x")

    assert result.module_scope.kind is ScopeKind.MODULE
    assert [symbol.kind for symbol in result.symbols] == [
        SymbolKind.LET_BINDING,
        SymbolKind.VAR_BINDING,
    ]
    assert [symbol.id for symbol in result.symbols] == [0, 1]


def test_function_binding_collision_is_duplicate(
    resolve_source: Callable[[str], ResolutionResult],
) -> None:
    result = resolve_source("let f = 1\nfn f() -> None {}")

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["RESOLVE_DUPLICATE_NAME"]
    assert result.module_scope.lookup_local("f").kind is SymbolKind.FUNCTION  # type: ignore[union-attr]
