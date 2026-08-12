from __future__ import annotations

import io
import json
from pathlib import Path

import jsonschema

from kaj.ast import ImportDeclaration
from kaj.cli import EXIT_COMPILE_ERROR, EXIT_RUNTIME_ERROR, EXIT_SUCCESS, cli_main
from kaj.formatting import format_program
from kaj.pipeline import parse_source
from kaj.serialization import ast_from_json_value, ast_to_json_value


def invoke(arguments: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = cli_main(arguments, stdout=stdout, stderr=stderr)
    return code, stdout.getvalue(), stderr.getvalue()


def write(path: Path, source: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


def test_import_ast_json_and_formatter_round_trip() -> None:
    parsed = parse_source("import foo\nimport util.math\n", "main.kaj")
    assert parsed.diagnostics == ()
    imports = parsed.program.statements
    assert imports == (
        ImportDeclaration(imports[0].span, ("foo",)),
        ImportDeclaration(imports[1].span, ("util", "math")),
    )
    assert format_program(parsed.program) == "import foo\nimport util.math\n"
    encoded = ast_to_json_value(parsed.program)
    assert ast_from_json_value(encoded) == parsed.program
    schema = json.loads((Path(__file__).parents[2] / "schemas/ast/v1.json").read_text())
    jsonschema.validate(encoded, schema)


def test_check_and_run_single_and_dotted_modules(tmp_path: Path) -> None:
    write(tmp_path / "math.kaj", "fn double(value: Int) -> Int { return value * 2 }")
    write(
        tmp_path / "util" / "text.kaj",
        'fn greeting() -> String { return "hello" }',
    )
    entry = write(
        tmp_path / "main.kaj",
        "import math\nimport util.text\nprint(math.double(21))\nprint(util.text.greeting())\n",
    )
    assert invoke(["check", str(entry)]) == (EXIT_SUCCESS, "", "")
    assert invoke(["run", str(entry)]) == (EXIT_SUCCESS, "42\nhello\n", "")


def test_imported_nominal_types_work_in_type_and_value_positions(tmp_path: Path) -> None:
    write(
        tmp_path / "models.kaj",
        """type User { name: String }
enum Status { pending complete }
newtype UserId = String
fn name(user: User) -> String { return user.name }
""",
    )
    entry = write(
        tmp_path / "main.kaj",
        """import models
let user: models.User = models.User { name: "Kaj" }
let status: models.Status = models.Status.pending
let id: models.UserId = models.UserId("one")
print(models.name(user))
print(id.value)
""",
    )
    assert invoke(["run", str(entry)]) == (EXIT_SUCCESS, "Kaj\none\n", "")


def test_dependency_initialization_is_ordered_and_shared_once(tmp_path: Path) -> None:
    write(tmp_path / "shared.kaj", 'print("shared")\nlet value = 1')
    write(tmp_path / "left.kaj", 'import shared\nprint("left")')
    write(tmp_path / "right.kaj", 'import shared\nprint("right")')
    entry = write(
        tmp_path / "main.kaj",
        'import left\nimport right\nprint("main")',
    )
    assert invoke(["run", str(entry)]) == (
        EXIT_SUCCESS,
        "shared\nleft\nright\nmain\n",
        "",
    )


def test_transitive_imports_compile_without_becoming_direct_bindings(tmp_path: Path) -> None:
    write(tmp_path / "bar.kaj", "let answer = 42")
    write(tmp_path / "foo.kaj", "import bar\nfn answer() -> Int { return bar.answer }")
    entry = write(tmp_path / "main.kaj", "import foo\nprint(foo.answer())")
    assert invoke(["run", str(entry)]) == (EXIT_SUCCESS, "42\n", "")
    entry.write_text("import foo\nprint(bar.answer)", encoding="utf-8")
    code, _, stderr = invoke(["check", str(entry)])
    assert code == EXIT_COMPILE_ERROR and "RESOLVE_UNKNOWN_NAME" in stderr


def test_dependency_compile_and_runtime_errors_keep_dependency_path(tmp_path: Path) -> None:
    broken = write(tmp_path / "broken.kaj", 'let value: Int = "bad"')
    entry = write(tmp_path / "main.kaj", "import broken")
    code, stdout, stderr = invoke(["run", str(entry)])
    assert code == EXIT_COMPILE_ERROR and stdout == ""
    assert str(broken) in stderr and "TYPE_MISMATCH" in stderr

    failing = write(tmp_path / "failing.kaj", 'print("dependency")\nprint(1 / 0)')
    later = write(tmp_path / "later.kaj", 'print("later")')
    entry.write_text("import failing\nimport later\nprint(\"main\")", encoding="utf-8")
    code, stdout, stderr = invoke(["run", str(entry)])
    assert code == EXIT_RUNTIME_ERROR and stdout == "dependency\n"
    assert str(failing) in stderr and "RUNTIME_DIVISION_BY_ZERO" in stderr
    assert str(later) not in stdout


def test_same_named_nominal_types_from_modules_remain_distinct(tmp_path: Path) -> None:
    write(tmp_path / "a.kaj", "newtype Id = String\nfn make() -> Id { return Id(\"a\") }")
    write(tmp_path / "b.kaj", "newtype Id = String\nfn take(value: Id) -> None { return }")
    entry = write(tmp_path / "main.kaj", "import a\nimport b\nb.take(a.make())")
    code, _, stderr = invoke(["check", str(entry)])
    assert code == EXIT_COMPILE_ERROR and "TYPE_MISMATCH" in stderr


def test_import_binding_collides_with_top_level_value(tmp_path: Path) -> None:
    write(tmp_path / "foo.kaj", "let value = 1")
    entry = write(tmp_path / "main.kaj", "import foo\nlet foo = 1")
    code, _, stderr = invoke(["check", str(entry)])
    assert code == EXIT_COMPILE_ERROR and "RESOLVE_DUPLICATE_NAME" in stderr


def test_missing_duplicate_cycle_and_unknown_member_diagnostics(tmp_path: Path) -> None:
    missing = write(tmp_path / "missing-main.kaj", "import nowhere")
    code, _, stderr = invoke(["check", str(missing)])
    assert code == EXIT_COMPILE_ERROR and "IMPORT_NOT_FOUND" in stderr

    write(tmp_path / "thing.kaj", "let value = 1")
    duplicate = write(tmp_path / "duplicate.kaj", "import thing\nimport thing")
    code, _, stderr = invoke(["check", str(duplicate)])
    assert code == EXIT_COMPILE_ERROR and "IMPORT_DUPLICATE" in stderr

    write(tmp_path / "a.kaj", "import b")
    write(tmp_path / "b.kaj", "import a")
    cycle = write(tmp_path / "cycle-main.kaj", "import a")
    code, _, stderr = invoke(["check", str(cycle)])
    assert code == EXIT_COMPILE_ERROR and "IMPORT_CYCLE" in stderr

    unknown = write(tmp_path / "unknown.kaj", "import thing\nprint(thing.nope)")
    code, _, stderr = invoke(["check", str(unknown)])
    assert code == EXIT_COMPILE_ERROR and "IMPORT_UNKNOWN_MEMBER" in stderr


def test_fmt_and_ast_do_not_load_imported_modules(tmp_path: Path) -> None:
    entry = write(tmp_path / "main.kaj", "import absent.path")
    assert invoke(["fmt", str(entry)]) == (EXIT_SUCCESS, "", "")
    code, stdout, stderr = invoke(["ast", str(entry)])
    assert code == EXIT_SUCCESS and '"kind":"import_declaration"' in stdout and stderr == ""
