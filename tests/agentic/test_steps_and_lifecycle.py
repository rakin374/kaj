from __future__ import annotations

import json

import pytest

from kaj.ast import StepStatement, TaskDeclaration
from kaj.formatting import format_program
from kaj.pipeline import compile_source, parse_source
from kaj.runtime import (
    RuntimeOutput,
    StepState,
    TaskInstance,
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


def runtime_for(source: str, *, output: RuntimeOutput | None = None) -> TaskRuntime:
    compiled = compile_valid(source)
    return TaskRuntime(
        compiled.program, compiled.resolution, compiled.types, output=output
    )


def test_named_steps_parse_format_and_round_trip() -> None:
    source = "task Work() -> None { step prepare { print(1) } return none }"
    parsed = parse_source(source)
    assert parsed.diagnostics == ()
    task = parsed.program.statements[0]
    assert isinstance(task, TaskDeclaration)
    step = task.body.statements[0]
    assert isinstance(step, StepStatement)
    assert step.name == "prepare"
    formatted = format_program(parsed.program)
    assert formatted == (
        "task Work() -> None {\n"
        "    step prepare {\n"
        "        print(1)\n"
        "    }\n"
        "    return none\n"
        "}\n"
    )
    reparsed = parse_source(formatted)
    assert reparsed.diagnostics == ()
    encoded = ast_to_json(reparsed.program)
    node = json.loads(encoded)["program"]["statements"][0]["body"]["statements"][0]
    assert node["kind"] == "step_statement"
    assert set(node) == {"kind", "span", "name", "body"}
    assert ast_from_json(encoded) == reparsed.program


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ("step stray {}", "TASK_STEP_OUTSIDE_TASK"),
        (
            "fn helper() -> None { step stray {} return none }",
            "TASK_STEP_OUTSIDE_TASK",
        ),
        (
            "task Work() -> None { if true { step nested {} } return none }",
            "TASK_INVALID_STEP_PLACEMENT",
        ),
        (
            "task Work() -> None { while false { step nested {} } return none }",
            "TASK_INVALID_STEP_PLACEMENT",
        ),
        (
            (
                "task Work() -> None { match some(1) { some(v) => { step nested {} } "
                "none => {} } return none }"
            ),
            "TASK_INVALID_STEP_PLACEMENT",
        ),
    ],
)
def test_step_placement_is_rejected(source: str, code: str) -> None:
    result = parse_source(source)
    assert code in [item.code for item in result.diagnostics]


def test_missing_and_duplicate_step_names_are_rejected() -> None:
    missing = parse_source("task Work() -> None { step { } return none }")
    duplicate = compile_source(
        "task Work() -> None { step same {} step same {} return none }"
    )
    assert "PARSE_EXPECTED_IDENTIFIER" in [item.code for item in missing.diagnostics]
    assert [item.code for item in duplicate.diagnostics] == ["TASK_DUPLICATE_STEP"]


def test_step_scope_and_outer_mutation() -> None:
    valid = compile_valid(
        "task Count(seed: Int) -> Int { var count = seed "
        "step first { let amount = 1 count = count + amount } "
        "step second { count = count + 1 } return count }"
    )
    instance = TaskRuntime(valid.program, valid.resolution, valid.types).start_task("Count", [40])
    assert instance.state is TaskState.COMPLETED
    assert instance.result == 42
    escaped = compile_source(
        "task Bad() -> Int { step local { let hidden = 1 } return hidden }"
    )
    assert [item.code for item in escaped.diagnostics] == ["RESOLVE_UNKNOWN_NAME"]


def test_return_inside_step_completes_task_and_leaves_later_step_pending() -> None:
    runtime = runtime_for(
        "task Early() -> Int { step first { return 42 } "
        "step never { print(0) } return 0 }"
    )
    instance = runtime.start_task("Early")
    assert instance.state is TaskState.COMPLETED
    assert instance.result == 42
    assert instance.step("first").state is StepState.COMPLETED  # type: ignore[union-attr]
    assert instance.step("never").state is StepState.PENDING  # type: ignore[union-attr]


def test_break_continue_and_step_order() -> None:
    runtime = runtime_for(
        "task Ordered() -> Int { var total = 0 "
        "step first { for value in range(0, 5) { if value == 1 { continue } "
        "if value == 3 { break } total = total + value } } "
        "step second { total = total + 40 } return total }"
    )
    instance = runtime.start_task("Ordered")
    assert instance.result == 42
    assert [item.state for item in instance.step_executions] == [
        StepState.COMPLETED,
        StepState.COMPLETED,
    ]


