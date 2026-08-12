from __future__ import annotations

import io
from pathlib import Path

import pytest

from kaj.cli import EXIT_SUCCESS, cli_main

EXAMPLES = Path(__file__).parents[2] / "examples"
ENTRY_EXAMPLES = tuple(sorted(EXAMPLES.glob("*.kaj"))) + (
    EXAMPLES / "modules" / "main.kaj",
) + tuple(sorted((EXAMPLES / "apps").glob("**/main.kaj")))


def invoke(command: str, path: Path) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = cli_main([command, str(path)], stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


@pytest.mark.parametrize("path", ENTRY_EXAMPLES, ids=lambda path: str(path.relative_to(EXAMPLES)))
def test_documented_example_checks(path: Path) -> None:
    assert invoke("check", path) == (EXIT_SUCCESS, "", "")


@pytest.mark.parametrize("path", ENTRY_EXAMPLES, ids=lambda path: str(path.relative_to(EXAMPLES)))
def test_documented_example_runs_without_diagnostics(path: Path) -> None:
    code, _, stderr = invoke("run", path)
    assert code == EXIT_SUCCESS
    assert stderr == ""


def test_high_value_examples_have_stable_output() -> None:
    assert invoke("run", EXAMPLES / "hello.kaj") == (EXIT_SUCCESS, "Hello, Kaj!\n", "")
    assert invoke("run", EXAMPLES / "factorial.kaj") == (EXIT_SUCCESS, "120\n", "")
    assert invoke("run", EXAMPLES / "user-directory.kaj") == (EXIT_SUCCESS, "Alice\n", "")
    assert invoke("run", EXAMPLES / "modules" / "main.kaj") == (EXIT_SUCCESS, "5\n", "")
