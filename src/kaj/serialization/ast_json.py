from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from decimal import Decimal, InvalidOperation
from typing import cast

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
    CapabilityOperationSignature,
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
    MapEntry,
    MapLiteral,
    MatchCase,
    MatchStatement,
    MemberAccessExpression,
    NamedType,
    NewtypeDeclaration,
    Node,
    NoneLiteral,
    Parameter,
    PatternBinding,
    PlanRegion,
    Program,
    RecordConstructionExpression,
    RecordDeclaration,
    RecordFieldDeclaration,
    RecordFieldInitializer,
    RequireClause,
    ReturnStatement,
    StartTaskExpression,
    Statement,
    StepStatement,
    StringLiteral,
    SuccessClause,
    SuccessParameter,
    TaskDeclaration,
    TypeExpression,
    UnaryExpression,
    UnaryOperator,
    UseCapabilityDeclaration,
    WhileStatement,
)
from kaj.source import SourceLocation, SourceSpan

type JSONValue = None | bool | int | float | str | list[JSONValue] | dict[str, JSONValue]
type JSONPath = tuple[str | int, ...]

ASTJSON_INVALID_JSON = "ASTJSON_INVALID_JSON"
ASTJSON_INVALID_DOCUMENT = "ASTJSON_INVALID_DOCUMENT"
ASTJSON_UNSUPPORTED_VERSION = "ASTJSON_UNSUPPORTED_VERSION"
ASTJSON_UNKNOWN_NODE_KIND = "ASTJSON_UNKNOWN_NODE_KIND"
ASTJSON_MISSING_FIELD = "ASTJSON_MISSING_FIELD"
ASTJSON_INVALID_FIELD = "ASTJSON_INVALID_FIELD"
ASTJSON_INVALID_ENUM_VALUE = "ASTJSON_INVALID_ENUM_VALUE"

_INTEGER_PATTERN = re.compile(r"(?:0|[1-9][0-9]*)\Z")
_DECIMAL_PATTERN = re.compile(r"[0-9]+\.[0-9]+\Z")

_UNARY_TO_JSON = {
    UnaryOperator.POSITIVE: "positive",
    UnaryOperator.NEGATE: "negate",
    UnaryOperator.NOT: "not",
}
_UNARY_FROM_JSON = {value: key for key, value in _UNARY_TO_JSON.items()}

_BINARY_TO_JSON = {
    BinaryOperator.ADD: "add",
    BinaryOperator.SUBTRACT: "subtract",
    BinaryOperator.MULTIPLY: "multiply",
    BinaryOperator.DIVIDE: "divide",
    BinaryOperator.MODULO: "modulo",
    BinaryOperator.POWER: "power",
    BinaryOperator.EQUAL: "equal",
    BinaryOperator.NOT_EQUAL: "not_equal",
    BinaryOperator.LESS: "less",
    BinaryOperator.LESS_EQUAL: "less_equal",
    BinaryOperator.GREATER: "greater",
    BinaryOperator.GREATER_EQUAL: "greater_equal",
    BinaryOperator.AND: "and",
    BinaryOperator.OR: "or",
}
_BINARY_FROM_JSON = {value: key for key, value in _BINARY_TO_JSON.items()}

_ASSIGNMENT_TO_JSON = {
    AssignmentOperator.ASSIGN: "assign",
    AssignmentOperator.ADD_ASSIGN: "add_assign",
    AssignmentOperator.SUBTRACT_ASSIGN: "subtract_assign",
    AssignmentOperator.MULTIPLY_ASSIGN: "multiply_assign",
    AssignmentOperator.DIVIDE_ASSIGN: "divide_assign",
}
_ASSIGNMENT_FROM_JSON = {value: key for key, value in _ASSIGNMENT_TO_JSON.items()}

_BINDING_TO_JSON = {BindingKind.LET: "let", BindingKind.VAR: "var"}
_BINDING_FROM_JSON = {value: key for key, value in _BINDING_TO_JSON.items()}


class ASTJSONError(ValueError):
    def __init__(self, code: str, message: str, path: JSONPath = ()) -> None:
        self.code = code
        self.message = message
        self.path = path
        super().__init__(f"{code} at {self.path_string}: {message}")

    @property
    def path_string(self) -> str:
        result = "$"
        for component in self.path:
            if isinstance(component, int):
                result += f"[{component}]"
            else:
                result += f".{component}"
        return result


def ast_to_json_value(program: Program) -> dict[str, JSONValue]:
    return {
        "format": "kaj-ast",
        "version": 1,
        "program": _encode_node(program),
    }


def ast_from_json_value(value: object) -> Program:
    document = _expect_object(value, ())
    _check_fields(document, {"format", "version", "program"}, ())

    format_value = _required(document, "format", ())
    if format_value != "kaj-ast":
        raise ASTJSONError(
            ASTJSON_INVALID_DOCUMENT,
            "Document format must be 'kaj-ast'.",
            ("format",),
        )

    version = _required(document, "version", ())
    if type(version) is not int:
        raise ASTJSONError(ASTJSON_INVALID_FIELD, "Version must be an integer.", ("version",))
    if version != 1:
        raise ASTJSONError(
            ASTJSON_UNSUPPORTED_VERSION,
            f"Unsupported AST JSON version: {version}.",
            ("version",),
        )

    program = _decode_node(_required(document, "program", ()), ("program",))
    if not isinstance(program, Program):
        raise ASTJSONError(
            ASTJSON_INVALID_FIELD,
            "The document program field must contain a program node.",
            ("program",),
        )
    return program


def ast_to_json(program: Program, *, indent: int | None = None) -> str:
    return json.dumps(
        ast_to_json_value(program),
        ensure_ascii=False,
        indent=indent,
        separators=(",", ":") if indent is None else None,
    )


def ast_from_json(text: str) -> Program:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise ASTJSONError(
            ASTJSON_INVALID_JSON,
            f"Invalid JSON at line {error.lineno}, column {error.colno}.",
        ) from None
    return ast_from_json_value(value)


