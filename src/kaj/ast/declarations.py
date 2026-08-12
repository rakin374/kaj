from dataclasses import dataclass

from kaj.ast.base import Node, Statement, TypeExpression
from kaj.ast.statements import Block


@dataclass(frozen=True)
class Parameter(Node):
    name: str
    type_annotation: TypeExpression
    mutable: bool


@dataclass(frozen=True)
class FunctionDeclaration(Statement):
    name: str
    parameters: tuple[Parameter, ...]
    return_type: TypeExpression
    body: Block


@dataclass(frozen=True)
class RecordFieldDeclaration(Node):
    name: str
    type_annotation: TypeExpression


@dataclass(frozen=True)
class RecordDeclaration(Statement):
    name: str
    fields: tuple[RecordFieldDeclaration, ...]


@dataclass(frozen=True)
class EnumPayloadField(Node):
    name: str
    type_annotation: TypeExpression


@dataclass(frozen=True)
class EnumVariantDeclaration(Node):
    name: str
    payload: tuple[EnumPayloadField, ...]


@dataclass(frozen=True)
class EnumDeclaration(Statement):
    name: str
    variants: tuple[EnumVariantDeclaration, ...]
