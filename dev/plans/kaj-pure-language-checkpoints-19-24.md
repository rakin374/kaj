# Kaj Pure Language — Checkpoints 19–24

**Status:** Complete

This section extends the pure-language implementation plan after the initial v0 core and conformance work.

Checkpoint-specific implementation steps, tests, verification, and Definition of Done items belong in `dev/plans/`. Public language semantics belong in the appropriate files under `docs/language/` or `docs/getting-started/`.

---

# Checkpoint 19 — Loop Control

## Goal

Complete Kaj's existing loop-control syntax by making `break` and `continue` executable in the reference interpreter.

Both keywords already parse. Valid execution must no longer produce `RUNTIME_INVALID_OPERATION`.

## Semantics

`continue` skips the remainder of the current iteration of the nearest enclosing loop.

```kaj
for value in [1, 2, 3, 4, 5] {
    if value == 3 {
        continue
    }

    print(value)
}
```

Expected:

```text
1
2
4
5
```

`break` terminates the nearest enclosing loop.

```kaj
for value in [1, 2, 3, 4, 5] {
    if value == 4 {
        break
    }

    print(value)
}
```

Expected:

```text
1
2
3
```

Both must work in `for` and `while`.

Nested-loop behavior must be nearest-loop only. An inner `break` or `continue` must never affect an outer loop.

`return` inside a loop must continue to escape the containing function.

## Runtime Model

Prefer explicit interpreter control-flow signals:

```text
ReturnSignal
BreakSignal
ContinueSignal
```

Conceptually:

```text
statement execution
    ├── normal completion
    ├── ReturnSignal(value)
    ├── BreakSignal
    └── ContinueSignal
```

A loop consumes only `BreakSignal` and `ContinueSignal`; `ReturnSignal` propagates to function execution.

## Diagnostics

Reject loop control outside loops before runtime.

Stabilize dedicated diagnostics such as:

```text
CONTROL_BREAK_OUTSIDE_LOOP
CONTROL_CONTINUE_OUTSIDE_LOOP
```

Follow the repo's existing naming convention if a different prefix is already established.

## Required Tests

Cover:

```text
break in for
continue in for
break in while
continue in while
break/continue inside conditional
nested for/for
nested while/while
nested for/while
nested while/for
nearest-loop behavior
return from inside loop
break outside loop
continue outside loop
```

## Definition of Done

```text
[ ] break executes in for and while
[ ] continue executes in for and while
[ ] nested loops use nearest-loop semantics
[ ] return semantics remain correct
[ ] break outside loop has stable diagnostic
[ ] continue outside loop has stable diagnostic
[ ] valid break/continue no longer produce RUNTIME_INVALID_OPERATION
[ ] interpreter, semantic, and CLI regression tests pass
```

---

# Checkpoint 20 — Ranges

## Goal

Provide a concise way to iterate over arbitrary integer ranges.

Initial surface:

```kaj
range(start, end)
```

## Semantics

`range(start, end)` yields `Int` values beginning at `start` and excluding `end`.

```kaj
for i in range(0, 5) {
    print(i)
}
```

Expected:

```text
0
1
2
3
4
```

The initial range is ascending and end-exclusive.

If `start >= end`, the range is empty:

```kaj
for i in range(5, 5) {
    print(i)
}
```

prints nothing.

Likewise `range(10, 5)` is empty in the initial two-argument design.

Descending ranges and a `step` argument are deferred.

## Typing

Both arguments must be `Int`.

Conceptually:

```text
range(Int, Int) -> Range
```

The implementation may use a dedicated internal `KajRange` without exposing a general `Range<T>` type.

No implicit Decimal-to-Int conversion is introduced.

## Runtime

Prefer a lazy range representation rather than allocating a full list.

```text
KajRange(start, end)
```

`for` should advance through the range directly.

## Diagnostics

Wrong arity and non-`Int` arguments should use normal Kaj call/type diagnostics where sufficient.

Do not leak host-language range errors.

## Required Tests

```text
range(0, 5)
range(3, 7)
range(0, 0)
range(5, 2)
variables as bounds
range inside function
nested ranges
break over range
continue over range
wrong arity
non-Int start/end
large range does not materialize a giant list
```

## Definition of Done

```text
[ ] range(start, end) exists
[ ] arguments require Int
[ ] end is exclusive
[ ] empty ranges are deterministic
[ ] for can iterate ranges
[ ] break/continue work over ranges
[ ] range does not require list materialization
[ ] errors use Kaj diagnostics
[ ] formatter handles range calls
[ ] regression suite remains green
```

