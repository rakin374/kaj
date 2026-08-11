from __future__ import annotations

from dataclasses import dataclass

from kaj.ast.base import AssignmentOperator, BindingKind, Expression, Statement, TypeExpression


@dataclass(frozen=True)
class Block(Statement):
    statements: tuple[Statement, ...]


@dataclass(frozen=True)
class BindingDeclaration(Statement):
    name: str
    kind: BindingKind
    annotation: TypeExpression | None
    initializer: Expression


@dataclass(frozen=True)
class AssignmentStatement(Statement):
    target: Expression
    operator: AssignmentOperator
    value: Expression


@dataclass(frozen=True)
class ExpressionStatement(Statement):
    expression: Expression


@dataclass(frozen=True)
class IfStatement(Statement):
    condition: Expression
    then_branch: Block
    else_branch: Block | IfStatement | None


@dataclass(frozen=True)
class WhileStatement(Statement):
    condition: Expression
    body: Block


@dataclass(frozen=True)
class ForStatement(Statement):
    name: str
    iterable: Expression
    body: Block


@dataclass(frozen=True)
class BreakStatement(Statement):
    pass


@dataclass(frozen=True)
class ContinueStatement(Statement):
    pass


@dataclass(frozen=True)
class ReturnStatement(Statement):
    value: Expression | None
