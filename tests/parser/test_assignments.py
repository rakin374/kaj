from collections.abc import Callable

import pytest

from kaj.ast import (
    AssignmentOperator,
    AssignmentStatement,
    Identifier,
    IndexExpression,
    MemberAccessExpression,
)
from kaj.parser import ParserResult


@pytest.mark.parametrize(
    ("source", "operator"),
    [
        ("x = 1", AssignmentOperator.ASSIGN),
        ("x += 1", AssignmentOperator.ADD_ASSIGN),
        ("x -= 1", AssignmentOperator.SUBTRACT_ASSIGN),
        ("x *= 2", AssignmentOperator.MULTIPLY_ASSIGN),
        ("x /= 2", AssignmentOperator.DIVIDE_ASSIGN),
    ],
)
def test_assignment_operators(
    parse: Callable[[str], ParserResult], source: str, operator: AssignmentOperator
) -> None:
    statement = parse(source).program.statements[0]

    assert isinstance(statement, AssignmentStatement)
    assert isinstance(statement.target, Identifier)
    assert statement.operator is operator


@pytest.mark.parametrize(
    ("source", "target_type"),
    [
        ('user.name = "Alice"', MemberAccessExpression),
        ("items[0] = value", IndexExpression),
    ],
)
def test_structural_assignment_targets(
    parse: Callable[[str], ParserResult], source: str, target_type: type[object]
) -> None:
    statement = parse(source).program.statements[0]

    assert isinstance(statement, AssignmentStatement)
    assert isinstance(statement.target, target_type)


@pytest.mark.parametrize("source", ["1 = 2", "foo() = 3", "(a + b) = c"])
def test_invalid_assignment_targets_are_diagnosed(
    parse: Callable[[str], ParserResult], source: str
) -> None:
    result = parse(source)

    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "PARSE_INVALID_ASSIGNMENT_TARGET"
    ]