def _encode_node(node: Node) -> dict[str, JSONValue]:
    span = _encode_span(node.span)

    if isinstance(node, Program):
        return _node(
            "program", {"statements": [_encode_node(item) for item in node.statements]}, span
        )
    if isinstance(node, IntegerLiteral):
        value = str(node.value)
        if _INTEGER_PATTERN.fullmatch(value) is None:
            raise ASTJSONError(
                ASTJSON_INVALID_FIELD, "Integer literals must be unsigned base-10 values."
            )
        return _node("integer_literal", {"value": value}, span)
    if isinstance(node, DecimalLiteral):
        value = str(node.value)
        if _DECIMAL_PATTERN.fullmatch(value) is None:
            raise ASTJSONError(
                ASTJSON_INVALID_FIELD, "Decimal literals must use DIGIT+'.'DIGIT+ form."
            )
        return _node("decimal_literal", {"value": value}, span)
    if isinstance(node, StringLiteral):
        return _node("string_literal", {"value": node.value}, span)
    if isinstance(node, InterpolatedString):
        return _node(
            "interpolated_string",
            {
                "parts": [
                    {"kind": "text", "value": part}
                    if isinstance(part, str)
                    else {"kind": "expression", "value": _encode_node(part)}
                    for part in node.parts
                ]
            },
            span,
        )
    if isinstance(node, BooleanLiteral):
        return _node("boolean_literal", {"value": node.value}, span)
    if isinstance(node, NoneLiteral):
        return _node("none_literal", {}, span)
    if isinstance(node, Identifier):
        return _node("identifier", {"name": node.name}, span)
    if isinstance(node, UnaryExpression):
        return _node(
            "unary_expression",
            {"operator": _UNARY_TO_JSON[node.operator], "operand": _encode_node(node.operand)},
            span,
        )
    if isinstance(node, BinaryExpression):
        return _node(
            "binary_expression",
            {
                "operator": _BINARY_TO_JSON[node.operator],
                "left": _encode_node(node.left),
                "right": _encode_node(node.right),
            },
            span,
        )
    if isinstance(node, CallArgument):
        return _node(
            "call_argument",
            {"name": node.name, "value": _encode_node(node.value)},
            span,
        )
    if isinstance(node, CallExpression):
        return _node(
            "call_expression",
            {
                "callee": _encode_node(node.callee),
                "arguments": [_encode_node(argument) for argument in node.arguments],
            },
            span,
        )
    if isinstance(node, HumanInteractionExpression):
        return _node(
            "human_interaction_expression",
            {
                "interaction_kind": node.kind,
                "type_argument": (
                    None if node.type_argument is None else _encode_node(node.type_argument)
                ),
                "arguments": [_encode_node(item) for item in node.arguments],
            },
            span,
        )
    if isinstance(node, StartTaskExpression):
        return _node(
            "start_task_expression",
            {
                "task_name": node.task_name,
                "arguments": [_encode_node(argument) for argument in node.arguments],
            },
            span,
        )
    if isinstance(node, AwaitTaskExpression):
        return _node("await_task_expression", {"operand": _encode_node(node.operand)}, span)
    if isinstance(node, MemberAccessExpression):
        return _node(
            "member_access_expression",
            {"object": _encode_node(node.object), "member": node.member},
            span,
        )
    if isinstance(node, IndexExpression):
        return _node(
            "index_expression",
            {"object": _encode_node(node.object), "index": _encode_node(node.index)},
            span,
        )
    if isinstance(node, ListLiteral):
        return _node(
            "list_literal",
            {"elements": [_encode_node(element) for element in node.elements]},
            span,
        )
    if isinstance(node, MapEntry):
        return _node(
            "map_entry",
            {"key": _encode_node(node.key), "value": _encode_node(node.value)},
            span,
        )
    if isinstance(node, MapLiteral):
        return _node(
            "map_literal",
            {"entries": [_encode_node(entry) for entry in node.entries]},
            span,
        )
    if isinstance(node, RecordFieldInitializer):
        return _node(
            "record_field_initializer",
            {"name": node.name, "value": _encode_node(node.value)},
            span,
        )
    if isinstance(node, RecordConstructionExpression):
        return _node(
            "record_construction_expression",
            {
                "type_name": node.type_name,
                "fields": [_encode_node(field) for field in node.fields],
            },
            span,
        )
    if isinstance(node, EnumConstructorArgument):
        return _node(
            "enum_constructor_argument",
            {"name": node.name, "value": _encode_node(node.value)},
            span,
        )
    if isinstance(node, EnumConstructionExpression):
        return _node(
            "enum_construction_expression",
            {
                "type_name": node.type_name,
                "variant_name": node.variant_name,
                "arguments": None
                if node.arguments is None
                else [_encode_node(item) for item in node.arguments],
            },
            span,
        )
    if isinstance(node, NamedType):
        return _node("named_type", {"name": node.name}, span)
    if isinstance(node, GenericType):
        return _node(
            "generic_type",
            {
                "base": _encode_node(node.base),
                "arguments": [_encode_node(argument) for argument in node.arguments],
            },
            span,
        )
    if isinstance(node, Block):
        return _node(
            "block", {"statements": [_encode_node(item) for item in node.statements]}, span
        )
    if isinstance(node, BindingDeclaration):
        return _node(
            "binding_declaration",
            {
                "binding_kind": _BINDING_TO_JSON[node.kind],
                "name": node.name,
                "annotation": None if node.annotation is None else _encode_node(node.annotation),
                "initializer": _encode_node(node.initializer),
            },
            span,
        )
    if isinstance(node, AssignmentStatement):
        return _node(
            "assignment_statement",
            {
                "operator": _ASSIGNMENT_TO_JSON[node.operator],
                "target": _encode_node(node.target),
                "value": _encode_node(node.value),
            },
            span,
        )
    if isinstance(node, ExpressionStatement):
        return _node("expression_statement", {"expression": _encode_node(node.expression)}, span)
    if isinstance(node, IfStatement):
        return _node(
            "if_statement",
            {
                "condition": _encode_node(node.condition),
                "then_branch": _encode_node(node.then_branch),
                "else_branch": None if node.else_branch is None else _encode_node(node.else_branch),
            },
            span,
        )
    if isinstance(node, WhileStatement):
        return _node(
            "while_statement",
            {"condition": _encode_node(node.condition), "body": _encode_node(node.body)},
            span,
        )
    if isinstance(node, ForStatement):
        return _node(
            "for_statement",
            {
                "name": node.name,
                "iterable": _encode_node(node.iterable),
                "body": _encode_node(node.body),
            },
            span,
        )
    if isinstance(node, BreakStatement):
        return _node("break_statement", {}, span)
    if isinstance(node, ContinueStatement):
        return _node("continue_statement", {}, span)
    if isinstance(node, StepStatement):
        return _node(
            "step_statement",
            {"name": node.name, "body": _encode_node(node.body)},
            span,
        )
    if isinstance(node, UseCapabilityDeclaration):
        payload: dict[str, object] = {
            "capability_name": node.capability_name,
            "alias": node.alias,
        }
        if node.capability_module:
            payload["capability_module"] = list(node.capability_module)
        return _node(
            "use_capability_declaration",
            payload,
            span,
        )
    if isinstance(node, PlanRegion):
        return _node("plan_region", {"body": _encode_node(node.body)}, span)
    if isinstance(node, GoalClause):
        return _node("goal_clause", {"expression": _encode_node(node.expression)}, span)
    if isinstance(node, RequireClause):
        return _node("require_clause", {"condition": _encode_node(node.condition)}, span)
    if isinstance(node, InvariantClause):
        return _node("invariant_clause", {"condition": _encode_node(node.condition)}, span)
    if isinstance(node, SuccessParameter):
        return _node(
            "success_parameter",
            {"name": node.name, "type_annotation": _encode_node(node.type_annotation)},
            span,
        )
    if isinstance(node, SuccessClause):
        return _node(
            "success_clause",
            {
                "parameter": (None if node.parameter is None else _encode_node(node.parameter)),
                "condition": _encode_node(node.condition),
            },
            span,
        )
    if isinstance(node, ReturnStatement):
        return _node(
            "return_statement",
            {"value": None if node.value is None else _encode_node(node.value)},
            span,
        )
    if isinstance(node, PatternBinding):
        return _node("pattern_binding", {"name": node.name}, span)
    if isinstance(node, EnumPattern):
        return _node(
            "enum_pattern",
            {
                "variant_name": node.variant_name,
                "bindings": [_encode_node(item) for item in node.bindings],
            },
            span,
        )
    if isinstance(node, MatchCase):
        return _node(
            "match_case",
            {"pattern": _encode_node(node.pattern), "body": _encode_node(node.body)},
            span,
        )
    if isinstance(node, MatchStatement):
        return _node(
            "match_statement",
            {
                "scrutinee": _encode_node(node.scrutinee),
                "cases": [_encode_node(item) for item in node.cases],
            },
            span,
        )
    if isinstance(node, Parameter):
        return _node(
            "parameter",
            {
                "name": node.name,
                "type_annotation": _encode_node(node.type_annotation),
                "mutable": node.mutable,
            },
            span,
        )
    if isinstance(node, FunctionDeclaration):
        return _node(
            "function_declaration",
            {
                "name": node.name,
                "parameters": [_encode_node(parameter) for parameter in node.parameters],
                "return_type": _encode_node(node.return_type),
                "body": _encode_node(node.body),
            },
            span,
        )
    if isinstance(node, TaskDeclaration):
        return _node(
            "task_declaration",
            {
                "name": node.name,
                "parameters": [_encode_node(parameter) for parameter in node.parameters],
                "return_type": _encode_node(node.return_type),
                "body": _encode_node(node.body),
            },
            span,
        )
    if isinstance(node, CapabilityOperationSignature):
        return _node(
            "capability_operation_signature",
            {
                "name": node.name,
                "parameters": [_encode_node(parameter) for parameter in node.parameters],
                "return_type": _encode_node(node.return_type),
            },
            span,
        )
    if isinstance(node, CapabilityDeclaration):
        return _node(
            "capability_declaration",
            {
                "name": node.name,
                "operations": [_encode_node(operation) for operation in node.operations],
            },
            span,
        )
    if isinstance(node, RecordFieldDeclaration):
        return _node(
            "record_field_declaration",
            {"name": node.name, "type_annotation": _encode_node(node.type_annotation)},
            span,
        )
    if isinstance(node, RecordDeclaration):
        return _node(
            "record_declaration",
            {"name": node.name, "fields": [_encode_node(field) for field in node.fields]},
            span,
        )
    if isinstance(node, EnumPayloadField):
        return _node(
            "enum_payload_field",
            {"name": node.name, "type_annotation": _encode_node(node.type_annotation)},
            span,
        )
    if isinstance(node, EnumVariantDeclaration):
        return _node(
            "enum_variant_declaration",
            {"name": node.name, "payload": [_encode_node(item) for item in node.payload]},
            span,
        )
    if isinstance(node, EnumDeclaration):
        return _node(
            "enum_declaration",
            {"name": node.name, "variants": [_encode_node(item) for item in node.variants]},
            span,
        )
    if isinstance(node, NewtypeDeclaration):
        return _node(
            "newtype_declaration",
            {"name": node.name, "underlying_type": _encode_node(node.underlying_type)},
            span,
        )
    if isinstance(node, ImportDeclaration):
        return _node("import_declaration", {"path": list(node.path)}, span)
    raise ASTJSONError(
        ASTJSON_UNKNOWN_NODE_KIND, f"Unsupported internal AST node: {type(node).__name__}."
    )


