# Kaj Checkpoint 16 — CLI Completion

**Audience:** Codex / implementation agent  
**Checkpoint:** 16  
**Goal:** Complete the v0 command-line interface around the existing frontend, formatter, AST JSON encoder, and reference interpreter.

---

# 1. Primary Instruction

Implement **Checkpoint 16 only**.

Before editing code, read:

```text
docs/getting-started/cli.md
docs/language/formatting.md
docs/compiler/ast-json.md
docs/internals/interpreter.md
docs/language/primitive-types.md
docs/language/functions.md
docs/language/lists.md
docs/language/records.md
docs/language/enums-and-match.md
docs/language/optional-and-result.md
docs/language/maps.md
docs/language/newtypes.md
dev/plans/pure-language-v0.md
```

Treat:

```text
docs/getting-started/cli.md
```

as authoritative.

Do not begin Checkpoint 17 Module Imports.

---

# 2. Required Commands

Support:

```bash
kaj check <file>
kaj run <file>
kaj fmt <file>
kaj ast <file>
kaj --version
```

Also preserve:

```bash
python -m kaj
```

according to the package's existing entrypoint behavior.

---

# 3. Exit Codes

Use exactly:

```text
0  success
1  compile error
2  runtime error
64 CLI misuse
```

Create named constants/enum if helpful.

Do not scatter raw numbers throughout command handlers.

---

# 4. CLI Framework

Use the repository's existing CLI approach if one already exists.

If the current entrypoint uses `argparse`, extending it is preferred over adding a new dependency solely for this checkpoint.

Do not add Click/Typer unless already present or there is a compelling repository-level reason.

---

# 5. Refactor Shared Pipelines First

Before wiring commands, identify/refactor reusable helpers.

Recommended conceptual APIs:

```python
parse_source(source: str, source_name: str) -> ParseResult
compile_source(source: str, source_name: str) -> CompileResult
```

Where `compile_source` performs:

```text
lex
parse
resolve
type check
```

Do not duplicate pipeline orchestration in each CLI command.

---

# 6. Parse Result

A parse helper should provide enough data for:

```text
fmt
ast
```

such as:

```text
Program AST
lexer/parser diagnostics
```

No semantic analysis required.

---

# 7. Compile Result

A compile helper should provide enough data for:

```text
check
run
```

such as:

```text
Program AST
ResolutionResult
TypeCheckResult
all compile diagnostics
```

Do not interpret if any compile errors exist.

---

# 8. Source Loading

Implement one source-file loading helper.

Validate:

```text
exactly one path
.kaj extension
file exists
regular/readable file where practical
UTF-8 decoding
```

Failures:

```text
stderr
exit 64
```

Do not expose Python `FileNotFoundError`, `PermissionError`, or Unicode tracebacks.

---

# 9. Diagnostic Renderer

Add/centralize a deterministic diagnostic renderer.

Minimum shape:

```text
path:line:column: CODE: message
```

Use existing spans/source locations.

If diagnostics already have a renderer, reuse it.

Do not create command-specific diagnostic formatting.

---

# 10. Diagnostic Streams

Compiler and runtime diagnostics:

```text
stderr
```

Command/program output:

```text
stdout
```

Test these streams separately.

---

# 11. `kaj --version`

Preserve/use:

```text
src/kaj/__init__.py::__version__
```

or the repository's canonical version source.

Output:

```text
kaj <version>
```

newline terminated.

Exit `0`.

---

# 12. `kaj check`

Implement:

```text
load file
compile_source
if diagnostics:
    render all
    exit 1
else:
    exit 0
```

No stdout on successful check.

No interpreter.

---

# 13. `kaj run`

Implement:

```text
load file
compile_source
if compile diagnostics:
    render
    exit 1

interpret(program, resolution, types, stdout output sink)

if runtime error:
    render runtime diagnostic
    exit 2

exit 0
```

Do not run partially compiled programs.

---

# 14. Runtime Output

Connect the interpreter's existing output abstraction directly to CLI stdout.

Do not intercept and reformat Kaj `print` values in CLI code.

---

# 15. Runtime Error Rendering

Render structured runtime diagnostics through the same or compatible renderer.

Include:

```text
path
line
column
runtime diagnostic code
message
```

where span exists.

Exit `2`.

---

# 16. `kaj fmt`

Implement in-place formatting.

Pipeline:

