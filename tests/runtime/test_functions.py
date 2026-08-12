from collections.abc import Callable

from .conftest import PipelineResult


def output(result: PipelineResult) -> str:
    assert result.execution is not None
    assert result.execution.runtime_error is None
    return result.execution.output


def test_function_call_and_return(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source("fn add(a: Int, b: Int) -> Int { return a + b }\nprint(add(2, 3))")
    assert output(result) == "5\n"


def test_nested_return_exits_function(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source(
        "fn choose(value: Bool) -> Int { if value { return 1 } return 2 }\n"
        "print(choose(true))\nprint(choose(false))"
    )
    assert output(result) == "1\n2\n"


def test_none_function_fallthrough_and_bare_return(
    run_source: Callable[[str], PipelineResult],
) -> None:
    result = run_source(
        'fn fallthrough() -> None { print("a") }\n'
        'fn explicit() -> None { print("b") return print("c") }\n'
        "print(fallthrough())\nprint(explicit())"
    )
    assert output(result) == "a\nnone\nb\nc\nnone\n"


def test_argument_and_return_promotions_materialize_decimal(
    run_source: Callable[[str], PipelineResult],
) -> None:
    result = run_source(
        "fn identity(x: Decimal) -> Decimal { return x }\n"
        "fn value() -> Decimal { return 10 }\n"
        "print(identity(5) / 2)\nprint(value() / 4)"
    )
    assert output(result) == "2.5\n2.5\n"


def test_named_arguments_evaluate_in_source_order(
    run_source: Callable[[str], PipelineResult],
) -> None:
    result = run_source(
        "fn observe(first: None, second: None) -> None {}\n"
        'observe(second: print("second-source-first"), first: print("first-source-second"))'
    )
    assert output(result) == "second-source-first\nfirst-source-second\n"


def test_var_parameter_does_not_mutate_caller(
    run_source: Callable[[str], PipelineResult],
) -> None:
    result = run_source(
        "fn change(var x: Int) -> Int { x = 20 return x }\n"
        "let original = 10\nlet changed = change(original)\n"
        "print(original)\nprint(changed)"
    )
    assert output(result) == "10\n20\n"
