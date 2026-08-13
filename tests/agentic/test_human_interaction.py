from __future__ import annotations

import json

import pytest

from kaj.ast import HumanInteractionExpression
from kaj.formatting import format_program
from kaj.pipeline import compile_source, parse_source
from kaj.runtime import (
    BufferOutput,
    InteractionKind,
    InteractionStatus,
    StepState,
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


def runtime_for(source: str) -> TaskRuntime:
    result = compile_valid(source)
    return TaskRuntime(result.program, result.resolution, result.types)


@pytest.mark.parametrize(
    "source",
    [
        'task T() -> String { return ask<String>("Name?") }',
        'task T() -> Int { return ask<Int>("Age?") }',
        'task T() -> String { return choose<String>("Color?", ["red", "blue"]) }',
        'task T() -> Bool { return confirm("Continue?") }',
        'task T() -> None { inform("Done") return none }',
        'task T() -> None { handoff("Complete setup") return none }',
    ],
)
def test_interaction_syntax_types_and_format_round_trip(source: str) -> None:
    compiled = compile_valid(source)
    formatted = format_program(compiled.program)
    reparsed = parse_source(formatted)
    assert reparsed.diagnostics == ()
    assert format_program(reparsed.program) == formatted
    encoded = ast_to_json(reparsed.program)
    assert "human_interaction_expression" in encoded
    assert "interaction_id" not in encoded
    assert ast_from_json(encoded) == reparsed.program


def test_interaction_ast_json_has_only_source_fields() -> None:
    parsed = parse_source('task T() -> String { return ask<String>("Name?") }')
    returned = parsed.program.statements[0].body.statements[0]  # type: ignore[attr-defined]
    expression = returned.value  # type: ignore[attr-defined]
    assert isinstance(expression, HumanInteractionExpression)
    node = json.loads(ast_to_json(parsed.program))["program"]["statements"][0]["body"][
        "statements"
    ][0]["value"]
    assert set(node) == {
        "kind",
        "span",
        "interaction_kind",
        "type_argument",
        "arguments",
    }


@pytest.mark.parametrize(
    ("source", "code"),
    [
        (
            'fn Bad() -> String { return ask<String>("Name?") }',
            "TASK_HUMAN_INTERACTION_OUTSIDE_TASK",
        ),
        (
            'task Bad() -> None { require { confirm("Okay?") } return none }',
            "TASK_HUMAN_INTERACTION_IN_CONTRACT",
        ),
        (
            "task Bad() -> String { return ask<String>(42) }",
            "TASK_INTERACTION_PROMPT_TYPE_MISMATCH",
        ),
        (
            'task Bad() -> Int { return choose<Int>("Pick", ["wrong"]) }',
            "TYPE_MISMATCH",
        ),
        (
            'task Bad() -> Int { return choose<Int>("Pick", []) }',
            "TASK_CHOOSE_EMPTY_OPTIONS",
        ),
    ],
)
def test_static_restrictions(source: str, code: str) -> None:
    result = compile_source(source)
    assert code in [item.code for item in result.diagnostics]


def test_interaction_arity_is_diagnosed() -> None:
    result = compile_source('task Bad() -> Bool { return confirm("one", "two") }')
    assert "TYPE_ARGUMENT_COUNT_MISMATCH" in [item.code for item in result.diagnostics]


@pytest.mark.parametrize(
    ("source", "kind"),
    [
        ('task T() -> String { return ask<String>("Name?") }', InteractionKind.ASK),
        (
            'task T() -> String { return choose<String>("Color?", ["red"]) }',
            InteractionKind.CHOOSE,
        ),
        ('task T() -> Bool { return confirm("Continue?") }', InteractionKind.CONFIRM),
        ('task T() -> None { handoff("Finish") return none }', InteractionKind.HANDOFF),
    ],
)
def test_blocking_interactions_wait_and_are_inspectable(
    source: str, kind: InteractionKind
) -> None:
    runtime = runtime_for(source)
    instance = runtime.start_task("T")
    interaction = runtime.get_pending_interaction(instance.id)
    assert instance.state is TaskState.WAITING_FOR_HUMAN
    assert interaction is instance.pending_interaction
    assert interaction is not None
    assert interaction.kind is kind
    assert interaction.status is InteractionStatus.PENDING
    assert str(interaction.id)


def test_ask_validates_response_and_resumes_exactly_once() -> None:
    runtime = runtime_for(
        'task Ask() -> String { let name = ask<String>("Name?") '
        'inform("received {name}") return name }'
    )
    instance = runtime.start_task("Ask")
    interaction = instance.pending_interaction
    assert interaction is not None
    with pytest.raises(TaskStartError) as invalid:
        runtime.respond_to_interaction(instance.id, interaction.id, 42)
    assert invalid.value.code == "TASK_INTERACTION_RESPONSE_TYPE_MISMATCH"
    assert instance.state is TaskState.WAITING_FOR_HUMAN
    assert interaction.status is InteractionStatus.PENDING
    runtime.respond_to_interaction(instance.id, interaction.id, "Kaj")
    assert instance.state is TaskState.COMPLETED
    assert instance.result == "Kaj"
    assert instance.inform_events == ["received Kaj"]
    assert len(instance.interactions) == 1


def test_suspended_statement_does_not_duplicate_prior_effects_on_resume() -> None:
    compiled = compile_valid(
        'task Once() -> String { step work { print("before") '
        'let name = ask<String>("Name?") print(name) return name } return "never" }'
    )
    output = BufferOutput()
    runtime = TaskRuntime(
        compiled.program, compiled.resolution, compiled.types, output=output
    )
    instance = runtime.start_task("Once")
    assert output.text == ""
    assert instance.pending_interaction is not None
    runtime.respond_to_interaction(
        instance.id, instance.pending_interaction.id, "Kaj"
    )
    assert output.text == "before\nKaj\n"


def test_choose_requires_membership() -> None:
    runtime = runtime_for(
        'task Choose() -> String { return choose<String>("Color?", ["red", "blue"]) }'
    )
    instance = runtime.start_task("Choose")
    interaction = instance.pending_interaction
    assert interaction is not None
    assert interaction.options == ("red", "blue")
    with pytest.raises(TaskStartError) as invalid:
        runtime.respond_to_interaction(instance.id, interaction.id, "green")
    assert invalid.value.code == "TASK_CHOOSE_RESPONSE_INVALID"
    assert instance.state is TaskState.WAITING_FOR_HUMAN
    runtime.respond_to_interaction(instance.id, interaction.id, "blue")
    assert instance.result == "blue"


@pytest.mark.parametrize(("response", "expected"), [(True, True), (False, False)])
def test_confirm_responses(response: bool, expected: bool) -> None:
    runtime = runtime_for('task Confirm() -> Bool { return confirm("Continue?") }')
    instance = runtime.start_task("Confirm")
    assert instance.pending_interaction is not None
    runtime.respond_to_interaction(
        instance.id, instance.pending_interaction.id, response
    )
    assert instance.state is TaskState.COMPLETED
    assert instance.result is expected


def test_handoff_completion_and_inform_nonblocking() -> None:
    runtime = runtime_for(
        'task Flow() -> None { inform("starting") handoff("Do it") inform("done") return none }'
    )
    instance = runtime.start_task("Flow")
    interaction = instance.pending_interaction
    assert interaction is not None
    assert instance.inform_events == ["starting"]
    runtime.complete_handoff(instance.id, interaction.id)
    assert instance.state is TaskState.COMPLETED
    assert instance.inform_events == ["starting", "done"]


def test_step_remains_running_and_later_step_waits() -> None:
    runtime = runtime_for(
        'task Steps() -> None { step approval { confirm("Proceed?") } '
        'step later { inform("later") } return none }'
    )
    instance = runtime.start_task("Steps")
    assert instance.state is TaskState.WAITING_FOR_HUMAN
    assert instance.step("approval").state is StepState.RUNNING  # type: ignore[union-attr]
    assert instance.step("later").state is StepState.PENDING  # type: ignore[union-attr]
    interaction = instance.pending_interaction
    assert interaction is not None
    runtime.respond_to_interaction(instance.id, interaction.id, True)
    assert instance.step("approval").state is StepState.COMPLETED  # type: ignore[union-attr]
    assert instance.step("later").state is StepState.COMPLETED  # type: ignore[union-attr]


def test_interaction_cancellation_cancels_task() -> None:
    runtime = runtime_for('task T() -> String { return ask<String>("Name?") }')
    instance = runtime.start_task("T")
    interaction = instance.pending_interaction
    assert interaction is not None
    runtime.cancel_interaction(instance.id, interaction.id)
    assert interaction.status is InteractionStatus.CANCELLED
    assert instance.state is TaskState.CANCELLED
    assert instance.failure is None


def test_stale_duplicate_unknown_and_wrong_task_responses_are_rejected() -> None:
    runtime = runtime_for('task T() -> String { return ask<String>("Name?") }')
    first = runtime.start_task("T")
    second = runtime.start_task("T")
    one = first.pending_interaction
    two = second.pending_interaction
    assert one is not None and two is not None and one.id != two.id
    with pytest.raises(TaskStartError) as wrong_task:
        runtime.respond_to_interaction(first.id, two.id, "wrong")
    assert wrong_task.value.code == "TASK_INTERACTION_STALE"
    with pytest.raises(TaskStartError) as unknown:
        runtime.respond_to_interaction("missing", one.id, "wrong")
    assert unknown.value.code == "TASK_INTERACTION_NOT_FOUND"
    runtime.respond_to_interaction(first.id, one.id, "done")
    with pytest.raises(TaskStartError) as duplicate:
        runtime.respond_to_interaction(first.id, one.id, "again")
    assert duplicate.value.code == "TASK_INTERACTION_ALREADY_COMPLETED"
