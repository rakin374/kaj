# Kaj Checkpoint 8 — Interpreter Core

**Audience:** Codex / implementation agent  
**Checkpoint:** 8  
**Goal:** Implement Kaj's Python reference interpreter for the primitive/core executable subset.

---

# 1. Primary Instruction

Implement **Checkpoint 8 only**.

Before editing code, read:

```text
docs/internals/interpreter.md
docs/language/primitive-types.md
docs/language/functions.md
docs/internals/name-resolution.md
docs/internals/ast.md
docs/compiler/ast-json.md
dev/plans/pure-language-v0.md
```

Inspect the completed resolver and type checker.

Treat:

```text
docs/internals/interpreter.md
```

as authoritative for runtime architecture and execution semantics.

Treat the primitive/function language docs as authoritative for static/operator/function behavior.

Do not begin Checkpoint 9 collection/list implementation.

---

# 2. Acceptance Target

This program must pass the frontend and execute:

```kaj
fn factorial(n: Int) -> Int {
    if n <= 1 {
        return 1
    }

    return n * factorial(n - 1)
}

print(factorial(5))
```

Captured output must be exactly:

```text
120
```

plus one newline.

---

# 3. Important Builtin Change

Checkpoint 8 introduces exactly one host builtin:

```text
print
```

Earlier resolver rules intentionally had no implicit builtins.

Extend resolution/type checking in a narrow explicit way so `print` is provided through a builtin scope/symbol environment.

Do **not** add a speculative standard library.

---

# 4. Suggested Source Structure

Add:

```text
src/kaj/
└── runtime/
    ├── __init__.py
    ├── values.py
    ├── environment.py
    ├── builtins.py
    ├── errors.py
    └── interpreter.py
```

If fewer files are clearer, consolidate responsibly.

Do not create a VM/bytecode architecture yet.

Likely tests:

```text
tests/runtime/
├── test_literals.py
├── test_bindings.py
├── test_assignment.py
├── test_operators.py
├── test_conditionals.py
├── test_while.py
├── test_functions.py
├── test_recursion.py
├── test_returns.py
├── test_print_builtin.py
├── test_runtime_scopes.py
├── test_numeric_runtime.py
└── test_runtime_errors.py
```

---

# 5. Runtime Values

Use explicit Kaj semantics with practical Python backing:

```text
Bool    -> bool
Int     -> int
Decimal -> decimal.Decimal
String  -> str
Bytes   -> bytes
None    -> dedicated sentinel or controlled None
```

Do not allow Python-specific type relationships to leak into Kaj.

In particular:

```text
Bool must not behave as Int
Decimal must never become float
```

---

# 6. Runtime Environment

Implement explicit runtime environments.

Each environment has:

```text
parent
symbol -> runtime slot/value
```

Use resolver symbol identity.

Do not generate Python variables or use `globals()/locals()`.

Support:

```text
define
read
assign
```

with mutability metadata or symbol metadata sufficient for defensive enforcement.

---

# 7. Runtime Scope Layout

Mirror lexical scope:

```text
builtin environment/scope
    ↓
module environment
    ↓
function call environment
    ↓
nested block environment
```

Function direct-body declarations live in the call environment with parameters.

Nested `if`/`while` blocks get child environments.

---

# 8. Builtin `print` Resolution

Extend resolver construction so a host-provided builtin symbol for:

```text
print
```

exists outside module scope.

Module/local declarations may shadow it normally.

Do not classify `print` as a source declaration.

Use a distinct symbol kind if useful:

```text
BUILTIN_FUNCTION
```

Update resolver tests to preserve all previous semantics.

---

# 9. Builtin `print` Type Checking

Checkpoint 7's ordinary function signatures cannot naturally express "one argument of any currently printable primitive type" without generics/overloads/Any.

Handle `print` explicitly and narrowly in the type checker.

Rules:

```text
print(value)
```

- exactly one positional argument
- accepted value type: Bool, Int, Decimal, String, Bytes, None
- no named arguments
- result type: None

Do not introduce general overload resolution or `Any`.

---

# 10. Output Abstraction

Interpreter output must be injectable/capturable.

Do not require tests to patch global stdout.

Provide an abstraction such as:

```text
RuntimeOutput.write_line(text)
```

or a file-like sink.

CLI/default execution can target stdout.

Tests should use an in-memory sink.

---

# 11. Function Installation

Before executing normal module statements:

```text
install all top-level Kaj functions into module environment
```

