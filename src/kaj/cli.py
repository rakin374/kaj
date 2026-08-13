from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import TextIO

from kaj import __version__
from kaj.diagnostics import Diagnostic
from kaj.formatting import format_program
from kaj.modules import compile_module_graph
from kaj.pipeline import parse_source
from kaj.runtime import Interpreter, KajModuleValue, StreamOutput, TaskRuntime, TaskStartError
from kaj.serialization import ast_to_json

EXIT_SUCCESS = 0
EXIT_COMPILE_ERROR = 1
EXIT_RUNTIME_ERROR = 2
EXIT_CLI_MISUSE = 64

USAGE = (
    "usage: kaj {check|run|fmt|ast} <file>\n"
    "       kaj task run <file> <TaskName>\n"
    "       kaj --version"
)


def cli_main(
    argv: list[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    out = sys.stdout if stdout is None else stdout
    err = sys.stderr if stderr is None else stderr
    if not arguments:
        print(f"Kaj {__version__}", file=out)
        return EXIT_SUCCESS
    if arguments in (["--version"], ["-V"]):
        print(f"kaj {__version__}", file=out)
        return EXIT_SUCCESS
    if arguments in (["--help"], ["-h"]):
        print(USAGE, file=out)
        return EXIT_SUCCESS
    command = arguments[0]
    if command == "task":
        return _task_command(arguments, out, err)
    if command not in {"check", "run", "fmt", "ast"}:
        return _misuse(f"unknown command '{command}'", err)
    if len(arguments) == 2 and arguments[1] in {"--help", "-h"}:
        print(f"usage: kaj {command} <file>", file=out)
        return EXIT_SUCCESS
    if len(arguments) < 2:
        return _misuse(f"missing file argument for '{command}'", err, command)
    if len(arguments) > 2:
        return _misuse(f"too many arguments for '{command}'", err, command)
    path = Path(arguments[1])
    loaded = _load_source(path, err)
    if loaded is None:
        return EXIT_CLI_MISUSE
    if command == "check":
        return _check(loaded, path, err)
    if command == "run":
        return _run(loaded, path, out, err)
    if command == "fmt":
        return _fmt(loaded, path, err)
    return _ast(loaded, path, out, err)


def _task_command(arguments: list[str], stdout: TextIO, stderr: TextIO) -> int:
    usage = "usage: kaj task run <file> <TaskName>"
    if arguments in (["task", "--help"], ["task", "-h"]):
        print(usage, file=stdout)
        return EXIT_SUCCESS
    if len(arguments) < 2 or arguments[1] != "run":
        print("error: expected 'run' after 'task'", file=stderr)
        print(usage, file=stderr)
        return EXIT_CLI_MISUSE
    if len(arguments) != 4:
        print("error: task run requires a file and task name", file=stderr)
        print(usage, file=stderr)
        return EXIT_CLI_MISUSE
    path = Path(arguments[2])
    source = _load_source(path, stderr)
    if source is None:
        return EXIT_CLI_MISUSE
    return _run_task(source, path, arguments[3], stdout, stderr)


def _misuse(message: str, stderr: TextIO, command: str | None = None) -> int:
    print(f"error: {message}", file=stderr)
    print(f"usage: kaj {command} <file>" if command else USAGE, file=stderr)
    return EXIT_CLI_MISUSE


def _load_source(path: Path, stderr: TextIO) -> str | None:
    if path.suffix != ".kaj":
        print(f"error: source path must have .kaj extension: {path}", file=stderr)
        return None
    try:
        if not path.is_file():
            print(
                f"error: source file does not exist or is not a regular file: {path}", file=stderr
            )
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        print(f"error: cannot read source file {path}: {error}", file=stderr)
        return None


def render_diagnostic(path: Path, diagnostic: Diagnostic) -> str:
    location = diagnostic.span.start
    return f"{path}:{location.line}:{location.column}: {diagnostic.code}: {diagnostic.message}"


def _render_diagnostics(path: Path, diagnostics: tuple[Diagnostic, ...], stderr: TextIO) -> None:
    for diagnostic in diagnostics:
        print(render_diagnostic(path, diagnostic), file=stderr)


def _check(source: str, path: Path, stderr: TextIO) -> int:
    graph = compile_module_graph(path, source)
    if graph.diagnostics:
        for item in graph.diagnostics:
            print(render_diagnostic(item.path, item.diagnostic), file=stderr)
        return EXIT_COMPILE_ERROR
    return EXIT_SUCCESS


def _run(source: str, path: Path, stdout: TextIO, stderr: TextIO) -> int:
    graph = compile_module_graph(path, source)
    if graph.diagnostics:
        for item in graph.diagnostics:
            print(render_diagnostic(item.path, item.diagnostic), file=stderr)
        return EXIT_COMPILE_ERROR
    if graph.entry is None:
        raise RuntimeError("module graph omitted entry without diagnostics")
    initialized: dict[str, KajModuleValue] = {}
    output = StreamOutput(stdout)
    for result in graph.modules:
        imported = {
            id(declaration): _runtime_namespace_chain(declaration.path, initialized)
            for declaration, _ in result.imported_namespaces
        }
        execution = Interpreter(
            result.resolution,
            result.types,
            output=output,
            imported_modules=imported,
        ).interpret(result.loaded.program)
        if execution.runtime_error is not None:
            diagnostic = Diagnostic(
                execution.runtime_error.code,
                execution.runtime_error.message,
                execution.runtime_error.span,
            )
            print(render_diagnostic(result.loaded.path, diagnostic), file=stderr)
            return EXIT_RUNTIME_ERROR
        if result.loaded.name is not None:
            initialized[result.loaded.name.dotted] = KajModuleValue(
                result.loaded.name.dotted, execution.exports
            )
    return EXIT_SUCCESS


def _run_task(source: str, path: Path, task_name: str, stdout: TextIO, stderr: TextIO) -> int:
    graph = compile_module_graph(path, source)
    if graph.diagnostics:
        for item in graph.diagnostics:
            print(render_diagnostic(item.path, item.diagnostic), file=stderr)
        return EXIT_COMPILE_ERROR
    if graph.entry is None:
        raise RuntimeError("module graph omitted entry without diagnostics")
    initialized: dict[str, KajModuleValue] = {}
    output = StreamOutput(stdout)
    for result in graph.modules[:-1]:
        imported = {
            id(declaration): _runtime_namespace_chain(declaration.path, initialized)
            for declaration, _ in result.imported_namespaces
        }
        execution = Interpreter(
            result.resolution, result.types, output=output, imported_modules=imported
        ).interpret(result.loaded.program)
        if execution.runtime_error is not None:
            diagnostic = Diagnostic(
                execution.runtime_error.code,
                execution.runtime_error.message,
                execution.runtime_error.span,
            )
            print(render_diagnostic(result.loaded.path, diagnostic), file=stderr)
            return EXIT_RUNTIME_ERROR
        if result.loaded.name is not None:
            initialized[result.loaded.name.dotted] = KajModuleValue(
                result.loaded.name.dotted, execution.exports
            )
    entry = graph.entry
    imported = {
        id(declaration): _runtime_namespace_chain(declaration.path, initialized)
        for declaration, _ in entry.imported_namespaces
    }
    runtime = TaskRuntime(
        entry.loaded.program,
        entry.resolution,
        entry.types,
        output=output,
        imported_modules=imported,
    )
    try:
        instance = runtime.start_task(task_name)
    except TaskStartError as error:
        diagnostic = Diagnostic(error.code, error.message, entry.loaded.program.span)
        print(render_diagnostic(path, diagnostic), file=stderr)
        return EXIT_RUNTIME_ERROR
    if instance.failure is not None:
        diagnostic = Diagnostic(
            instance.failure.code,
            instance.failure.message,
            instance.failure.runtime_error.span,
        )
        print(render_diagnostic(path, diagnostic), file=stderr)
        return EXIT_RUNTIME_ERROR
    return EXIT_SUCCESS


def _runtime_namespace_chain(
    path: tuple[str, ...], initialized: dict[str, KajModuleValue]
) -> KajModuleValue:
    target = initialized[".".join(path)]
    namespace = target
    for index in range(len(path) - 2, -1, -1):
        namespace = KajModuleValue(".".join(path[: index + 1]), ((path[index + 1], namespace),))
    return namespace


def _fmt(source: str, path: Path, stderr: TextIO) -> int:
    result = parse_source(source, str(path))
    if result.diagnostics:
        _render_diagnostics(path, result.diagnostics, stderr)
        return EXIT_COMPILE_ERROR
    formatted = format_program(result.program)
    temporary: Path | None = None
    try:
        descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        temporary = Path(name)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(formatted)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as error:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
        print(f"error: cannot write formatted source {path}: {error}", file=stderr)
        return EXIT_CLI_MISUSE
    return EXIT_SUCCESS


def _ast(source: str, path: Path, stdout: TextIO, stderr: TextIO) -> int:
    result = parse_source(source, str(path))
    if result.diagnostics:
        _render_diagnostics(path, result.diagnostics, stderr)
        return EXIT_COMPILE_ERROR
    stdout.write(ast_to_json(result.program) + "\n")
    return EXIT_SUCCESS
