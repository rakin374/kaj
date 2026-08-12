from collections.abc import Callable
from decimal import Decimal

from kaj.runtime import KajList

from .conftest import PipelineResult


def output(result: PipelineResult) -> str:
    assert result.execution is not None
    assert result.execution.runtime_error is None
    return result.execution.output


def test_list_acceptance_program(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source("let values = [1, 2, 3]\nfor value in values { print(value) }")
    assert output(result) == "1\n2\n3\n"


def test_index_count_and_nested_lists(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source("let rows = [[1, 2], [3, 4]]\nprint(rows[1][0])\nprint(rows.count)")
    assert output(result) == "3\n2\n"


def test_empty_list_count(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source("let values: List<Int> = []\nprint(values.count)")
    assert output(result) == "0\n"


def test_contextual_list_promotion_is_materialized(
    run_source: Callable[[str], PipelineResult],
) -> None:
    result = run_source("let values: List<Decimal> = [1, 2]\nprint(values[0] / 2)")
    assert output(result) == "0.5\n"


def test_kaj_list_is_controlled_value() -> None:
    value = KajList((Decimal(1), Decimal("2.5")))
    assert value.elements == (Decimal(1), Decimal("2.5"))
    assert not hasattr(value, "append")


def test_list_rebinding(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source("var values = [1, 2]\nvalues = [3, 4]\nprint(values[0])")
    assert output(result) == "3\n"
