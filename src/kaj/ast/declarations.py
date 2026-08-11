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
