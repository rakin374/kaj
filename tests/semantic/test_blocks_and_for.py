from collections.abc import Callable

from kaj.semantic import ResolutionResult, SymbolKind


def test_nested_shadowing_has_distinct_symbol_identity(
    resolve_source: Callable[[str], ResolutionResult],
) -> None:
    result = resolve_source("let x = 1\nif true { let x = x x }\nx")

    outer, inner, final = (reference.symbol for reference in result.references)
    assert outer.id != inner.id
    assert outer is final
    assert result.diagnostics == ()


def test_sibling_and_escaped_block_names_are_unknown(
    resolve_source: Callable[[str], ResolutionResult],
) -> None:
    result = resolve_source("if true { let hidden = 1 } else { hidden }\nhidden")

    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "RESOLVE_UNKNOWN_NAME",
        "RESOLVE_UNKNOWN_NAME",
    ]


def test_else_if_condition_uses_surrounding_scope(
    resolve_source: Callable[[str], ResolutionResult],
) -> None:
    result = resolve_source("let ready = true\nif ready {} else if ready {}")

    assert result.diagnostics == ()
    assert result.references[0].symbol is result.references[1].symbol


def test_for_order_scope_and_duplicate_recovery(
    resolve_source: Callable[[str], ResolutionResult],
) -> None:
    result = resolve_source("let item = [1]\nfor item in item { item let item = 2 item }\nitem")

    iterable, body_before, body_after, after_loop = (
        reference.symbol for reference in result.references
    )
    assert iterable is after_loop
    assert body_before is body_after
    assert body_before.kind is SymbolKind.LOOP_VARIABLE
    assert body_before.id != iterable.id
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["RESOLVE_DUPLICATE_NAME"]


def test_for_variable_is_not_visible_in_iterable_or_after_loop(
    resolve_source: Callable[[str], ResolutionResult],
) -> None:
    result = resolve_source("for item in item { item }\nitem")

    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "RESOLVE_UNKNOWN_NAME",
        "RESOLVE_UNKNOWN_NAME",
    ]
    assert result.references[0].symbol.kind is SymbolKind.LOOP_VARIABLE
