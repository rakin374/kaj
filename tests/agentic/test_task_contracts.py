from __future__ import annotations

import json

import pytest

from kaj.ast import GoalClause, InvariantClause, RequireClause, SuccessClause, TaskDeclaration
from kaj.formatting import format_program
from kaj.pipeline import compile_source, parse_source
from kaj.runtime import (
    ContractFailureKind,
    KajEnumValue,
    RuntimeOutput,
    TaskInstance,
    TaskRuntime,
    TaskState,
)
from kaj.serialization import ast_from_json, ast_to_json


def compile_valid(source: str):  # type: ignore[no-untyped-def]
    result = compile_source(source)
    assert result.diagnostics == ()
    assert result.resolution is not None
    assert result.types is not None
    return result


def runtime_for(source: str, *, output: RuntimeOutput | None = None) -> TaskRuntime:
    result = compile_valid(source)
    return TaskRuntime(result.program, result.resolution, result.types, output=output)


def test_contracts_parse_format_and_round_trip() -> None:
    parsed = parse_source(
        'task Work(limit: Int) -> Int { goal "Stay below {limit}" '
        "require { limit > 0 } invariant { limit > 0 } "
        "success(result: Int) { result <= limit } return limit }"
    )
    assert parsed.diagnostics == ()
    task = parsed.program.statements[0]
    assert isinstance(task, TaskDeclaration)
    assert [type(item) for item in task.body.statements[:4]] == [
        GoalClause,
        RequireClause,
        InvariantClause,
        SuccessClause,
    ]
    formatted = format_program(parsed.program)
    assert formatted == (
        "task Work(limit: Int) -> Int {\n"
        '    goal "Stay below {limit}"\n'
        "    require {\n"
        "        limit > 0\n"
        "    }\n"
        "    invariant {\n"
        "        limit > 0\n"
        "    }\n"
        "    success(result: Int) {\n"
        "        result <= limit\n"
        "    }\n"
        "    return limit\n"
        "}\n"
    )
    encoded = ast_to_json(parsed.program)
    payload = json.loads(encoded)
    clauses = payload["program"]["statements"][0]["body"]["statements"][:4]
    assert [item["kind"] for item in clauses] == [
        "goal_clause",
        "require_clause",
        "invariant_clause",
        "success_clause",
    ]
    assert all("state" not in item and "passed" not in item for item in clauses)
    assert ast_from_json(encoded) == parsed.program
    assert format_program(parse_source(formatted).program) == formatted


@pytest.mark.parametrize(
    "source",
    [
        'goal "outside"',
        'fn Bad() -> None { goal "inside fn" return none }',
        'task Bad() -> None { step nested { require { true } } return none }',
        'task Bad() -> None { if true { invariant { true } } return none }',
        'task Bad() -> None { while false { success { true } } return none }',
        (
            "task Bad() -> None { match some(1) { some(v) => { require { true } } "
            "none => {} } return none }"
        ),
    ],
)
def test_contract_placement_is_direct_task_body_only(source: str) -> None:
    result = parse_source(source)
    assert "TASK_CONTRACT_INVALID_PLACEMENT" in [item.code for item in result.diagnostics]


def test_duplicate_goal_and_success_are_rejected_but_multiple_conditions_are_allowed() -> None:
    duplicate_goal = compile_source(
        'task Bad() -> None { goal "one" goal "two" return none }'
    )
    duplicate_success = compile_source(
        "task Bad() -> None { success { true } success { true } return none }"
    )
    multiple = compile_source(
        "task Good(x: Int) -> Int { require { x > 0 } require { x < 10 } "
        "invariant { x > 0 } invariant { x < 10 } return x }"
    )
    assert "TASK_DUPLICATE_GOAL" in [item.code for item in duplicate_goal.diagnostics]
    assert "TASK_DUPLICATE_SUCCESS" in [item.code for item in duplicate_success.diagnostics]
    assert multiple.diagnostics == ()


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ("task Bad() -> None { goal 42 return none }", "TASK_GOAL_TYPE_MISMATCH"),
        (
            "task Bad() -> None { require { 42 } return none }",
            "TASK_REQUIRE_TYPE_MISMATCH",
        ),
        (
            "task Bad() -> None { invariant { 42 } return none }",
            "TASK_INVARIANT_TYPE_MISMATCH",
        ),
        (
            "task Bad() -> None { success { 42 } return none }",
            "TASK_SUCCESS_TYPE_MISMATCH",
        ),
        (
            "task Bad() -> Int { success(result: String) { true } return 1 }",
            "TASK_SUCCESS_PARAMETER_MISMATCH",
        ),
        (
            "task Bad() -> Int { success { true } return 1 }",
            "TASK_SUCCESS_PARAMETER_MISMATCH",
        ),
        (
            "task Bad() -> None { success(result: None) { true } return none }",
            "TASK_SUCCESS_PARAMETER_MISMATCH",
        ),
    ],
)
def test_contract_typing(source: str, code: str) -> None:
    result = compile_source(source)
    assert code in [item.code for item in result.diagnostics]


def test_parameterless_none_success_and_pure_function_calls_are_valid() -> None:
    compile_valid(
        "fn positive(value: Int) -> Bool { return value > 0 } "
        "task Good(value: Int) -> None { require { positive(value) } "
        "success { true } return none }"
    )


def test_impure_function_call_is_rejected_in_contract() -> None:
    result = compile_source(
        "fn noisy(value: Int) -> Bool { print(value) return value > 0 } "
        "task Bad(value: Int) -> None { require { noisy(value) } return none }"
    )
    assert "TASK_CONTRACT_NOT_PURE" in [item.code for item in result.diagnostics]


