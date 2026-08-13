from __future__ import annotations

import json
from decimal import Decimal

import pytest

from kaj.pipeline import compile_source
from kaj.runtime import (
    InMemoryTaskStore,
    JSONDirectoryTaskStore,
    KajValueCodec,
    StepState,
    TaskInstance,
    TaskPersistenceError,
    TaskRuntime,
    TaskStartError,
    TaskState,
)


def compiled(source: str):  # type: ignore[no-untyped-def]
    result = compile_source(source)
    assert result.diagnostics == ()
    assert result.resolution is not None
    assert result.types is not None
    return result


def runtime_for(source: str, store=None, output=None):  # type: ignore[no-untyped-def]
    result = compiled(source)
    return TaskRuntime(
        result.program,
        result.resolution,
        result.types,
        store=store,
        output=output,
    )


def test_value_codec_preserves_scalars_exactly_and_rejects_native_objects() -> None:
    result = compiled("task T() -> None { return none }")
    codec = KajValueCodec(result.types)
    values = (True, 10**100, Decimal("1.23000000000000000001"), "héllo", b"\x00\xff", None)
    assert tuple(codec.decode(codec.encode(value)) for value in values) == values
    with pytest.raises(TaskPersistenceError) as failure:
        codec.encode(object())  # type: ignore[arg-type]
    assert failure.value.code == "TASK_PERSISTENCE_VALUE_NOT_SERIALIZABLE"


@pytest.mark.parametrize(
    "source",
    [
        "task T() -> List<Int> { return [1, 2] }",
        'task T() -> Map<String, Int> { return {"x": 1} }',
        "task T() -> Optional<Int> { return some(2) }",
        "task T() -> Result<Int, String> { return ok(2) }",
        "type R { value: Int } task T() -> R { return R { value: 2 } }",
        "enum E { item(value: Int) } task T() -> E { return E.item(value: 2) }",
        "newtype UserId = Int task T() -> UserId { return UserId(2) }",
    ],
)
def test_value_codec_preserves_composite_and_nominal_values(source: str) -> None:
    result = compiled(source)
    instance = TaskRuntime(result.program, result.resolution, result.types).start_task("T")
    codec = KajValueCodec(result.types)
    assert codec.decode(codec.encode(instance.result)) == instance.result


def test_snapshot_round_trip_and_restart_after_creation() -> None:
    store = InMemoryTaskStore()
    source = "task Add(value: Int) -> Int { return value + 1 }"
    first = runtime_for(source, store)
    instance = first.create_task("Add", [41])
    snapshot = store.load(str(instance.id))
    assert snapshot.schema_version == 1
    assert snapshot.task_id == str(instance.id)
    assert snapshot.task_definition_fingerprint

    second = runtime_for(source, store)
    restored = second.restore_task(instance.id)
    assert restored.id == instance.id
    second.resume_task(restored)
    assert restored.state is TaskState.COMPLETED
    assert restored.result == 42


def test_waiting_interaction_identity_and_continuation_survive_restart() -> None:
    store = InMemoryTaskStore()
    source = (
        'task Review() -> Int { step collect { let value = ask<Int>("Number?") '
        "inform(String(value)) } return 42 }"
    )
    first = runtime_for(source, store)
    original = first.start_task("Review")
    interaction = original.pending_interaction
    assert interaction is not None

    second = runtime_for(source, store)
    restored = second.restore_task(original.id)
    pending = second.get_pending_interaction(restored.id)
    assert restored.state.value == TaskState.WAITING_FOR_HUMAN.value
    assert pending is not None
    assert pending.id == interaction.id
    second.respond_to_interaction(restored.id, pending.id, 7)
    assert restored.state is TaskState.COMPLETED
    assert restored.result == 42
    assert restored.inform_events == ["7"]

    third = runtime_for(source, store)
    finished = third.restore_task(restored.id)
    with pytest.raises(TaskStartError) as duplicate:
        third.respond_to_interaction(finished.id, pending.id, 8)
    assert duplicate.value.code == "TASK_INTERACTION_ALREADY_COMPLETED"


class CrashOutput:
    def __init__(self, crash_on: str) -> None:
        self.crash_on = crash_on
        self.lines: list[str] = []

    def write_line(self, text: str) -> None:
        self.lines.append(text)
        if text == self.crash_on:
            raise SystemExit("simulated process crash")


def test_crash_replays_incomplete_step_but_not_committed_prior_step() -> None:
    store = InMemoryTaskStore()
    source = (
        'task Work() -> Int { var total = 0 step first { total = total + 1 print("first") } '
        'step second { total = total + 10 print("second") } return total }'
    )
    crashing = CrashOutput("second")
    first = runtime_for(source, store, crashing)
    instance = first.create_task("Work")
    with pytest.raises(SystemExit):
        first.run_task(instance)
    assert crashing.lines == ["first", "second"]

    recovered_output = CrashOutput("never")
    second = runtime_for(source, store, recovered_output)
    restored = second.restore_task(instance.id)
    assert restored.state is TaskState.READY
    assert restored.step("first") is not None
    assert restored.step("first").state is StepState.COMPLETED
    assert restored.step("second") is not None
    assert restored.step("second").state is StepState.PENDING
    second.resume_task(restored)
    assert restored.result == 11
    assert recovered_output.lines == ["second"]


