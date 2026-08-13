from __future__ import annotations

from decimal import Decimal

from kaj.ast import (
    AssignmentOperator,
    AssignmentStatement,
    AwaitTaskExpression,
    BinaryExpression,
    BinaryOperator,
    BindingDeclaration,
    BindingKind,
    Block,
    BooleanLiteral,
    BreakStatement,
    CallArgument,
    CallExpression,
    CapabilityDeclaration,
    ContinueStatement,
    DecimalLiteral,
    EnumConstructionExpression,
    EnumDeclaration,
    EnumPattern,
    Expression,
    ExpressionStatement,
    ForStatement,
    FunctionDeclaration,
    GenericType,
    GoalClause,
    HumanInteractionExpression,
    Identifier,
    IfStatement,
    ImportDeclaration,
    IndexExpression,
    IntegerLiteral,
    InterpolatedString,
    InvariantClause,
    ListLiteral,
    MapLiteral,
    MatchStatement,
    MemberAccessExpression,
    NamedType,
    NewtypeDeclaration,
    NoneLiteral,
    PlanRegion,
    Program,
    RecordConstructionExpression,
    RecordDeclaration,
    RequireClause,
    ReturnStatement,
    StartTaskExpression,
    Statement,
    StepStatement,
    StringLiteral,
    SuccessClause,
    TaskDeclaration,
    TypeExpression,
    UnaryExpression,
    UnaryOperator,
    UseCapabilityDeclaration,
    WhileStatement,
)

INDENT = "    "
LINE_WIDTH = 88

_ASSIGNMENT = {
    AssignmentOperator.ASSIGN: "=",
    AssignmentOperator.ADD_ASSIGN: "+=",
    AssignmentOperator.SUBTRACT_ASSIGN: "-=",
    AssignmentOperator.MULTIPLY_ASSIGN: "*=",
    AssignmentOperator.DIVIDE_ASSIGN: "/=",
}
_BINARY = {
    BinaryOperator.ADD: "+",
    BinaryOperator.SUBTRACT: "-",
    BinaryOperator.MULTIPLY: "*",
    BinaryOperator.DIVIDE: "/",
    BinaryOperator.MODULO: "%",
    BinaryOperator.POWER: "**",
    BinaryOperator.EQUAL: "==",
    BinaryOperator.NOT_EQUAL: "!=",
    BinaryOperator.LESS: "<",
    BinaryOperator.LESS_EQUAL: "<=",
    BinaryOperator.GREATER: ">",
    BinaryOperator.GREATER_EQUAL: ">=",
    BinaryOperator.AND: "and",
    BinaryOperator.OR: "or",
}
_PRECEDENCE = {
    BinaryOperator.OR: 1,
    BinaryOperator.AND: 2,
    BinaryOperator.EQUAL: 3,
    BinaryOperator.NOT_EQUAL: 3,
    BinaryOperator.LESS: 4,
    BinaryOperator.LESS_EQUAL: 4,
    BinaryOperator.GREATER: 4,
    BinaryOperator.GREATER_EQUAL: 4,
    BinaryOperator.ADD: 5,
    BinaryOperator.SUBTRACT: 5,
    BinaryOperator.MULTIPLY: 6,
    BinaryOperator.DIVIDE: 6,
    BinaryOperator.MODULO: 6,
    BinaryOperator.POWER: 8,
}


class FormatterError(ValueError):
    pass


def format_program(program: Program) -> str:
    formatter = _Formatter()
    groups: list[str] = []
    previous_declaration = False
    for statement in program.statements:
        rendered = formatter.statement(statement, 0)
        declaration = isinstance(
            statement,
            (
                FunctionDeclaration,
                TaskDeclaration,
                RecordDeclaration,
                EnumDeclaration,
                NewtypeDeclaration,
            ),
        )
        if groups and (declaration or previous_declaration):
            groups.append("")
        groups.extend(rendered)
        previous_declaration = declaration
    if not groups:
        return ""
    return "\n".join(line.rstrip() for line in groups).rstrip("\n") + "\n"


