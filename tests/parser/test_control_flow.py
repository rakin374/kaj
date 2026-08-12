from collections.abc import Callable

from kaj.ast import (
    BreakStatement,
    CallExpression,
    ContinueStatement,
    ExpressionStatement,
    ForStatement,
    IfStatement,
    ReturnStatement,
    WhileStatement,
)
from kaj.parser import ParserResult


def test_if_else_and_else_if(parse: Callable[[str], ParserResult]) -> None:
    simple = parse("if ready { run() }").program.statements[0]
    with_else = parse("if ready { run() } else { wait() }").program.statements[0]
    chain = parse("if a { one() } else if b { two() } else { three() }").program.statements[0]

    assert isinstance(simple, IfStatement)
    assert simple.else_branch is None
    assert isinstance(with_else, IfStatement)
    assert with_else.else_branch is not None
    assert isinstance(chain, IfStatement)
    assert isinstance(chain.else_branch, IfStatement)
    assert chain.else_branch.else_branch is not None


def test_while_and_for(parse: Callable[[str], ParserResult]) -> None:
    while_statement = parse("while ready { run() }").program.statements[0]
    for_statement = parse("for item in items { print(item) }").program.statements[0]

    assert isinstance(while_statement, WhileStatement)
    assert isinstance(for_statement, ForStatement)
    assert for_statement.name == "item"


def test_break_continue_and_return(parse: Callable[[str], ParserResult]) -> None:
    result = parse("break continue return 1")

    assert isinstance(result.program.statements[0], BreakStatement)
    assert isinstance(result.program.statements[1], ContinueStatement)
    assert isinstance(result.program.statements[2], ReturnStatement)
    assert result.program.statements[2].value is not None


def test_bare_return_before_block_end(parse: Callable[[str], ParserResult]) -> None:
    function = parse("fn noop() -> None { return }").program.statements[0]
    return_statement = function.body.statements[0]  # type: ignore[attr-defined]

    assert isinstance(return_statement, ReturnStatement)
    assert return_statement.value is None


def test_calls_remain_expression_statements_in_blocks(
    parse: Callable[[str], ParserResult],
) -> None:
    statement = parse("if ready { run() }").program.statements[0]
    assert isinstance(statement, IfStatement)
    body_statement = statement.then_branch.statements[0]
    assert isinstance(body_statement, ExpressionStatement)
    assert isinstance(body_statement.expression, CallExpression)
