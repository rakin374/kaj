from collections.abc import Callable

import pytest

from kaj.runtime import Environment
from kaj.semantic import Symbol, SymbolKind
from kaj.source import SourceLocation, SourceSpan

from .conftest import PipelineResult


def span() -> SourceSpan:
    location = SourceLocation(0, 1, 1)
    return SourceSpan(location, location)


def test_environment_uses_symbol_identity_and_parent_lookup() -> None:
    outer_symbol = Symbol(1, "x", SymbolKind.LET_BINDING, span())
    inner_symbol = Symbol(2, "x", SymbolKind.VAR_BINDING, span())
    outer = Environment()
    inner = Environment(outer)
    outer.define(outer_symbol, 1, mutable=False)
    inner.define(inner_symbol, 2, mutable=True)

    assert inner.read(outer_symbol) == 1
    assert inner.read(inner_symbol) == 2
    inner.assign(inner_symbol, 3)
    assert inner.read(inner_symbol) == 3
    with pytest.raises(PermissionError):
        inner.assign(outer_symbol, 4)


def test_future_collection_execution_is_rejected(
    run_source: Callable[[str], PipelineResult],
) -> None:
    result = run_source("let values = [1, 2]")
    assert result.execution is not None
    assert result.execution.runtime_error is not None
    assert result.execution.runtime_error.code == "RUNTIME_INVALID_OPERATION"