def _node(
    kind: str, fields: dict[str, JSONValue], span: dict[str, JSONValue]
) -> dict[str, JSONValue]:
    return {"kind": kind, **fields, "span": span}


def _encode_span(span: SourceSpan) -> dict[str, JSONValue]:
    if span.end.offset < span.start.offset:
        raise ASTJSONError(ASTJSON_INVALID_FIELD, "Span end offset precedes start offset.")
    return {"start": _encode_location(span.start), "end": _encode_location(span.end)}


def _encode_location(location: SourceLocation) -> dict[str, JSONValue]:
    if (
        type(location.offset) is not int
        or type(location.line) is not int
        or type(location.column) is not int
        or location.offset < 0
        or location.line < 1
        or location.column < 1
    ):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, "Source location values are out of range.")
    return {"offset": location.offset, "line": location.line, "column": location.column}


def _decode_node(value: object, path: JSONPath) -> Node:
    obj = _expect_object(value, path)
    kind_value = _required(obj, "kind", path)
    if not isinstance(kind_value, str):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, "Node kind must be a string.", path + ("kind",))
    decoder = _NODE_DECODERS.get(kind_value)
    if decoder is None:
        raise ASTJSONError(
            ASTJSON_UNKNOWN_NODE_KIND, f"Unknown node kind: {kind_value!r}.", path + ("kind",)
        )
    return decoder(obj, path)


