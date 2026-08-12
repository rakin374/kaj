from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from kaj.ast import FunctionDeclaration
from kaj.runtime.environment import Environment
from kaj.semantic import FunctionType, Symbol


@dataclass(frozen=True)
class KajList:
    elements: tuple[RuntimeValue, ...]


@dataclass(frozen=True)
class KajFunction:
    declaration: FunctionDeclaration
    symbol: Symbol
    signature: FunctionType
    environment: Environment


class BuiltinFunction(Enum):
    PRINT = "print"


type RuntimeValue = (
    bool | int | Decimal | str | bytes | None | KajList | KajFunction | BuiltinFunction
)