```text
load file
parse_source
if lex/parse errors:
    render
    exit 1

canonical = format_program(ast)
write atomically
exit 0
```

Do not run resolution/type checking.

---

# 17. Atomic Rewrite

Use a safe write pattern.

Recommended:

```text
temporary sibling file
fsync if existing repository conventions warrant it
os.replace
```

At minimum ensure formatter computation succeeds before opening/truncating the target.

A formatter/compiler error must leave original file unchanged.

---

# 18. Preserve File Encoding Contract

Read/write UTF-8.

Canonical formatter supplies LF and one final newline.

Do not preserve CRLF during `kaj fmt`; canonical formatting intentionally normalizes it.

---

# 19. `kaj ast`

Pipeline:

```text
load file
parse_source
if lex/parse errors:
    render
    exit 1

json = AST JSON encode
stdout.write(json + newline)
exit 0
```

Do not type-check.

---

# 20. AST JSON Output

Use the existing canonical encoder.

Ensure:

```text
format = kaj-ast
version = 1
deterministic ordering
ensure_ascii=False
```

according to `docs/compiler/ast-json.md`.

Do not create a second JSON serializer for CLI use.

---

# 21. `fmt` and Semantic Errors

Add regression test:

A syntactically valid file containing an unknown name should still format successfully.

Example:

```kaj
let x=unknown
```

`kaj fmt` should canonicalize it and return `0`.

`kaj check` should then return `1`.

---

# 22. `ast` and Semantic Errors

Likewise:

```bash
kaj ast syntactically-valid-but-semantically-invalid.kaj
```

must still emit AST JSON and exit `0`.

This proves `ast` stops after parsing.

---

# 23. CLI Misuse

Return `64` for:

```text
unknown subcommand
missing file
extra file
invalid extension
missing file on disk
unreadable source
invalid option
```

Print concise usage/error message to stderr.

---

# 24. Help Behavior

Ensure:

```bash
kaj --help
```

works if supported by the parser.

Prefer command-specific help:

```bash
kaj check --help
kaj run --help
kaj fmt --help
kaj ast --help
```

Help exits `0`.

---

# 25. No Tracebacks

Add subprocess tests ensuring normal user errors do not contain:

```text
Traceback (most recent call last)
```

on stderr.

This includes compile/runtime/file/usage errors.

---

# 26. Command Functions

Prefer small command handlers:

```text
cmd_check
cmd_run
cmd_fmt
cmd_ast
```

that return exit codes rather than directly calling `sys.exit` deep in implementation.

Top-level `main()` can convert return value to process exit status.

This improves testing.

---

# 27. Entry Point

Keep:

```toml
kaj = "kaj.__main__:main"
```

or current equivalent.

Do not change packaging unnecessarily.

---

# 28. `python -m kaj`

Ensure package module invocation reaches the same CLI parser/logic.

Avoid two divergent CLI implementations.

---

# 29. Unit Tests

Add direct handler/helper tests for:

```text
source loading
diagnostic rendering
exit code classification
parse pipeline
compile pipeline
atomic format write
```

where useful.

---

# 30. Subprocess Tests

Add end-to-end tests invoking the installed/module CLI.

Use:

```text
python -m kaj ...
```

in tests if invoking the console script is environment-sensitive.

Verify:

```text
returncode
stdout
stderr
file contents
```

---

# 31. Required Test — Version

Run:

```bash
kaj --version
```

Expected:

```text
kaj <current-version>
```

exit `0`.

Also verify:

```bash
python -m kaj --version
```

matches.

---

# 32. Required Test — Check Success

File:

```kaj
let x = 1
```

Run:

```bash
kaj check file.kaj
```

Expected:

```text
exit 0
stdout empty
stderr empty
```

---

# 33. Required Test — Check Compile Failure

File:

```kaj
let x = "a" + 1
```

Expected:

```text
exit 1
stderr contains TYPE_MISMATCH
no traceback
```

---

# 34. Required Test — Run Success

File:

```kaj
fn factorial(n: Int) -> Int {
    if n <= 1 {
        return 1
    }

    return n * factorial(n - 1)
}

print(factorial(5))
```

Expected:

```text
stdout = "120\n"
stderr empty
exit 0
```

---

# 35. Required Test — Run Compile Failure

Use a type-invalid program.

Expected:

```text
exit 1
interpreter not invoked
stderr contains compile diagnostic
```

If practical, mock/spying can verify no interpreter call.

---