def _decode_program(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"statements"}, path)
    statements = _node_list(obj, "statements", path, _expect_statement)
    return Program(span=_span_field(obj, path), statements=tuple(statements))


def _decode_integer(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"value"}, path)
    text = _string_field(obj, "value", path)
    if _INTEGER_PATTERN.fullmatch(text) is None:
        raise ASTJSONError(
            ASTJSON_INVALID_FIELD, "Invalid integer literal string.", path + ("value",)
        )
    return IntegerLiteral(span=_span_field(obj, path), value=int(text))


def _decode_decimal(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"value"}, path)
    text = _string_field(obj, "value", path)
    if _DECIMAL_PATTERN.fullmatch(text) is None:
        raise ASTJSONError(
            ASTJSON_INVALID_FIELD, "Invalid decimal literal string.", path + ("value",)
        )
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise ASTJSONError(
            ASTJSON_INVALID_FIELD, "Invalid decimal literal string.", path + ("value",)
        ) from None
    return DecimalLiteral(span=_span_field(obj, path), value=value)


def _decode_string(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"value"}, path)
    return StringLiteral(span=_span_field(obj, path), value=_string_field(obj, "value", path))


def _decode_interpolated_string(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"parts"}, path)
    raw_parts_value = _required(obj, "parts", path)
    if not isinstance(raw_parts_value, list):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, "parts must be an array.", path + ("parts",))
    raw_parts = raw_parts_value
    parts: list[str | Expression] = []
    for index, raw in enumerate(raw_parts):
        part_path = path + ("parts", index)
        part = _expect_object(raw, part_path)
        _check_fields(part, {"kind", "value"}, part_path)
        kind = _string_field(part, "kind", part_path)
        if kind == "text":
            parts.append(_string_field(part, "value", part_path))
        elif kind == "expression":
            decoded = _decode_node(_required(part, "value", part_path), part_path + ("value",))
            if not isinstance(decoded, Expression):
                raise ASTJSONError(
                    ASTJSON_INVALID_FIELD, "Interpolation value must be an expression.", part_path
                )
            parts.append(decoded)
        else:
            raise ASTJSONError(
                ASTJSON_INVALID_FIELD,
                "Interpolation part kind must be text or expression.",
                part_path + ("kind",),
            )
    return InterpolatedString(span=_span_field(obj, path), parts=tuple(parts))


def _decode_boolean(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"value"}, path)
    value = _required(obj, "value", path)
    if type(value) is not bool:
        raise ASTJSONError(
            ASTJSON_INVALID_FIELD, "Boolean literal value must be a boolean.", path + ("value",)
        )
    return BooleanLiteral(span=_span_field(obj, path), value=value)


def _decode_none(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, set(), path)
    return NoneLiteral(span=_span_field(obj, path))


def _decode_identifier(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name"}, path)
    return Identifier(span=_span_field(obj, path), name=_string_field(obj, "name", path))


def _decode_unary(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"operator", "operand"}, path)
    operator = _enum_field(obj, "operator", path, _UNARY_FROM_JSON)
    operand = _expression_field(obj, "operand", path)
    return UnaryExpression(span=_span_field(obj, path), operator=operator, operand=operand)


def _decode_binary(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"operator", "left", "right"}, path)
    operator = _enum_field(obj, "operator", path, _BINARY_FROM_JSON)
    return BinaryExpression(
        span=_span_field(obj, path),
        operator=operator,
        left=_expression_field(obj, "left", path),
        right=_expression_field(obj, "right", path),
    )


def _decode_call_argument(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name", "value"}, path)
    name = _required(obj, "name", path)
    if name is not None and not isinstance(name, str):
        raise ASTJSONError(
            ASTJSON_INVALID_FIELD, "Call argument name must be a string or null.", path + ("name",)
        )
    return CallArgument(
        span=_span_field(obj, path),
        name=name,
        value=_expression_field(obj, "value", path),
    )


def _decode_call(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"callee", "arguments"}, path)
    arguments = _node_list(obj, "arguments", path, _expect_call_argument)
    return CallExpression(
        span=_span_field(obj, path),
        callee=_expression_field(obj, "callee", path),
        arguments=tuple(arguments),
    )


def _decode_human_interaction(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"interaction_kind", "type_argument", "arguments"}, path)
    kind = _string_field(obj, "interaction_kind", path)
    if kind not in {"ask", "choose", "confirm", "inform", "handoff"}:
        raise ASTJSONError(
            ASTJSON_INVALID_FIELD,
            "Unknown human interaction kind.",
            path + ("interaction_kind",),
        )
    type_data = _required(obj, "type_argument", path)
    type_argument = None
    if type_data is not None:
        type_argument = _expect_type_expression(
            _decode_node(type_data, path + ("type_argument",)),
            path + ("type_argument",),
        )
    return HumanInteractionExpression(
        span=_span_field(obj, path),
        kind=kind,
        type_argument=type_argument,
        arguments=tuple(_node_list(obj, "arguments", path, _expect_call_argument)),
    )


def _decode_start_task(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"task_name", "arguments"}, path)
    return StartTaskExpression(
        _span_field(obj, path),
        _string_field(obj, "task_name", path),
        tuple(_node_list(obj, "arguments", path, _expect_call_argument)),
    )