Each runtime function value should retain:

```text
function declaration
function symbol/signature
module lexical environment reference
```

This enables forward calls and recursion.

---

# 12. Module Execution

Then execute module statements in source order.

Function declarations do not execute their bodies when encountered.

They are already installed.

Bindings and expression statements execute normally.

---

# 13. Literal Evaluation

Implement primitive literals.

For Decimal:

```python
decimal.Decimal
```

must be used.

Do not convert via float.

---

# 14. Identifier Evaluation

Use:

```text
ResolutionResult:
Identifier node -> Symbol
```

then runtime environment lookup by Symbol.

Do not resolve identifiers again by text.

---

# 15. Binding Execution

For `let` / `var`:

1. evaluate initializer
2. materialize any statically approved boundary promotion required by annotation
3. store under declaration symbol
4. preserve mutability

Use the type-check result to determine declared/static target type when promotion is needed.

---

# 16. Assignment

Support identifier target assignment.

1. obtain resolved target symbol
2. evaluate RHS
3. apply target-type promotion if required
4. update slot

Defensively reject immutable mutation if it somehow reaches runtime.

Do not implement member/index mutation yet.

---

# 17. Compound Assignment

Support identifier targets for:

```text
+=
-=
*=
/=
```

Use the same operator helpers as binary expressions.

Then perform assignment-boundary conversion and update.

---

# 18. Runtime Numeric Conversion

Implement one helper conceptually:

```text
coerce_runtime(value, source_type, target_type)
```

Required conversion:

```text
Int -> Decimal
```

No other implicit primitive runtime conversions.

Use this at:

```text
binding annotation boundaries
assignments
function arguments
function returns
```

where the type checker approved promotion.

---

# 19. Binary Operators

Implement reusable Kaj operator evaluation rather than scattered direct Python operations.

Support:

```text
+
-
*
/
%
**
==
!=
<
<=
>
>=
and
or
```

Follow Checkpoint 6 exactly.

---

# 20. Short Circuit

Implement:

```kaj
false and rhs
```

without evaluating `rhs`.

Implement:

```kaj
true or rhs
```

without evaluating `rhs`.

Do not evaluate both operands before dispatching `and`/`or`.

---

# 21. Division

Always return Decimal for numeric `/`.

Specifically:

```kaj
5 / 2
```

must produce Decimal `2.5`.

Do not use floor division.

Catch zero denominator and return structured:

```text
RUNTIME_DIVISION_BY_ZERO
```

---

# 22. Decimal Context

Use a deterministic Decimal context, recommended precision 34.

Do not mutate unrelated global Decimal behavior unpredictably.

Prefer a local context around operations where appropriate.

Never use float fallback.

---

# 23. Unary Operators

Support:

```text
+
-
not
```

according to type-checker-approved operand types.

---

# 24. `if`

Evaluate Bool condition.

Execute selected branch in a child block environment.

Propagate function return control immediately through nested blocks.

---

# 25. `while`

Repeatedly:

1. evaluate Bool condition
2. if false, exit
3. create fresh iteration block environment
4. execute body
5. propagate return immediately if encountered
6. reevaluate condition

Do not implement generic Python truthiness.

---

# 26. Functions

For Kaj function call:

1. evaluate call arguments left-to-right in source order
2. retrieve Checkpoint 7 argument-to-parameter mapping
3. apply required Int->Decimal parameter conversions
4. create fresh function-call environment
5. bind parameter symbols
6. execute direct function body statements in that environment
7. catch internal return signal
8. materialize return boundary promotion
9. return runtime value

If a None function falls through, return Kaj None.

---

# 27. Named Arguments

Named argument mapping is semantic metadata from Checkpoint 7.

Do not reorder AST arguments for evaluation.

Example:

```kaj
f(second: a(), first: b())
```

must evaluate:

```text
a()
then b()
```

because that is source order, even though values bind to different parameters.

---

# 28. `var` Parameters

Bind parameter values into fresh local runtime slots.

A `var` parameter slot is mutable.

Reassigning it changes only the current call frame.

It must never write back to caller bindings.

Test this explicitly.

---

# 29. Return Control

Implement private non-local return control.

A private exception-like signal is acceptable:

```text
_ReturnSignal(value)
```

Catch it only at Kaj function-call boundaries.

Do not expose `_ReturnSignal` as a runtime error.

---

# 30. Return Boundary Promotion

If function declares:

```text
Decimal
```

