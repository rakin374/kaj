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
class MapType:
    key_type: ValueType
    value_type: ValueType


@dataclass(frozen=True)
class RangeType:
    pass


@dataclass(frozen=True)
class MapEntryType:
    key_type: ValueType
    value_type: ValueType


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


@dataclass(frozen=True)
class NewtypeType:
    symbol: TypeSymbol


@dataclass(frozen=True)
class OptionalType:
    value_type: ValueType


@dataclass(frozen=True)
class ResultType:
    ok_type: ValueType
    err_type: ValueType


type ValueType = (
    PrimitiveType
    | ListType
    | MapType
    | RangeType
    | MapEntryType
    | RecordType
    | EnumType
    | NewtypeType
    | OptionalType
    | ResultType
)


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
class NewtypeDefinition:
    type: NewtypeType
    underlying_type: ValueType


@dataclass(frozen=True)
class ModuleType:
    name: str
    values: tuple[tuple[str, SemanticType], ...]
    types: tuple[tuple[str, ValueType], ...]
    modules: tuple[tuple[str, ModuleType], ...] = ()
    records: tuple[RecordDefinition, ...] = ()
    enums: tuple[EnumDefinition, ...] = ()
    newtypes: tuple[NewtypeDefinition, ...] = ()


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
    RANGE = "range"
    STRING = "String"
    UTF8_ENCODE = "utf8_encode"
    UTF8_DECODE = "utf8_decode"


type SemanticType = ValueType | FunctionType | BuiltinFunctionType | ModuleType


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
    if isinstance(semantic_type, ModuleType):
        return f"<module {semantic_type.name}>"
    if isinstance(semantic_type, ListType):
        return f"List<{format_type(semantic_type.element_type)}>"
    if isinstance(semantic_type, MapType):
        return (
            f"Map<{format_type(semantic_type.key_type)}, {format_type(semantic_type.value_type)}>"
        )
    if isinstance(semantic_type, RangeType):
        return "Range"
    if isinstance(semantic_type, MapEntryType):
        return (
            f"MapEntry<{format_type(semantic_type.key_type)}, "
            f"{format_type(semantic_type.value_type)}>"
        )
    if isinstance(semantic_type, OptionalType):
        return f"Optional<{format_type(semantic_type.value_type)}>"
    if isinstance(semantic_type, ResultType):
        return (
            f"Result<{format_type(semantic_type.ok_type)}, {format_type(semantic_type.err_type)}>"
        )
    if isinstance(semantic_type, (RecordType, EnumType, NewtypeType)):
        return semantic_type.symbol.name
    parameters = ", ".join(format_type(parameter.type) for parameter in semantic_type.parameters)
    return f"({parameters}) -> {format_type(semantic_type.return_type)}"
