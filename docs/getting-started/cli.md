# Kaj Command-Line Interface

**Status:** Authoritative for Kaj v0 CLI behavior  
**Scope:** `kaj check`, `kaj run`, `kaj fmt`, `kaj ast`, `kaj --version`, diagnostics, and exit-code classes  
**Not covered:** package management, REPL, watch mode, LSP integration, project manifests, multi-file module builds

---

# 1. Purpose

The `kaj` command is the standard command-line interface for Kaj source files.

Kaj v0 provides:

```bash
kaj check
kaj run
kaj fmt
kaj ast
kaj --version
```

These commands expose the existing lexer, parser, semantic analyzer, interpreter, formatter, and AST JSON pipeline.

---

# 2. Command Overview

Canonical commands:

```text
kaj check <file>
kaj run <file>
kaj fmt <file>
kaj ast <file>
kaj --version
```

Each source-oriented command operates on one `.kaj` source file in v0.

Multi-file module execution belongs to the imports/modules checkpoint.

---

# 3. Exit-Code Classes

Kaj CLI distinguishes four result classes:

```text
0  success
1  compile error
2  runtime error
64 CLI misuse
```

These numeric values are canonical for Kaj v0.

---

# 4. Success

Exit code:

```text
0
```

means the requested operation completed successfully.

Examples:

```text
kaj check file.kaj
```

with no compile diagnostics.

```text
kaj run file.kaj
```

with successful execution.

```text
kaj fmt file.kaj
```

with successful formatting.

---

# 5. Compile Error

Exit code:

```text
1
```

means the source could not successfully pass the required frontend stages.

This includes errors from:

```text
lexing
parsing
name resolution
type checking
AST/source validation needed before the command can complete
```

Compile diagnostics are user-visible.

---

# 6. Runtime Error

Exit code:

```text
2
```

is used by:

```bash
kaj run
```

when the program successfully compiles but execution encounters a Kaj runtime error.

Examples include:

```text
division by zero
index out of bounds
duplicate evaluated map key
other structured runtime failures
```

Compile errors take precedence over runtime execution: a program with compile errors is not run.

---

# 7. CLI Misuse

Exit code:

```text
64
```

means the command invocation itself is invalid.

Examples:

```text
unknown command
missing required file argument
too many positional arguments
invalid CLI option
invalid option combination
```

File-system failures for a requested input file, such as a missing/unreadable file, are treated as CLI/input misuse in v0 and use exit code `64`.

---

# 8. Diagnostics Stream

Compile and runtime diagnostics are written to:

```text
stderr
```

Normal program output and command data output are written to:

```text
stdout
```

This allows shell users to separate program output from diagnostics.

---

# 9. Diagnostic Ordering

Diagnostics are printed in deterministic source order where source locations exist.

When multiple diagnostics share a location, preserve compiler diagnostic order consistently.

The CLI does not invent a separate semantic ordering.

---

# 10. Diagnostic Format

The exact decorative presentation may evolve, but every source-based diagnostic should clearly include:

```text
diagnostic code
human-readable message
source file
line
column
```

where available.

Example shape:

```text
example.kaj:3:12: TYPE_MISMATCH: expected Int, found String
```

Source ranges/snippets may also be displayed.

The diagnostic code must remain visible.

---

# 11. `kaj --version`

Command:

```bash
kaj --version
```

prints the Kaj tool version and exits `0`.

Canonical output shape:

```text
kaj <version>
```

Example:

```text
kaj 0.0.1
```

The version comes from the package's canonical version source.

---

# 12. `kaj check`

Command:

```bash
kaj check <file>
```

runs the compile-time pipeline:

```text
read source
→ lex
→ parse
→ resolve
→ type check
```

It does not execute the program.

---

# 13. Successful `check`

If no compile errors exist:

```bash
kaj check program.kaj
```

exits:

```text
0
```

Canonical v0 behavior is quiet success: no stdout output is required.

This makes shell usage simple:

```bash
kaj check program.kaj && echo valid
```

---

# 14. Failed `check`

If compile errors exist:

```text
print diagnostics to stderr
exit 1
```

Do not run the interpreter.

---

# 15. `kaj run`

Command:

```bash
kaj run <file>
```

runs:

```text
read
→ lex
→ parse
→ resolve
→ type check
→ interpret
```

---

# 16. Successful `run`

Program output from Kaj's `print` builtin goes to stdout.

Example program:

```kaj
print(1 + 2)
```

Command:

```bash
kaj run program.kaj
```

prints:

```text
3
```

and exits `0`.

---

# 17. Compile Failure During `run`

If the source has compile errors:

```text
diagnostics -> stderr
no interpreter execution
exit 1
```

No partial program output should be produced by an interpreter because execution never begins.

---

# 18. Runtime Failure During `run`

If compilation succeeds but execution fails:

```text
runtime diagnostic -> stderr
exit 2
```

Any stdout emitted before the runtime failure remains normal observable program output.

The CLI does not roll output back.

---

# 19. `kaj fmt`

Command:

```bash
kaj fmt <file>
```

formats the file using the canonical AST formatter.

Default behavior is **in-place formatting**.

---

# 20. `kaj fmt` Pipeline

The command performs:

```text
read source
→ lex
→ parse
→ format AST
→ atomically replace source file
```