def test_terminal_states_restore_without_execution() -> None:
    store = InMemoryTaskStore()
    source = "task Done() -> Int { return 42 }"
    first = runtime_for(source, store)
    complete = first.start_task("Done")
    second = runtime_for(source, store)
    restored = second.restore_task(complete.id)
    assert restored.state is TaskState.COMPLETED
    assert restored.result == 42
    with pytest.raises(TaskStartError):
        second.resume_task(restored)


def test_failed_and_cancelled_terminal_states_persist() -> None:
    failed_store = InMemoryTaskStore()
    failed_source = "task Broken() -> Decimal { return 1 / 0 }"
    failed = runtime_for(failed_source, failed_store).start_task("Broken")
    restored_failed = runtime_for(failed_source, failed_store).restore_task(failed.id)
    assert restored_failed.state is TaskState.FAILED
    assert restored_failed.failure is not None
    assert restored_failed.failure.code == "RUNTIME_DIVISION_BY_ZERO"

    cancelled_store = InMemoryTaskStore()
    cancelled_source = 'task Cancelled() -> Bool { return confirm("Continue?") }'
    first = runtime_for(cancelled_source, cancelled_store)
    cancelled = first.start_task("Cancelled")
    first.cancel_task(cancelled)
    restored_cancelled = runtime_for(cancelled_source, cancelled_store).restore_task(cancelled.id)
    assert restored_cancelled.state is TaskState.CANCELLED
    assert restored_cancelled.pending_interaction is None


class PauseOutput:
    runtime: TaskRuntime
    instance: TaskInstance

    def write_line(self, text: str) -> None:
        self.runtime.request_pause(self.instance)


def test_paused_task_restores_paused_until_explicit_resume() -> None:
    store = InMemoryTaskStore()
    output = PauseOutput()
    source = (
        'task Work() -> Int { var value = 0 step first { value = 1 print("pause") } '
        "step second { value = value + 1 } return value }"
    )
    first = runtime_for(source, store, output)
    instance = first.create_task("Work")
    output.runtime = first
    output.instance = instance
    first.run_task(instance)
    assert instance.state is TaskState.PAUSED

    second = runtime_for(source, store)
    restored = second.restore_task(instance.id)
    assert restored.state.value == TaskState.PAUSED.value
    assert restored.step("first") is not None
    assert restored.step("first").state is StepState.COMPLETED
    second.resume_task(restored)
    assert restored.state is TaskState.COMPLETED
    assert restored.result == 2


class FailStepCommitStore(InMemoryTaskStore):
    def save(self, snapshot):  # type: ignore[no-untyped-def]
        if any(state == StepState.COMPLETED.value for _, state in snapshot.step_states):
            raise TaskPersistenceError("TASK_PERSISTENCE_WRITE_FAILED", "simulated write failure")
        super().save(snapshot)


def test_failed_step_commit_is_not_treated_as_durable() -> None:
    store = FailStepCommitStore()
    source = 'task Work() -> Int { step work { print("work") } return 42 }'
    first = runtime_for(source, store)
    instance = first.create_task("Work")
    with pytest.raises(TaskPersistenceError) as failure:
        first.run_task(instance)
    assert failure.value.code == "TASK_PERSISTENCE_WRITE_FAILED"

    second = runtime_for(source, store)
    restored = second.restore_task(instance.id)
    assert restored.step("work") is not None
    assert restored.step("work").state is StepState.PENDING


def test_definition_mismatch_is_rejected() -> None:
    store = InMemoryTaskStore()
    original = runtime_for("task T() -> Int { return 1 }", store).create_task("T")
    changed = runtime_for("task T() -> Int { return 2 }", store)
    with pytest.raises(TaskPersistenceError) as failure:
        changed.restore_task(original.id)
    assert failure.value.code == "TASK_DEFINITION_MISMATCH"


def test_atomic_json_store_and_corrupt_or_unsupported_snapshots(tmp_path) -> None:  # type: ignore[no-untyped-def]
    store = JSONDirectoryTaskStore(tmp_path)
    source = "task T() -> None { return none }"
    instance = runtime_for(source, store).create_task("T")
    assert store.load(str(instance.id)).task_id == str(instance.id)

    path = tmp_path / f"{instance.id}.json"
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(TaskPersistenceError) as corrupt:
        store.load(str(instance.id))
    assert corrupt.value.code == "TASK_PERSISTENCE_CORRUPT"

    path.write_text(json.dumps({"schema_version": 999}), encoding="utf-8")
    with pytest.raises(TaskPersistenceError) as unsupported:
        store.load(str(instance.id))
    assert unsupported.value.code == "TASK_PERSISTENCE_VERSION_UNSUPPORTED"
