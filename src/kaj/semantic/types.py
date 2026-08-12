from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PrimitiveType(Enum):
    BOOL = "Bool"
    INT = "Int"
    DECIMAL = "Decimal"
    STRING = "String"
    BYTES = "Bytes"
    NONE = "None"
    ERROR = "<error>"


@dataclass(frozen=True)
class FunctionParameterType:
    name: str
    type: PrimitiveType
    mutable: bool


@dataclass(frozen=True)
class FunctionType:
    parameters: tuple[FunctionParameterType, ...]
    return_type: PrimitiveType


class BuiltinFunctionType(Enum):
    PRINT = "print"


type SemanticType = PrimitiveType | FunctionType | BuiltinFunctionType


PRIMITIVE_TYPES_BY_NAME: dict[str, PrimitiveType] = {
    primitive.value: primitive
    for primitive in PrimitiveType
    if primitive is not PrimitiveType.ERROR
}


def is_assignable(source: SemanticType, target: SemanticType) -> bool:
    if PrimitiveType.ERROR in (source, target):
        return True
    return source == target or (source is PrimitiveType.INT and target is PrimitiveType.DECIMAL)


def format_type(semantic_type: SemanticType) -> str:
    if isinstance(semantic_type, PrimitiveType):
        return semantic_type.value
    if isinstance(semantic_type, BuiltinFunctionType):
        return f"<builtin {semantic_type.value}>"
    parameters = ", ".join(parameter.type.value for parameter in semantic_type.parameters)
    return f"({parameters}) -> {semantic_type.return_type.value}"
