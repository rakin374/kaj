from enum import Enum


class PrimitiveType(Enum):
    BOOL = "Bool"
    INT = "Int"
    DECIMAL = "Decimal"
    STRING = "String"
    BYTES = "Bytes"
    NONE = "None"
    ERROR = "<error>"


PRIMITIVE_TYPES_BY_NAME: dict[str, PrimitiveType] = {
    primitive.value: primitive
    for primitive in PrimitiveType
    if primitive is not PrimitiveType.ERROR
}


def is_assignable(source: PrimitiveType, target: PrimitiveType) -> bool:
    if PrimitiveType.ERROR in (source, target):
        return True
    return source is target or (source is PrimitiveType.INT and target is PrimitiveType.DECIMAL)
