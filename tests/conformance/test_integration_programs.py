from __future__ import annotations

import io
from pathlib import Path

from kaj.cli import EXIT_SUCCESS, cli_main
from kaj.formatting import format_program
from kaj.pipeline import parse_source

from .helpers import run_ok

SINGLE_MODULE_PROGRAM = """newtype UserId = String
type User { id: UserId name: String scores: List<Int> }
enum Status { active inactive(reason: String) }

fn total(values: List<Int>) -> Int {
    var result = 0
    for value in values { result += value }
    return result
}

let user = User { id: UserId("u1"), name: "Kaj", scores: [10, 20] }
let status: Optional<Status> = some(Status.active)
let outcome: Result<Int, String> = ok(total(user.scores))
let labels: Map<String, Int> = {"score": total(user.scores)}
match status { some(value) => match value { active => print(user.name) inactive(reason) => print(reason) } none => print("none") }
match outcome { ok(value) => print(value) err(message) => print(message) }
match labels["score"] { some(value) => print(value) none => print(0) }
print(user.id.value)
"""


def invoke(arguments: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = cli_main(arguments, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def test_full_single_module_program_formats_compiles_and_runs() -> None:
    parsed = parse_source(SINGLE_MODULE_PROGRAM)
    assert tuple(item.code for item in parsed.diagnostics) == ()
    formatted = format_program(parsed.program)
    reparsed = parse_source(formatted)
    assert tuple(item.code for item in reparsed.diagnostics) == ()
    assert format_program(reparsed.program) == formatted
    assert run_ok(formatted).stdout == "Kaj\n30\n30\nu1\n"


def test_full_multi_module_project_checks_and_runs(tmp_path: Path) -> None:
    (tmp_path / "domain.kaj").write_text(
        """newtype UserId = String
type User { id: UserId name: String }
enum State { ready blocked(reason: String) }
fn user(name: String) -> User { return User { id: UserId(name), name: name } }
""",
        encoding="utf-8",
    )
    (tmp_path / "service.kaj").write_text(
        """import domain
fn describe(user: domain.User, state: domain.State) -> String {
    match state { ready => return user.name blocked(reason) => return reason }
}
""",
        encoding="utf-8",
    )
    entry = tmp_path / "main.kaj"
    entry.write_text(
        """import domain
import service
let user: domain.User = domain.user("Kaj")
let state: domain.State = domain.State.ready
print(service.describe(user, state))
print(user.id.value)
""",
        encoding="utf-8",
    )
    assert invoke(["check", str(entry)]) == (EXIT_SUCCESS, "", "")
    assert invoke(["run", str(entry)]) == (EXIT_SUCCESS, "Kaj\nKaj\n", "")