Formatting does not require name resolution, type checking, or execution.

This lets syntactically valid code be formatted even if it contains semantic/type errors.

---

# 21. `fmt` Parse Errors

If lexing/parsing fails:

```text
diagnostics -> stderr
file remains unchanged
exit 1
```

No partially formatted output is written.

---

# 22. Atomic Formatting

In-place formatting should avoid corrupting the source file.

Use an atomic replacement strategy where practical:

```text
format fully
write temporary sibling file
replace original
```

A failed write must not intentionally truncate the original source.

---

# 23. `fmt` Success

Successful formatting exits `0`.

No stdout output is required.

Repeated:

```bash
kaj fmt file.kaj
```

must be idempotent because the canonical formatter is idempotent.

---

# 24. `kaj ast`

Command:

```bash
kaj ast <file>
```

parses source and emits canonical AST JSON to stdout.

Pipeline:

```text
read source
→ lex
→ parse
→ AST JSON encode
```

It does not require name resolution, type checking, or execution.

AST JSON represents syntax, not semantic-analysis results.

---

# 25. `ast` Output

Output must conform to:

```text
docs/compiler/ast-json.md
schemas/ast/v1.json
```

Use the canonical deterministic AST JSON encoder.

Output ends with one newline.

---

# 26. `ast` Failure

If lexing or parsing fails:

```text
diagnostics -> stderr
no AST JSON emitted
exit 1
```

---

# 27. Why `fmt` and `ast` Stop at Parse

`fmt` and `ast` operate on syntax.

Therefore semantically invalid but syntactically valid Kaj may still be formatted or serialized to AST JSON.

Example:

```kaj
let x = unknown_name
```

may be valid input to:

```bash
kaj fmt
kaj ast
```

even though:

```bash
kaj check
kaj run
```

would fail name resolution.

---

# 28. Source File Argument

Source commands take exactly one file path in v0:

```text
check
run
fmt
ast
```

Directories and project manifests are not command targets yet.

---

# 29. `.kaj` Extension

The CLI should accept `.kaj` files.

For v0, a path without `.kaj` may be rejected as misuse to keep command behavior explicit.

Canonical behavior:

```text
source-oriented commands require a `.kaj` file path
```

Invalid extension uses exit `64`.

---

# 30. Standard Input

Reading source from stdin using `-` is not required in v0.

Do not imply stdin support unless explicitly implemented later.

---

# 31. Standard Output

The CLI writes only command-result data and Kaj program output to stdout.

Examples:

```text
kaj run -> program output
kaj ast -> JSON
kaj --version -> version
```

`check` and successful in-place `fmt` may remain silent.

---

# 32. Standard Error

Use stderr for:

```text
compile diagnostics
runtime diagnostics
CLI usage errors
file read/write errors
```

---

# 33. Usage Errors

A usage error should print a concise explanation and a short usage hint.

Example shape:

```text
error: missing file argument
usage: kaj check <file>
```

Do not print Python traceback output.

---

# 34. Help

`kaj --help` and command-specific help may be supported by the CLI framework.

If supported, help exits `0`.

Help text should list the v0 commands and basic syntax.

Help is ordinary CLI behavior and does not change Kaj language semantics.

---

# 35. No Python Tracebacks

Expected user-facing failures must not expose Python tracebacks.

This includes:

```text
compile errors
runtime errors
missing files
bad arguments
formatter parse failures
AST parse failures
```

Unexpected internal compiler bugs may be handled separately, but normal errors must remain structured.

---

# 36. Compile Pipeline Reuse

`check` and `run` must reuse one canonical frontend pipeline rather than implementing subtly different lex/parse/resolve/type-check logic.

Conceptually:

```text
compile_source(...)
```

returns:

```text
AST
resolution
types
diagnostics
```

as appropriate.

---

# 37. Parse Pipeline Reuse

`fmt` and `ast` should reuse one canonical syntax pipeline:

```text
parse_source(...)
```

rather than duplicating lexer/parser orchestration.

---

# 38. File Names in Diagnostics

The actual CLI-provided path should be associated with source diagnostics.

Do not display a generic placeholder filename when a real path is known.

---

# 39. Path Preservation

`kaj fmt` rewrites the requested file but does not rename or move it.

Other commands do not modify source files.

---

# 40. Runtime Output Sink

`kaj run` connects the interpreter's output sink to stdout.

Tests may continue using in-memory output sinks.

The CLI should not duplicate print formatting logic.

---

# 41. AST Output and Unicode

AST JSON output uses UTF-8/Unicode-readable encoding as defined by the AST JSON specification.

Do not unnecessarily ASCII-escape Unicode strings.

---

# 42. Exit-Code Precedence

For `kaj run`:

```text
CLI misuse      -> 64
compile failure -> 1
runtime failure -> 2
success         -> 0
```

Only one final process exit code is returned.

---

# 43. Internal Failures

Unexpected internal compiler/interpreter bugs are not part of the four normal semantic outcome classes.

The CLI should still avoid silently returning success.

A future internal-error exit code/policy may be standardized separately.

Do not map ordinary user mistakes to internal failures.

---

# 44. Source of Truth

For Kaj v0 CLI behavior:

```text
docs/getting-started/cli.md
```

defines the enduring command-line interface contract.

The CLI implementation must conform to it.
