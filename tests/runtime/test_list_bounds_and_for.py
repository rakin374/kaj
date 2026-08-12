from collections.abc import Callable

import pytest

from .conftest import PipelineResult


@pytest.mark.parametrize("index", ["-1", "3", "999"])
def test_index_out_of_bounds_is_structured(
    run_source: Callable[[str], PipelineResult], index: str
) -> None:
    result = run_source(f"let values = [1, 2, 3]\nprint(values[{index}])")
    assert result.execution is not None
    assert result.execution.runtime_error is not None
    assert result.execution.runtime_error.code == "RUNTIME_INDEX_OUT_OF_BOUNDS"


def test_for_shadowing_and_order(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source(
        "let value = 100\nlet values = [1, 2]\n"
        "for value in values { print(value) }\nprint(value)"
    )
    assert result.execution is not None
    assert result.execution.runtime_error is None
    assert result.execution.output == "1\n2\n100\n"


def test_for_iterable_evaluates_once(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source(
        'fn make() -> List<Int> { print("make") return [1, 2] }\n'
        "for value in make() { print(value) }"
    )
    assert result.execution is not None
    assert result.execution.runtime_error is None
    assert result.execution.output == "make\n1\n2\n"


def test_return_propagates_through_for(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source(
        "fn first(values: List<Int>) -> Int { "
        "for value in values { return value } return 0 }\n"
        "print(first([7, 8]))\nprint(first([]))"
    )
    assert result.execution is not None
    assert result.execution.runtime_error is None
    assert result.execution.output == "7\n0\n"
