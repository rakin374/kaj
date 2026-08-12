from __future__ import annotations

from collections.abc import Mapping
from enum import Enum, auto
from types import MappingProxyType

from kaj.semantic.symbols import Symbol


class ScopeKind(Enum):
    MODULE = auto()
    FUNCTION = auto()
    BLOCK = auto()


class Scope:
    def __init__(self, kind: ScopeKind, parent: Scope | None = None) -> None:
        self.kind = kind
        self.parent = parent
        self._symbols: dict[str, Symbol] = {}
        self._children: list[Scope] = []
        if parent is not None:
            parent._children.append(self)

    @property
    def symbols(self) -> Mapping[str, Symbol]:
        return MappingProxyType(self._symbols)

    @property
    def children(self) -> tuple[Scope, ...]:
        return tuple(self._children)

    def declare(self, symbol: Symbol) -> bool:
        if symbol.name in self._symbols:
            return False
        self._symbols[symbol.name] = symbol
        return True

    def lookup_local(self, name: str) -> Symbol | None:
        return self._symbols.get(name)

    def lookup(self, name: str) -> Symbol | None:
        scope: Scope | None = self
        while scope is not None:
            symbol = scope.lookup_local(name)
            if symbol is not None:
                return symbol
            scope = scope.parent
        return None