def _decode_await_task(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"operand"}, path)
    return AwaitTaskExpression(_span_field(obj, path), _expression_field(obj, "operand", path))


def _decode_member(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"object", "member"}, path)
    return MemberAccessExpression(
        span=_span_field(obj, path),
        object=_expression_field(obj, "object", path),
        member=_string_field(obj, "member", path),
    )


def _decode_index(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"object", "index"}, path)
    return IndexExpression(
        span=_span_field(obj, path),
        object=_expression_field(obj, "object", path),
        index=_expression_field(obj, "index", path),
    )


def _decode_list(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"elements"}, path)
    elements = _node_list(obj, "elements", path, _expect_expression)
    return ListLiteral(span=_span_field(obj, path), elements=tuple(elements))


def _decode_map_entry(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"key", "value"}, path)
    return MapEntry(
        span=_span_field(obj, path),
        key=_expression_field(obj, "key", path),
        value=_expression_field(obj, "value", path),
    )


def _decode_map(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"entries"}, path)
    entries = _node_list(obj, "entries", path, _expect_map_entry)
    return MapLiteral(span=_span_field(obj, path), entries=tuple(entries))


def _decode_record_field_initializer(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name", "value"}, path)
    return RecordFieldInitializer(
        span=_span_field(obj, path),
        name=_string_field(obj, "name", path),
        value=_expression_field(obj, "value", path),
    )


def _decode_record_construction(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"type_name", "fields"}, path)
    fields = _node_list(obj, "fields", path, _expect_record_field_initializer)
    return RecordConstructionExpression(
        span=_span_field(obj, path),
        type_name=_string_field(obj, "type_name", path),
        fields=tuple(fields),
    )


def _decode_enum_constructor_argument(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name", "value"}, path)
    return EnumConstructorArgument(
        _span_field(obj, path),
        _string_field(obj, "name", path),
        _expression_field(obj, "value", path),
    )


def _decode_enum_construction(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"type_name", "variant_name", "arguments"}, path)
    raw = _required(obj, "arguments", path)
    arguments = None
    if raw is not None:
        arguments = tuple(_node_list(obj, "arguments", path, _expect_enum_constructor_argument))
    return EnumConstructionExpression(
        _span_field(obj, path),
        _string_field(obj, "type_name", path),
        _string_field(obj, "variant_name", path),
        arguments,
    )


def _decode_named_type(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name"}, path)
    return NamedType(span=_span_field(obj, path), name=_string_field(obj, "name", path))


def _decode_generic_type(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"base", "arguments"}, path)
    base = _decode_node(_required(obj, "base", path), path + ("base",))
    if not isinstance(base, NamedType):
        raise ASTJSONError(
            ASTJSON_INVALID_FIELD, "Generic type base must be a named_type.", path + ("base",)
        )
    arguments = _node_list(obj, "arguments", path, _expect_type_expression)
    return GenericType(span=_span_field(obj, path), base=base, arguments=tuple(arguments))


def _decode_block(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"statements"}, path)
    statements = _node_list(obj, "statements", path, _expect_statement)
    return Block(span=_span_field(obj, path), statements=tuple(statements))


def _decode_binding(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"binding_kind", "name", "annotation", "initializer"}, path)
    annotation_value = _required(obj, "annotation", path)
    annotation = None
    if annotation_value is not None:
        annotation = _expect_type_expression(
            _decode_node(annotation_value, path + ("annotation",)), path + ("annotation",)
        )
    return BindingDeclaration(
        span=_span_field(obj, path),
        kind=_enum_field(obj, "binding_kind", path, _BINDING_FROM_JSON),
        name=_string_field(obj, "name", path),
        annotation=annotation,
        initializer=_expression_field(obj, "initializer", path),
    )


def _decode_assignment(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"operator", "target", "value"}, path)
    return AssignmentStatement(
        span=_span_field(obj, path),
        operator=_enum_field(obj, "operator", path, _ASSIGNMENT_FROM_JSON),
        target=_expression_field(obj, "target", path),
        value=_expression_field(obj, "value", path),
    )


def _decode_expression_statement(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"expression"}, path)
    return ExpressionStatement(
        span=_span_field(obj, path),
        expression=_expression_field(obj, "expression", path),
    )


def _decode_if(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"condition", "then_branch", "else_branch"}, path)
    then_branch = _decode_node(_required(obj, "then_branch", path), path + ("then_branch",))
    if not isinstance(then_branch, Block):
        raise ASTJSONError(
            ASTJSON_INVALID_FIELD, "then_branch must be a block.", path + ("then_branch",)
        )
    else_value = _required(obj, "else_branch", path)
    else_branch = None
    if else_value is not None:
        decoded_else = _decode_node(else_value, path + ("else_branch",))
        if not isinstance(decoded_else, (Block, IfStatement)):
            raise ASTJSONError(
                ASTJSON_INVALID_FIELD,
                "else_branch must be a block, if_statement, or null.",
                path + ("else_branch",),
            )
        else_branch = decoded_else
    return IfStatement(
        span=_span_field(obj, path),
        condition=_expression_field(obj, "condition", path),
        then_branch=then_branch,
        else_branch=else_branch,
    )


def _decode_while(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"condition", "body"}, path)
    body = _block_field(obj, "body", path)
    return WhileStatement(
        span=_span_field(obj, path),
        condition=_expression_field(obj, "condition", path),
        body=body,
    )


