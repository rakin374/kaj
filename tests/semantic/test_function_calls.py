from collections.abc import Callable

import pytest

from kaj.ast import BindingDeclaration, CallExpression, Program
from kaj.semantic import PrimitiveType, TypeCheckResult


def test_positional_call_and_result_type(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source(
        "fn add(a: Int, b: Int) -> Int { return a + b }\nlet x = add(1, 2)"
    )
    x = result.resolution.module_scope.lookup_local("x")
    assert x is not None

    assert result.type_of_symbol(x) is PrimitiveType.INT
    assert result.diagnostics == ()


def test_int_promotes_at_call_boundary(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("fn f(x: Decimal) -> Decimal { return x }\nlet y = f(10)")
    assert result.diagnostics == ()


def test_wrong_argument_retains_call_return_type(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source('fn f(x: Int) -> String { return "ok" }\nlet y = f("bad")')
    y = result.resolution.module_scope.lookup_local("y")
    assert y is not None

    assert result.type_of_symbol(y) is PrimitiveType.STRING
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["TYPE_MISMATCH"]


@pytest.mark.parametrize(
    ("call", "code"),
    [
        ("f(1)", "TYPE_MISSING_ARGUMENT"),
        ("f(1, 2, 3)", "TYPE_TOO_MANY_ARGUMENTS"),
        ("f(a: 1, unknown: 2)", "TYPE_UNKNOWN_NAMED_ARGUMENT"),
        ("f(1, a: 2, b: 3)", "TYPE_DUPLICATE_ARGUMENT"),
    ],
)
def test_argument_mapping_errors(
    check_source: Callable[[str], TypeCheckResult], call: str, code: str
) -> None:
    result = check_source(f"fn f(a: Int, b: Int) -> None {{}}\n{call}")

    assert code in [diagnostic.code for diagnostic in result.diagnostics]


def test_non_callable_value(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("let x = 10\nx()")
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["TYPE_NOT_CALLABLE"]


@pytest.mark.parametrize(
    "call",
    [
        'send("hello", 2)',
        'send(message: "hello", priority: 2)',
        'send("hello", priority: 2)',
    ],
)
def test_positional_named_and_mixed_calls(
    check_source: Callable[[str], TypeCheckResult], call: str
) -> None:
    result = check_source(
        "fn send(message: String, priority: Int) -> None {}\n" + call
    )
    assert result.diagnostics == ()


def test_argument_parameter_mapping_preserves_ast_order(
    parse_program: Callable[[str], Program],
) -> None:
    from kaj.semantic import Resolver, TypeChecker

    program = parse_program(
        'fn send(message: String, priority: Int) -> None {}\n'
        'let x = send("hello", priority: 2)'
    )
    resolution = Resolver().resolve(program)
    result = TypeChecker(resolution).check(program)
    binding = program.statements[1]
    assert isinstance(binding, BindingDeclaration)
    call = binding.initializer
    assert isinstance(call, CallExpression)

    assert [result.parameter_for_argument(argument).name for argument in call.arguments] == [  # type: ignore[union-attr]
        "message",
        "priority",
    ]
