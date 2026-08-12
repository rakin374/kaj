from collections.abc import Callable

from .conftest import PipelineResult


def output(result: PipelineResult) -> str:
    assert result.execution is not None
    assert result.execution.runtime_error is None
    return result.execution.output


def test_let_binding_and_shadowing(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source("let x = 1\nif true { let x = 2 print(x) }\nprint(x)")
    assert output(result) == "2\n1\n"


def test_var_assignment_and_compound_assignment(
    run_source: Callable[[str], PipelineResult],
) -> None:
    result = run_source("var x = 1\nx = 2\nx += 3\nx *= 2\nx -= 1\nprint(x)")
    assert output(result) == "9\n"


def test_assignment_boundary_materializes_decimal(
    run_source: Callable[[str], PipelineResult],
) -> None:
    result = run_source("var x: Decimal = 1\nx = 2\nprint(x / 4)")
    assert output(result) == "0.5\n"


def test_if_selects_only_one_branch(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source('if false { print("bad") } else { print("good") }')
    assert output(result) == "good\n"


def test_while_updates_outer_slot(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source("var x = 0\nwhile x < 3 { let snapshot = x x += 1 }\nprint(x)")
    assert output(result) == "3\n"