def _decode_for(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name", "iterable", "body"}, path)
    return ForStatement(
        span=_span_field(obj, path),
        name=_string_field(obj, "name", path),
        iterable=_expression_field(obj, "iterable", path),
        body=_block_field(obj, "body", path),
    )


def _decode_break(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, set(), path)
    return BreakStatement(span=_span_field(obj, path))


def _decode_continue(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, set(), path)
    return ContinueStatement(span=_span_field(obj, path))


def _decode_step(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name", "body"}, path)
    return StepStatement(
        span=_span_field(obj, path),
        name=_string_field(obj, "name", path),
        body=_block_field(obj, "body", path),
    )


def _decode_use_capability(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"capability_name", "alias"}, path)
    module_field = obj.get("capability_module")
    capability_module: tuple[str, ...] = ()
    if module_field is not None:
        if not isinstance(module_field, list) or not all(
            isinstance(item, str) for item in module_field
        ):
            raise ValueError(f"{path}.capability_module must be a string array")
        capability_module = tuple(module_field)
    return UseCapabilityDeclaration(
        span=_span_field(obj, path),
        capability_name=_string_field(obj, "capability_name", path),
        alias=_string_field(obj, "alias", path),
        capability_module=capability_module,
    )


def _decode_plan_region(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"body"}, path)
    return PlanRegion(_span_field(obj, path), _block_field(obj, "body", path))


def _decode_goal(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"expression"}, path)
    return GoalClause(
        span=_span_field(obj, path),
        expression=_expression_field(obj, "expression", path),
    )


def _decode_require(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"condition"}, path)
    return RequireClause(
        span=_span_field(obj, path),
        condition=_expression_field(obj, "condition", path),
    )


def _decode_invariant(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"condition"}, path)
    return InvariantClause(
        span=_span_field(obj, path),
        condition=_expression_field(obj, "condition", path),
    )


def _decode_success_parameter(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name", "type_annotation"}, path)
    annotation = _expect_type_expression(
        _decode_node(_required(obj, "type_annotation", path), path + ("type_annotation",)),
        path + ("type_annotation",),
    )
    return SuccessParameter(
        span=_span_field(obj, path),
        name=_string_field(obj, "name", path),
        type_annotation=annotation,
    )


def _decode_success(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"parameter", "condition"}, path)
    parameter_data = _required(obj, "parameter", path)
    parameter: SuccessParameter | None = None
    if parameter_data is not None:
        decoded = _decode_node(parameter_data, path + ("parameter",))
        if not isinstance(decoded, SuccessParameter):
            raise ASTJSONError(
                ASTJSON_INVALID_FIELD,
                "Success parameter must be a success_parameter node or null.",
                path + ("parameter",),
            )
        parameter = decoded
    return SuccessClause(
        span=_span_field(obj, path),
        parameter=parameter,
        condition=_expression_field(obj, "condition", path),
    )


def _decode_return(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"value"}, path)
    value_data = _required(obj, "value", path)
    value = (
        None
        if value_data is None
        else _expect_expression(_decode_node(value_data, path + ("value",)), path + ("value",))
    )
    return ReturnStatement(span=_span_field(obj, path), value=value)


def _decode_pattern_binding(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name"}, path)
    return PatternBinding(_span_field(obj, path), _string_field(obj, "name", path))


def _decode_enum_pattern(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"variant_name", "bindings"}, path)
    return EnumPattern(
        _span_field(obj, path),
        _string_field(obj, "variant_name", path),
        tuple(_node_list(obj, "bindings", path, _expect_pattern_binding)),
    )


def _decode_match_case(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"pattern", "body"}, path)
    pattern = _decode_node(_required(obj, "pattern", path), path + ("pattern",))
    if not isinstance(pattern, EnumPattern):
        raise ASTJSONError(
            ASTJSON_INVALID_FIELD, "pattern must be an enum_pattern.", path + ("pattern",)
        )
    body = _expect_statement(
        _decode_node(_required(obj, "body", path), path + ("body",)), path + ("body",)
    )
    return MatchCase(_span_field(obj, path), pattern, body)


def _decode_match_statement(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"scrutinee", "cases"}, path)
    return MatchStatement(
        _span_field(obj, path),
        _expression_field(obj, "scrutinee", path),
        tuple(_node_list(obj, "cases", path, _expect_match_case)),
    )