and returns statically approved Int:

```kaj
return 10
```

the runtime return value must become Decimal.

Use type-checker semantic information rather than guessing.

---

# 31. `print` Runtime

Implement builtin:

```kaj
print(value)
```

format:

```text
Bool    -> true / false
Int     -> decimal integer
Decimal -> decimal text, no Decimal(...) wrapper
String  -> raw contents
Bytes   -> deterministic representation
None    -> none
```

Write exactly one newline.

Return Kaj None.

---

# 32. Runtime Errors

Implement structured runtime error/result model.

At minimum:

```text
RUNTIME_DIVISION_BY_ZERO
RUNTIME_INVALID_OPERATION
RUNTIME_INTERNAL_ERROR
```

Expected Kaj runtime failures must not leak raw Python exceptions.

Include source span.

A runtime failure terminates program execution for this checkpoint.

---

# 33. Unsupported Nodes

Do not accidentally execute future features through Python.

Explicitly reject unsupported runtime nodes such as:

```text
ListLiteral
MapLiteral
ForStatement
MemberAccessExpression
IndexExpression
```

where they require future semantics.

Do not begin Checkpoint 9.

---

# 34. No `eval` / `exec`

Forbidden implementation strategies:

```python
eval(...)
exec(...)
```

Do not transpile Kaj expressions into Python snippets.

Walk the AST directly.

---

# 35. Required Tests — Literals

Evaluate primitive literals directly through AST/program execution.

Verify:

```text
Int exactness
Decimal exactness
Unicode String
Bool
None
```

---

# 36. Required Tests — Bindings

Test:

```kaj
let x = 10
print(x)
```

→ `10`

Test shadowing:

```kaj
let x = 1

if true {
    let x = 2
    print(x)
}

print(x)
```

→

```text
2
1
```

---

# 37. Required Tests — Assignment

Test:

```kaj
var x = 1
x = 2
print(x)
```

→ `2`

Test:

```kaj
var x = 1
x += 2
print(x)
```

→ `3`

Test Decimal promotion on annotated assignment.

---

# 38. Required Tests — Operators

Verify:

```kaj
print(10 + 2)
```

→ `12`

```kaj
print(10 + 2.5)
```

→ `12.5`

```kaj
print(5 / 2)
```

→ `2.5`

Verify comparisons and Boolean operations.

Verify short-circuit with a RHS that would fail if evaluated, using a suitable valid construction.

---

# 39. Required Tests — If

Test true/false branches and nested shadowing.

---

# 40. Required Tests — While

Example:

```kaj
var x = 0

while x < 3 {
    x += 1
}

print(x)
```

→ `3`

Verify fresh block-local environment per iteration where observable.

---

# 41. Required Tests — Functions

Test:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}

print(add(2, 3))
```

→ `5`

Test None-returning function.

Test nested return through if.

Test argument Int->Decimal promotion.

Test return Int->Decimal promotion.

---

# 42. Required Tests — Recursion

Required:

```kaj
fn factorial(n: Int) -> Int {
    if n <= 1 {
        return 1
    }

    return n * factorial(n - 1)
}

print(factorial(5))
```

→ `120`

Also test enough recursion depth to prove call frames are independent, without stress-testing Python recursion limits.

---

# 43. Required Tests — Mutable Parameters

Example:

```kaj
fn change(var x: Int) -> Int {
    x = 20
    return x
}

let original = 10
let changed = change(original)

