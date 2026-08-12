from __future__ import annotations

from dataclasses import dataclass

from kaj.ast import (
    AssignmentStatement,
    BinaryExpression,
    BindingDeclaration,
    BindingKind,
    Block,
    BooleanLiteral,
    BreakStatement,
    CallExpression,
    ContinueStatement,
    DecimalLiteral,
    EnumConstructionExpression,
    EnumDeclaration,
    Expression,
    ExpressionStatement,
    ForStatement,
    FunctionDeclaration,
    Identifier,
    IfStatement,
    IndexExpression,
    IntegerLiteral,
    ListLiteral,
    MapLiteral,
    MatchStatement,
    MemberAccessExpression,
    Node,
    NoneLiteral,
    Program,
    RecordConstructionExpression,
    RecordDeclaration,
    ReturnStatement,
    Statement,
    StringLiteral,
    UnaryExpression,
    WhileStatement,
)
from kaj.diagnostics import Diagnostic
from kaj.semantic.scope import Scope, ScopeKind
from kaj.semantic.symbols import Symbol, SymbolKind
from kaj.source import SourceSpan


@dataclass(frozen=True)
class ResolvedReference:
    identifier: Identifier
    symbol: Symbol


@dataclass(frozen=True)
class DeclaredSymbol:
    declaration: Node
    symbol: Symbol


@dataclass(frozen=True)
class ResolutionResult:
    module_scope: Scope
    symbols: tuple[Symbol, ...]
    references: tuple[ResolvedReference, ...]
    declarations: tuple[DeclaredSymbol, ...]
    diagnostics: tuple[Diagnostic, ...]

    def symbol_for(self, identifier: Identifier) -> Symbol | None:
        """Return the symbol associated with this exact AST node."""
        for reference in self.references:
            if reference.identifier is identifier:
                return reference.symbol
        return None

    def symbol_for_declaration(self, declaration: Node) -> Symbol | None:
        """Return the symbol introduced by this exact declaration node."""
        for association in self.declarations:
            if association.declaration is declaration:
                return association.symbol
        return None