def _decode_parameter(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name", "type_annotation", "mutable"}, path)
    mutable = _required(obj, "mutable", path)
    if type(mutable) is not bool:
        raise ASTJSONError(
            ASTJSON_INVALID_FIELD, "Parameter mutable must be a boolean.", path + ("mutable",)
        )
    annotation = _expect_type_expression(
        _decode_node(_required(obj, "type_annotation", path), path + ("type_annotation",)),
        path + ("type_annotation",),
    )
    return Parameter(
        span=_span_field(obj, path),
        name=_string_field(obj, "name", path),
        type_annotation=annotation,
        mutable=mutable,
    )


def _decode_function(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name", "parameters", "return_type", "body"}, path)
    parameters = _node_list(obj, "parameters", path, _expect_parameter)
    return_type = _expect_type_expression(
        _decode_node(_required(obj, "return_type", path), path + ("return_type",)),
        path + ("return_type",),
    )
    return FunctionDeclaration(
        span=_span_field(obj, path),
        name=_string_field(obj, "name", path),
        parameters=tuple(parameters),
        return_type=return_type,
        body=_block_field(obj, "body", path),
    )


def _decode_task(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name", "parameters", "return_type", "body"}, path)
    parameters = _node_list(obj, "parameters", path, _expect_parameter)
    return_type = _expect_type_expression(
        _decode_node(_required(obj, "return_type", path), path + ("return_type",)),
        path + ("return_type",),
    )
    return TaskDeclaration(
        span=_span_field(obj, path),
        name=_string_field(obj, "name", path),
        parameters=tuple(parameters),
        return_type=return_type,
        body=_block_field(obj, "body", path),
    )


def _decode_capability_operation(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name", "parameters", "return_type"}, path)
    parameters = _node_list(obj, "parameters", path, _expect_parameter)
    return_type = _expect_type_expression(
        _decode_node(_required(obj, "return_type", path), path + ("return_type",)),
        path + ("return_type",),
    )
    return CapabilityOperationSignature(
        _span_field(obj, path),
        _string_field(obj, "name", path),
        tuple(parameters),
        return_type,
    )


def _expect_capability_operation(node: Node, path: JSONPath) -> CapabilityOperationSignature:
    if not isinstance(node, CapabilityOperationSignature):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, "Expected capability operation.", path)
    return node


def _decode_capability(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name", "operations"}, path)
    operations = _node_list(obj, "operations", path, _expect_capability_operation)
    return CapabilityDeclaration(
        _span_field(obj, path),
        _string_field(obj, "name", path),
        tuple(operations),
    )


def _decode_record_field_declaration(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name", "type_annotation"}, path)
    annotation = _expect_type_expression(
        _decode_node(_required(obj, "type_annotation", path), path + ("type_annotation",)),
        path + ("type_annotation",),
    )
    return RecordFieldDeclaration(
        span=_span_field(obj, path),
        name=_string_field(obj, "name", path),
        type_annotation=annotation,
    )


def _decode_record_declaration(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name", "fields"}, path)
    fields = _node_list(obj, "fields", path, _expect_record_field_declaration)
    return RecordDeclaration(
        span=_span_field(obj, path),
        name=_string_field(obj, "name", path),
        fields=tuple(fields),
    )


def _decode_enum_payload_field(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name", "type_annotation"}, path)
    annotation = _expect_type_expression(
        _decode_node(_required(obj, "type_annotation", path), path + ("type_annotation",)),
        path + ("type_annotation",),
    )
    return EnumPayloadField(_span_field(obj, path), _string_field(obj, "name", path), annotation)


def _decode_enum_variant(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name", "payload"}, path)
    return EnumVariantDeclaration(
        _span_field(obj, path),
        _string_field(obj, "name", path),
        tuple(_node_list(obj, "payload", path, _expect_enum_payload_field)),
    )


def _decode_enum_declaration(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name", "variants"}, path)
    return EnumDeclaration(
        _span_field(obj, path),
        _string_field(obj, "name", path),
        tuple(_node_list(obj, "variants", path, _expect_enum_variant)),
    )


def _decode_newtype_declaration(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"name", "underlying_type"}, path)
    underlying = _expect_type_expression(
        _decode_node(_required(obj, "underlying_type", path), path + ("underlying_type",)),
        path + ("underlying_type",),
    )
    return NewtypeDeclaration(
        span=_span_field(obj, path),
        name=_string_field(obj, "name", path),
        underlying_type=underlying,
    )


def _decode_import_declaration(obj: dict[str, object], path: JSONPath) -> Node:
    _check_node_fields(obj, {"path"}, path)
    raw = _required(obj, "path", path)
    if not isinstance(raw, list) or not raw or any(not isinstance(item, str) for item in raw):
        raise ASTJSONError(
            ASTJSON_INVALID_FIELD,
            "Import path must be a non-empty array of strings.",
            path + ("path",),
        )
    return ImportDeclaration(span=_span_field(obj, path), path=tuple(cast(list[str], raw)))


type NodeDecoder = Callable[[dict[str, object], JSONPath], Node]
_NODE_DECODERS: dict[str, NodeDecoder] = {
    "program": _decode_program,
    "integer_literal": _decode_integer,
    "decimal_literal": _decode_decimal,
    "string_literal": _decode_string,
    "interpolated_string": _decode_interpolated_string,
    "boolean_literal": _decode_boolean,
    "none_literal": _decode_none,
    "identifier": _decode_identifier,
    "unary_expression": _decode_unary,
    "binary_expression": _decode_binary,
    "call_argument": _decode_call_argument,
    "call_expression": _decode_call,
    "human_interaction_expression": _decode_human_interaction,
    "start_task_expression": _decode_start_task,
    "await_task_expression": _decode_await_task,
    "member_access_expression": _decode_member,
    "index_expression": _decode_index,
    "list_literal": _decode_list,
    "map_entry": _decode_map_entry,
    "map_literal": _decode_map,
    "record_field_initializer": _decode_record_field_initializer,
    "record_construction_expression": _decode_record_construction,
    "enum_constructor_argument": _decode_enum_constructor_argument,
    "enum_construction_expression": _decode_enum_construction,
    "named_type": _decode_named_type,
    "generic_type": _decode_generic_type,
    "block": _decode_block,
    "binding_declaration": _decode_binding,
    "assignment_statement": _decode_assignment,
    "expression_statement": _decode_expression_statement,
    "if_statement": _decode_if,
    "while_statement": _decode_while,
    "for_statement": _decode_for,
    "break_statement": _decode_break,
    "continue_statement": _decode_continue,
    "step_statement": _decode_step,
    "use_capability_declaration": _decode_use_capability,
    "plan_region": _decode_plan_region,
    "goal_clause": _decode_goal,
    "require_clause": _decode_require,
    "invariant_clause": _decode_invariant,
    "success_parameter": _decode_success_parameter,
    "success_clause": _decode_success,
    "return_statement": _decode_return,
    "pattern_binding": _decode_pattern_binding,
    "enum_pattern": _decode_enum_pattern,
    "match_case": _decode_match_case,
    "match_statement": _decode_match_statement,
    "parameter": _decode_parameter,
    "function_declaration": _decode_function,
    "task_declaration": _decode_task,
    "capability_operation_signature": _decode_capability_operation,
    "capability_declaration": _decode_capability,
    "record_field_declaration": _decode_record_field_declaration,
    "record_declaration": _decode_record_declaration,
    "enum_payload_field": _decode_enum_payload_field,
    "enum_variant_declaration": _decode_enum_variant,
    "enum_declaration": _decode_enum_declaration,
    "newtype_declaration": _decode_newtype_declaration,
    "import_declaration": _decode_import_declaration,
}


def _check_node_fields(obj: dict[str, object], semantic_fields: set[str], path: JSONPath) -> None:
    _check_fields(obj, {"kind", *semantic_fields, "span"}, path)


def _check_fields(obj: dict[str, object], expected: set[str], path: JSONPath) -> None:
    missing = expected - obj.keys()
    if missing:
        field = min(missing)
        raise ASTJSONError(
            ASTJSON_MISSING_FIELD, f"Missing required field: {field}.", path + (field,)
        )
    unknown = obj.keys() - expected
    if unknown:
        field = min(unknown)
        raise ASTJSONError(ASTJSON_INVALID_FIELD, f"Unknown field: {field}.", path + (field,))


def _required(obj: dict[str, object], field: str, path: JSONPath) -> object:
    if field not in obj:
        raise ASTJSONError(
            ASTJSON_MISSING_FIELD, f"Missing required field: {field}.", path + (field,)
        )
    return obj[field]


def _expect_object(value: object, path: JSONPath) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        code = ASTJSON_INVALID_DOCUMENT if not path else ASTJSON_INVALID_FIELD
        raise ASTJSONError(code, "Expected a JSON object.", path)
    return cast(dict[str, object], value)


def _string_field(obj: dict[str, object], field: str, path: JSONPath) -> str:
    value = _required(obj, field, path)
    if not isinstance(value, str):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, f"{field} must be a string.", path + (field,))
    return value


def _span_field(obj: dict[str, object], path: JSONPath) -> SourceSpan:
    return _decode_span(_required(obj, "span", path), path + ("span",))


def _decode_span(value: object, path: JSONPath) -> SourceSpan:
    obj = _expect_object(value, path)
    _check_fields(obj, {"start", "end"}, path)
    start = _decode_location(_required(obj, "start", path), path + ("start",))
    end = _decode_location(_required(obj, "end", path), path + ("end",))
    if end.offset < start.offset:
        raise ASTJSONError(
            ASTJSON_INVALID_FIELD,
            "Span end offset precedes start offset.",
            path + ("end", "offset"),
        )
    return SourceSpan(start=start, end=end)


def _decode_location(value: object, path: JSONPath) -> SourceLocation:
    obj = _expect_object(value, path)
    _check_fields(obj, {"offset", "line", "column"}, path)
    offset = _nonnegative_integer_field(obj, "offset", path, minimum=0)
    line = _nonnegative_integer_field(obj, "line", path, minimum=1)
    column = _nonnegative_integer_field(obj, "column", path, minimum=1)
    return SourceLocation(offset=offset, line=line, column=column)


def _nonnegative_integer_field(
    obj: dict[str, object], field: str, path: JSONPath, *, minimum: int
) -> int:
    value = _required(obj, field, path)
    if type(value) is not int or value < minimum:
        raise ASTJSONError(
            ASTJSON_INVALID_FIELD,
            f"{field} must be an integer greater than or equal to {minimum}.",
            path + (field,),
        )
    return value


def _expression_field(obj: dict[str, object], field: str, path: JSONPath) -> Expression:
    child_path = path + (field,)
    return _expect_expression(_decode_node(_required(obj, field, path), child_path), child_path)


def _block_field(obj: dict[str, object], field: str, path: JSONPath) -> Block:
    child_path = path + (field,)
    node = _decode_node(_required(obj, field, path), child_path)
    if not isinstance(node, Block):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, f"{field} must be a block.", child_path)
    return node


def _node_list[T](
    obj: dict[str, object],
    field: str,
    path: JSONPath,
    validator: Callable[[Node, JSONPath], T],
) -> list[T]:
    value = _required(obj, field, path)
    if not isinstance(value, list):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, f"{field} must be an array.", path + (field,))
    result: list[T] = []
    for index, item in enumerate(value):
        item_path = path + (field, index)
        node = _decode_node(item, item_path)
        result.append(validator(node, item_path))
    return result


def _expect_expression(node: Node, path: JSONPath) -> Expression:
    if not isinstance(node, Expression):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, "Expected an expression node.", path)
    return node


def _expect_statement(node: Node, path: JSONPath) -> Statement:
    if not isinstance(node, Statement):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, "Expected a statement node.", path)
    return node


def _expect_type_expression(node: Node, path: JSONPath) -> TypeExpression:
    if not isinstance(node, TypeExpression):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, "Expected a type-expression node.", path)
    return node


def _expect_call_argument(node: Node, path: JSONPath) -> CallArgument:
    if not isinstance(node, CallArgument):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, "Expected a call_argument node.", path)
    return node


def _expect_map_entry(node: Node, path: JSONPath) -> MapEntry:
    if not isinstance(node, MapEntry):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, "Expected a map_entry node.", path)
    return node


