from collections.abc import Callable

from kaj.semantic import TypeCheckResult


def test_self_recursion(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source(
        "fn factorial(n: Int) -> Int { "
        "if n == 0 { return 1 } else { return n * factorial(n - 1) } }"
    )
    assert result.diagnostics == ()


def test_mutual_recursion(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source(
        "fn even(n: Int) -> Bool { if n == 0 { return true } "
        "else { return odd(n - 1) } }\n"
        "fn odd(n: Int) -> Bool { if n == 0 { return false } "
        "else { return even(n - 1) } }"
    )
    assert result.diagnostics == ()


def test_forward_function_call(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("fn first() -> Int { return second() }\nfn second() -> Int { return 2 }")
    assert result.diagnostics == ()


def test_var_parameter_is_local_mutability(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source(
        "fn increment(var x: Int) -> Int { x += 1 return x }\n"
        "let original = 10\nlet a = increment(10)\nlet b = increment(original)"
    )
    assert result.diagnostics == ()


def test_var_parameter_still_checks_assignment_type(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source("fn f(var x: Int) -> Int { x = 2.5 return x }")
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["TYPE_MISMATCH"]
