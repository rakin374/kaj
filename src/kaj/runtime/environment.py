from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from kaj.semantic import Symbol

if TYPE_CHECKING:
    from kaj.runtime.values import RuntimeValue


@dataclass
class RuntimeSlot:
    symbol: Symbol
    value: RuntimeValue
    mutable: bool


class Environment:
    def __init__(self, parent: Environment | None = None) -> None:
        self.parent = parent
        self._slots: dict[int, RuntimeSlot] = {}

    def define(self, symbol: Symbol, value: RuntimeValue, *, mutable: bool) -> None:
        self._slots[symbol.id] = RuntimeSlot(symbol, value, mutable)

    def read(self, symbol: Symbol) -> RuntimeValue:
        return self._find_slot(symbol).value

    def assign(self, symbol: Symbol, value: RuntimeValue) -> None:
        slot = self._find_slot(symbol)
        if not slot.mutable:
            raise PermissionError(f"Runtime binding '{symbol.name}' is immutable")
        slot.value = value

    def _find_slot(self, symbol: Symbol) -> RuntimeSlot:
        environment: Environment | None = self
        while environment is not None:
            slot = environment._slots.get(symbol.id)
            if slot is not None:
                return slot
            environment = environment.parent
        raise KeyError(symbol.id)
