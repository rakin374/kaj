from collections.abc import Callable

from .conftest import PipelineResult


def output(result: PipelineResult) -> str:
    assert result.execution is not None
    assert result.execution.runtime_error is None
    return result.execution.output


def test_factorial_acceptance_program(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source(
        "fn factorial(n: Int) -> Int { "
        "if n <= 1 { return 1 } return n * factorial(n - 1) }\n"
        "print(factorial(5))"
    )
    assert output(result) == "120\n"


def test_mutual_recursion_has_independent_frames(
    run_source: Callable[[str], PipelineResult],
) -> None:
    result = run_source(
        "fn even(n: Int) -> Bool { if n == 0 { return true } return odd(n - 1) }\n"
        "fn odd(n: Int) -> Bool { if n == 0 { return false } return even(n - 1) }\n"
        "print(even(10))\nprint(odd(10))"
    )
    assert output(result) == "true\nfalse\n"