class Resolver:
    def __init__(self, *, include_builtins: bool = False) -> None:
        self._include_builtins = include_builtins
        self._next_symbol_id = 0
        self._symbols: list[Symbol] = []
        self._references: list[ResolvedReference] = []
        self._declarations: list[DeclaredSymbol] = []
        self._diagnostics: list[Diagnostic] = []

    def resolve(self, program: Program) -> ResolutionResult:
        self._next_symbol_id = 0
        self._symbols = []
        self._references = []
        self._declarations = []
        self._diagnostics = []
        builtin_scope = Scope(ScopeKind.MODULE) if self._include_builtins else None
        if builtin_scope is not None:
            print_symbol = self._new_symbol("print", SymbolKind.BUILTIN_FUNCTION, program.span)
            builtin_scope.declare(print_symbol)
        module_scope = Scope(ScopeKind.MODULE, builtin_scope)

        for statement in program.statements:
            if isinstance(statement, FunctionDeclaration):
                self._declare(
                    module_scope,
                    statement.name,
                    SymbolKind.FUNCTION,
                    statement.span,
                    statement,
                )

        for statement in program.statements:
            if isinstance(statement, FunctionDeclaration):
                self._resolve_function(statement, module_scope)
            else:
                self._resolve_statement(statement, module_scope)

        return ResolutionResult(
            module_scope=module_scope,
            symbols=tuple(self._symbols),
            references=tuple(self._references),
            declarations=tuple(self._declarations),
            diagnostics=tuple(self._diagnostics),
        )

    def _new_symbol(self, name: str, kind: SymbolKind, span: SourceSpan) -> Symbol:
        symbol = Symbol(self._next_symbol_id, name, kind, span)
        self._next_symbol_id += 1
        self._symbols.append(symbol)
        return symbol

    def _declare(
        self,
        scope: Scope,
        name: str,
        kind: SymbolKind,
        span: SourceSpan,
        declaration: Node,
    ) -> Symbol | None:
        if scope.lookup_local(name) is not None:
            self._diagnostics.append(
                Diagnostic(
                    code="RESOLVE_DUPLICATE_NAME",
                    message=f"Name '{name}' is already declared in this scope.",
                    span=span,
                )
            )
            return None
        symbol = self._new_symbol(name, kind, span)
        scope.declare(symbol)
        self._declarations.append(DeclaredSymbol(declaration, symbol))
        return symbol

    def _resolve_function(self, declaration: FunctionDeclaration, module_scope: Scope) -> None:
        function_scope = Scope(ScopeKind.FUNCTION, module_scope)
        for parameter in declaration.parameters:
            self._declare(
                function_scope,
                parameter.name,
                SymbolKind.PARAMETER,
                parameter.span,
                parameter,
            )
        self._resolve_statements(declaration.body.statements, function_scope)

    def _resolve_statements(self, statements: tuple[Statement, ...], scope: Scope) -> None:
        for statement in statements:
            self._resolve_statement(statement, scope)

    def _resolve_block(self, block: Block, parent: Scope) -> None:
        self._resolve_statements(block.statements, Scope(ScopeKind.BLOCK, parent))

    def _resolve_statement(self, statement: Statement, scope: Scope) -> None:
        if isinstance(statement, BindingDeclaration):
            self._resolve_expression(statement.initializer, scope)
            kind = (
                SymbolKind.LET_BINDING
                if statement.kind is BindingKind.LET
                else SymbolKind.VAR_BINDING
            )
            self._declare(scope, statement.name, kind, statement.span, statement)
        elif isinstance(statement, AssignmentStatement):
            self._resolve_expression(statement.target, scope)
            self._resolve_expression(statement.value, scope)
        elif isinstance(statement, ExpressionStatement):
            self._resolve_expression(statement.expression, scope)
        elif isinstance(statement, IfStatement):
            self._resolve_expression(statement.condition, scope)
            self._resolve_block(statement.then_branch, scope)
            if isinstance(statement.else_branch, Block):
                self._resolve_block(statement.else_branch, scope)
            elif statement.else_branch is not None:
                self._resolve_statement(statement.else_branch, scope)
        elif isinstance(statement, WhileStatement):
            self._resolve_expression(statement.condition, scope)
            self._resolve_block(statement.body, scope)
        elif isinstance(statement, ForStatement):
            self._resolve_expression(statement.iterable, scope)
            body_scope = Scope(ScopeKind.BLOCK, scope)
            self._declare(
                body_scope,
                statement.name,
                SymbolKind.LOOP_VARIABLE,
                statement.span,
                statement,
            )
            self._resolve_statements(statement.body.statements, body_scope)
        elif isinstance(statement, ReturnStatement):
            if statement.value is not None:
                self._resolve_expression(statement.value, scope)
        elif isinstance(statement, MatchStatement):
            self._resolve_expression(statement.scrutinee, scope)
            for case in statement.cases:
                case_scope = Scope(ScopeKind.BLOCK, scope)
                for binding in case.pattern.bindings:
                    self._declare(
                        case_scope, binding.name, SymbolKind.PATTERN_BINDING, binding.span, binding
                    )
                if isinstance(case.body, Block):
                    self._resolve_statements(case.body.statements, case_scope)
                else:
                    self._resolve_statement(case.body, case_scope)
        elif isinstance(statement, Block):
            self._resolve_block(statement, scope)
        elif isinstance(statement, FunctionDeclaration):
            # Named functions are module-level only in Kaj v0. Valid parsed programs
            # reach function declarations through the module traversal above.
            return
        elif isinstance(
            statement, (RecordDeclaration, EnumDeclaration, BreakStatement, ContinueStatement)
        ):
            return
        else:
            raise TypeError(f"Unsupported statement node: {type(statement).__name__}")

    def _resolve_expression(self, expression: Expression, scope: Scope) -> None:
        if isinstance(expression, Identifier):
            symbol = scope.lookup(expression.name)
            if symbol is None:
                self._diagnostics.append(
                    Diagnostic(
                        code="RESOLVE_UNKNOWN_NAME",
                        message=f"Unknown name '{expression.name}'.",
                        span=expression.span,
                    )
                )
            else:
                self._references.append(ResolvedReference(expression, symbol))
        elif isinstance(expression, UnaryExpression):
            self._resolve_expression(expression.operand, scope)
        elif isinstance(expression, BinaryExpression):
            self._resolve_expression(expression.left, scope)
            self._resolve_expression(expression.right, scope)
        elif isinstance(expression, CallExpression):
            if not (
                isinstance(expression.callee, Identifier)
                and expression.callee.name in {"some", "ok", "err"}
            ):
                self._resolve_expression(expression.callee, scope)
            for argument in expression.arguments:
                self._resolve_expression(argument.value, scope)
        elif isinstance(expression, MemberAccessExpression):
            self._resolve_expression(expression.object, scope)
        elif isinstance(expression, IndexExpression):
            self._resolve_expression(expression.object, scope)
            self._resolve_expression(expression.index, scope)
        elif isinstance(expression, ListLiteral):
            for element in expression.elements:
                self._resolve_expression(element, scope)
        elif isinstance(expression, MapLiteral):
            for entry in expression.entries:
                self._resolve_expression(entry.key, scope)
                self._resolve_expression(entry.value, scope)
        elif isinstance(expression, RecordConstructionExpression):
            for field in expression.fields:
                self._resolve_expression(field.value, scope)
        elif isinstance(expression, EnumConstructionExpression):
            if expression.arguments is not None:
                for enum_argument in expression.arguments:
                    self._resolve_expression(enum_argument.value, scope)
        elif isinstance(
            expression,
            (
                IntegerLiteral,
                DecimalLiteral,
                StringLiteral,
                BooleanLiteral,
                NoneLiteral,
            ),
        ):
            return
        else:
            raise TypeError(f"Unsupported expression node: {type(expression).__name__}")
