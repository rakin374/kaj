from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from kaj.ast import FunctionDeclaration
from kaj.runtime.environment import Environment
from kaj.semantic import (
    EnumType,
    FunctionType,
    MapType,
    NewtypeType,
    OptionalType,
    PrimitiveType,
    RecordType,
    ResolutionResult,
    ResultType,
    Symbol,
    TypeCheckResult,
)


@dataclass(frozen=True)
class KajList:
    elements: tuple[RuntimeValue, ...]


@dataclass(frozen=True)
class KajMapKey:
    type: PrimitiveType | NewtypeType
    value: bool | int | Decimal | str | bytes | KajMapKey


@dataclass(frozen=True)
class KajMap:
    type: MapType
    entries: tuple[tuple[KajMapKey, RuntimeValue], ...]

    def read(self, key: KajMapKey) -> RuntimeValue:
        for stored_key, value in self.entries:
            if stored_key == key:
                return value
        raise KeyError(key)


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
class KajNewtypeValue:
    type: NewtypeType
    value: RuntimeValue


@dataclass(frozen=True)
class KajModuleValue:
    name: str
    members: tuple[tuple[str, RuntimeValue], ...]

    def read(self, name: str) -> RuntimeValue:
        for member_name, value in self.members:
            if member_name == name:
                return value
        raise KeyError(name)


@dataclass(frozen=True)
class KajFunction:
    declaration: FunctionDeclaration
    symbol: Symbol
    signature: FunctionType
    environment: Environment
    resolution: ResolutionResult
    types: TypeCheckResult


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
    | KajMap
    | KajRecord
    | KajEnumValue
    | KajNewtypeValue
    | KajModuleValue
    | KajFunction
    | BuiltinFunction
)