---

# Checkpoint 21 — Strings and Explicit Conversion

## Goal

Make Kaj strings practical without weakening explicit typing.

This checkpoint includes:

```text
string interpolation
primitive -> String conversion
explicit String/Bytes encoding boundary
```

## String Interpolation

Support interpolation in ordinary strings:

```kaj
let name = "Alice"
let age = 30

print("{name} is {age} years old")
```

Prefer ordinary Kaj expressions inside interpolation if feasible:

```kaj
print("next = {count + 1}")
```

If the first implementation supports a narrower expression subset, document the restriction explicitly.

Define an escape mechanism for literal braces, preferably:

```text
{{  -> {
}}  -> }
```

Interpolation must use Kaj-defined conversion/display behavior rather than Python `str()`.

## Explicit Primitive to String Conversion

Provide an explicit conversion surface, preferably:

```kaj
String(value)
```

for supported primitives.

Examples:

```kaj
String(42)
String(2.5)
String(true)
String("hello")
```

Conceptual results:

```text
"42"
"2.5"
"true"
"hello"
```

Kaj must still reject arbitrary implicit coercion.

Keep existing safe implicit `Int -> Decimal` behavior unchanged.

## String / Bytes Boundary

`String` and `Bytes` remain distinct.

Encoding and decoding are explicit.

At minimum freeze these rules:

```text
String -> Bytes requires explicit encoding
Bytes -> String requires explicit decoding
invalid decode is a typed failure
UTF-8 is supported first
no silent replacement of invalid bytes
```

A minimal v0 API may be:

```kaj
utf8_encode(text)
utf8_decode(bytes)
```

if a general encoding-name API would add unnecessary complexity.

## Required Tests

Interpolation:

```text
single interpolation
multiple interpolations
expression interpolation if supported
escaped braces
Unicode
Int/Decimal/Bool/String values
unterminated interpolation
```

Conversion:

```text
Int -> String
Decimal -> String
Bool -> String
String -> String
Unicode preservation
exact Decimal textual form
```

Bytes:

```text
UTF-8 encode
UTF-8 decode
Unicode round trip
invalid UTF-8 typed failure
no implicit String/Bytes assignment
```

## Definition of Done

```text
[ ] interpolation implemented and documented
[ ] interpolation uses deterministic Kaj conversion
[ ] primitive -> String conversion exists
[ ] no arbitrary implicit coercion added
[ ] String/Bytes boundary is explicit
[ ] UTF-8 encode/decode behavior is implemented or frozen
[ ] decoding failure is typed
[ ] formatter and AST JSON handle interpolation deterministically
[ ] parser/type/runtime tests pass
```

---

# Checkpoint 22 — Collection Ergonomics

## Goal

Make lists and maps comfortable enough for ordinary programs while preserving immutable/value-like collection semantics.

Focus on:

```text
List.first
List.last
Map iteration
collection diagnostics
```

Do not turn this into a large collection standard library.

## `List.first`

For `List<T>`:

```text
.first -> Optional<T>
```

Example:

```kaj
match values.first {
    some(value) => print(value)
    none => print("empty")
}
```

An empty list returns `Optional<T>.none`.

## `List.last`

For `List<T>`:

```text
.last -> Optional<T>
```

An empty list also returns `Optional<T>.none`.

Existing `.count` behavior remains unchanged.

## Map Iteration

Maps become iterable without introducing tuple destructuring.

Recommended surface:

```kaj
for entry in users {
    print(entry.key)
    print(entry.value)
}
```

Conceptually, the loop variable is a built-in:

```text
MapEntry<K, V>
```

with:

```text
entry.key
entry.value
```

The entry type does not need to be user-constructible.

## Iteration Order

Define map iteration order explicitly.

Recommended v0 rule:

```text
insertion order
```

Do not leave ordering accidentally dependent on Python implementation behavior.

## Mutation

Do not add collection mutation in this checkpoint.

Defer:

```text
append/push mutation
remove mutation
map assignment
index assignment
```

unless separately designed.

## Diagnostics

Audit and stabilize:

```text
invalid list index type
list index out of bounds
unknown list member
unknown map member
invalid map key type
invalid map lookup key
for over non-iterable
empty collection inference
```

Map lookup remains:

```text
Map<K,V>[K] -> Optional<V>
```

and missing keys are not runtime errors.

## Required Tests

