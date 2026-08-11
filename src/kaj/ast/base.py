from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from kaj.source import SourceSpan


@dataclass(frozen=True)
class Node:
    span: SourceSpan


@dataclass(frozen=True)
class Expression(Node):
    pass


@dataclass(frozen=True)
class Statement(Node):
    pass


@dataclass(frozen=True)
class TypeExpression(Node):
    pass


@dataclass(frozen=True)
class Program(Node):
    statements: tuple[Statement, ...]


class BindingKind(Enum):
    LET = auto()
    VAR = auto()


class UnaryOperator(Enum):
    POSITIVE = auto()
    NEGATE = auto()
    NOT = auto()


class BinaryOperator(Enum):
    ADD = auto()
    SUBTRACT = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()
    POWER = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    AND = auto()
    OR = auto()


class AssignmentOperator(Enum):
    ASSIGN = auto()
    ADD_ASSIGN = auto()
    SUBTRACT_ASSIGN = auto()
    MULTIPLY_ASSIGN = auto()
    DIVIDE_ASSIGN = auto()
