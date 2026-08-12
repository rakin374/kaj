from collections.abc import Callable

from .conftest import PipelineResult


def output(result: PipelineResult) -> str:
    assert result.execution is not None
    assert result.execution.runtime_error is None
    return result.execution.output


def test_numeric_and_string_operators(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source(
        'print(10 + 2)\nprint(10 + 2.5)\nprint(5 / 2)\nprint(5 % 2)\n'
        'print(2 ** 10)\nprint("a" + "b")'
    )
    assert output(result) == "12\n12.5\n2.5\n1\n1024\nab\n"


def test_unary_comparison_and_boolean_operators(
    run_source: Callable[[str], PipelineResult],
) -> None:
    result = run_source(
        "print(-2)\nprint(+2.5)\nprint(not false)\nprint(1 < 2.0)\n"
        "print(2 == 2.0)\nprint(true and false)\nprint(false or true)"
    )
    assert output(result) == "-2\n2.5\ntrue\ntrue\ntrue\nfalse\ntrue\n"


def test_boolean_operators_short_circuit(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source(
        "print(false and (1 / 0 == 0))\nprint(true or (1 / 0 == 0))"
    )
    assert output(result) == "false\ntrue\n"


def test_division_by_zero_is_structured(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source("print(1 / 0)")
    assert result.execution is not None
    assert result.execution.runtime_error is not None

    assert result.execution.runtime_error.code == "RUNTIME_DIVISION_BY_ZERO"
    assert result.execution.output == ""


def test_negative_int_power_never_leaks_float(
    run_source: Callable[[str], PipelineResult],
) -> None:
    result = run_source("print(2 ** -1)")
    assert result.execution is not None
    assert result.execution.runtime_error is not None
    assert result.execution.runtime_error.code == "RUNTIME_INVALID_OPERATION"
