from __future__ import annotations

import json
from pathlib import Path

from kaj.ast import PlanRegion, TaskDeclaration
from kaj.formatting import format_program
from kaj.pipeline import compile_source, parse_source
from kaj.runtime import AGENTIC_CONFORMANCE_VERSION, PlannerProposal
from kaj.serialization import ast_from_json, ast_to_json

from .host import DeterministicPlanner, DeterministicTestHost

FIXTURES = Path(__file__).parent / "fixtures"


def _keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {key for item in value.values() for key in _keys(item)}
    if isinstance(value, list):
        return {key for item in value for key in _keys(item)}
    return set()


def _plan(source: str) -> PlannerProposal:
    parsed = parse_source(f"task P() -> None {{ plan {{ {source} }} return none }}")
    assert parsed.diagnostics == ()
    task = parsed.program.statements[0]
    assert isinstance(task, TaskDeclaration)
    region = next(item for item in task.body.statements if isinstance(item, PlanRegion))
    return PlannerProposal(region.body)


def test_all_positive_agentic_conformance_fixtures_compile_and_format() -> None:
    paths = sorted(FIXTURES.glob("**/*.kaj"))
    assert len(paths) == 10
    for path in paths:
        source = path.read_text(encoding="utf-8")
        compiled = compile_source(source)
        assert compiled.diagnostics == (), path
        formatted = format_program(compiled.program)
        reparsed = parse_source(formatted)
        assert reparsed.diagnostics == (), path
        assert format_program(reparsed.program) == formatted
        assert ast_from_json(ast_to_json(compiled.program)) == compiled.program


def test_source_ast_json_is_deterministic_and_runtime_state_free() -> None:
    source = """capability C { fn read() -> Int }
task Child() -> Int { return 1 }
task All() -> Int {
    goal "all nodes"
    require { true }
    invariant { true }
    success(result: Int) { result > 0 }
    use C as c
    step work { let child = start Child() let value = await child }
    plan {}
    return c.read()
}
"""
    result = compile_source(source)
    assert result.diagnostics == ()
    first = ast_to_json(result.program)
    assert ast_to_json(ast_from_json(first)) == first
    forbidden = {
        "task_id",
        "interaction_id",
        "capability_request_id",
        "planning_attempt_id",
        "task_state",
        "step_state",
        "runtime_result",
        "snapshot",
        "host_binding_id",
        "plan_revision",
    }
    assert _keys(json.loads(first)).isdisjoint(forbidden)


def test_conformance_version_and_structured_event_trace() -> None:
    assert AGENTIC_CONFORMANCE_VERSION == "Agentic Kaj Conformance 1"
    host = DeterministicTestHost(
        "task P() -> Int { goal \"work\" plan {} return 42 }",
        DeterministicPlanner([_plan("step work { let value = 1 }")]),
    )
    task = host.runtime.start_task("P")
    assert task.result == 42
    kinds = host.event_kinds()
    assert kinds[0] == "task_created"
    assert "planner_requested" in kinds
    assert "plan_accepted" in kinds
    assert "step_started" in kinds and "step_completed" in kinds
    assert kinds[-1] == "task_completed"
    assert [event.sequence for event in host.recorded_events] == list(
        range(1, len(host.recorded_events) + 1)
    )


def test_negative_fixture_freezes_stable_diagnostic_codes() -> None:
    expected = json.loads((FIXTURES / "negative" / "expectations.json").read_text())
    assert expected == {
        "stale_human_response": "TASK_INTERACTION_STALE",
        "stale_capability_response": "CAPABILITY_REQUEST_STALE",
        "stale_planner_response": "PLANNER_ATTEMPT_STALE",
        "corrupt_snapshot": "TASK_PERSISTENCE_CORRUPT",
        "definition_mismatch": "TASK_DEFINITION_MISMATCH",
    }
