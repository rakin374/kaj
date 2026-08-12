from collections.abc import Callable

import pytest

from kaj.semantic import TypeCheckResult


@pytest.mark.parametrize(
    "source",
    [
        "var x = 10\nx = 20",
        "var x: Decimal = 10\nx = 20.5",
        "var x: Decimal = 1\nx += 2",
        "var x = 1\nx += 2",
        "var x = 4\nx -= 2\nx *= 3",
    ],
)
def test_valid_assignments(check_source: Callable[[str], TypeCheckResult], source: str) -> None:
    assert check_source(source).diagnostics == ()


def test_assignment_type_mismatch(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("var x = 10\nx = 20.5")
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["TYPE_MISMATCH"]


def test_compound_result_must_assign_back(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("var x: Int = 1\nx += 2.5\nx /= 2")
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "TYPE_MISMATCH",
        "TYPE_MISMATCH",
    ]


def test_immutable_assignment_is_diagnosed(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("let x = 10\nx = 20")
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["ASSIGN_TO_IMMUTABLE"]


def test_parameter_mutability(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source(
        "fn immutable(x: Int) -> None { x = 2 }\nfn mutable(var x: Int) -> None { x = 2 }"
    )
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["ASSIGN_TO_IMMUTABLE"]


def test_bool_only_conditions(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("let ready = true\nif ready {}\nwhile true {}")
    assert result.diagnostics == ()


def test_non_bool_conditions_are_diagnosed(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source('if 1 {}\nwhile "yes" {}')
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "TYPE_CONDITION_NOT_BOOL",
        "TYPE_CONDITION_NOT_BOOL",
    ]
