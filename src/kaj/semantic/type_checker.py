from __future__ import annotations

from dataclasses import dataclass

from kaj.ast import (
    AssignmentOperator,
    AssignmentStatement,
    BinaryExpression,
    BinaryOperator,
    BindingDeclaration,
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
    MapLiteral,
    MatchCase,
    MatchStatement,
    MemberAccessExpression,
    NamedType,
    NoneLiteral,
    Parameter,
    Program,
    RecordConstructionExpression,
    RecordDeclaration,
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
from kaj.semantic.resolver import ResolutionResult
from kaj.semantic.symbols import Symbol, SymbolKind
from kaj.semantic.types import (
    PRIMITIVE_TYPES_BY_NAME,
    BuiltinFunctionType,
    EnumDefinition,
    EnumPayloadFieldType,
    EnumType,
    EnumVariant,
    FunctionParameterType,
    FunctionType,
    ListType,
    PrimitiveType,
    RecordDefinition,
    RecordField,
    RecordType,
    SemanticType,
    TypeSymbol,
    ValueType,
    format_type,
    is_assignable,
)
from kaj.source import SourceSpan


@dataclass(frozen=True)
class TypedExpression:
    expression: Expression
    type: SemanticType


@dataclass(frozen=True)
class TypedSymbol:
    symbol: Symbol
    type: SemanticType


@dataclass(frozen=True)
class MappedArgument:
    argument: CallArgument
    parameter: FunctionParameterType
    parameter_index: int


@dataclass(frozen=True)
class MappedRecordField:
    initializer: RecordFieldInitializer
    field: RecordField


@dataclass(frozen=True)
class MappedEnumArgument:
    argument: EnumConstructorArgument
    field: EnumPayloadFieldType


@dataclass(frozen=True)
class MappedMatchCase:
    case: MatchCase
    enum_type: EnumType
    variant: EnumVariant


@dataclass(frozen=True)
class TypeCheckResult:
    resolution: ResolutionResult
    expressions: tuple[TypedExpression, ...]
    symbols: tuple[TypedSymbol, ...]
    arguments: tuple[MappedArgument, ...]
    records: tuple[RecordDefinition, ...]
    record_fields: tuple[MappedRecordField, ...]
    enums: tuple[EnumDefinition, ...]
    enum_arguments: tuple[MappedEnumArgument, ...]
    match_cases: tuple[MappedMatchCase, ...]
    diagnostics: tuple[Diagnostic, ...]

    def type_of_expression(self, expression: Expression) -> SemanticType | None:
        for typed in self.expressions:
            if typed.expression is expression:
                return typed.type
        return None

    def type_of_symbol(self, symbol: Symbol) -> SemanticType | None:
        for typed in self.symbols:
            if typed.symbol is symbol:
                return typed.type
        return None

    def parameter_for_argument(self, argument: CallArgument) -> FunctionParameterType | None:
        for mapped in self.arguments:
            if mapped.argument is argument:
                return mapped.parameter
        return None

    def mapping_for_argument(self, argument: CallArgument) -> MappedArgument | None:
        for mapped in self.arguments:
            if mapped.argument is argument:
                return mapped
        return None

    def field_for_initializer(self, initializer: RecordFieldInitializer) -> RecordField | None:
        for mapped in self.record_fields:
            if mapped.initializer is initializer:
                return mapped.field
        return None

    def record_definition(self, record_type: RecordType) -> RecordDefinition | None:
        for definition in self.records:
            if definition.type == record_type:
                return definition
        return None

    def field_for_enum_argument(
        self, argument: EnumConstructorArgument
    ) -> EnumPayloadFieldType | None:
        return next((item.field for item in self.enum_arguments if item.argument is argument), None)

    def mapping_for_match_case(self, case: MatchCase) -> MappedMatchCase | None:
        return next((item for item in self.match_cases if item.case is case), None)

    def enum_definition(self, enum_type: EnumType) -> EnumDefinition | None:
        return next((item for item in self.enums if item.type == enum_type), None)


class TypeChecker:
    def __init__(self, resolution: ResolutionResult) -> None:
        self._resolution = resolution
        self._expression_types: dict[int, TypedExpression] = {}
        self._symbol_types: dict[int, TypedSymbol] = {}
        self._mutable_symbols: dict[int, bool] = {}
        self._function_types: dict[int, FunctionType] = {}
        self._mapped_arguments: list[MappedArgument] = []
        self._diagnostics: list[Diagnostic] = []
        self._current_return_type: ValueType | None = None
        self._record_types_by_name: dict[str, RecordType] = {}
        self._record_types_by_declaration: dict[int, RecordType] = {}
        self._record_definitions: list[RecordDefinition] = []
        self._mapped_record_fields: list[MappedRecordField] = []
        self._enum_types_by_name: dict[str, EnumType] = {}
        self._enum_types_by_declaration: dict[int, EnumType] = {}
        self._enum_definitions: list[EnumDefinition] = []
        self._mapped_enum_arguments: list[MappedEnumArgument] = []
        self._mapped_match_cases: list[MappedMatchCase] = []
        self._exhaustive_matches: set[int] = set()

    def check(self, program: Program) -> TypeCheckResult:
        self._expression_types = {}
        self._symbol_types = {}
        self._mutable_symbols = {}
        self._function_types = {}
        self._mapped_arguments = []
        self._diagnostics = []
        self._current_return_type = None
        self._record_types_by_name = {}
        self._record_types_by_declaration = {}
        self._record_definitions = []
        self._mapped_record_fields = []
        self._enum_types_by_name = {}
        self._enum_types_by_declaration = {}
        self._enum_definitions = []
        self._mapped_enum_arguments = []
        self._mapped_match_cases = []
        self._exhaustive_matches = set()
        self._predeclare_types(program)
        self._define_records(program)
        self._define_enums(program)
        for symbol in self._resolution.symbols:
            if symbol.kind is SymbolKind.BUILTIN_FUNCTION and symbol.name == "print":
                self._record_symbol(symbol, BuiltinFunctionType.PRINT)
        for statement in program.statements:
            if isinstance(statement, FunctionDeclaration):
                self._declare_function_signature(statement)
        for statement in program.statements:
            self._check_statement(statement)
        return TypeCheckResult(
            resolution=self._resolution,
            expressions=tuple(self._expression_types.values()),
            symbols=tuple(self._symbol_types.values()),
            arguments=tuple(self._mapped_arguments),
            records=tuple(self._record_definitions),
            record_fields=tuple(self._mapped_record_fields),
            enums=tuple(self._enum_definitions),
            enum_arguments=tuple(self._mapped_enum_arguments),
            match_cases=tuple(self._mapped_match_cases),
            diagnostics=tuple(self._diagnostics),
        )

    def _record_expression(
        self, expression: Expression, semantic_type: SemanticType
    ) -> SemanticType:
        self._expression_types[id(expression)] = TypedExpression(expression, semantic_type)
        return semantic_type

    def _record_symbol(self, symbol: Symbol, semantic_type: SemanticType) -> None:
        self._symbol_types[symbol.id] = TypedSymbol(symbol, semantic_type)

    def _symbol_type(self, symbol: Symbol | None) -> SemanticType:
        if symbol is None:
            return PrimitiveType.ERROR
        typed = self._symbol_types.get(symbol.id)
        return PrimitiveType.ERROR if typed is None else typed.type

    def _predeclare_types(self, program: Program) -> None:
        next_id = 0
        for statement in program.statements:
            if not isinstance(statement, (RecordDeclaration, EnumDeclaration)):
                continue
            if (
                statement.name in self._record_types_by_name
                or statement.name in self._enum_types_by_name
            ):
                self._diagnose(
                    "TYPE_DUPLICATE_TYPE_NAME",
                    f"Type '{statement.name}' is already declared.",
                    statement.span,
                )
                continue
            symbol = TypeSymbol(next_id, statement.name, statement.span)
            next_id += 1
            if isinstance(statement, RecordDeclaration):
                record_type = RecordType(symbol)
                self._record_types_by_name[statement.name] = record_type
                self._record_types_by_declaration[id(statement)] = record_type
            else:
                enum_type = EnumType(symbol)
                self._enum_types_by_name[statement.name] = enum_type
                self._enum_types_by_declaration[id(statement)] = enum_type

    def _define_records(self, program: Program) -> None:
        for statement in program.statements:
            if not isinstance(statement, RecordDeclaration):
                continue
            record_type = self._record_types_by_declaration.get(id(statement))
            if record_type is None:
                continue
            fields: list[RecordField] = []
            names: set[str] = set()
            for field in statement.fields:
                field_type = self._resolve_annotation(field.type_annotation)
                if field.name in names:
                    self._diagnose(
                        "TYPE_DUPLICATE_FIELD",
                        f"Field '{field.name}' is declared more than once.",
                        field.span,
                    )
                    continue
                names.add(field.name)
                fields.append(RecordField(field.name, field_type, field.span))
            self._record_definitions.append(RecordDefinition(record_type, tuple(fields)))

    def _define_enums(self, program: Program) -> None:
        for statement in program.statements:
            if not isinstance(statement, EnumDeclaration):
                continue
            enum_type = self._enum_types_by_declaration.get(id(statement))
            if enum_type is None:
                continue
            variants: list[EnumVariant] = []
            variant_names: set[str] = set()
            for variant in statement.variants:
                if variant.name in variant_names:
                    self._diagnose(
                        "TYPE_DUPLICATE_VARIANT",
                        f"Variant '{variant.name}' is declared more than once.",
                        variant.span,
                    )
                    continue
                variant_names.add(variant.name)
                payload: list[EnumPayloadFieldType] = []
                field_names: set[str] = set()
                for field in variant.payload:
                    field_type = self._resolve_annotation(field.type_annotation)
                    if field.name in field_names:
                        self._diagnose(
                            "TYPE_DUPLICATE_FIELD",
                            f"Field '{field.name}' is declared more than once.",
                            field.span,
                        )
                        continue
                    field_names.add(field.name)
                    payload.append(EnumPayloadFieldType(field.name, field_type, field.span))
                variants.append(EnumVariant(variant.name, tuple(payload), variant.span))
            self._enum_definitions.append(EnumDefinition(enum_type, tuple(variants)))

    def _declare_function_signature(self, declaration: FunctionDeclaration) -> None:
        parameters = tuple(
            FunctionParameterType(
                name=parameter.name,
                type=self._resolve_annotation(parameter.type_annotation),
                mutable=parameter.mutable,
            )
            for parameter in declaration.parameters
        )
        signature = FunctionType(
            parameters=parameters,
            return_type=self._resolve_annotation(declaration.return_type),
        )
        self._function_types[id(declaration)] = signature
        symbol = self._resolution.symbol_for_declaration(declaration)
        if symbol is not None:
            self._record_symbol(symbol, signature)

    def _diagnose(self, code: str, message: str, span: SourceSpan) -> None:
        self._diagnostics.append(Diagnostic(code=code, message=message, span=span))

    def _resolve_annotation(self, annotation: TypeExpression) -> ValueType:
        if isinstance(annotation, NamedType):
            primitive = PRIMITIVE_TYPES_BY_NAME.get(annotation.name)
            if primitive is not None:
                return primitive
            if annotation.name == "List":
                self._diagnose(
                    "TYPE_INVALID_TYPE_ARGUMENTS",
                    "List requires exactly one type argument.",
                    annotation.span,
                )
                return PrimitiveType.ERROR
            record_type = self._record_types_by_name.get(annotation.name)
            if record_type is not None:
                return record_type
            enum_type = self._enum_types_by_name.get(annotation.name)
            if enum_type is not None:
                return enum_type
        elif isinstance(annotation, GenericType):
            if annotation.base.name == "List":
                if len(annotation.arguments) != 1:
                    self._diagnose(
                        "TYPE_INVALID_TYPE_ARGUMENTS",
                        "List requires exactly one type argument.",
                        annotation.span,
                    )
                    return PrimitiveType.ERROR
                element_type = self._resolve_annotation(annotation.arguments[0])
                return ListType(element_type)
        else:
            raise TypeError(f"Unsupported type expression: {type(annotation).__name__}")
        self._diagnose(
            "TYPE_UNKNOWN_TYPE",
            "Type annotation is not a known primitive type.",
            annotation.span,
        )
        return PrimitiveType.ERROR

    def _check_binding(self, declaration: BindingDeclaration) -> None:
        declared_type = (
            self._resolve_annotation(declaration.annotation)
            if declaration.annotation is not None
            else None
        )
        initializer_type = self._infer(declaration.initializer, declared_type)
        symbol = self._resolution.symbol_for_declaration(declaration)
        static_type = initializer_type if declared_type is None else declared_type
        if declared_type is not None and not is_assignable(initializer_type, declared_type):
            self._diagnose(
                "TYPE_MISMATCH",
                f"Cannot assign {format_type(initializer_type)} to {format_type(declared_type)}.",
                declaration.initializer.span,
            )
        if symbol is not None:
            self._record_symbol(symbol, static_type)
            self._mutable_symbols[symbol.id] = symbol.kind is SymbolKind.VAR_BINDING

    def _check_parameter(self, parameter: Parameter, semantic_type: ValueType) -> None:
        symbol = self._resolution.symbol_for_declaration(parameter)
        if symbol is not None:
            self._record_symbol(symbol, semantic_type)
            self._mutable_symbols[symbol.id] = parameter.mutable

    def _check_statement(self, statement: Statement) -> None:
        if isinstance(statement, BindingDeclaration):
            self._check_binding(statement)
        elif isinstance(statement, AssignmentStatement):
            self._check_assignment(statement)
        elif isinstance(statement, ExpressionStatement):
            self._infer(statement.expression)
        elif isinstance(statement, IfStatement):
            self._check_condition(statement.condition)
            self._check_block(statement.then_branch)
            if isinstance(statement.else_branch, Block):
                self._check_block(statement.else_branch)
            elif statement.else_branch is not None:
                self._check_statement(statement.else_branch)
        elif isinstance(statement, WhileStatement):
            self._check_condition(statement.condition)
            self._check_block(statement.body)
        elif isinstance(statement, ForStatement):
            iterable_type = self._infer(statement.iterable)
            symbol = self._resolution.symbol_for_declaration(statement)
            if symbol is not None:
                if isinstance(iterable_type, ListType):
                    self._record_symbol(symbol, iterable_type.element_type)
                    self._mutable_symbols[symbol.id] = False
                else:
                    self._record_symbol(symbol, PrimitiveType.ERROR)
            if iterable_type is not PrimitiveType.ERROR and not isinstance(iterable_type, ListType):
                self._diagnose(
                    "TYPE_NOT_ITERABLE",
                    f"Type {format_type(iterable_type)} is not iterable.",
                    statement.iterable.span,
                )
            self._check_block(statement.body)
        elif isinstance(statement, FunctionDeclaration):
            signature = self._function_types.get(id(statement))
            if signature is None:
                # Named functions are module-level only in Kaj v0. The parser's
                # general Statement shape can still represent an unsupported nested one.
                return
            for parameter, descriptor in zip(
                statement.parameters, signature.parameters, strict=True
            ):
                self._check_parameter(parameter, descriptor.type)
            previous_return_type = self._current_return_type
            self._current_return_type = signature.return_type
            self._check_block(statement.body)
            self._current_return_type = previous_return_type
            if signature.return_type not in (
                PrimitiveType.NONE,
                PrimitiveType.ERROR,
            ) and not self._block_definitely_returns(statement.body):
                self._diagnose(
                    "TYPE_MISSING_RETURN",
                    f"Function '{statement.name}' may reach its end without returning.",
                    statement.span,
                )
        elif isinstance(statement, (RecordDeclaration, EnumDeclaration)):
            return
        elif isinstance(statement, MatchStatement):
            self._check_match(statement)
        elif isinstance(statement, ReturnStatement):
            self._check_return(statement)
        elif isinstance(statement, Block):
            self._check_block(statement)
        elif isinstance(statement, (BreakStatement, ContinueStatement)):
            return
        else:
            raise TypeError(f"Unsupported statement node: {type(statement).__name__}")

    def _check_block(self, block: Block) -> None:
        for statement in block.statements:
            self._check_statement(statement)

    def _check_condition(self, condition: Expression) -> None:
        condition_type = self._infer(condition)
        if condition_type not in (PrimitiveType.BOOL, PrimitiveType.ERROR):
            self._diagnose(
                "TYPE_CONDITION_NOT_BOOL",
                f"Condition must be Bool, not {format_type(condition_type)}.",
                condition.span,
            )

    def _check_assignment(self, statement: AssignmentStatement) -> None:
        target_type = self._infer(statement.target)
        value_type = self._infer(statement.value, target_type)
        if isinstance(statement.target, IndexExpression) and isinstance(
            self._recorded_expression_type(statement.target.object), ListType
        ):
            self._diagnose(
                "TYPE_MISMATCH",
                "List index assignment is not supported in Kaj v0 Checkpoint 9.",
                statement.target.span,
            )
            return
        if isinstance(statement.target, MemberAccessExpression) and isinstance(
            self._recorded_expression_type(statement.target.object), RecordType
        ):
            self._diagnose(
                "TYPE_FIELD_ASSIGNMENT_NOT_SUPPORTED",
                "Record fields are immutable in Kaj v0.",
                statement.target.span,
            )
            return
        symbol = (
            self._resolution.symbol_for(statement.target)
            if isinstance(statement.target, Identifier)
            else None
        )
        if symbol is not None and self._mutable_symbols.get(symbol.id) is False:
            self._diagnose(
                "ASSIGN_TO_IMMUTABLE",
                f"Cannot assign to immutable name '{symbol.name}'.",
                statement.target.span,
            )

        result_type = value_type
        if statement.operator is not AssignmentOperator.ASSIGN:
            operator = {
                AssignmentOperator.ADD_ASSIGN: BinaryOperator.ADD,
                AssignmentOperator.SUBTRACT_ASSIGN: BinaryOperator.SUBTRACT,
                AssignmentOperator.MULTIPLY_ASSIGN: BinaryOperator.MULTIPLY,
                AssignmentOperator.DIVIDE_ASSIGN: BinaryOperator.DIVIDE,
            }[statement.operator]
            result_type = self._infer_binary_types(
                operator, target_type, value_type, statement.span
            )
        if not is_assignable(result_type, target_type):
            self._diagnose(
                "TYPE_MISMATCH",
                f"Cannot assign {format_type(result_type)} to {format_type(target_type)}.",
                statement.value.span,
            )

    def _recorded_expression_type(self, expression: Expression) -> SemanticType | None:
        typed = self._expression_types.get(id(expression))
        return None if typed is None else typed.type

    def _infer(self, expression: Expression, expected: SemanticType | None = None) -> SemanticType:
        result: SemanticType
        if isinstance(expression, BooleanLiteral):
            result = PrimitiveType.BOOL
        elif isinstance(expression, IntegerLiteral):
            result = PrimitiveType.INT
        elif isinstance(expression, DecimalLiteral):
            result = PrimitiveType.DECIMAL
        elif isinstance(expression, StringLiteral):
            result = PrimitiveType.STRING
        elif isinstance(expression, NoneLiteral):
            result = PrimitiveType.NONE
        elif isinstance(expression, Identifier):
            result = self._symbol_type(self._resolution.symbol_for(expression))
        elif isinstance(expression, UnaryExpression):
            result = self._infer_unary(expression)
        elif isinstance(expression, BinaryExpression):
            left = self._infer(expression.left)
            right = self._infer(expression.right)
            result = self._infer_binary_types(expression.operator, left, right, expression.span)
        elif isinstance(expression, CallExpression):
            result = self._infer_call(expression)
        elif isinstance(expression, RecordConstructionExpression):
            result = self._infer_record_construction(expression)
        elif isinstance(expression, EnumConstructionExpression):
            result = self._infer_enum_construction(expression)
        elif isinstance(expression, MemberAccessExpression):
            object_type = self._infer(expression.object)
            if isinstance(object_type, ListType):
                if expression.member == "count":
                    result = PrimitiveType.INT
                else:
                    self._diagnose(
                        "TYPE_UNKNOWN_MEMBER",
                        f"List has no member '{expression.member}'.",
                        expression.span,
                    )
                    result = PrimitiveType.ERROR
            elif isinstance(object_type, RecordType):
                definition = self._record_definition(object_type)
                field = next(
                    (item for item in definition.fields if item.name == expression.member),
                    None,
                )
                if field is None:
                    self._diagnose(
                        "TYPE_UNKNOWN_FIELD",
                        f"Record '{object_type.symbol.name}' has no field '{expression.member}'.",
                        expression.span,
                    )
                    result = PrimitiveType.ERROR
                else:
                    result = field.type
            else:
                result = PrimitiveType.ERROR
        elif isinstance(expression, IndexExpression):
            object_type = self._infer(expression.object)
            index_type = self._infer(expression.index)
            if index_type not in (PrimitiveType.INT, PrimitiveType.ERROR):
                self._diagnose(
                    "TYPE_MISMATCH",
                    f"List index must be Int, not {format_type(index_type)}.",
                    expression.index.span,
                )
            if isinstance(object_type, ListType):
                result = object_type.element_type
            else:
                result = PrimitiveType.ERROR
        elif isinstance(expression, ListLiteral):
            result = self._infer_list(expression, expected)
        elif isinstance(expression, MapLiteral):
            for entry in expression.entries:
                self._infer(entry.key)
                self._infer(entry.value)
            result = PrimitiveType.ERROR
        else:
            raise TypeError(f"Unsupported expression node: {type(expression).__name__}")
        return self._record_expression(expression, result)

    def _infer_list(self, expression: ListLiteral, expected: SemanticType | None) -> SemanticType:
        if isinstance(expected, ListType):
            for element in expression.elements:
                element_type = self._infer(element, expected.element_type)
                if not is_assignable(element_type, expected.element_type):
                    self._diagnose(
                        "TYPE_MISMATCH",
                        f"Cannot use {format_type(element_type)} in {format_type(expected)}.",
                        element.span,
                    )
            return expected
        if not expression.elements:
            self._diagnose(
                "TYPE_CANNOT_INFER_LIST_ELEMENT",
                "Cannot infer the element type of an empty list.",
                expression.span,
            )
            return PrimitiveType.ERROR
        element_types = [self._infer(element) for element in expression.elements]
        known = [item for item in element_types if item is not PrimitiveType.ERROR]
        if not known:
            return PrimitiveType.ERROR
        common = known[0]
        for item in known[1:]:
            if item == common:
                continue
            if {item, common} == {PrimitiveType.INT, PrimitiveType.DECIMAL}:
                common = PrimitiveType.DECIMAL
                continue
            self._diagnose(
                "TYPE_MISMATCH",
                f"List elements {format_type(common)} and {format_type(item)} have no common type.",
                expression.span,
            )
            return PrimitiveType.ERROR
        if isinstance(common, (PrimitiveType, ListType, RecordType, EnumType)):
            return ListType(common)
        self._diagnose(
            "TYPE_MISMATCH",
            "List elements must have a supported value type.",
            expression.span,
        )
        return PrimitiveType.ERROR

    def _record_definition(self, record_type: RecordType) -> RecordDefinition:
        for definition in self._record_definitions:
            if definition.type == record_type:
                return definition
        raise RuntimeError(f"Missing definition for record {record_type.symbol.name}")

    def _enum_definition(self, enum_type: EnumType) -> EnumDefinition:
        return next(item for item in self._enum_definitions if item.type == enum_type)

    def _infer_enum_construction(self, expression: EnumConstructionExpression) -> SemanticType:
        enum_type = self._enum_types_by_name.get(expression.type_name)
        arguments = () if expression.arguments is None else expression.arguments
        if enum_type is None:
            for argument in arguments:
                self._infer(argument.value)
            self._diagnose(
                "TYPE_UNKNOWN_TYPE", f"Unknown enum type '{expression.type_name}'.", expression.span
            )
            return PrimitiveType.ERROR
        variant = next(
            (
                item
                for item in self._enum_definition(enum_type).variants
                if item.name == expression.variant_name
            ),
            None,
        )
        if variant is None:
            for argument in arguments:
                self._infer(argument.value)
            self._diagnose(
                "TYPE_UNKNOWN_VARIANT",
                f"Enum '{expression.type_name}' has no variant '{expression.variant_name}'.",
                expression.span,
            )
            return PrimitiveType.ERROR
        if expression.arguments is None:
            if variant.payload:
                self._diagnose(
                    "TYPE_INVALID_VARIANT_CONSTRUCTION",
                    f"Variant '{variant.name}' requires payload arguments.",
                    expression.span,
                )
            return enum_type
        if not variant.payload:
            self._diagnose(
                "TYPE_INVALID_VARIANT_CONSTRUCTION",
                f"Unit variant '{variant.name}' does not accept arguments.",
                expression.span,
            )
        fields = {field.name: field for field in variant.payload}
        supplied: set[str] = set()
        for argument in arguments:
            field = fields.get(argument.name)
            if argument.name in supplied:
                self._infer(argument.value, None if field is None else field.type)
                self._diagnose(
                    "TYPE_DUPLICATE_FIELD",
                    f"Field '{argument.name}' is initialized more than once.",
                    argument.span,
                )
                continue
            supplied.add(argument.name)
            if field is None:
                self._infer(argument.value)
                self._diagnose(
                    "TYPE_UNKNOWN_FIELD",
                    f"Variant '{variant.name}' has no field '{argument.name}'.",
                    argument.span,
                )
                continue
            actual = self._infer(argument.value, field.type)
            self._mapped_enum_arguments.append(MappedEnumArgument(argument, field))
            if not is_assignable(actual, field.type):
                self._diagnose(
                    "TYPE_MISMATCH",
                    f"Cannot initialize field '{field.name}' of type {format_type(field.type)} with {format_type(actual)}.",
                    argument.value.span,
                )
        missing = [field.name for field in variant.payload if field.name not in supplied]
        if missing:
            self._diagnose(
                "TYPE_MISSING_FIELD",
                f"Missing required field(s): {', '.join(missing)}.",
                expression.span,
            )
        return enum_type

    def _check_match(self, statement: MatchStatement) -> None:
        scrutinee_type = self._infer(statement.scrutinee)
        if not isinstance(scrutinee_type, EnumType):
            self._diagnose(
                "TYPE_MATCH_REQUIRES_ENUM",
                "Match scrutinee must have an enum type.",
                statement.scrutinee.span,
            )
            for case in statement.cases:
                self._check_statement(case.body)
            return
        definition = self._enum_definition(scrutinee_type)
        covered: set[str] = set()
        for case in statement.cases:
            variant = next(
                (item for item in definition.variants if item.name == case.pattern.variant_name),
                None,
            )
            if variant is None:
                self._diagnose(
                    "TYPE_UNKNOWN_VARIANT",
                    f"Enum '{scrutinee_type.symbol.name}' has no variant '{case.pattern.variant_name}'.",
                    case.pattern.span,
                )
            else:
                if variant.name in covered:
                    self._diagnose(
                        "TYPE_DUPLICATE_MATCH_CASE",
                        f"Variant '{variant.name}' is matched more than once.",
                        case.pattern.span,
                    )
                else:
                    covered.add(variant.name)
                self._mapped_match_cases.append(MappedMatchCase(case, scrutinee_type, variant))
                if len(case.pattern.bindings) != len(variant.payload):
                    self._diagnose(
                        "TYPE_PATTERN_ARITY_MISMATCH",
                        f"Variant '{variant.name}' expects {len(variant.payload)} binding(s), got {len(case.pattern.bindings)}.",
                        case.pattern.span,
                    )
                for binding, field in zip(case.pattern.bindings, variant.payload):
                    symbol = self._resolution.symbol_for_declaration(binding)
                    if symbol is not None:
                        self._record_symbol(symbol, field.type)
                        self._mutable_symbols[symbol.id] = False
            self._check_statement(case.body)
        missing = [variant.name for variant in definition.variants if variant.name not in covered]
        if missing:
            self._diagnose(
                "NON_EXHAUSTIVE_MATCH",
                f"Match is missing variant(s): {', '.join(missing)}.",
                statement.span,
            )
        else:
            self._exhaustive_matches.add(id(statement))

    def _infer_record_construction(self, expression: RecordConstructionExpression) -> SemanticType:
        record_type = self._record_types_by_name.get(expression.type_name)
        if record_type is None:
            for initializer in expression.fields:
                self._infer(initializer.value)
            self._diagnose(
                "TYPE_UNKNOWN_TYPE",
                f"Unknown record type '{expression.type_name}'.",
                expression.span,
            )
            return PrimitiveType.ERROR
        definition = self._record_definition(record_type)
        fields_by_name = {field.name: field for field in definition.fields}
        supplied: set[str] = set()
        for initializer in expression.fields:
            field = fields_by_name.get(initializer.name)
            if initializer.name in supplied:
                self._infer(initializer.value, None if field is None else field.type)
                self._diagnose(
                    "TYPE_DUPLICATE_FIELD",
                    f"Field '{initializer.name}' is initialized more than once.",
                    initializer.span,
                )
                continue
            supplied.add(initializer.name)
            if field is None:
                self._infer(initializer.value)
                self._diagnose(
                    "TYPE_UNKNOWN_FIELD",
                    f"Record '{expression.type_name}' has no field '{initializer.name}'.",
                    initializer.span,
                )
                continue
            value_type = self._infer(initializer.value, field.type)
            self._mapped_record_fields.append(MappedRecordField(initializer, field))
            if not is_assignable(value_type, field.type):
                self._diagnose(
                    "TYPE_MISMATCH",
                    f"Cannot initialize field '{field.name}' of type "
                    f"{format_type(field.type)} with {format_type(value_type)}.",
                    initializer.value.span,
                )
        missing = [field.name for field in definition.fields if field.name not in supplied]
        if missing:
            self._diagnose(
                "TYPE_MISSING_FIELD",
                f"Missing required field(s): {', '.join(missing)}.",
                expression.span,
            )
        return record_type

    def _infer_unary(self, expression: UnaryExpression) -> PrimitiveType:
        operand = self._infer(expression.operand)
        if operand is PrimitiveType.ERROR:
            return PrimitiveType.ERROR
        if expression.operator in (UnaryOperator.POSITIVE, UnaryOperator.NEGATE):
            if operand in (PrimitiveType.INT, PrimitiveType.DECIMAL):
                return operand
        elif expression.operator is UnaryOperator.NOT and operand is PrimitiveType.BOOL:
            return PrimitiveType.BOOL
        self._diagnose(
            "TYPE_INVALID_OPERATOR",
            f"Operator {expression.operator.name} is invalid for {format_type(operand)}.",
            expression.span,
        )
        return PrimitiveType.ERROR

    def _infer_binary_types(
        self,
        operator: BinaryOperator,
        left: SemanticType,
        right: SemanticType,
        span: SourceSpan,
    ) -> PrimitiveType:
        if PrimitiveType.ERROR in (left, right):
            return PrimitiveType.ERROR
        numeric = (PrimitiveType.INT, PrimitiveType.DECIMAL)
        both_numeric = left in numeric and right in numeric

        if operator in (BinaryOperator.AND, BinaryOperator.OR):
            if left is right is PrimitiveType.BOOL:
                return PrimitiveType.BOOL
        elif operator in (BinaryOperator.EQUAL, BinaryOperator.NOT_EQUAL):
            if (isinstance(left, PrimitiveType) and left is right) or both_numeric:
                return PrimitiveType.BOOL
        elif operator in (
            BinaryOperator.LESS,
            BinaryOperator.LESS_EQUAL,
            BinaryOperator.GREATER,
            BinaryOperator.GREATER_EQUAL,
        ):
            if both_numeric:
                return PrimitiveType.BOOL
        elif operator is BinaryOperator.ADD and left is right is PrimitiveType.STRING:
            return PrimitiveType.STRING
        elif operator in (
            BinaryOperator.ADD,
            BinaryOperator.SUBTRACT,
            BinaryOperator.MULTIPLY,
            BinaryOperator.MODULO,
            BinaryOperator.POWER,
        ):
            if both_numeric:
                if left is right is PrimitiveType.INT:
                    return PrimitiveType.INT
                return PrimitiveType.DECIMAL
        elif operator is BinaryOperator.DIVIDE and both_numeric:
            return PrimitiveType.DECIMAL

        self._diagnose(
            "TYPE_MISMATCH",
            f"Operator {operator.name} cannot combine {format_type(left)} and {format_type(right)}.",
            span,
        )
        return PrimitiveType.ERROR

    def _infer_call(self, expression: CallExpression) -> SemanticType:
        callee_type = self._infer(expression.callee)
        if callee_type is PrimitiveType.ERROR:
            for argument in expression.arguments:
                self._infer(argument.value)
            return PrimitiveType.ERROR
        if callee_type is BuiltinFunctionType.PRINT:
            argument_types = [self._infer(argument.value) for argument in expression.arguments]
            return self._infer_print_call(expression, argument_types)
        if not isinstance(callee_type, FunctionType):
            for argument in expression.arguments:
                self._infer(argument.value)
            self._diagnose(
                "TYPE_NOT_CALLABLE",
                f"Value of type {format_type(callee_type)} is not callable.",
                expression.callee.span,
            )
            return PrimitiveType.ERROR

        assigned: set[int] = set()
        next_positional = 0
        for argument in expression.arguments:
            parameter_index: int | None
            if argument.name is None:
                parameter_index = next_positional
                next_positional += 1
                if parameter_index >= len(callee_type.parameters):
                    self._diagnose(
                        "TYPE_TOO_MANY_ARGUMENTS",
                        "Call has too many positional arguments.",
                        argument.span,
                    )
                    self._infer(argument.value)
                    continue
            else:
                parameter_index = next(
                    (
                        index
                        for index, parameter in enumerate(callee_type.parameters)
                        if parameter.name == argument.name
                    ),
                    None,
                )
                if parameter_index is None:
                    self._diagnose(
                        "TYPE_UNKNOWN_NAMED_ARGUMENT",
                        f"Unknown named argument '{argument.name}'.",
                        argument.span,
                    )
                    self._infer(argument.value)
                    continue
            parameter = callee_type.parameters[parameter_index]
            argument_type = self._infer(argument.value, parameter.type)
            if parameter_index in assigned:
                self._diagnose(
                    "TYPE_DUPLICATE_ARGUMENT",
                    f"Parameter '{callee_type.parameters[parameter_index].name}' is provided twice.",
                    argument.span,
                )
                continue
            assigned.add(parameter_index)
            self._mapped_arguments.append(MappedArgument(argument, parameter, parameter_index))
            if not is_assignable(argument_type, parameter.type):
                self._diagnose(
                    "TYPE_MISMATCH",
                    f"Cannot pass {format_type(argument_type)} to parameter "
                    f"'{parameter.name}' of type {format_type(parameter.type)}.",
                    argument.value.span,
                )

        missing = [
            parameter.name
            for index, parameter in enumerate(callee_type.parameters)
            if index not in assigned
        ]
        if missing:
            self._diagnose(
                "TYPE_MISSING_ARGUMENT",
                f"Missing required argument(s): {', '.join(missing)}.",
                expression.span,
            )
        return callee_type.return_type

    def _infer_print_call(
        self, expression: CallExpression, argument_types: list[SemanticType]
    ) -> PrimitiveType:
        if any(argument.name is not None for argument in expression.arguments):
            for argument in expression.arguments:
                if argument.name is not None:
                    self._diagnose(
                        "TYPE_UNKNOWN_NAMED_ARGUMENT",
                        "Builtin 'print' does not accept named arguments.",
                        argument.span,
                    )
        if len(expression.arguments) == 0:
            self._diagnose(
                "TYPE_MISSING_ARGUMENT",
                "Builtin 'print' requires one argument.",
                expression.span,
            )
        elif len(expression.arguments) > 1:
            self._diagnose(
                "TYPE_TOO_MANY_ARGUMENTS",
                "Builtin 'print' accepts exactly one argument.",
                expression.span,
            )
        if argument_types:
            printable = {
                PrimitiveType.BOOL,
                PrimitiveType.INT,
                PrimitiveType.DECIMAL,
                PrimitiveType.STRING,
                PrimitiveType.BYTES,
                PrimitiveType.NONE,
                PrimitiveType.ERROR,
            }
            if argument_types[0] not in printable:
                self._diagnose(
                    "TYPE_MISMATCH",
                    f"Builtin 'print' cannot print {format_type(argument_types[0])}.",
                    expression.arguments[0].value.span,
                )
        return PrimitiveType.NONE

    def _check_return(self, statement: ReturnStatement) -> None:
        if self._current_return_type is None:
            if statement.value is not None:
                self._infer(statement.value)
            self._diagnose(
                "TYPE_RETURN_OUTSIDE_FUNCTION",
                "Return statement is outside a function.",
                statement.span,
            )
            return
        actual = (
            PrimitiveType.NONE
            if statement.value is None
            else self._infer(statement.value, self._current_return_type)
        )
        if not is_assignable(actual, self._current_return_type):
            span = statement.span if statement.value is None else statement.value.span
            self._diagnose(
                "TYPE_MISMATCH",
                f"Cannot return {format_type(actual)} from a function returning "
                f"{format_type(self._current_return_type)}.",
                span,
            )

    def _block_definitely_returns(self, block: Block) -> bool:
        return any(self._statement_definitely_returns(statement) for statement in block.statements)

    def _statement_definitely_returns(self, statement: Statement) -> bool:
        if isinstance(statement, ReturnStatement):
            return True
        if isinstance(statement, Block):
            return self._block_definitely_returns(statement)
        if isinstance(statement, IfStatement):
            if statement.else_branch is None:
                return False
            then_returns = self._block_definitely_returns(statement.then_branch)
            else_returns = (
                self._block_definitely_returns(statement.else_branch)
                if isinstance(statement.else_branch, Block)
                else self._statement_definitely_returns(statement.else_branch)
            )
            return then_returns and else_returns
        if isinstance(statement, MatchStatement):
            return (
                id(statement) in self._exhaustive_matches
                and bool(statement.cases)
                and all(self._statement_definitely_returns(case.body) for case in statement.cases)
            )
        return False
