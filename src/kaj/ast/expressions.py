from dataclasses import dataclass
from decimal import Decimal

from kaj.ast.base import BinaryOperator, Expression, Node, UnaryOperator


@dataclass(frozen=True)
class IntegerLiteral(Expression):
    value: int


@dataclass(frozen=True)
class DecimalLiteral(Expression):
    value: Decimal


@dataclass(frozen=True)
class StringLiteral(Expression):
    value: str


@dataclass(frozen=True)
class BooleanLiteral(Expression):
    value: bool


@dataclass(frozen=True)
class NoneLiteral(Expression):
    pass


@dataclass(frozen=True)
class Identifier(Expression):
    name: str


@dataclass(frozen=True)
class UnaryExpression(Expression):
    operator: UnaryOperator
    operand: Expression


@dataclass(frozen=True)
class BinaryExpression(Expression):
    left: Expression
    operator: BinaryOperator
    right: Expression


@dataclass(frozen=True)
class CallArgument(Node):
    name: str | None
    value: Expression


@dataclass(frozen=True)
class CallExpression(Expression):
    callee: Expression
    arguments: tuple[CallArgument, ...]


@dataclass(frozen=True)
class MemberAccessExpression(Expression):
    object: Expression
    member: str


@dataclass(frozen=True)
class IndexExpression(Expression):
    object: Expression
    index: Expression


@dataclass(frozen=True)
class ListLiteral(Expression):
    elements: tuple[Expression, ...]


@dataclass(frozen=True)
class MapEntry(Node):
    key: Expression
    value: Expression


@dataclass(frozen=True)
class MapLiteral(Expression):
    entries: tuple[MapEntry, ...]


@dataclass(frozen=True)
class RecordFieldInitializer(Node):
    name: str
    value: Expression


@dataclass(frozen=True)
class RecordConstructionExpression(Expression):
    type_name: str
    fields: tuple[RecordFieldInitializer, ...]
