from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from kaj.source import SourceSpan


class PrimitiveType(Enum):
    BOOL = "Bool"
    INT = "Int"
    DECIMAL = "Decimal"
    STRING = "String"
    BYTES = "Bytes"
    NONE = "None"
    ERROR = "<error>"


@dataclass(frozen=True)
class ListType:
    element_type: ValueType


@dataclass(frozen=True)
class TypeSymbol:
    id: int
    name: str
    declaration_span: SourceSpan


@dataclass(frozen=True)
class RecordType:
    symbol: TypeSymbol


@dataclass(frozen=True)
class EnumType:
    symbol: TypeSymbol


type ValueType = PrimitiveType | ListType | RecordType | EnumType


@dataclass(frozen=True)
class RecordField:
    name: str
    type: ValueType
    declaration_span: SourceSpan


@dataclass(frozen=True)
class RecordDefinition:
    type: RecordType
    fields: tuple[RecordField, ...]


@dataclass(frozen=True)
class EnumPayloadFieldType:
    name: str
    type: ValueType
    declaration_span: SourceSpan


@dataclass(frozen=True)
class EnumVariant:
    name: str
    payload: tuple[EnumPayloadFieldType, ...]
    declaration_span: SourceSpan


@dataclass(frozen=True)
class EnumDefinition:
    type: EnumType
    variants: tuple[EnumVariant, ...]


@dataclass(frozen=True)
class FunctionParameterType:
    name: str
    type: ValueType
    mutable: bool


@dataclass(frozen=True)
class FunctionType:
    parameters: tuple[FunctionParameterType, ...]
    return_type: ValueType


class BuiltinFunctionType(Enum):
    PRINT = "print"


type SemanticType = ValueType | FunctionType | BuiltinFunctionType


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
    if isinstance(semantic_type, ListType):
        return f"List<{format_type(semantic_type.element_type)}>"
    if isinstance(semantic_type, (RecordType, EnumType)):
        return semantic_type.symbol.name
    parameters = ", ".join(format_type(parameter.type) for parameter in semantic_type.parameters)
    return f"({parameters}) -> {format_type(semantic_type.return_type)}"
