from collections.abc import Callable

from kaj.runtime import ExecutionResult
from kaj.semantic import PrimitiveType, SymbolKind

from .conftest import PipelineResult


def execution(result: PipelineResult) -> ExecutionResult:
    assert result.execution is not None
    assert result.execution.runtime_error is None
    return result.execution


def test_print_builtin_is_explicitly_resolved(
    run_source: Callable[[str], PipelineResult],
) -> None:
    result = run_source("print(1)")
    print_symbol = result.resolution.module_scope.lookup("print")

    assert print_symbol is not None
    assert print_symbol.kind is SymbolKind.BUILTIN_FUNCTION
    assert result.types.type_of_symbol(print_symbol) is not None
    assert execution(result).output == "1\n"


def test_primitive_print_formatting(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source(
        'print(true)\nprint(false)\nprint(123456789012345678901234567890)\n'
        'print(19.990)\nprint("héllo")\nprint(none)'
    )

    assert execution(result).output == (
        "true\nfalse\n123456789012345678901234567890\n19.990\nhéllo\nnone\n"
    )


def test_print_returns_none(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source('let value = print("hello")')
    value = result.resolution.module_scope.lookup_local("value")
    assert value is not None

    assert result.types.type_of_symbol(value) is PrimitiveType.NONE
    assert execution(result).output == "hello\n"


def test_print_arity_and_named_arguments_are_checked(
    run_source: Callable[[str], PipelineResult],
) -> None:
    missing = run_source("print()")
    named = run_source("print(value: 1)")
    extra = run_source("print(1, 2)")

    assert [item.code for item in missing.types.diagnostics] == ["TYPE_MISSING_ARGUMENT"]
    assert [item.code for item in named.types.diagnostics] == [
        "TYPE_UNKNOWN_NAMED_ARGUMENT"
    ]
    assert [item.code for item in extra.types.diagnostics] == [
        "TYPE_TOO_MANY_ARGUMENTS"
    ]


def test_module_binding_shadows_print(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source("let print = 10\nprint(1)")

    assert result.resolution.diagnostics == ()
    assert [item.code for item in result.types.diagnostics] == ["TYPE_NOT_CALLABLE"]
    assert result.execution is None
