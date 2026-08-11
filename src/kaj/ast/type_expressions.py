from dataclasses import dataclass

from kaj.ast.base import TypeExpression


@dataclass(frozen=True)
class NamedType(TypeExpression):
    name: str


@dataclass(frozen=True)
class GenericType(TypeExpression):
    base: NamedType
    arguments: tuple[TypeExpression, ...]
