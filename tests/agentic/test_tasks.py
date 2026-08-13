from __future__ import annotations

import json
from io import StringIO

import pytest

from kaj.ast import TaskDeclaration
from kaj.cli import EXIT_RUNTIME_ERROR, EXIT_SUCCESS, cli_main
from kaj.formatting import format_program
from kaj.pipeline import compile_source, parse_source
from kaj.runtime import (
    BufferOutput,
    Interpreter,
    KajEnumValue,
    TaskRuntime,
    TaskStartError,
    TaskState,
)
from kaj.serialization import ast_from_json, ast_to_json


def compile_valid(source: str):  # type: ignore[no-untyped-def]
    result = compile_source(source)
    assert result.diagnostics == ()
    assert result.resolution is not None
    assert result.types is not None
    return result


def test_task_parses_formats_and_round_trips_through_ast_json() -> None:
    source = "task Add(a: Int, var b: Int) -> Int { return a + b }"
    parsed = parse_source(source)
    assert parsed.diagnostics == ()
    declaration = parsed.program.statements[0]
    assert isinstance(declaration, TaskDeclaration)
    assert declaration.name == "Add"
    assert [parameter.mutable for parameter in declaration.parameters] == [False, True]
    assert format_program(parsed.program) == (
        "task Add(a: Int, var b: Int) -> Int {\n"
        "    return a + b\n"
        "}\n"
    )
    encoded = ast_to_json(parsed.program)
    payload = json.loads(encoded)
    node = payload["program"]["statements"][0]
    assert node["kind"] == "task_declaration"
    assert set(node) == {"kind", "span", "name", "parameters", "return_type", "body"}
    assert ast_from_json(encoded) == parsed.program


def test_nested_task_is_rejected() -> None:
    result = parse_source("fn outer() -> None { task Inner() -> None { return none } }")
    assert [item.code for item in result.diagnostics] == ["PARSE_UNEXPECTED_TOKEN"]


@pytest.mark.parametrize(
    "source",
    [
        "task Same() -> None { return none } fn Same() -> None { return none }",
        "fn Same() -> None { return none } task Same() -> None { return none }",
        "task Same() -> None { return none } task Same() -> None { return none }",
    ],
)
def test_tasks_share_the_module_value_namespace(source: str) -> None:
    result = compile_source(source)
    assert [item.code for item in result.diagnostics] == ["RESOLVE_DUPLICATE_NAME"]


def test_task_body_may_call_function() -> None:
    compile_valid(
        "fn double(value: Int) -> Int { return value * 2 } "
        "task Compute() -> Int { return double(21) }"
    )


@pytest.mark.parametrize(
    "source",
    [
        "task Work() -> None { return none } fn bad() -> None { Work() return none }",
        "task First() -> None { return none } task Second() -> None { First() return none }",
        "task Recur() -> None { Recur() return none }",
    ],
)
def test_ordinary_call_syntax_cannot_invoke_tasks(source: str) -> None:
    result = compile_source(source)
    assert [item.code for item in result.diagnostics] == ["TASK_CANNOT_CALL_AS_FUNCTION"]


def test_task_uses_function_return_checking() -> None:
    wrong = compile_source('task Wrong() -> Int { return "no" }')
    missing = compile_source("task Missing() -> Int { let value = 1 }")
    assert [item.code for item in wrong.diagnostics] == ["TYPE_MISMATCH"]
    assert [item.code for item in missing.diagnostics] == ["TYPE_MISSING_RETURN"]


def test_declaration_does_not_execute_during_normal_interpretation() -> None:
    compiled = compile_valid(
        'task Quiet() -> None { print("task ran") return none } print("module ran")'
    )
    execution = Interpreter(compiled.resolution, compiled.types).interpret(compiled.program)
    assert execution.runtime_error is None
    assert execution.output == "module ran\n"


def test_runtime_creates_distinct_completed_instances_and_validates_arguments() -> None:
    compiled = compile_valid("task Add(a: Int, b: Int) -> Int { return a + b }")
    runtime = TaskRuntime(compiled.program, compiled.resolution, compiled.types)
    first = runtime.start_task("Add", [20, 22])
    second = runtime.start_task("Add", [1, 2])
    assert first.state is TaskState.COMPLETED
    assert first.result == 42
    assert first.failure is None
    assert second.result == 3
    assert first.id != second.id
    with pytest.raises(TaskStartError, match="expects 2 arguments") as count:
        runtime.start_task("Add", [1])
    assert count.value.code == "TASK_ARGUMENT_COUNT_MISMATCH"
    with pytest.raises(TaskStartError) as argument_type:
        runtime.start_task("Add", ["one", 2])
    assert argument_type.value.code == "TASK_ARGUMENT_TYPE_MISMATCH"


def test_result_err_is_completed_domain_value() -> None:
    compiled = compile_valid(
        'task ExpectedFailure() -> Result<Int, String> { return err("not found") }'
    )
    instance = TaskRuntime(
        compiled.program, compiled.resolution, compiled.types
    ).start_task("ExpectedFailure")
    assert instance.state is TaskState.COMPLETED
    assert isinstance(instance.result, KajEnumValue)
    assert instance.result.variant == "err"
    assert instance.failure is None


def test_runtime_error_marks_task_failed() -> None:
    compiled = compile_valid("task Divide() -> Decimal { return 1 / 0 }")
    instance = TaskRuntime(compiled.program, compiled.resolution, compiled.types).start_task(
        "Divide"
    )
    assert instance.state is TaskState.FAILED
    assert instance.result is None
    assert instance.failure is not None
    assert instance.failure.code == "RUNTIME_DIVISION_BY_ZERO"


def test_cli_runs_zero_argument_task_without_printing_result(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "hello.kaj"
    path.write_text(
        'task Hello() -> Int { print("Hello from a Kaj task") return 42 }',
        encoding="utf-8",
    )
    stdout = StringIO()
    stderr = StringIO()
    assert cli_main(["task", "run", str(path), "Hello"], stdout=stdout, stderr=stderr) == EXIT_SUCCESS
    assert stdout.getvalue() == "Hello from a Kaj task\n"
    assert stderr.getvalue() == ""


def test_cli_reports_unknown_task_without_traceback(tmp_path) -> None:  # type: ignore[no-untyped-def]
    path = tmp_path / "hello.kaj"
    path.write_text("task Hello() -> None { return none }", encoding="utf-8")
    stderr = StringIO()
    assert cli_main(["task", "run", str(path), "Missing"], stderr=stderr) == EXIT_RUNTIME_ERROR
    assert "TASK_NOT_FOUND" in stderr.getvalue()
    assert "Traceback" not in stderr.getvalue()


def test_task_output_uses_injected_runtime_output() -> None:
    compiled = compile_valid('task Hello() -> None { print("hello") return none }')
    output = BufferOutput()
    instance = TaskRuntime(
        compiled.program, compiled.resolution, compiled.types, output=output
    ).start_task("Hello")
    assert instance.state is TaskState.COMPLETED
    assert output.text == "hello\n"
