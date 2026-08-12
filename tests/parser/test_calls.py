from collections.abc import Callable

from kaj.ast import (
    CallExpression,
    Expression,
    ExpressionStatement,
    Identifier,
    IndexExpression,
    IntegerLiteral,
    MemberAccessExpression,
)
from kaj.parser import ParserResult


def parsed_expression(parse: Callable[[str], ParserResult], source: str) -> Expression:
    statement = parse(source).program.statements[0]
    assert isinstance(statement, ExpressionStatement)
    return statement.expression


def test_zero_positional_and_named_arguments(parse: Callable[[str], ParserResult]) -> None:
    empty = parsed_expression(parse, "run()")
    mixed = parsed_expression(parse, "send(message, priority: 2)")

    assert isinstance(empty, CallExpression)
    assert empty.arguments == ()
    assert isinstance(mixed, CallExpression)
    assert [argument.name for argument in mixed.arguments] == [None, "priority"]
    assert isinstance(mixed.arguments[1].value, IntegerLiteral)


def test_postfix_chaining_is_left_to_right(parse: Callable[[str], ParserResult]) -> None:
    expression = parsed_expression(parse, "foo().bar[0](x)")

    assert isinstance(expression, CallExpression)
    assert isinstance(expression.callee, IndexExpression)
    assert isinstance(expression.callee.object, MemberAccessExpression)
    assert isinstance(expression.callee.object.object, CallExpression)
    assert isinstance(expression.arguments[0].value, Identifier)


def test_positional_after_named_is_diagnosed(parse: Callable[[str], ParserResult]) -> None:
    result = parse("send(priority: 2, message)")

    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "PARSE_POSITIONAL_AFTER_NAMED_ARGUMENT"
    ]
    assert result.diagnostics[0].span.start.offset == 18