# 36. Required Test — Run Runtime Failure

File:

```kaj
print(1 / 0)
```

Expected:

```text
exit 2
stderr contains RUNTIME_DIVISION_BY_ZERO
no traceback
```

---

# 37. Required Test — Partial Output Before Runtime Failure

Program:

```kaj
print("before")
print(1 / 0)
```

Expected:

```text
stdout = "before\n"
exit 2
```

Do not buffer-and-discard earlier valid output.

---

# 38. Required Test — Fmt

Input intentionally ugly but syntactically valid Kaj.

Run:

```bash
kaj fmt file.kaj
```

Expected:

```text
exit 0
stdout empty
stderr empty
file == canonical format
```

Run it again and ensure the file does not change.

---

# 39. Required Test — Fmt Parse Error

Malformed source.

Expected:

```text
exit 1
file bytes unchanged
stderr contains parse/lex diagnostic
```

---

# 40. Required Test — Fmt Semantic Error

Syntactically valid but unresolved:

```kaj
let x=missing_name
```

Expected:

```text
kaj fmt -> exit 0
```

and canonical source written.

This is important.

---

# 41. Required Test — Ast

Valid source:

```kaj
let x = 1
```

Run:

```bash
kaj ast file.kaj
```

Expected:

```text
exit 0
stdout valid AST JSON v1
stderr empty
```

Validate JSON with schema.

---

# 42. Required Test — Ast Semantic Error

Syntactically valid unresolved name.

Expected:

```text
exit 0
AST JSON emitted
```

No resolver/type checking.

---

# 43. Required Test — Ast Parse Error

Malformed syntax.

Expected:

```text
exit 1
stdout empty
stderr diagnostic
```

---

# 44. Required Test — Missing File

Run:

```bash
kaj check does-not-exist.kaj
```

Expected:

```text
exit 64
stderr concise file error
no traceback
```

Repeat representative source commands if shared loading path is not obviously covered.

---

# 45. Required Test — Wrong Extension

Run:

```bash
kaj check source.txt
```

Expected:

```text
exit 64
```

unless repository requirements already intentionally allow arbitrary extensions; if so, reconcile with authoritative CLI spec before implementation rather than silently deviating.

---

# 46. Required Test — Missing Arguments

Examples:

```bash
kaj check
kaj run
kaj fmt
kaj ast
```

Expected:

```text
exit 64
usage/error to stderr
```

Note: standard argparse defaults to exit code 2 for misuse. Override/catch parser exits so Kaj returns canonical `64`.

---

# 47. Required Test — Unknown Command

```bash
kaj wat
```

Expected:

```text
exit 64
```

Do not accept argparse's default exit 2 as final Kaj behavior.

---

# 48. Argparse Exit Handling

If using `argparse`, implement a parser subclass or exception strategy so user misuse maps to:

```text
64
```

while `--help` remains `0`.

Do not call broad exception handling that masks actual compiler bugs.

---

# 49. Compile Diagnostic Ordering

Create a fixture with multiple diagnostics and assert deterministic stderr ordering.

Do not sort in a way that changes the compiler's intended source ordering.

---

# 50. File Path in Diagnostics

Use the CLI input path as source name.

Test that stderr includes the filename.

---

# 51. No Command Leakage

Ensure:

```text
check does not run
fmt does not resolve/type-check
ast does not resolve/type-check
run always compiles first
```

Tests should make these phase boundaries explicit.

---

# 52. Suggested Files

Likely:

```text
src/kaj/__main__.py
src/kaj/cli.py
src/kaj/pipeline.py
src/kaj/diagnostics/render.py
```

Only add files that fit current repo structure.

Potential tests:

```text
tests/cli/test_check.py
tests/cli/test_run.py
tests/cli/test_fmt.py
tests/cli/test_ast.py
tests/cli/test_version.py
tests/cli/test_exit_codes.py
```

---

# 53. Suggested Implementation Order

### Step 1
Read `docs/getting-started/cli.md`.

### Step 2
Inspect current `__main__.py`, version handling, frontend helpers, formatter, AST JSON, interpreter.

### Step 3
Factor canonical parse and compile pipeline helpers.

### Step 4
Add stable exit-code constants.

### Step 5
Implement source loading and diagnostic rendering.

### Step 6
Implement CLI parser with misuse -> 64.

### Step 7
Implement `check`.

### Step 8
Implement `run`.

