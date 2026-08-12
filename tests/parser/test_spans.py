from collections.abc import Callable

from kaj.ast import BindingDeclaration, CallExpression, ExpressionStatement, FunctionDeclaration
from kaj.parser import ParserResult
from kaj.source import SourceLocation


def test_empty_program_span_is_zero_width_at_eof(parse: Callable[[str], ParserResult]) -> None:
    program = parse("").program

    assert program.span.start == SourceLocation(0, 1, 1)
    assert program.span.end == program.span.start


def test_binding_and_program_spans(parse: Callable[[str], ParserResult]) -> None:
    result = parse("let x = 10")
    binding = result.program.statements[0]

    assert isinstance(binding, BindingDeclaration)
    assert binding.span.start.offset == 0
    assert binding.span.end.offset == 10
    assert result.program.span == binding.span


def test_call_and_argument_spans(parse: Callable[[str], ParserResult]) -> None:
    statement = parse("send(value, priority: 2)").program.statements[0]

    assert isinstance(statement, ExpressionStatement)
    assert isinstance(statement.expression, CallExpression)
    assert statement.expression.span.start.offset == 0
    assert statement.expression.span.end.offset == 24
    assert statement.expression.arguments[1].span.start.offset == 12
    assert statement.expression.arguments[1].span.end.offset == 23


def test_function_span_includes_complete_block(parse: Callable[[str], ParserResult]) -> None:
    source = "fn f() -> None { return }"
    function = parse(source).program.statements[0]

    assert isinstance(function, FunctionDeclaration)
    assert function.span.start.offset == 0
    assert function.span.end.offset == len(source)