def test_goal_is_interpolated_and_requirements_run_in_source_order() -> None:
    runtime = runtime_for(
        'task Guard(value: Int) -> Int { goal "Process {value}" '
        "require { value > 0 } require { 1 / 0 > 0 } return value }"
    )
    instance = runtime.start_task("Guard", [-1])
    assert instance.goal == "Process -1"
    assert instance.state is TaskState.FAILED
    assert instance.failure is not None
    assert instance.failure.code == "TASK_REQUIREMENT_VIOLATED"
    assert instance.failure.contract_failure is not None
    assert (
        instance.failure.contract_failure.kind
        is ContractFailureKind.REQUIREMENT_VIOLATION
    )


def test_requirement_evaluation_failure_is_structured() -> None:
    runtime = runtime_for(
        "task Broken() -> None { require { 1 / 0 > 0 } return none }"
    )
    instance = runtime.start_task("Broken")
    assert instance.state is TaskState.FAILED
    assert instance.failure is not None
    assert instance.failure.code == "TASK_CONTRACT_EVALUATION_FAILED"
    assert instance.failure.contract_failure is not None
    assert instance.failure.contract_failure.kind is ContractFailureKind.EVALUATION_FAILURE
    assert instance.failure.contract_failure.underlying_error is not None


def test_initial_and_post_step_invariants() -> None:
    initial = runtime_for(
        "task Initial() -> Int { var count = -1 invariant { count >= 0 } return count }"
    ).start_task("Initial")
    assert initial.state is TaskState.FAILED
    assert initial.failure is not None
    assert initial.failure.code == "TASK_INVARIANT_VIOLATED"

    post_step = runtime_for(
        "task PostStep() -> Int { var count = 0 invariant { count >= 0 } "
        "step break_it { count = -1 } return count }"
    ).start_task("PostStep")
    assert post_step.state is TaskState.FAILED
    assert post_step.failure is not None
    assert post_step.failure.code == "TASK_INVARIANT_VIOLATED"


def test_invariant_is_checked_before_completion_without_steps() -> None:
    instance = runtime_for(
        "task Final() -> Int { var count = 0 invariant { count >= 0 } "
        "count = -1 return count }"
    ).start_task("Final")
    assert instance.state is TaskState.FAILED
    assert instance.result == -1
    assert instance.failure is not None
    assert instance.failure.code == "TASK_INVARIANT_VIOLATED"


class PauseOutput:
    def __init__(self) -> None:
        self.runtime: TaskRuntime | None = None
        self.instance: TaskInstance | None = None

    def write_line(self, text: str) -> None:
        assert self.runtime is not None and self.instance is not None
        self.runtime.request_pause(self.instance)


def test_invariant_is_rechecked_before_resume() -> None:
    output = PauseOutput()
    compiled = compile_valid(
        'task Pausable() -> Int { var count = 0 invariant { count >= 0 } '
        'step first { print("pause") } return count }'
    )
    runtime = TaskRuntime(
        compiled.program, compiled.resolution, compiled.types, output=output
    )
    instance = runtime.create_task("Pausable")
    output.runtime = runtime
    output.instance = instance
    runtime.run_task(instance)
    assert instance.state is TaskState.PAUSED
    count_symbol = next(
        symbol
        for symbol in compiled.resolution.symbols
        if symbol.name == "count"
    )
    assert instance._context is not None
    instance._context.environment.assign(count_symbol, -1)
    runtime.resume_task(instance)
    assert instance.state is TaskState.FAILED
    assert instance.failure is not None
    assert instance.failure.code == "TASK_INVARIANT_VIOLATED"


@pytest.mark.parametrize(
    ("condition", "state", "code"),
    [
        ("true", TaskState.COMPLETED, None),
        ("false", TaskState.FAILED, "TASK_SUCCESS_NOT_SATISFIED"),
        ("1 / 0 > 0", TaskState.FAILED, "TASK_CONTRACT_EVALUATION_FAILED"),
    ],
)
def test_success_validation(
    condition: str, state: TaskState, code: str | None
) -> None:
    runtime = runtime_for(
        f"task Result() -> Int {{ success(result: Int) {{ {condition} }} return 42 }}"
    )
    instance = runtime.start_task("Result")
    assert instance.state is state
    assert instance.result == 42
    assert (None if instance.failure is None else instance.failure.code) == code


def test_no_success_and_result_err_remain_normal_completion() -> None:
    no_success = runtime_for("task Plain() -> Int { return 42 }").start_task("Plain")
    result_err = runtime_for(
        'task Domain() -> Result<Int, String> { '
        "success(result: Result<Int, String>) { true } return err(\"missing\") }"
    ).start_task("Domain")
    assert no_success.state is TaskState.COMPLETED
    assert result_err.state is TaskState.COMPLETED
    assert isinstance(result_err.result, KajEnumValue)
    assert result_err.result.variant == "err"
    assert result_err.failure is None


class CancelOutput:
    def __init__(self) -> None:
        self.runtime: TaskRuntime | None = None
        self.instance: TaskInstance | None = None

    def write_line(self, text: str) -> None:
        assert self.runtime is not None and self.instance is not None
        self.runtime.cancel_task(self.instance)


def test_cancelled_task_does_not_evaluate_success() -> None:
    output = CancelOutput()
    compiled = compile_valid(
        'task Cancel() -> Int { step first { print("cancel") } '
        "success(result: Int) { false } return 1 }"
    )
    runtime = TaskRuntime(
        compiled.program, compiled.resolution, compiled.types, output=output
    )
    instance = runtime.create_task("Cancel")
    output.runtime = runtime
    output.instance = instance
    runtime.run_task(instance)
    assert instance.state is TaskState.CANCELLED
    assert instance.failure is None
    assert instance.result is None