def test_step_runtime_failure_fails_step_and_task() -> None:
    runtime = runtime_for(
        "task Broken() -> None { step okay {} "
        "step broken { print(1 / 0) } step never {} return none }"
    )
    instance = runtime.start_task("Broken")
    assert instance.state is TaskState.FAILED
    assert instance.failure is not None
    assert instance.failure.code == "RUNTIME_DIVISION_BY_ZERO"
    assert [item.state for item in instance.step_executions] == [
        StepState.COMPLETED,
        StepState.FAILED,
        StepState.PENDING,
    ]


class BoundaryControlOutput:
    def __init__(self, action: str) -> None:
        self.action = action
        self.runtime: TaskRuntime | None = None
        self.instance = None
        self.lines: list[str] = []
        self.observed_task_states: list[TaskState] = []
        self.observed_step_states: list[StepState] = []

    def write_line(self, text: str) -> None:
        self.lines.append(text)
        assert self.runtime is not None and self.instance is not None
        self.observed_task_states.append(self.instance.state)
        first = self.instance.step("first")
        assert first is not None
        self.observed_step_states.append(first.state)
        if self.action == "pause":
            self.runtime.request_pause(self.instance)
        elif self.action == "cancel":
            self.runtime.cancel_task(self.instance)


def controlled_runtime(
    action: str,
) -> tuple[TaskRuntime, TaskInstance, BoundaryControlOutput]:
    output = BoundaryControlOutput(action)
    runtime = runtime_for(
        'task Controlled() -> None { step first { print("first") } '
        'step second { print("second") } return none }',
        output=output,
    )
    instance = runtime.create_task("Controlled")
    output.runtime = runtime
    output.instance = instance
    return runtime, instance, output


def test_pause_at_step_boundary_and_resume_without_replay() -> None:
    runtime, instance, output = controlled_runtime("pause")
    runtime.run_task(instance)
    assert instance.state is TaskState.PAUSED
    assert output.lines == ["first"]
    assert output.observed_task_states == [TaskState.RUNNING]
    assert output.observed_step_states == [StepState.RUNNING]
    assert [item.state for item in instance.step_executions] == [
        StepState.COMPLETED,
        StepState.PENDING,
    ]
    output.action = "none"
    runtime.resume_task(instance)
    assert instance.state is TaskState.COMPLETED
    assert output.lines == ["first", "second"]


def test_cooperative_cancellation_prevents_later_steps() -> None:
    runtime, instance, output = controlled_runtime("cancel")
    runtime.run_task(instance)
    assert instance.state is TaskState.CANCELLED
    assert instance.failure is None
    assert output.lines == ["first"]
    assert instance.step("second").state is StepState.PENDING  # type: ignore[union-attr]
    with pytest.raises(TaskStartError) as terminal:
        runtime.resume_task(instance)
    assert terminal.value.code == "TASK_INVALID_STATE_TRANSITION"


def test_created_ready_and_terminal_transition_validation() -> None:
    runtime = runtime_for("task Empty() -> None { return none }")
    created = runtime.create_task("Empty")
    assert created.state is TaskState.CREATED
    runtime.ready_task(created)
    assert created.state is TaskState.READY
    runtime.run_task(created)
    assert created.state is TaskState.COMPLETED
    with pytest.raises(TaskStartError) as terminal:
        runtime.cancel_task(created)
    assert terminal.value.code == "TASK_INVALID_STATE_TRANSITION"
    cancelled = runtime.create_task("Empty")
    runtime.cancel_task(cancelled)
    assert cancelled.state is TaskState.CANCELLED
    ready_cancelled = runtime.create_task("Empty")
    runtime.ready_task(ready_cancelled)
    runtime.cancel_task(ready_cancelled)
    assert ready_cancelled.state is TaskState.CANCELLED


def test_paused_task_can_be_cancelled_and_step_transitions_are_validated() -> None:
    runtime, instance, _ = controlled_runtime("pause")
    runtime.run_task(instance)
    assert instance.state is TaskState.PAUSED
    runtime.cancel_task(instance)
    assert instance.state is TaskState.CANCELLED
    first = instance.step("first")
    assert first is not None
    with pytest.raises(TaskStartError) as step_terminal:
        first._transition(StepState.RUNNING)
    assert step_terminal.value.code == "TASK_INVALID_STEP_STATE_TRANSITION"
