from __future__ import annotations

from dataclasses import dataclass

from kaj.ast.base import (
    AssignmentOperator,
    BindingKind,
    Expression,
    Node,
    Statement,
    TypeExpression,
)


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
class StepStatement(Statement):
    name: str
    body: Block


@dataclass(frozen=True)
class UseCapabilityDeclaration(Statement):
    capability_name: str
    alias: str


@dataclass(frozen=True)
class PlanRegion(Statement):
    body: Block


@dataclass(frozen=True)
class GoalClause(Statement):
    expression: Expression


@dataclass(frozen=True)
class RequireClause(Statement):
    condition: Expression


@dataclass(frozen=True)
class InvariantClause(Statement):
    condition: Expression


@dataclass(frozen=True)
class SuccessParameter(Node):
    name: str
    type_annotation: TypeExpression


@dataclass(frozen=True)
class SuccessClause(Statement):
    parameter: SuccessParameter | None
    condition: Expression


@dataclass(frozen=True)
class ReturnStatement(Statement):
    value: Expression | None


@dataclass(frozen=True)
class PatternBinding(Node):
    name: str


@dataclass(frozen=True)
class EnumPattern(Node):
    variant_name: str
    bindings: tuple[PatternBinding, ...]


@dataclass(frozen=True)
class MatchCase(Node):
    pattern: EnumPattern
    body: Statement


@dataclass(frozen=True)
class MatchStatement(Statement):
    scrutinee: Expression
    cases: tuple[MatchCase, ...]