```text
first/last on non-empty list
first/last on empty list
first/last with structured values
iterate one-entry map
iterate multiple-entry map
iterate empty map
stable insertion order
entry.key / entry.value typing
nested map iteration
break during map iteration
continue during map iteration
collection diagnostic coverage
```

## Definition of Done

```text
[ ] List.first returns Optional<T>
[ ] List.last returns Optional<T>
[ ] empty list first/last return none
[ ] Map supports for iteration
[ ] map iteration exposes key/value safely
[ ] map iteration order is deterministic
[ ] break/continue work during map iteration
[ ] collection diagnostics are stable
[ ] no Python collection behavior leaks
[ ] regression suite remains green
```

---

# Checkpoint 23 — Value Equality and Display

## Goal

Define useful equality and deterministic display for existing structured Kaj values.

Focus on:

```text
Optional
Result
enums
newtypes
deterministic print/display
```

Record equality may remain deferred unless explicitly frozen here.

## Optional Equality

Allow equality when the wrapped type supports equality:

```text
some(a) == some(b) -> a == b
some(a) == none    -> false
none == some(b)    -> false
none == none       -> true
```

Primitive `None` and `Optional<T>.none` remain distinct runtime concepts.

## Result Equality

When payload types support equality:

```text
ok(a) == ok(b)   -> a == b
err(a) == err(b) -> a == b
ok(_) == err(_)  -> false
```

## Enum Equality

Enum values compare only within the same nominal enum type.

Payload variants compare corresponding payload values when those payload types support equality.

Different nominal enums are not comparable merely because their shapes match.

## Newtype Equality

Newtypes may compare when their wrapped values support equality:

```kaj
UserId("a") == UserId("a")
```

Different nominal newtypes remain incomparable:

```kaj
UserId("a") == OrderId("a")
```

must be rejected even if both wrap `String`.

## Records

Do not add record equality accidentally.

If included, define it explicitly as same-nominal-type, field-by-field equality requiring equality-capable fields.

Never use host object identity.

## Deterministic Display

Extend `print` beyond primitive-only values using Kaj-defined text formatting.

Do not expose Python `repr`.

Recommended conceptual forms:

```text
[1, 2, 3]
some(10)
none
ok(10)
err("bad")
Status.active
Status.suspended(reason: "review")
UserId("abc")
{"Alice": 30, "Bob": 40}
```

Map display must follow Kaj-defined deterministic order.

Keep direct string printing natural:

```kaj
print("hello")
```

prints:

```text
hello
```

rather than `"hello"`.

Nested strings inside composite displays may use quoted representation.

## Required Tests

Equality:

```text
Optional
Result
enum
enum payload
newtype
cross-newtype rejection
cross-enum rejection
unsupported nested equality rejection
```

Display:

```text
Bool
Int
Decimal
String
Bytes if supported
None
List
Map
Optional
Result
enum
newtype
record if included
Unicode
nested values
```

## Definition of Done

```text
[ ] Optional equality defined
[ ] Result equality defined
[ ] enum equality defined
[ ] newtype equality defined
[ ] nominal identity preserved
[ ] unsupported equality diagnosed statically
[ ] deterministic display layer exists
[ ] print uses Kaj display semantics
[ ] structured values print deterministically
[ ] Python repr/identity does not leak
[ ] Decimal display remains exact
[ ] runtime/type/CLI tests pass
```

---

# Checkpoint 24 — Pure Language Hardening

## Goal

Perform the final pure-language quality pass before agentic Kaj.

This checkpoint should add no major new language constructs.

Its purpose is to discover friction through real usage and fix correctness, diagnostics, formatting, module behavior, and integration issues.

## Dogfood Programs

Create realistic programs under:

```text
examples/apps/
```

Suggested examples:

```text
number-report/
inventory/
users/
gradebook/
multi-module-demo/
```

They should exercise combinations of:

```text
variables
conditionals
while
for
break
continue
range
functions
recursion
lists
maps
records
enums
match
Optional
Result
newtypes
imports
interpolation
explicit conversion
structured display
```

Prefer small real applications over isolated syntax snippets.

## Diagnostic Cleanup

Audit every stable diagnostic for:

```text
correct diagnostic code
correct source span
clear message
correct compiler phase
no Python exception leakage
no unrelated duplicate diagnostics
```

Pay special attention to:

```text
unknown names/types
wrong argument count
type mismatch
invalid condition type
bad indexing
bad member access
non-exhaustive match
invalid constructors
invalid map keys
bad imports
loop-control misuse
range misuse
conversion misuse
collection misuse
```

Normal invalid programs must not emit Python tracebacks.

