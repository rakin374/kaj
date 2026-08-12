from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Never, cast

from kaj.ast import (
    AssignmentOperator,
    AssignmentStatement,
    BinaryExpression,
    BinaryOperator,
    BindingDeclaration,
    BindingKind,
    Block,
    BooleanLiteral,
    BreakStatement,
    CallArgument,
    CallExpression,
    ContinueStatement,
    DecimalLiteral,
    EnumConstructionExpression,
    EnumConstructorArgument,
    EnumDeclaration,
    EnumPattern,
    EnumPayloadField,
    EnumVariantDeclaration,
    Expression,
    ExpressionStatement,
    ForStatement,
    FunctionDeclaration,
    GenericType,
    Identifier,
    IfStatement,
    IndexExpression,
    IntegerLiteral,
    ListLiteral,
    MapEntry,
    MapLiteral,
    MatchCase,
    MatchStatement,
    MemberAccessExpression,
    NamedType,
    NoneLiteral,
    Parameter,
    PatternBinding,
    Program,
    RecordConstructionExpression,
    RecordDeclaration,
    RecordFieldDeclaration,
    RecordFieldInitializer,
    ReturnStatement,
    Statement,
    StringLiteral,
    TypeExpression,
    UnaryExpression,
    UnaryOperator,
    WhileStatement,
)
from kaj.diagnostics import Diagnostic
from kaj.lexer import Token, TokenKind
from kaj.source import SourceSpan

PARSE_EXPECTED_EXPRESSION = "PARSE_EXPECTED_EXPRESSION"
PARSE_EXPECTED_IDENTIFIER = "PARSE_EXPECTED_IDENTIFIER"
PARSE_EXPECTED_TOKEN = "PARSE_EXPECTED_TOKEN"
PARSE_EXPECTED_TYPE = "PARSE_EXPECTED_TYPE"
PARSE_UNEXPECTED_TOKEN = "PARSE_UNEXPECTED_TOKEN"
PARSE_INVALID_ASSIGNMENT_TARGET = "PARSE_INVALID_ASSIGNMENT_TARGET"
PARSE_POSITIONAL_AFTER_NAMED_ARGUMENT = "PARSE_POSITIONAL_AFTER_NAMED_ARGUMENT"


UNARY_OPERATORS: dict[TokenKind, UnaryOperator] = {
    TokenKind.PLUS: UnaryOperator.POSITIVE,
    TokenKind.MINUS: UnaryOperator.NEGATE,
    TokenKind.NOT: UnaryOperator.NOT,
}

BINARY_OPERATORS: dict[TokenKind, BinaryOperator] = {
    TokenKind.PLUS: BinaryOperator.ADD,
    TokenKind.MINUS: BinaryOperator.SUBTRACT,
    TokenKind.STAR: BinaryOperator.MULTIPLY,
    TokenKind.SLASH: BinaryOperator.DIVIDE,
    TokenKind.PERCENT: BinaryOperator.MODULO,
    TokenKind.STAR_STAR: BinaryOperator.POWER,
    TokenKind.EQUAL_EQUAL: BinaryOperator.EQUAL,
    TokenKind.BANG_EQUAL: BinaryOperator.NOT_EQUAL,
    TokenKind.LESS: BinaryOperator.LESS,
    TokenKind.LESS_EQUAL: BinaryOperator.LESS_EQUAL,
    TokenKind.GREATER: BinaryOperator.GREATER,
    TokenKind.GREATER_EQUAL: BinaryOperator.GREATER_EQUAL,
    TokenKind.AND: BinaryOperator.AND,
    TokenKind.OR: BinaryOperator.OR,
}

ASSIGNMENT_OPERATORS: dict[TokenKind, AssignmentOperator] = {
    TokenKind.EQUAL: AssignmentOperator.ASSIGN,
    TokenKind.PLUS_EQUAL: AssignmentOperator.ADD_ASSIGN,
    TokenKind.MINUS_EQUAL: AssignmentOperator.SUBTRACT_ASSIGN,
    TokenKind.STAR_EQUAL: AssignmentOperator.MULTIPLY_ASSIGN,
    TokenKind.SLASH_EQUAL: AssignmentOperator.DIVIDE_ASSIGN,
}

