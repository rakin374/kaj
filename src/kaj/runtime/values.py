from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from kaj.ast import FunctionDeclaration
from kaj.runtime.environment import Environment
from kaj.semantic import EnumType, FunctionType, OptionalType, RecordType, ResultType, Symbol


@dataclass(frozen=True)
class KajList:
    elements: tuple[RuntimeValue, ...]


@dataclass(frozen=True)
class KajRecord:
    type: RecordType
    fields: tuple[tuple[str, RuntimeValue], ...]

    def read(self, name: str) -> RuntimeValue:
        for field_name, value in self.fields:
            if field_name == name:
                return value
        raise KeyError(name)


@dataclass(frozen=True)
class KajEnumValue:
    type: EnumType | OptionalType | ResultType
    variant: str
    payload: tuple[RuntimeValue, ...]


@dataclass(frozen=True)
class KajFunction:
    declaration: FunctionDeclaration
    symbol: Symbol
    signature: FunctionType
    environment: Environment


class BuiltinFunction(Enum):
    PRINT = "print"


type RuntimeValue = (
    bool
    | int
    | Decimal
    | str
    | bytes
    | None
    | KajList
    | KajRecord
    | KajEnumValue
    | KajFunction
    | BuiltinFunction
)