### Step 9
Implement `fmt` with safe in-place write.

### Step 10
Implement `ast`.

### Step 11
Verify `--version`, `--help`, and `python -m kaj`.

### Step 12
Add direct tests.

### Step 13
Add subprocess/end-to-end tests.

### Step 14
Run full repository verification.

### Step 15
Update:

```text
dev/plans/pure-language-v0.md
```

Do not proceed to Checkpoint 17.

---

# 54. Verification

Run:

```bash
pytest
ruff check .
mypy src

kaj --version
python -m kaj --version
```

Also manually or in tests verify:

```bash
kaj check <valid.kaj>
kaj run <valid.kaj>
kaj fmt <valid.kaj>
kaj ast <valid.kaj>
```

and representative failures for exit `1`, `2`, and `64`.

---

# 55. Definition of Done

Checkpoint 16 is complete only when:

```text
[ ] `kaj --version` implemented/preserved
[ ] `kaj check <file>` implemented
[ ] `kaj run <file>` implemented
[ ] `kaj fmt <file>` implemented
[ ] `kaj ast <file>` implemented
[ ] `python -m kaj` uses same CLI implementation

[ ] exit code 0 = success
[ ] exit code 1 = compile error
[ ] exit code 2 = runtime error
[ ] exit code 64 = CLI misuse
[ ] argparse/default parser misuse does not leak exit code 2

[ ] source loading centralized
[ ] .kaj path validation implemented
[ ] missing/unreadable file -> 64
[ ] UTF-8 reading used

[ ] parse pipeline centralized
[ ] compile pipeline centralized
[ ] check/run share compile pipeline
[ ] fmt/ast share syntax pipeline

[ ] compile diagnostics render to stderr
[ ] runtime diagnostics render to stderr
[ ] program output uses stdout
[ ] ast JSON uses stdout
[ ] version uses stdout

[ ] diagnostics include code
[ ] diagnostics include path/location where available
[ ] diagnostic ordering deterministic
[ ] normal failures emit no Python tracebacks

[ ] check success quiet and exit 0
[ ] check compile failure exit 1

[ ] run success exit 0
[ ] run compile failure exit 1
[ ] run runtime failure exit 2
[ ] compile failure prevents interpreter execution
[ ] partial stdout before runtime failure is preserved

[ ] fmt works in place
[ ] fmt only requires lex/parse
[ ] fmt semantic errors do not block formatting
[ ] fmt parse failure exits 1
[ ] fmt parse failure leaves file unchanged
[ ] fmt rewrite is safe/atomic where practical
[ ] fmt idempotence preserved

[ ] ast emits canonical AST JSON v1
[ ] ast only requires lex/parse
[ ] ast semantic errors do not block output
[ ] ast parse failure exits 1
[ ] ast output validates against schema

[ ] missing command args -> 64
[ ] unknown command -> 64
[ ] invalid extension -> 64
[ ] help exits 0

[ ] factorial CLI run prints 120
[ ] division-by-zero CLI run exits 2
[ ] compile-error CLI fixture exits 1
[ ] misuse fixture exits 64

[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] Checkpoints 0-15 remain passing

[ ] no module import implementation begun
[ ] no package/project CLI added
[ ] no REPL added
[ ] no watch mode added
[ ] no stdin source mode added unless already intentionally present

[ ] dev/plans/pure-language-v0.md updated
```

---

# 56. Completion Report

When finished, report:

```text
Checkpoint 16 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

CLI architecture:
- ...

Shared parse/compile pipeline:
- ...

Diagnostic rendering:
- ...

Commands:
- check: PASS/FAIL
- run: PASS/FAIL
- fmt: PASS/FAIL
- ast: PASS/FAIL
- --version: PASS/FAIL

Exit codes:
- success 0: PASS/FAIL
- compile error 1: PASS/FAIL
- runtime error 2: PASS/FAIL
- CLI misuse 64: PASS/FAIL

Acceptance:
- factorial via `kaj run`: PASS/FAIL
- compile failure classification: PASS/FAIL
- runtime failure classification: PASS/FAIL
- misuse classification: PASS/FAIL

Verification:
- pytest: PASS/FAIL
- ruff check .: PASS/FAIL
- mypy src: PASS/FAIL
- console script: PASS/FAIL
- python -m kaj: PASS/FAIL

Decisions/deviations:
- ...

Known issues:
- ...
```

Do not proceed to Checkpoint 17.