STATEMENT_STARTS = {
    TokenKind.LET,
    TokenKind.VAR,
    TokenKind.FN,
    TokenKind.TYPE,
    TokenKind.ENUM,
    TokenKind.IF,
    TokenKind.WHILE,
    TokenKind.FOR,
    TokenKind.BREAK,
    TokenKind.CONTINUE,
    TokenKind.RETURN,
    TokenKind.MATCH,
}

DEFERRED_STATEMENT_KEYWORDS = {
    TokenKind.NEWTYPE,
    TokenKind.MATCH,
    TokenKind.IMPORT,
}


@dataclass(frozen=True)
class ParserResult:
    program: Program
    diagnostics: tuple[Diagnostic, ...]


class _ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: list[Token], filename: str = "<source>") -> None:
        if not tokens or tokens[-1].kind is not TokenKind.EOF:
            raise ValueError("Parser token streams must end with EOF.")
        self.tokens = tokens
        self.filename = filename
        self._index = 0
        self._diagnostics: list[Diagnostic] = []
        self._parsing_control_condition = False

    def parse(self) -> ParserResult:
        self._index = 0
        self._diagnostics.clear()
        self._parsing_control_condition = False
        statements: list[Statement] = []

        while not self._check(TokenKind.EOF):
            statement = self._parse_statement_recovering(in_block=False)
            if statement is not None:
                statements.append(statement)

        eof = self._current()
        if statements:
            span = SourceSpan(statements[0].span.start, statements[-1].span.end)
        else:
            span = SourceSpan(eof.span.start, eof.span.end)
        return ParserResult(
            program=Program(span=span, statements=tuple(statements)),
            diagnostics=tuple(self._diagnostics),
        )

    def _parse_statement_recovering(self, *, in_block: bool) -> Statement | None:
        start_index = self._index
        try:
            return self._parse_statement()
        except _ParseError:
            self._synchronize(start_index=start_index, in_block=in_block)
            return None

    def _parse_statement(self) -> Statement:
        if self._match(TokenKind.LET):
            return self._parse_binding(self._previous(), BindingKind.LET)
        if self._match(TokenKind.VAR):
            return self._parse_binding(self._previous(), BindingKind.VAR)
        if self._match(TokenKind.FN):
            return self._parse_function(self._previous())
        if self._match(TokenKind.TYPE):
            return self._parse_record_declaration(self._previous())
        if self._match(TokenKind.ENUM):
            return self._parse_enum_declaration(self._previous())
        if self._match(TokenKind.IF):
            return self._parse_if(self._previous())
        if self._match(TokenKind.WHILE):
            return self._parse_while(self._previous())
        if self._match(TokenKind.FOR):
            return self._parse_for(self._previous())
        if self._match(TokenKind.BREAK):
            token = self._previous()
            return BreakStatement(span=token.span)
        if self._match(TokenKind.CONTINUE):
            token = self._previous()
            return ContinueStatement(span=token.span)
        if self._match(TokenKind.RETURN):
            return self._parse_return(self._previous())
        if self._match(TokenKind.MATCH):
            return self._parse_match(self._previous())
        if self._current().kind in DEFERRED_STATEMENT_KEYWORDS:
            self._raise(
                PARSE_UNEXPECTED_TOKEN,
                f"{self._current().lexeme!r} is reserved but not parsed in Checkpoint 3.",
                self._current().span,
            )
        return self._parse_expression_or_assignment_statement()

    def _parse_binding(self, start: Token, kind: BindingKind) -> BindingDeclaration:
        name = self._consume(
            TokenKind.IDENTIFIER,
            PARSE_EXPECTED_IDENTIFIER,
            "Expected a binding name.",
        )
        annotation = None
        if self._match(TokenKind.COLON):
            annotation = self._parse_type_expression()
        self._consume(TokenKind.EQUAL, PARSE_EXPECTED_TOKEN, "Expected '=' in binding.")
        initializer = self._parse_expression()
        return BindingDeclaration(
            span=SourceSpan(start.span.start, initializer.span.end),
            name=name.lexeme,
            kind=kind,
            annotation=annotation,
            initializer=initializer,
        )

    def _parse_function(self, start: Token) -> FunctionDeclaration:
        name = self._consume(
            TokenKind.IDENTIFIER,
            PARSE_EXPECTED_IDENTIFIER,
            "Expected a function name.",
        )
        self._consume(
            TokenKind.LEFT_PAREN,
            PARSE_EXPECTED_TOKEN,
            "Expected '(' after function name.",
        )
        parameters: list[Parameter] = []
        if not self._check(TokenKind.RIGHT_PAREN):
            while True:
                parameters.append(self._parse_parameter())
                if not self._match(TokenKind.COMMA):
                    break
        self._consume(
            TokenKind.RIGHT_PAREN,
            PARSE_EXPECTED_TOKEN,
            "Expected ')' after parameters.",
        )
        self._consume(
            TokenKind.ARROW,
            PARSE_EXPECTED_TOKEN,
            "Expected '->' before function return type.",
        )
        return_type = self._parse_type_expression()
        body = self._parse_block()
        return FunctionDeclaration(
            span=SourceSpan(start.span.start, body.span.end),
            name=name.lexeme,
            parameters=tuple(parameters),
            return_type=return_type,
            body=body,
        )

    def _parse_parameter(self) -> Parameter:
        mutable_token = self._advance() if self._check(TokenKind.VAR) else None
        name = self._consume(
            TokenKind.IDENTIFIER,
            PARSE_EXPECTED_IDENTIFIER,
            "Expected a parameter name.",
        )
        self._consume(
            TokenKind.COLON,
            PARSE_EXPECTED_TOKEN,
            "Expected ':' after parameter name.",
        )
        annotation = self._parse_type_expression()
        start = mutable_token.span.start if mutable_token is not None else name.span.start
        return Parameter(
            span=SourceSpan(start, annotation.span.end),
            name=name.lexeme,
            type_annotation=annotation,
            mutable=mutable_token is not None,
        )

    def _parse_record_declaration(self, start: Token) -> RecordDeclaration:
        name = self._consume(
            TokenKind.IDENTIFIER,
            PARSE_EXPECTED_IDENTIFIER,
            "Expected a record type name.",
        )
        self._consume(
            TokenKind.LEFT_BRACE,
            PARSE_EXPECTED_TOKEN,
            "Expected '{' after record type name.",
        )
        fields: list[RecordFieldDeclaration] = []
        while not self._check(TokenKind.RIGHT_BRACE) and not self._check(TokenKind.EOF):
            field_name = self._consume(
                TokenKind.IDENTIFIER,
                PARSE_EXPECTED_IDENTIFIER,
                "Expected a record field name.",
            )
            self._consume(
                TokenKind.COLON,
                PARSE_EXPECTED_TOKEN,
                "Expected ':' after record field name.",
            )
            annotation = self._parse_type_expression()
            fields.append(
                RecordFieldDeclaration(
                    span=SourceSpan(field_name.span.start, annotation.span.end),
                    name=field_name.lexeme,
                    type_annotation=annotation,
                )
            )
        end = self._consume(
            TokenKind.RIGHT_BRACE,
            PARSE_EXPECTED_TOKEN,
            "Expected '}' after record fields.",
        )
        return RecordDeclaration(
            span=SourceSpan(start.span.start, end.span.end),
            name=name.lexeme,
            fields=tuple(fields),
        )

    def _parse_enum_declaration(self, start: Token) -> EnumDeclaration:
        name = self._consume(
            TokenKind.IDENTIFIER, PARSE_EXPECTED_IDENTIFIER, "Expected an enum type name."
        )
        self._consume(
            TokenKind.LEFT_BRACE, PARSE_EXPECTED_TOKEN, "Expected '{' after enum type name."
        )
        variants: list[EnumVariantDeclaration] = []
        while not self._check(TokenKind.RIGHT_BRACE) and not self._check(TokenKind.EOF):
            variant = self._consume(
                TokenKind.IDENTIFIER, PARSE_EXPECTED_IDENTIFIER, "Expected an enum variant name."
            )
            payload: list[EnumPayloadField] = []
            end = variant.span.end
            if self._match(TokenKind.LEFT_PAREN):
                if not self._check(TokenKind.RIGHT_PAREN):
                    while True:
                        field = self._consume(
                            TokenKind.IDENTIFIER,
                            PARSE_EXPECTED_IDENTIFIER,
                            "Expected a payload field name.",
                        )
                        self._consume(
                            TokenKind.COLON,
                            PARSE_EXPECTED_TOKEN,
                            "Expected ':' after payload field name.",
                        )
                        annotation = self._parse_type_expression()
                        payload.append(
                            EnumPayloadField(
                                SourceSpan(field.span.start, annotation.span.end),
                                field.lexeme,
                                annotation,
                            )
                        )
                        if not self._match(TokenKind.COMMA):
                            break
                end = self._consume(
                    TokenKind.RIGHT_PAREN,
                    PARSE_EXPECTED_TOKEN,
                    "Expected ')' after payload fields.",
                ).span.end
            variants.append(
                EnumVariantDeclaration(
                    SourceSpan(variant.span.start, end), variant.lexeme, tuple(payload)
                )
            )
        close = self._consume(
            TokenKind.RIGHT_BRACE, PARSE_EXPECTED_TOKEN, "Expected '}' after enum variants."
        )
        return EnumDeclaration(
            SourceSpan(start.span.start, close.span.end), name.lexeme, tuple(variants)
        )

    def _parse_match(self, start: Token) -> MatchStatement:
        scrutinee = self._parse_control_condition()
        self._consume(
            TokenKind.LEFT_BRACE, PARSE_EXPECTED_TOKEN, "Expected '{' after match expression."
        )
        cases: list[MatchCase] = []
        while not self._check(TokenKind.RIGHT_BRACE) and not self._check(TokenKind.EOF):
            variant = self._consume(
                TokenKind.IDENTIFIER, PARSE_EXPECTED_IDENTIFIER, "Expected an enum variant pattern."
            )
            bindings: list[PatternBinding] = []
            pattern_end = variant.span.end
            if self._match(TokenKind.LEFT_PAREN):
                if not self._check(TokenKind.RIGHT_PAREN):
                    while True:
                        binding = self._consume(
                            TokenKind.IDENTIFIER,
                            PARSE_EXPECTED_IDENTIFIER,
                            "Expected a pattern binding name.",
                        )
                        bindings.append(PatternBinding(binding.span, binding.lexeme))
                        if not self._match(TokenKind.COMMA):
                            break
                pattern_end = self._consume(
                    TokenKind.RIGHT_PAREN,
                    PARSE_EXPECTED_TOKEN,
                    "Expected ')' after pattern bindings.",
                ).span.end
            pattern = EnumPattern(
                SourceSpan(variant.span.start, pattern_end), variant.lexeme, tuple(bindings)
            )
            self._consume(
                TokenKind.FAT_ARROW, PARSE_EXPECTED_TOKEN, "Expected '=>' after match pattern."
            )
            body = (
                self._parse_block()
                if self._check(TokenKind.LEFT_BRACE)
                else self._parse_statement()
            )
            cases.append(MatchCase(SourceSpan(pattern.span.start, body.span.end), pattern, body))
        close = self._consume(
            TokenKind.RIGHT_BRACE, PARSE_EXPECTED_TOKEN, "Expected '}' after match cases."
        )
        return MatchStatement(SourceSpan(start.span.start, close.span.end), scrutinee, tuple(cases))

    def _parse_type_expression(self) -> TypeExpression:
        name = self._consume(
            TokenKind.IDENTIFIER,
            PARSE_EXPECTED_TYPE,
            "Expected a type name.",
        )
        named = NamedType(span=name.span, name=name.lexeme)
        if not self._match(TokenKind.LESS):
            return named

        arguments = [self._parse_type_expression()]
        while self._match(TokenKind.COMMA):
            arguments.append(self._parse_type_expression())
        end = self._consume(
            TokenKind.GREATER,
            PARSE_EXPECTED_TOKEN,
            "Expected '>' after generic type arguments.",
        )
        return GenericType(
            span=SourceSpan(named.span.start, end.span.end),
            base=named,
            arguments=tuple(arguments),
        )

    def _parse_if(self, start: Token) -> IfStatement:
        condition = self._parse_control_condition()
        then_branch = self._parse_block()
        else_branch: Block | IfStatement | None = None
        if self._match(TokenKind.ELSE):
            if self._match(TokenKind.IF):
                else_branch = self._parse_if(self._previous())
            else:
                else_branch = self._parse_block()
        end = else_branch.span.end if else_branch is not None else then_branch.span.end
        return IfStatement(
            span=SourceSpan(start.span.start, end),
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
        )

    def _parse_while(self, start: Token) -> WhileStatement:
        condition = self._parse_control_condition()
        body = self._parse_block()
        return WhileStatement(
            span=SourceSpan(start.span.start, body.span.end),
            condition=condition,
            body=body,
        )

    def _parse_control_condition(self) -> Expression:
        self._parsing_control_condition = True
        try:
            return self._parse_expression()
        finally:
            self._parsing_control_condition = False

    def _parse_for(self, start: Token) -> ForStatement:
        name = self._consume(
            TokenKind.IDENTIFIER,
            PARSE_EXPECTED_IDENTIFIER,
            "Expected a loop binding name.",
        )
        self._consume(TokenKind.IN, PARSE_EXPECTED_TOKEN, "Expected 'in' in for statement.")
        iterable = self._parse_expression()
        body = self._parse_block()
        return ForStatement(
            span=SourceSpan(start.span.start, body.span.end),
            name=name.lexeme,
            iterable=iterable,
            body=body,
        )

    def _parse_return(self, start: Token) -> ReturnStatement:
        if self._check(TokenKind.RIGHT_BRACE) or self._check(TokenKind.EOF):
            return ReturnStatement(span=start.span, value=None)
        value = self._parse_expression()
        return ReturnStatement(
            span=SourceSpan(start.span.start, value.span.end),
            value=value,
        )

    def _parse_block(self) -> Block:
        start = self._consume(
            TokenKind.LEFT_BRACE,
            PARSE_EXPECTED_TOKEN,
            "Expected '{' to begin block.",
        )
        statements: list[Statement] = []
        while not self._check(TokenKind.RIGHT_BRACE) and not self._check(TokenKind.EOF):
            statement = self._parse_statement_recovering(in_block=True)
            if statement is not None:
                statements.append(statement)
        end = self._consume(
            TokenKind.RIGHT_BRACE,
            PARSE_EXPECTED_TOKEN,
            "Expected '}' after block.",
        )
        return Block(
            span=SourceSpan(start.span.start, end.span.end),
            statements=tuple(statements),
        )

    def _parse_expression_or_assignment_statement(self) -> Statement:
        expression = self._parse_expression()
        assignment = ASSIGNMENT_OPERATORS.get(self._current().kind)
        if assignment is None:
            return ExpressionStatement(span=expression.span, expression=expression)

        self._advance()
        value = self._parse_expression()
        if not isinstance(expression, (Identifier, MemberAccessExpression, IndexExpression)):
            self._report(
                PARSE_INVALID_ASSIGNMENT_TARGET,
                "Assignment target must be an identifier, member access, or index expression.",
                expression.span,
            )
        return AssignmentStatement(
            span=SourceSpan(expression.span.start, value.span.end),
            target=expression,
            operator=assignment,
            value=value,
        )

    def _parse_expression(self) -> Expression:
        return self._parse_or()

    def _parse_or(self) -> Expression:
        return self._parse_left_associative(self._parse_and, {TokenKind.OR})

    def _parse_and(self) -> Expression:
        return self._parse_left_associative(self._parse_equality, {TokenKind.AND})

    def _parse_equality(self) -> Expression:
        return self._parse_left_associative(
            self._parse_comparison,
            {TokenKind.EQUAL_EQUAL, TokenKind.BANG_EQUAL},
        )

    def _parse_comparison(self) -> Expression:
        return self._parse_left_associative(
            self._parse_term,
            {
                TokenKind.LESS,
                TokenKind.LESS_EQUAL,
                TokenKind.GREATER,
                TokenKind.GREATER_EQUAL,
            },
        )

    def _parse_term(self) -> Expression:
        return self._parse_left_associative(
            self._parse_factor,
            {TokenKind.PLUS, TokenKind.MINUS},
        )

    def _parse_factor(self) -> Expression:
        return self._parse_left_associative(
            self._parse_unary,
            {TokenKind.STAR, TokenKind.SLASH, TokenKind.PERCENT},
        )

    def _parse_left_associative(
        self,
        operand_parser: Callable[[], Expression],
        operators: set[TokenKind],
    ) -> Expression:
        expression = operand_parser()
        while self._current().kind in operators:
            operator = self._advance()
            right = operand_parser()
            expression = BinaryExpression(
                span=SourceSpan(expression.span.start, right.span.end),
                left=expression,
                operator=BINARY_OPERATORS[operator.kind],
                right=right,
            )
        return expression

    def _parse_unary(self) -> Expression:
        operator = UNARY_OPERATORS.get(self._current().kind)
        if operator is None:
            return self._parse_power()
        token = self._advance()
        operand = self._parse_unary()
        return UnaryExpression(
            span=SourceSpan(token.span.start, operand.span.end),
            operator=operator,
            operand=operand,
        )

    def _parse_power(self) -> Expression:
        expression = self._parse_postfix()
        if self._match(TokenKind.STAR_STAR):
            right = self._parse_unary()
            return BinaryExpression(
                span=SourceSpan(expression.span.start, right.span.end),
                left=expression,
                operator=BinaryOperator.POWER,
                right=right,
            )
        return expression

    def _parse_postfix(self) -> Expression:
        expression = self._parse_primary()
        while True:
            if self._match(TokenKind.LEFT_PAREN):
                expression = self._finish_call(expression)
            elif self._match(TokenKind.DOT):
                member = self._consume(
                    TokenKind.IDENTIFIER,
                    PARSE_EXPECTED_IDENTIFIER,
                    "Expected member name after '.'.",
                )
                if isinstance(expression, Identifier) and expression.name[:1].isupper():
                    expression = EnumConstructionExpression(
                        span=SourceSpan(expression.span.start, member.span.end),
                        type_name=expression.name,
                        variant_name=member.lexeme,
                        arguments=None,
                    )
                else:
                    expression = MemberAccessExpression(
                        span=SourceSpan(expression.span.start, member.span.end),
                        object=expression,
                        member=member.lexeme,
                    )
            elif self._match(TokenKind.LEFT_BRACKET):
                index = self._parse_expression()
                end = self._consume(
                    TokenKind.RIGHT_BRACKET,
                    PARSE_EXPECTED_TOKEN,
                    "Expected ']' after index.",
                )
                expression = IndexExpression(
                    span=SourceSpan(expression.span.start, end.span.end),
                    object=expression,
                    index=index,
                )
            else:
                return expression

    def _finish_call(self, callee: Expression) -> Expression:
        arguments: list[CallArgument] = []
        saw_named = False
        if not self._check(TokenKind.RIGHT_PAREN):
            while True:
                if self._check(TokenKind.IDENTIFIER) and self._peek_kind() is TokenKind.COLON:
                    name = self._advance()
                    self._advance()
                    value = self._parse_expression()
                    saw_named = True
                    arguments.append(
                        CallArgument(
                            span=SourceSpan(name.span.start, value.span.end),
                            name=name.lexeme,
                            value=value,
                        )
                    )
                else:
                    value = self._parse_expression()
                    if saw_named:
                        self._report(
                            PARSE_POSITIONAL_AFTER_NAMED_ARGUMENT,
                            "Positional arguments must precede named arguments.",
                            value.span,
                        )
                    arguments.append(CallArgument(span=value.span, name=None, value=value))
                if not self._match(TokenKind.COMMA):
                    break
        end = self._consume(
            TokenKind.RIGHT_PAREN,
            PARSE_EXPECTED_TOKEN,
            "Expected ')' after call arguments.",
        )
        if isinstance(callee, EnumConstructionExpression):
            enum_arguments: list[EnumConstructorArgument] = []
            for argument in arguments:
                if argument.name is None:
                    self._report(
                        PARSE_EXPECTED_IDENTIFIER,
                        "Enum constructor arguments must be named.",
                        argument.span,
                    )
                    continue
                enum_arguments.append(
                    EnumConstructorArgument(argument.span, argument.name, argument.value)
                )
            return EnumConstructionExpression(
                SourceSpan(callee.span.start, end.span.end),
                callee.type_name,
                callee.variant_name,
                tuple(enum_arguments),
            )
        return CallExpression(
            span=SourceSpan(callee.span.start, end.span.end),
            callee=callee,
            arguments=tuple(arguments),
        )

    def _parse_primary(self) -> Expression:
        token = self._current()
        primary_kinds = {
            TokenKind.INTEGER,
            TokenKind.DECIMAL,
            TokenKind.STRING,
            TokenKind.TRUE,
            TokenKind.FALSE,
            TokenKind.NONE,
            TokenKind.IDENTIFIER,
            TokenKind.LEFT_PAREN,
            TokenKind.LEFT_BRACKET,
            TokenKind.LEFT_BRACE,
        }
        if token.kind not in primary_kinds:
            self._raise(
                PARSE_EXPECTED_EXPRESSION,
                "Expected an expression.",
                token.span,
            )
        self._advance()
        if token.kind is TokenKind.INTEGER:
            return IntegerLiteral(span=token.span, value=cast(int, token.value))
        if token.kind is TokenKind.DECIMAL:
            return DecimalLiteral(span=token.span, value=cast(Decimal, token.value))
        if token.kind is TokenKind.STRING:
            return StringLiteral(span=token.span, value=cast(str, token.value))
        if token.kind is TokenKind.TRUE:
            return BooleanLiteral(span=token.span, value=True)
        if token.kind is TokenKind.FALSE:
            return BooleanLiteral(span=token.span, value=False)
        if token.kind is TokenKind.NONE:
            return NoneLiteral(span=token.span)
        if token.kind is TokenKind.IDENTIFIER:
            if self._check(TokenKind.LEFT_BRACE) and self._looks_like_record_construction():
                return self._finish_record_construction(token)
            return Identifier(span=token.span, name=token.lexeme)
        if token.kind is TokenKind.LEFT_PAREN:
            expression = self._parse_expression()
            end = self._consume(
                TokenKind.RIGHT_PAREN,
                PARSE_EXPECTED_TOKEN,
                "Expected ')' after grouped expression.",
            )
            return replace(expression, span=SourceSpan(token.span.start, end.span.end))
        if token.kind is TokenKind.LEFT_BRACKET:
            return self._finish_list(token)
        if token.kind is TokenKind.LEFT_BRACE:
            return self._finish_map(token)
        raise AssertionError("Unhandled primary token kind")

    def _looks_like_record_construction(self) -> bool:
        brace_index = self._index
        next_index = min(brace_index + 1, len(self.tokens) - 1)
        after_index = min(brace_index + 2, len(self.tokens) - 1)
        return (
            not self._parsing_control_condition
            and self.tokens[next_index].kind is TokenKind.RIGHT_BRACE
        ) or (
            self.tokens[next_index].kind is TokenKind.IDENTIFIER
            and self.tokens[after_index].kind is TokenKind.COLON
        )

    def _finish_record_construction(self, name: Token) -> RecordConstructionExpression:
        self._consume(
            TokenKind.LEFT_BRACE,
            PARSE_EXPECTED_TOKEN,
            "Expected '{' after record type name.",
        )
        fields: list[RecordFieldInitializer] = []
        if not self._check(TokenKind.RIGHT_BRACE):
            while True:
                field_name = self._consume(
                    TokenKind.IDENTIFIER,
                    PARSE_EXPECTED_IDENTIFIER,
                    "Expected a record initializer field name.",
                )
                self._consume(
                    TokenKind.COLON,
                    PARSE_EXPECTED_TOKEN,
                    "Expected ':' after record initializer field name.",
                )
                value = self._parse_expression()
                fields.append(
                    RecordFieldInitializer(
                        span=SourceSpan(field_name.span.start, value.span.end),
                        name=field_name.lexeme,
                        value=value,
                    )
                )
                if not self._match(TokenKind.COMMA):
                    break
        end = self._consume(
            TokenKind.RIGHT_BRACE,
            PARSE_EXPECTED_TOKEN,
            "Expected '}' after record initializer fields.",
        )
        return RecordConstructionExpression(
            span=SourceSpan(name.span.start, end.span.end),
            type_name=name.lexeme,
            fields=tuple(fields),
        )

    def _finish_list(self, start: Token) -> ListLiteral:
        elements: list[Expression] = []
        if not self._check(TokenKind.RIGHT_BRACKET):
            while True:
                elements.append(self._parse_expression())
                if not self._match(TokenKind.COMMA):
                    break
        end = self._consume(
            TokenKind.RIGHT_BRACKET,
            PARSE_EXPECTED_TOKEN,
            "Expected ']' after list literal.",
        )
        return ListLiteral(
            span=SourceSpan(start.span.start, end.span.end),
            elements=tuple(elements),
        )

    def _finish_map(self, start: Token) -> MapLiteral:
        entries: list[MapEntry] = []
        if not self._check(TokenKind.RIGHT_BRACE):
            while True:
                key = self._parse_expression()
                self._consume(
                    TokenKind.COLON,
                    PARSE_EXPECTED_TOKEN,
                    "Expected ':' between map key and value.",
                )
                value = self._parse_expression()
                entries.append(
                    MapEntry(
                        span=SourceSpan(key.span.start, value.span.end),
                        key=key,
                        value=value,
                    )
                )
                if not self._match(TokenKind.COMMA):
                    break
        end = self._consume(
            TokenKind.RIGHT_BRACE,
            PARSE_EXPECTED_TOKEN,
            "Expected '}' after map literal.",
        )
        return MapLiteral(
            span=SourceSpan(start.span.start, end.span.end),
            entries=tuple(entries),
        )

    def _consume(self, kind: TokenKind, code: str, message: str) -> Token:
        if self._check(kind):
            return self._advance()
        self._raise(code, message, self._current().span)

    def _synchronize(self, *, start_index: int, in_block: bool) -> None:
        if self._index == start_index:
            if in_block and self._check(TokenKind.RIGHT_BRACE):
                return
            if not self._check(TokenKind.EOF):
                self._advance()

        while not self._check(TokenKind.EOF):
            if in_block and self._check(TokenKind.RIGHT_BRACE):
                return
            if self._current().kind in STATEMENT_STARTS:
                return
            self._advance()

    def _report(self, code: str, message: str, span: SourceSpan) -> None:
        self._diagnostics.append(Diagnostic(code=code, message=message, span=span))

    def _raise(self, code: str, message: str, span: SourceSpan) -> Never:
        self._report(code, message, span)
        raise _ParseError

    def _match(self, *kinds: TokenKind) -> bool:
        if self._current().kind not in kinds:
            return False
        self._advance()
        return True

    def _check(self, kind: TokenKind) -> bool:
        return self._current().kind is kind

    def _advance(self) -> Token:
        token = self._current()
        if token.kind is not TokenKind.EOF:
            self._index += 1
        return token

    def _current(self) -> Token:
        return self.tokens[self._index]

    def _previous(self) -> Token:
        return self.tokens[self._index - 1]

    def _peek_kind(self) -> TokenKind:
        next_index = min(self._index + 1, len(self.tokens) - 1)
        return self.tokens[next_index].kind