def _expect_record_field_initializer(node: Node, path: JSONPath) -> RecordFieldInitializer:
    if not isinstance(node, RecordFieldInitializer):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, "Expected a record_field_initializer node.", path)
    return node


def _expect_record_field_declaration(node: Node, path: JSONPath) -> RecordFieldDeclaration:
    if not isinstance(node, RecordFieldDeclaration):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, "Expected a record_field_declaration node.", path)
    return node


def _expect_enum_constructor_argument(node: Node, path: JSONPath) -> EnumConstructorArgument:
    if not isinstance(node, EnumConstructorArgument):
        raise ASTJSONError(
            ASTJSON_INVALID_FIELD, "Expected an enum_constructor_argument node.", path
        )
    return node


def _expect_pattern_binding(node: Node, path: JSONPath) -> PatternBinding:
    if not isinstance(node, PatternBinding):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, "Expected a pattern_binding node.", path)
    return node


def _expect_match_case(node: Node, path: JSONPath) -> MatchCase:
    if not isinstance(node, MatchCase):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, "Expected a match_case node.", path)
    return node


def _expect_enum_payload_field(node: Node, path: JSONPath) -> EnumPayloadField:
    if not isinstance(node, EnumPayloadField):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, "Expected an enum_payload_field node.", path)
    return node


def _expect_enum_variant(node: Node, path: JSONPath) -> EnumVariantDeclaration:
    if not isinstance(node, EnumVariantDeclaration):
        raise ASTJSONError(
            ASTJSON_INVALID_FIELD, "Expected an enum_variant_declaration node.", path
        )
    return node


def _expect_parameter(node: Node, path: JSONPath) -> Parameter:
    if not isinstance(node, Parameter):
        raise ASTJSONError(ASTJSON_INVALID_FIELD, "Expected a parameter node.", path)
    return node


def _enum_field[T](
    obj: dict[str, object], field: str, path: JSONPath, values: Mapping[str, T]
) -> T:
    value = _required(obj, field, path)
    if not isinstance(value, str) or value not in values:
        raise ASTJSONError(
            ASTJSON_INVALID_ENUM_VALUE, f"Invalid {field} value: {value!r}.", path + (field,)
        )
    return values[value]
