from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

from kaj import __version__
from kaj.cli import (
    EXIT_CLI_MISUSE,
    EXIT_COMPILE_ERROR,
    EXIT_RUNTIME_ERROR,
    EXIT_SUCCESS,
    cli_main,
)


def invoke(arguments: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = cli_main(arguments, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def source(tmp_path: Path, text: str, name: str = "program.kaj") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_version_help_and_legacy_no_argument_behavior() -> None:
    assert invoke(["--version"]) == (EXIT_SUCCESS, f"kaj {__version__}\n", "")
    assert invoke([]) == (EXIT_SUCCESS, f"Kaj {__version__}\n", "")
    code, stdout, stderr = invoke(["--help"])
    assert code == EXIT_SUCCESS and "kaj {check|run|fmt|ast}" in stdout and not stderr
    assert invoke(["check", "--help"])[0] == EXIT_SUCCESS


def test_check_success_and_compile_failure(tmp_path: Path) -> None:
    valid = source(tmp_path, "let x = 1")
    assert invoke(["check", str(valid)]) == (EXIT_SUCCESS, "", "")
    invalid = source(tmp_path, 'let x = "a" + 1', "invalid.kaj")
    code, stdout, stderr = invoke(["check", str(invalid)])
    assert code == EXIT_COMPILE_ERROR and stdout == ""
    assert str(invalid) in stderr and "TYPE_MISMATCH" in stderr
    assert "Traceback" not in stderr


def test_run_success_runtime_error_and_partial_output(tmp_path: Path) -> None:
    factorial = source(
        tmp_path,
        """fn factorial(n: Int) -> Int {
    if n <= 1 { return 1 }
    return n * factorial(n - 1)
}
print(factorial(5))
""",
    )
    assert invoke(["run", str(factorial)]) == (EXIT_SUCCESS, "120\n", "")
    failing = source(tmp_path, 'print("before") print(1 / 0)', "runtime.kaj")
    code, stdout, stderr = invoke(["run", str(failing)])
    assert code == EXIT_RUNTIME_ERROR and stdout == "before\n"
    assert "RUNTIME_DIVISION_BY_ZERO" in stderr and "Traceback" not in stderr


def test_run_compile_failure_has_no_program_output(tmp_path: Path) -> None:
    path = source(tmp_path, 'print("must not run") let x: Int = "bad"')
    code, stdout, stderr = invoke(["run", str(path)])
    assert code == EXIT_COMPILE_ERROR and stdout == ""
    assert "TYPE_MISMATCH" in stderr


def test_fmt_is_atomic_idempotent_and_stops_after_parse(tmp_path: Path) -> None:
    path = source(tmp_path, "let x=missing_name")
    assert invoke(["fmt", str(path)]) == (EXIT_SUCCESS, "", "")
    assert path.read_text() == "let x = missing_name\n"
    first = path.read_bytes()
    assert invoke(["fmt", str(path)]) == (EXIT_SUCCESS, "", "")
    assert path.read_bytes() == first
    malformed = source(tmp_path, "let x =", "malformed.kaj")
    before = malformed.read_bytes()
    code, stdout, stderr = invoke(["fmt", str(malformed)])
    assert code == EXIT_COMPILE_ERROR and stdout == "" and "PARSE_" in stderr
    assert malformed.read_bytes() == before


def test_ast_is_parse_only_and_schema_valid(tmp_path: Path) -> None:
    path = source(tmp_path, "let x = missing_name")
    code, stdout, stderr = invoke(["ast", str(path)])
    assert code == EXIT_SUCCESS and stderr == "" and stdout.endswith("\n")
    document = json.loads(stdout)
    schema = json.loads((Path(__file__).parents[2] / "schemas" / "ast" / "v1.json").read_text())
    jsonschema.validate(document, schema)
    malformed = source(tmp_path, "let x =", "bad.kaj")
    code, stdout, stderr = invoke(["ast", str(malformed)])
    assert code == EXIT_COMPILE_ERROR and stdout == "" and "PARSE_" in stderr


@pytest.mark.parametrize(
    "arguments",
    [
        ["wat"],
        ["check"],
        ["run"],
        ["fmt"],
        ["ast"],
        ["check", "a.kaj", "b.kaj"],
        ["check", "source.txt"],
        ["check", "does-not-exist.kaj"],
        ["check", "--unknown"],
    ],
)
def test_cli_misuse_is_64_without_traceback(arguments: list[str]) -> None:
    code, stdout, stderr = invoke(arguments)
    assert code == EXIT_CLI_MISUSE and stdout == ""
    assert "error:" in stderr and "Traceback" not in stderr


def test_python_module_entrypoint_uses_same_cli(tmp_path: Path) -> None:
    path = source(tmp_path, "print(6 * 7)")
    result = subprocess.run(
        [sys.executable, "-m", "kaj", "run", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == EXIT_SUCCESS
    assert result.stdout == "42\n" and result.stderr == ""

    misuse = subprocess.run(
        [sys.executable, "-m", "kaj", "wat"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert misuse.returncode == EXIT_CLI_MISUSE
    assert "Traceback" not in misuse.stderr