## Formatter Coverage

Verify the formatter over the entire language surface:

```text
idempotence
semantic AST preservation
operator precedence
unary/power precedence
records
enums
match
Optional/Result
maps
newtypes
imports
ranges
interpolation
nested control flow
multiline constructs
```

Maintain:

```text
parse(source)
→ format
→ parse(formatted)
```

semantic equivalence ignoring spans.

Running formatting twice must produce identical bytes.

## Module Integration

Build realistic multi-module projects, e.g.:

```text
project/
├── main.kaj
├── models.kaj
├── math.kaj
└── services/
    └── users.kaj
```

Exercise:

```text
transitive loading
qualified functions
qualified records
qualified enums
qualified newtypes
forward references
module initialization order
nominal identity across modules
duplicate imports
missing imports
cycles
```

Modules must initialize once and dependency order must remain deterministic.

## Regression Suite

Extend the pure-language suite for checkpoints 19–23.

Keep all four testing layers:

```text
component
semantic pipeline
runtime end-to-end
CLI subprocess
```

Every stable diagnostic needs at least one test.

Unexpected extra diagnostics should fail invalid-program tests.

## Python Leakage Audit

Re-run and expand host-semantics isolation tests.

Verify Kaj does not inherit:

```text
Python Bool/Int equality
negative list indexing
dict key collisions
dict missing-key exceptions
Python repr
arbitrary getattr
Python list concatenation
float semantics
truthiness
host object identity equality
```

Add checks for:

```text
range semantics remain Kaj-defined
structured display remains Kaj-defined
enum/newtype equality remains nominal
map iteration order remains Kaj-defined
UTF-8 decode does not silently repair invalid input
```

## CLI Regression

Verify:

```bash
kaj check <file>
kaj run <file>
kaj fmt <file>
kaj ast <file>
kaj --version
```

Exit codes remain:

```text
0  success
1  compile error
2  runtime error
64 CLI misuse
```

And:

```text
diagnostics -> stderr
program output -> stdout
AST JSON -> stdout
version -> stdout
```

## VS Code Dogfooding

Use the Kaj VS Code extension while testing.

Update syntax support where checkpoints 19–23 introduce new lexical syntax, especially interpolation.

Do not add LSP functionality here.

## Documentation Audit

Review:

```text
docs/getting-started/
docs/guide/
docs/language/
docs/compiler/
docs/internals/
examples/
```

User-facing docs must describe implemented behavior, not planned behavior.

After Checkpoint 19, remove the old warning that executable `break`/`continue` produce `RUNTIME_INVALID_OPERATION`.

Add or update language-facing semantics for ranges, interpolation, conversion, collection ergonomics, and equality/display only after those features are implemented and frozen.

Checkpoint implementation details remain in `dev/plans/`.

Run:

```bash
mkdocs build
```

and require a clean documentation build.

## Final Dogfood

Before starting agentic Kaj, manually run a substantial multi-module program through:

```bash
kaj fmt
kaj check
kaj run
kaj ast
```

Record friction discovered through actual use.

Fix correctness problems before advancing. Purely ergonomic wishlist items may be deferred.

## Pure Language Freeze Criteria

```text
[ ] break/continue fully executable
[ ] ranges usable
[ ] strings practical
[ ] explicit conversion exists
[ ] core collection ergonomics sufficient
[ ] structured equality defined where required
[ ] deterministic display exists

[ ] stable diagnostics covered
[ ] no known Python semantic leaks
[ ] formatter idempotent
[ ] AST JSON deterministic
[ ] module integration stable
[ ] CLI behavior stable

[ ] dogfood applications succeed
[ ] VS Code highlighting reflects current syntax
[ ] docs reflect actual implementation
[ ] mkdocs build succeeds
[ ] full regression suite green
```

---

# After Checkpoint 24

Once Checkpoint 24 is complete, stop expanding ordinary Kaj merely for completeness.

The next phase is **Agentic Kaj**.

Recommended progression:

```text
Pure Kaj
   ↓
Capability model
   ↓
Task contracts
   ↓
Task execution state
   ↓
Human collaboration primitives
   ↓
Typed capability calls
   ↓
Persistence / resume
   ↓
Controlled replanning
   ↓
Real host adapters
```

Agentic Kaj should layer on top of the pure language rather than weaken or bypass it.

The dependency direction should remain:

```text
Kaj pure language
        ↓
Kaj agentic runtime
        ↓
host capabilities / applications
```

not:

```text
host application concepts
        ↓
hard-coded into Kaj core
```