print(original)
print(changed)
```

must output:

```text
10
20
```

---

# 44. Required Tests — `print`

Verify:

```text
Int
Decimal
Bool
String
None
```

formatting.

Verify `print` resolves without source declaration.

Verify a module binding can shadow builtin `print`, and calling the shadowing non-function gets `TYPE_NOT_CALLABLE` before execution.

---

# 45. Required Tests — Runtime Errors

Test statically valid division by zero:

```kaj
print(1 / 0)
```

returns structured:

```text
RUNTIME_DIVISION_BY_ZERO
```

No raw Python exception escapes.

---

# 46. End-to-End Helper

Add a test/helper path that runs:

```text
source
→ lexer
→ parser
→ resolver with builtins
→ type checker
→ interpreter
```

and returns:

```text
diagnostics
output
runtime result
```

Do not make tests manually stitch every phase when an internal testing helper can cleanly centralize the pipeline.

Avoid turning this helper into a new public CLI architecture.

---

# 47. CLI

If the current CLI architecture makes it natural, adding:

```bash
kaj run file.kaj
```

is useful during Checkpoint 8.

However, the original roadmap placed CLI completion later.

Therefore:

- adding a minimal `kaj run` is optional
- do not redesign the full CLI
- interpreter API and tests are mandatory regardless

If added, `kaj run` must run all frontend checks before interpretation.

---

# 48. Suggested Implementation Order

### Step 1
Read interpreter/type/function/name-resolution specifications.

### Step 2
Extend resolver with explicit injected `print` builtin.

### Step 3
Extend type checker with narrow `print` semantics.

### Step 4
Implement runtime value/output/error abstractions.

### Step 5
Implement runtime environment keyed by symbols.

### Step 6
Implement function preinstallation.

### Step 7
Implement literal/identifier/binding execution.

### Step 8
Implement runtime coercion helper for Int->Decimal.

### Step 9
Implement operators including short-circuit.

### Step 10
Implement assignment/compound assignment.

### Step 11
Implement `if`.

### Step 12
Implement `while`.

### Step 13
Implement function invocation and call frames.

### Step 14
Implement return signal/fallthrough.

### Step 15
Implement `print`.

### Step 16
Implement structured runtime errors.

### Step 17
Add end-to-end and factorial tests.

### Step 18
Run full repository quality gates.

### Step 19
Update:

```text
dev/plans/pure-language-v0.md
```

Do not begin Checkpoint 9.

---

# 49. Verification

Run:

```bash
pytest
ruff check .
mypy src
kaj --version
python -m kaj
```

If `kaj run` is added, also run the factorial acceptance program through it.

All previous checkpoint tests must remain green.

---

# 50. Definition of Done

Checkpoint 8 is complete only when:

```text
[ ] docs/internals/interpreter.md treated as authoritative

[ ] reference interpreter exists
[ ] runtime environment exists
[ ] symbol-identity lookup used
[ ] module environment exists
[ ] function call frames exist
[ ] nested block environments exist

[ ] primitive literals execute
[ ] Decimal uses decimal.Decimal
[ ] no float leakage
[ ] bindings execute
[ ] identifier lookup executes
[ ] identifier assignment executes
[ ] compound assignment executes

[ ] arithmetic operators execute
[ ] Int / Int -> Decimal executes
[ ] equality/comparison execute
[ ] Bool operators execute
[ ] and/or short-circuit

[ ] if executes
[ ] while executes

[ ] function values preinstalled
[ ] positional calls execute
[ ] named calls use semantic parameter mapping
[ ] arguments evaluate left-to-right
[ ] recursion executes
[ ] fresh frame per call
[ ] var parameters mutate locally only

[ ] return signal implemented
[ ] return immediately exits function
[ ] bare return yields None
[ ] None fallthrough yields None

[ ] Int->Decimal promotion materialized at:
    [ ] arithmetic
    [ ] bindings
    [ ] assignments
    [ ] arguments
    [ ] returns

[ ] builtin print introduced explicitly
[ ] resolver recognizes print through builtin scope
[ ] type checker validates print narrowly
[ ] print returns None
[ ] output sink capturable
[ ] primitive print formatting deterministic

[ ] runtime errors structured
[ ] division by zero structured
[ ] expected raw Python exceptions do not leak

[ ] unsupported future AST nodes rejected rather than accidentally executed
[ ] no eval/exec
[ ] no Python-source transpilation

[ ] factorial(5) prints 120
[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] Checkpoints 0-7 remain passing

[ ] no Lists checkpoint work
[ ] no generic for-loop runtime semantics
[ ] no records/enums/Optional/Result work
[ ] no bytecode/VM/native backend work

[ ] dev/plans/pure-language-v0.md updated
```

---

# 51. Completion Report

When finished, report:

```text
Checkpoint 8 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

Runtime value model:
- ...

Environment model:
- ...

Builtin changes:
- ...

Operator execution:
- ...

Function/call execution:
- ...

Return control:
- ...

Runtime errors:
- ...

Acceptance:
- factorial(5) output: ...
- exact expected output 120: PASS/FAIL

Verification:
- pytest: PASS/FAIL
- ruff check .: PASS/FAIL
- mypy src: PASS/FAIL
- Kaj bootstrap CLI: PASS/FAIL
- kaj run (if implemented): PASS/FAIL

Decisions/deviations:
- ...

Known issues:
- ...
```

Do not proceed to Checkpoint 9.