class _Formatter:
    def statement(self, statement: Statement, depth: int) -> list[str]:
        prefix = INDENT * depth
        if isinstance(statement, BindingDeclaration):
            kind = "let" if statement.kind is BindingKind.LET else "var"
            annotation = (
                ""
                if statement.annotation is None
                else f": {self.type_expression(statement.annotation)}"
            )
            return [
                f"{prefix}{kind} {statement.name}{annotation} = {self.expression(statement.initializer, depth)}"
            ]
        if isinstance(statement, AssignmentStatement):
            return [
                f"{prefix}{self.expression(statement.target, depth)} {_ASSIGNMENT[statement.operator]} {self.expression(statement.value, depth)}"
            ]
        if isinstance(statement, ExpressionStatement):
            return [prefix + self.expression(statement.expression, depth)]
        if isinstance(statement, ReturnStatement):
            suffix = (
                "" if statement.value is None else " " + self.expression(statement.value, depth)
            )
            return [prefix + "return" + suffix]
        if isinstance(statement, BreakStatement):
            return [prefix + "break"]
        if isinstance(statement, ContinueStatement):
            return [prefix + "continue"]
        if isinstance(statement, StepStatement):
            return self.header_block(f"step {statement.name}", statement.body, depth)
        if isinstance(statement, UseCapabilityDeclaration):
            return [prefix + f"use {statement.capability_name} as {statement.alias}"]
        if isinstance(statement, PlanRegion):
            return self.header_block("plan", statement.body, depth)
        if isinstance(statement, GoalClause):
            return [prefix + "goal " + self.expression(statement.expression, depth)]
        if isinstance(statement, RequireClause):
            return self.contract_condition("require", statement.condition, depth)
        if isinstance(statement, InvariantClause):
            return self.contract_condition("invariant", statement.condition, depth)
        if isinstance(statement, SuccessClause):
            parameter = ""
            if statement.parameter is not None:
                parameter = (
                    f"({statement.parameter.name}: "
                    f"{self.type_expression(statement.parameter.type_annotation)})"
                )
            return self.contract_condition("success" + parameter, statement.condition, depth)
        if isinstance(statement, Block):
            return self.block(statement, depth)
        if isinstance(statement, FunctionDeclaration):
            parameters = ", ".join(
                ("var " if parameter.mutable else "")
                + parameter.name
                + ": "
                + self.type_expression(parameter.type_annotation)
                for parameter in statement.parameters
            )
            header = f"fn {statement.name}({parameters}) -> {self.type_expression(statement.return_type)}"
            return self.header_block(header, statement.body, depth)
        if isinstance(statement, TaskDeclaration):
            parameters = ", ".join(
                ("var " if parameter.mutable else "")
                + parameter.name
                + ": "
                + self.type_expression(parameter.type_annotation)
                for parameter in statement.parameters
            )
            header = (
                f"task {statement.name}({parameters}) -> "
                f"{self.type_expression(statement.return_type)}"
            )
            return self.header_block(header, statement.body, depth)
        if isinstance(statement, CapabilityDeclaration):
            lines = [prefix + f"capability {statement.name} {{"]
            for operation in statement.operations:
                parameters = ", ".join(
                    parameter.name + ": " + self.type_expression(parameter.type_annotation)
                    for parameter in operation.parameters
                )
                lines.append(
                    INDENT * (depth + 1)
                    + f"fn {operation.name}({parameters}) -> "
                    + self.type_expression(operation.return_type)
                )
            lines.append(prefix + "}")
            return lines
        if isinstance(statement, RecordDeclaration):
            lines = [prefix + f"type {statement.name} {{"]
            lines.extend(
                INDENT * (depth + 1)
                + f"{field.name}: {self.type_expression(field.type_annotation)}"
                for field in statement.fields
            )
            lines.append(prefix + "}")
            return lines
        if isinstance(statement, EnumDeclaration):
            lines = [prefix + f"enum {statement.name} {{"]
            for variant in statement.variants:
                payload = ""
                if variant.payload:
                    payload = (
                        "("
                        + ", ".join(
                            f"{field.name}: {self.type_expression(field.type_annotation)}"
                            for field in variant.payload
                        )
                        + ")"
                    )
                lines.append(INDENT * (depth + 1) + variant.name + payload)
            lines.append(prefix + "}")
            return lines
        if isinstance(statement, NewtypeDeclaration):
            return [
                prefix
                + f"newtype {statement.name} = {self.type_expression(statement.underlying_type)}"
            ]
        if isinstance(statement, ImportDeclaration):
            return [prefix + "import " + ".".join(statement.path)]
        if isinstance(statement, IfStatement):
            return self.if_statement(statement, depth)
        if isinstance(statement, WhileStatement):
            return self.header_block(
                f"while {self.expression(statement.condition, depth)}", statement.body, depth
            )
        if isinstance(statement, ForStatement):
            return self.header_block(
                f"for {statement.name} in {self.expression(statement.iterable, depth)}",
                statement.body,
                depth,
            )
        if isinstance(statement, MatchStatement):
            lines = [prefix + f"match {self.expression(statement.scrutinee, depth)} {{"]
            for case in statement.cases:
                pattern = self.pattern(case.pattern)
                if isinstance(case.body, Block):
                    lines.append(INDENT * (depth + 1) + pattern + " => {")
                    for child in case.body.statements:
                        lines.extend(self.statement(child, depth + 2))
                    lines.append(INDENT * (depth + 1) + "}")
                else:
                    body = self.statement(case.body, 0)
                    lines.append(INDENT * (depth + 1) + pattern + " => " + body[0])
                    lines.extend(INDENT * (depth + 1) + line for line in body[1:])
            lines.append(prefix + "}")
            return lines
        raise FormatterError(f"FORMAT_UNSUPPORTED_NODE: {type(statement).__name__}")

    def contract_condition(self, header: str, condition: Expression, depth: int) -> list[str]:
        prefix = INDENT * depth
        return [
            prefix + header + " {",
            INDENT * (depth + 1) + self.expression(condition, depth + 1),
            prefix + "}",
        ]

    def if_statement(self, statement: IfStatement, depth: int) -> list[str]:
        lines = self.header_block(
            f"if {self.expression(statement.condition, depth)}", statement.then_branch, depth
        )
        if statement.else_branch is None:
            return lines
        lines[-1] += " else"
        if isinstance(statement.else_branch, IfStatement):
            nested = self.if_statement(statement.else_branch, depth)
            lines[-1] += " " + nested[0].lstrip()
            lines.extend(nested[1:])
        else:
            lines[-1] += " {"
            for child in statement.else_branch.statements:
                lines.extend(self.statement(child, depth + 1))
            lines.append(INDENT * depth + "}")
        return lines

    def header_block(self, header: str, block: Block, depth: int) -> list[str]:
        lines = [INDENT * depth + header + " {"]
        for child in block.statements:
            lines.extend(self.statement(child, depth + 1))
        lines.append(INDENT * depth + "}")
        return lines

    def block(self, block: Block, depth: int) -> list[str]:
        lines = [INDENT * depth + "{"]
        for child in block.statements:
            lines.extend(self.statement(child, depth + 1))
        lines.append(INDENT * depth + "}")
        return lines

    def type_expression(self, expression: TypeExpression) -> str:
        if isinstance(expression, NamedType):
            return expression.name
        if isinstance(expression, GenericType):
            rendered = (
                expression.base.name
                + "<"
                + ", ".join(self.type_expression(argument) for argument in expression.arguments)
                + ">"
            )
            return rendered.replace(">>", "> >")
        raise FormatterError(f"FORMAT_UNSUPPORTED_NODE: {type(expression).__name__}")

    def pattern(self, pattern: EnumPattern) -> str:
        if not pattern.bindings:
            return pattern.variant_name
        return pattern.variant_name + "(" + ", ".join(item.name for item in pattern.bindings) + ")"

    def expression(
        self,
        expression: Expression,
        depth: int = 0,
        parent_precedence: int = 0,
        side: str = "",
        parent_operator: BinaryOperator | None = None,
    ) -> str:
        precedence = self.expression_precedence(expression)
        if isinstance(expression, IntegerLiteral):
            text = str(expression.value)
        elif isinstance(expression, DecimalLiteral):
            text = self.decimal(expression.value)
        elif isinstance(expression, StringLiteral):
            text = self.string(expression.value)
        elif isinstance(expression, InterpolatedString):
            text = self.interpolated_string(expression)
        elif isinstance(expression, BooleanLiteral):
            text = "true" if expression.value else "false"
        elif isinstance(expression, NoneLiteral):
            text = "none"
        elif isinstance(expression, Identifier):
            text = expression.name
        elif isinstance(expression, UnaryExpression):
            operator = {
                UnaryOperator.POSITIVE: "+",
                UnaryOperator.NEGATE: "-",
                UnaryOperator.NOT: "not ",
            }[expression.operator]
            text = operator + self.expression(expression.operand, depth, 7, "right")
        elif isinstance(expression, BinaryExpression):
            own = _PRECEDENCE[expression.operator]
            left = self.expression(expression.left, depth, own, "left", expression.operator)
            right = self.expression(expression.right, depth, own, "right", expression.operator)
            text = f"{left} {_BINARY[expression.operator]} {right}"
        elif isinstance(expression, CallExpression):
            callee = self.expression(expression.callee, depth, 9, "left")
            text = self.comma_construct(
                callee + "(",
                [self.call_argument(item, depth) for item in expression.arguments],
                ")",
                depth,
            )
        elif isinstance(expression, HumanInteractionExpression):
            generic = (
                ""
                if expression.type_argument is None
                else f"<{self.type_expression(expression.type_argument)}>"
            )
            text = self.comma_construct(
                expression.kind + generic + "(",
                [self.call_argument(item, depth) for item in expression.arguments],
                ")",
                depth,
            )
        elif isinstance(expression, StartTaskExpression):
            text = self.comma_construct(
                "start " + expression.task_name + "(",
                [self.call_argument(item, depth) for item in expression.arguments],
                ")",
                depth,
            )
        elif isinstance(expression, AwaitTaskExpression):
            text = "await " + self.expression(expression.operand, depth, 8)
        elif isinstance(expression, MemberAccessExpression):
            text = self.expression(expression.object, depth, 9, "left") + "." + expression.member
        elif isinstance(expression, IndexExpression):
            text = (
                self.expression(expression.object, depth, 9, "left")
                + "["
                + self.expression(expression.index, depth)
                + "]"
            )
        elif isinstance(expression, ListLiteral):
            text = self.comma_construct(
                "[", [self.expression(item, depth + 1) for item in expression.elements], "]", depth
            )
        elif isinstance(expression, MapLiteral):
            text = self.comma_construct(
                "{",
                [
                    f"{self.expression(item.key, depth + 1)}: {self.expression(item.value, depth + 1)}"
                    for item in expression.entries
                ],
                "}",
                depth,
            )
        elif isinstance(expression, RecordConstructionExpression):
            text = self.comma_construct(
                expression.type_name + " {",
                [
                    f"{item.name}: {self.expression(item.value, depth + 1)}"
                    for item in expression.fields
                ],
                "}",
                depth,
            )
        elif isinstance(expression, EnumConstructionExpression):
            base = expression.type_name + "." + expression.variant_name
            text = (
                base
                if expression.arguments is None
                else self.comma_construct(
                    base + "(",
                    [
                        f"{item.name}: {self.expression(item.value, depth + 1)}"
                        for item in expression.arguments
                    ],
                    ")",
                    depth,
                )
            )
        else:
            raise FormatterError(f"FORMAT_UNSUPPORTED_NODE: {type(expression).__name__}")
        needs_parentheses = precedence < parent_precedence
        if precedence == parent_precedence and isinstance(expression, BinaryExpression):
            if parent_operator is BinaryOperator.POWER:
                needs_parentheses = side == "left"
            elif side == "right":
                needs_parentheses = True
        return f"({text})" if needs_parentheses else text

    def expression_precedence(self, expression: Expression) -> int:
        if isinstance(expression, BinaryExpression):
            return _PRECEDENCE[expression.operator]
        if isinstance(expression, UnaryExpression):
            return 7
        if isinstance(
            expression,
            (
                CallExpression,
                HumanInteractionExpression,
                MemberAccessExpression,
                IndexExpression,
            ),
        ):
            return 9
        return 10

    def call_argument(self, argument: CallArgument, depth: int) -> str:
        value = self.expression(argument.value, depth + 1)
        return value if argument.name is None else f"{argument.name}: {value}"

    def comma_construct(self, opening: str, items: list[str], closing: str, depth: int) -> str:
        if not items:
            return opening + closing
        inline = opening + ", ".join(items) + closing
        if "\n" not in inline and len(INDENT * depth + inline) <= LINE_WIDTH:
            return inline
        inner = INDENT * (depth + 1)
        return (
            opening
            + "\n"
            + "\n".join(inner + item + "," for item in items)
            + "\n"
            + INDENT * depth
            + closing
        )

    def decimal(self, value: Decimal) -> str:
        text = format(value, "f")
        if "." not in text:
            text += ".0"
        integer, fraction = text.split(".", 1)
        fraction = fraction.rstrip("0") or "0"
        return integer + "." + fraction

    def string(self, value: str) -> str:
        escaped = (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t")
        )
        return '"' + escaped + '"'

    def interpolated_string(self, expression: InterpolatedString) -> str:
        parts: list[str] = []
        for part in expression.parts:
            if isinstance(part, str):
                escaped = self.string(part)[1:-1]
                parts.append(escaped.replace("{", "{{").replace("}", "}}"))
            else:
                parts.append("{" + self.expression(part) + "}")
        return '"' + "".join(parts) + '"'
