# Kaj Checkpoint 18 — Pure Language Test Suite

**Audience:** Codex / implementation agent  
**Checkpoint:** 18  
**Goal:** Build a comprehensive language conformance suite covering the complete pure-language core before any agentic Kaj features begin.

---

# 1. Primary Instruction

Implement **Checkpoint 18 only**.

This checkpoint adds **tests, fixtures, test helpers, and any minimal test-only refactors needed for coverage**.

Do not add new public language features.

Before editing code, read:

```text
docs/language/lexical-structure.md
docs/internals/ast.md
docs/compiler/ast-json.md
docs/internals/name-resolution.md
docs/language/primitive-types.md
docs/language/functions.md
docs/internals/interpreter.md
docs/language/lists.md
docs/language/records.md
docs/language/enums-and-match.md
docs/language/optional-and-result.md
docs/language/maps.md
docs/language/newtypes.md
docs/language/formatting.md
docs/getting-started/cli.md
docs/language/imports.md
dev/plans/pure-language-v0.md
```

Treat the existing authoritative docs as the language contract.

The purpose of this checkpoint is to prove that implementation behavior matches those contracts.

Do not begin agentic Kaj.

---

# 2. Core Principle

The conformance suite must test Kaj as a language, not merely individual Python helper functions.

Where practical, tests should use the public compiler pipeline:

```text
source
→ lexer
→ parser
→ AST
→ resolver
→ type checker
→ interpreter
```

and CLI/end-to-end paths where appropriate.

Unit tests remain useful for focused components, but conformance coverage should be observable at language boundaries.

---

# 3. Required Test Categories

Create comprehensive coverage for:

```text
lexer
parser
source spans
AST JSON
scope
shadowing
types
numeric promotion
functions
recursion
control flow
lists
records
enums
match
Optional
Result
maps
newtypes
formatter
runtime behavior
diagnostics
modules
```

Every category must contain both valid and invalid cases where applicable.

---

# 4. Stable Diagnostic Rule

For **every invalid construct tested**, assert the stable diagnostic code.

Do not write tests that merely assert:

```text
"there was an error"
```

Instead assert exact codes such as:

```text
LEX_INVALID_CHARACTER
PARSE_EXPECTED_EXPRESSION
RESOLVE_UNKNOWN_NAME
TYPE_MISMATCH
NON_EXHAUSTIVE_MATCH
IMPORT_NOT_FOUND
```

Where multiple diagnostics are expected, assert the exact ordered code sequence where deterministic.

---

# 5. Test Layering

Use four complementary layers:

```text
1. component tests
2. semantic pipeline tests
3. runtime/end-to-end tests
4. CLI subprocess tests
```

Do not duplicate every case at every layer.

Use the lowest layer that proves the rule, plus representative end-to-end coverage for each major feature.

---

# 6. Suggested Test Layout

Prefer a clear conformance-oriented structure such as:

```text
tests/
├── conformance/
│   ├── lexer/
│   ├── parser/
│   ├── spans/
│   ├── ast_json/
│   ├── resolution/
│   ├── types/
│   ├── functions/
│   ├── control_flow/
│   ├── lists/
│   ├── records/
│   ├── enums_match/
│   ├── optional_result/
│   ├── maps/
│   ├── newtypes/
│   ├── formatter/
│   ├── runtime/
│   ├── diagnostics/
│   └── modules/
└── fixtures/
```

If the repository already has a well-organized structure, integrate cleanly instead of forcing this exact tree.

---

# 7. Shared Test Helpers

Create reusable helpers for common language assertions.

Recommended conceptual helpers:

```python
parse_ok(source) -> Program
compile_ok(source) -> CompileResult
compile_error_codes(source) -> list[str]
run_ok(source) -> CapturedExecution
run_error(source) -> RuntimeFailure
format_ok(source) -> str
ast_json_ok(source) -> dict
```

For modules, add temporary-project helpers.

Avoid copy-pasting full compiler orchestration into every test file.

---

# 8. Diagnostic Assertion Helper

Add a helper conceptually like:

```python
assert_diagnostic_codes(
    diagnostics,
    ["TYPE_MISMATCH", "TYPE_MISSING_RETURN"],
)
```

It should compare stable codes, preferably in deterministic order.

Optionally allow source-span assertions separately.

Do not hide unexpected additional diagnostics.

---

# 9. Lexer Conformance

Cover at minimum:

```text
identifiers
keywords
integers
decimals
strings
escapes
comments
operators
punctuation
longest-match operators
EOF exactly once
invalid characters
unterminated string
invalid escape
invalid number
unterminated block comment
```

Assert token kinds, lexemes, decoded values where applicable, and spans.

---

# 10. Lexer Numeric Edge Cases

Explicitly test:

```text
0
1
123
1.0
0.5
1.
.5
1.2.3
```

Valid/invalid behavior must match lexical spec.

Assert:

```text
LEX_INVALID_NUMBER
```

for invalid numeric forms where specified.

---

# 11. Lexer String Edge Cases

Test:

```text
\"
\\
\n
\r
\t
Unicode
raw newline rejection
unterminated string
invalid escape
```

Verify decoded semantic value and exact source span.

---

# 12. Parser Conformance

Cover:

```text
literals
identifiers
grouping
unary expressions
binary expressions
precedence
associativity
calls
named arguments
member access
index access
lists
maps
bindings
assignments
if/else
while
for
break
continue
return
functions
records
enums
match
newtypes
imports
```

Every supported syntax form must have at least one successful parse test.

---

# 13. Parser Precedence Matrix

Assert AST shape for:

```text
a + b * c
(a + b) * c
a - b - c
a ** b ** c
(a ** b) ** c
-2 ** 2
(-2) ** 2
not a and b
a or b and c
f(x).field[0]
```

Do not rely only on formatter round-trip to prove precedence.

---

# 14. Parser Invalid Cases

Cover exact parser diagnostics for:

```text
missing expression
missing identifier
missing token
missing type
unexpected token
invalid assignment target
positional argument after named argument
malformed declaration
malformed match
malformed import
```

Assert exact stable codes.

---

# 15. Source Span Conformance

Verify:

```text
offset zero-based
line one-based
column one-based
end-exclusive spans
```

Test:

```text
single-line tokens
multi-line source
tabs
Unicode inside strings
nested expressions
declarations
diagnostics
```

Spans should point to the intended source region.

---

# 16. AST Construction Conformance

Manually instantiate representative AST nodes where useful.

Verify:

```text
immutability where intended
tuple child collections
operator enums
source spans
syntax-only nodes
```

Do not add semantic state to AST.

---

# 17. AST JSON Conformance

Cover:

```text
AST -> JSON
JSON -> AST
AST -> JSON -> AST equality
source -> AST -> JSON -> AST equality
schema validation
deterministic output
Unicode
strict unknown-field rejection
unsupported version
unknown node kind
missing field
invalid enum value
```

Assert exact AST JSON diagnostics.

---

# 18. AST JSON Full Feature Coverage

Round-trip representative syntax for:

```text
functions
lists
maps
records
enums
match
newtypes
imports
Optional/Result syntax as represented by AST
```

Ensure no semantic/runtime-only state appears in JSON.

---

# 19. Scope Conformance

Cover:

```text
module scope
function scope
block scope
if branch scopes
while scope
for scope
match case scopes
module import bindings
```

Assert which identifiers resolve to which symbol identity.

---

# 20. Shadowing Conformance

Test:

```text
nested let shadowing allowed
nested var shadowing allowed
parameter shadowed in nested block allowed
same function-scope duplicate rejected
loop variable shadowing outer name allowed
match pattern binding shadowing outer name allowed
```

Assert:

```text
RESOLVE_DUPLICATE_NAME
```

for same-scope duplicates.

---

# 21. Unknown Name Conformance

Cover:

```text
unknown local
unknown module binding
unknown imported member if dedicated
name outside loop scope
pattern binding outside match branch
```

Assert stable resolver/member diagnostic.

---

# 22. Forward Function Resolution

Test:

```text
forward function call
self recursion
mutual recursion
```

Resolve correctly.

Also preserve rule that ordinary module bindings are not forward-visible.

---

# 23. Primitive Type Conformance

Cover:

```text
Bool
Int
Decimal
String
Bytes
None
```

Verify literal expression types and explicit annotation resolution.

Unknown types:

```text
TYPE_UNKNOWN_TYPE
```

---

# 24. Numeric Promotion Conformance

Exhaustively test relevant combinations:

```text
Int + Int -> Int
Int + Decimal -> Decimal
Decimal + Int -> Decimal
Decimal + Decimal -> Decimal

Int / Int -> Decimal
```

Also:

```text
assignment Int -> Decimal valid
Decimal -> Int invalid
function argument Int -> Decimal valid
return Int -> Decimal valid
record field Int -> Decimal valid
list contextual Int -> Decimal valid
map contextual Int -> Decimal valid
Optional/Result payload Int -> Decimal valid
newtype constructor Int -> Decimal valid
```

---

# 25. Invalid Primitive Operations

Assert exact codes for:

```text
String + Int
Bool arithmetic
non-Bool if condition
non-Bool while condition
invalid equality
invalid ordering
immutable assignment
```

Expected codes include:

```text
TYPE_MISMATCH
TYPE_INVALID_OPERATOR
TYPE_CONDITION_NOT_BOOL
ASSIGN_TO_IMMUTABLE
```

according to authoritative behavior.

---

# 26. Function Conformance

Cover:

```text
signature formation
parameter order
parameter names
parameter mutability
return type
positional calls
named calls
mixed calls
missing args
too many args
unknown named arg
duplicate argument binding
non-callable call
return type mismatch
bare return
None fallthrough
return outside function
```

Assert stable diagnostics.

---

# 27. Missing Return Conformance

Test:

```text
direct return
if/else both return
if without else
else-if chain
while return not considered total
for return not considered total
exhaustive match all branches return
exhaustive match with one falling branch
None function fallthrough
```

Assert:

```text
TYPE_MISSING_RETURN
```

where required.

---

# 28. Recursion Conformance

Runtime and type-check:

```text
factorial
mutual even/odd
recursive function with local state
```

Verify independent call frames.

---

# 29. Control Flow Conformance

Cover:

```text
if true/false
nested if
while zero iterations
while multiple iterations
for list iteration
return through nested control flow
```

If `break`/`continue` remain syntax-only or deferred at runtime, test according to their actual current supported status and authoritative docs.

Do not invent behavior.

---

# 30. Runtime Boolean Semantics

Explicitly guard against Python leakage:

```text
Bool is not Int
no truthiness
and/or short-circuit
```

Use RHS expressions whose evaluation is observable or would fail if evaluated.

---

# 31. List Conformance

Cover:

```text
List<T> annotations
nested lists
literal inference
Int/Decimal promotion
heterogeneous rejection
empty list without context
typed empty list
contextual list typing
index access
index type
bounds
negative index rejection
count
for iteration
loop variable type/scope/mutability
```

Assert all stable diagnostics/runtime codes.

---

# 32. List Runtime Conformance

Test:

```text
element evaluation order
zero-based indexing
fresh loop-body environment each iteration
var list binding rebinding
no index mutation
no Python negative indexing
```

---

# 33. Record Conformance

Cover:

```text
type declarations
type namespace
forward type references
duplicate type names
duplicate fields
unknown field types
construction
field ordering
missing field
unknown field
duplicate initializer
field type mismatch
field access
nested field access
nominal incompatibility
functions with records
lists of records
```

Assert exact codes.

---

# 34. Record Runtime Conformance

Test:

```text
construction field evaluation order
independent record values
field access
nested records
whole-record rebinding
field mutation rejection
```

No Python attribute leakage.

---

# 35. Enum Conformance

Cover:

```text
unit variants
payload variants
duplicate variants
payload field typing
unit construction
payload construction
unknown variant
missing/unknown/duplicate payload fields
nominal identity
```

Assert exact codes.

---

# 36. Match Conformance

Cover:

```text
unit patterns
payload bindings
binding types
case scopes
pattern arity
unknown variant
duplicate case
exhaustiveness
scrutinee must be enum/tagged type
definite return
runtime selected branch only
scrutinee evaluated once
```

Required stable code:

```text
NON_EXHAUSTIVE_MATCH
```

for every missing-case fixture.

---

# 37. Optional Conformance

Cover:

```text
Optional<T> arity
some inference
contextual some
primitive none
contextual Optional none
runtime distinction primitive None vs Optional.none
some/none match
pattern binding type
exhaustiveness
function return context
call argument context
list/record context
```

---

# 38. Result Conformance

Cover:

```text
Result<T,E> arity
contextual ok
contextual err
uncontextualized ok error
uncontextualized err error
payload type checking
payload promotion
ok/err matching
binding types
exhaustiveness
function return context
call argument context
lists/records
```

Assert:

```text
TYPE_CANNOT_INFER_RESULT_TYPE
```

where required.

---

# 39. Map Conformance

Cover:

```text
Map<K,V> arity
valid key types
invalid key types
literal inference
key promotion
value promotion
heterogeneous rejection
empty map context
lookup typing
lookup Optional result
present lookup
missing lookup
count
duplicate runtime key
Bool-vs-Int key distinction
Decimal key exactness
no map iteration
no mutation
```

Assert exact static/runtime codes.

---

# 40. Newtype Conformance

Cover:

```text
declaration
nominal identity
underlying type resolution
construction
constructor arity
constructor type checking
explicit unwrap
no implicit wrap
no implicit unwrap
distinct newtypes incompatible
recursive newtype rejection
functions
records
lists
Optional/Result
map keys
operator non-inheritance
```

Assert:

```text
TYPE_RECURSIVE_NEWTYPE
TYPE_MISMATCH
```

as appropriate.

---

# 41. Formatter Conformance

For representative source across every feature:

```text
parse
format
parse
```

must preserve semantic AST.

Also assert:

```text
idempotence
canonical exact output
LF
4 spaces
one final newline
no trailing whitespace
precedence
Unicode strings
Decimal remains Decimal
source order preserved
comments intentionally not preserved
```

---

# 42. Formatter Full-Language Fixture

Create at least one large `.kaj` fixture containing:

```text
imports
newtype
record
enum
functions
lists
maps
Optional
Result
match
control flow
calls
nested expressions
```

Run:

```text
parse -> format -> parse
```

and semantic AST compare.

This acts as a high-value integration fixture.

---

# 43. Runtime Conformance

Cover observable execution semantics for:

```text
literals
bindings
assignment
operators
numeric promotion
if
while
for
functions
recursion
return
lists
records
enums
match
Optional
Result
maps
newtypes
imports
print
```

Assert exact stdout.

---

# 44. Runtime Error Conformance

Cover exact codes:

```text
RUNTIME_DIVISION_BY_ZERO
RUNTIME_INDEX_OUT_OF_BOUNDS
RUNTIME_DUPLICATE_MAP_KEY
```

and any other stable runtime codes currently defined.

Ensure no raw Python exceptions escape.

---

# 45. Python-Semantics Leakage Tests

Add explicit regression cases proving Kaj does not inherit accidental Python behavior:

```text
true + 1 invalid
if 1 invalid
negative list index invalid
Bool/Int map keys distinct
Decimal never becomes float
no Python list concatenation
no Python dict missing-key exception
no arbitrary getattr member access
newtype wrappers preserve nominal identity
```

These are especially important for the Python reference interpreter.

---

# 46. Diagnostic Conformance Matrix

Create a centralized machine-readable or test-parametrized table of invalid programs and expected diagnostic codes.

Example conceptual data:

```python
[
    ("let x = unknown", ["RESOLVE_UNKNOWN_NAME"]),
    ('let x = "1" + 2', ["TYPE_MISMATCH"]),
    (...),
]
```

This matrix should cover every stable public diagnostic code reachable in the pure-language core.

---

# 47. Diagnostic Code Inventory

Build an inventory from implementation/docs and ensure each stable code has at least one test.

At minimum include all codes defined across checkpoints:

```text
LEX_INVALID_CHARACTER
LEX_UNTERMINATED_STRING
LEX_INVALID_ESCAPE
LEX_INVALID_NUMBER
LEX_UNTERMINATED_COMMENT

PARSE_EXPECTED_EXPRESSION
PARSE_EXPECTED_IDENTIFIER
PARSE_EXPECTED_TOKEN
PARSE_EXPECTED_TYPE
PARSE_UNEXPECTED_TOKEN
PARSE_INVALID_ASSIGNMENT_TARGET
PARSE_POSITIONAL_AFTER_NAMED_ARGUMENT

ASTJSON_INVALID_JSON
ASTJSON_INVALID_DOCUMENT
ASTJSON_UNSUPPORTED_VERSION
ASTJSON_UNKNOWN_NODE_KIND
ASTJSON_MISSING_FIELD
ASTJSON_INVALID_FIELD
ASTJSON_INVALID_ENUM_VALUE

RESOLVE_DUPLICATE_NAME
RESOLVE_UNKNOWN_NAME

TYPE_MISMATCH
TYPE_INVALID_OPERATOR
TYPE_CONDITION_NOT_BOOL
TYPE_UNKNOWN_TYPE
ASSIGN_TO_IMMUTABLE

TYPE_NOT_CALLABLE
TYPE_UNKNOWN_NAMED_ARGUMENT
TYPE_DUPLICATE_ARGUMENT
TYPE_MISSING_ARGUMENT
TYPE_TOO_MANY_ARGUMENTS
TYPE_MISSING_RETURN
TYPE_RETURN_OUTSIDE_FUNCTION

TYPE_CANNOT_INFER_LIST_ELEMENT
TYPE_INVALID_TYPE_ARGUMENTS
TYPE_UNKNOWN_MEMBER
TYPE_NOT_ITERABLE

TYPE_DUPLICATE_TYPE_NAME
TYPE_DUPLICATE_FIELD
TYPE_MISSING_FIELD
TYPE_UNKNOWN_FIELD

TYPE_DUPLICATE_VARIANT
TYPE_UNKNOWN_VARIANT
TYPE_PATTERN_ARITY_MISMATCH
TYPE_DUPLICATE_MATCH_CASE
TYPE_MATCH_REQUIRES_ENUM
NON_EXHAUSTIVE_MATCH

TYPE_CANNOT_INFER_RESULT_TYPE

TYPE_CANNOT_INFER_MAP_TYPE
TYPE_INVALID_MAP_KEY_TYPE

TYPE_RECURSIVE_NEWTYPE

RUNTIME_DIVISION_BY_ZERO
RUNTIME_INVALID_OPERATION
RUNTIME_INTERNAL_ERROR
RUNTIME_INDEX_OUT_OF_BOUNDS
RUNTIME_DUPLICATE_MAP_KEY

IMPORT_NOT_FOUND
IMPORT_DUPLICATE
IMPORT_CYCLE
```

If implementation contains additional stable codes, include them too.

If a listed code was superseded by an authoritative later decision, reconcile the docs/tests rather than silently omitting it.

---

# 48. No Broad Message Assertions

Diagnostic message text may be tested selectively for high-value clarity, but stable conformance should primarily bind to diagnostic code and source location.

Avoid brittle full-message snapshots everywhere.

---

# 49. CLI Conformance

Use subprocess tests for:

```text
kaj --version
kaj check
kaj run
kaj fmt
kaj ast
```

Assert:

```text
stdout
stderr
exit code
file mutation for fmt
```

Cover:

```text
0 success
1 compile error
2 runtime error
64 CLI misuse
```

---

# 50. Module Conformance

Use temporary project trees.

Cover:

```text
import foo
import foo.bar
qualified function access
qualified type access
transitive imports
shared dependency
initialization once
initialization order
duplicate import
missing import
import cycle
dependency compile error
dependency runtime error
project-root resolution independent of CWD
no remote resolution
```

---

# 51. Module Nominal Identity

Explicitly test that same-named record/enum/newtype declarations in different modules remain distinct nominal types.

Do not allow name-only identity.

---

# 52. Module Formatter/AST Boundaries

Verify:

```text
kaj fmt file.kaj
```

does not load/format dependencies.

Verify:

```text
kaj ast file.kaj
```

does not require imported modules to resolve semantically if the source parses.

This preserves CLI phase boundaries.

---

# 53. Fixture Strategy

Prefer small focused source strings for most tests.

Use `.kaj` fixture files for:

```text
large end-to-end programs
module trees
formatter golden files
diagnostic multi-line span cases
CLI subprocess tests
```

Avoid creating hundreds of near-duplicate fixture files when parametrized strings are clearer.

---

# 54. Golden Files

Golden canonical-output files are appropriate for formatter and selected AST JSON tests.

If used:

```text
input.kaj
expected.kaj
```

or:

```text
expected.ast.json
```

must be deterministic and reviewed.

Do not use broad golden snapshots as a substitute for semantic assertions.

---

# 55. Randomized / Property Tests

Property-style tests are encouraged where deterministic and maintainable.

High-value properties include:

```text
format(parse(format(parse(source)))) is idempotent
AST JSON round-trip preserves AST
integer literal round-trip
string escape round-trip
```

Do not add a heavy fuzzing dependency unless already appropriate.

A small deterministic generated corpus is sufficient.

---

# 56. Regression Seeds

When a bug is found during this checkpoint, add a minimal regression test before/fix alongside implementation changes.

Do not fix behavior without preserving a test.

---

# 57. Coverage Expectations

Do not optimize only for a numeric coverage percentage.

The goal is semantic coverage of every frozen pure-language rule.

If coverage tooling already exists, use it as a secondary signal.

Do not introduce a new coverage gate solely for vanity percentage.

---

# 58. Test Determinism

Tests must not depend on:

```text
wall clock
network
random unordered dict iteration
machine-specific absolute paths
current working directory unless explicitly under test
Python hash randomization
```

Normalize temporary paths in assertions where necessary.

---

# 59. No Network

The complete pure-language suite must run offline.

Module tests use local temporary files only.

No registry/network access.

---

# 60. Performance Sanity

The conformance suite should remain practical for local development.

Avoid pathological recursion/input sizes.

A few medium integration fixtures are useful; thousands of redundant end-to-end subprocess tests are not.

---

# 61. Test Naming

Use behavior-oriented names.

Examples:

```text
test_int_decimal_addition_promotes_to_decimal
test_missing_match_case_reports_non_exhaustive_match
test_distinct_newtypes_with_same_underlying_type_are_incompatible
test_map_missing_key_returns_optional_none
test_import_cycle_reports_import_cycle
```

Avoid vague names like:

```text
test_case_1
test_invalid
```

---

# 62. Documentation Drift Checks

Where practical, encode important examples from authoritative docs directly into tests.

The suite should make it difficult for implementation and docs to drift apart.

Do not copy checkpoint-specific Definition-of-Done material into language docs.

---

# 63. Pure-Language Boundary

Checkpoint 18 must not add:

```text
task
step
goal
success
ask
choose
confirm
handoff
capabilities
effects
browser
filesystem
robot
agent planning
AST patches
```

Those belong after pure-language stabilization.

---

# 64. Required End-to-End Pure Program

Add at least one valid multi-feature single-module program using:

```text
newtype
record
enum
Optional/Result
list
map
functions
match
loops
formatter
runtime
```

Assert compile + run output.

This proves features compose.

---

# 65. Required End-to-End Multi-Module Program

Add a small local project using:

```text
imports
qualified type
qualified function
record/newtype/enum across modules
runtime execution
```

Assert:

```text
kaj check -> 0
kaj run -> expected stdout + 0
```

---

# 66. Invalid Composition Cases

Test failures where multiple features interact, for example:

```text
wrong newtype passed across module boundary
non-exhaustive match on imported enum
wrong Map key newtype
Optional.none in wrong context
record field expects Result with wrong payload
List of nominally different imported records
```

Assert exact stable codes.

---

# 67. Test Helper Quality

Helpers must not accidentally bypass the behavior being tested.

Examples:

- parser tests should not call a helper that silently drops diagnostics
- runtime helpers must compile before executing unless specifically testing interpreter internals
- diagnostic helpers must fail on unexpected extra errors
- module helpers must use the same project-root rules as CLI/compiler

---

# 68. No Feature Fixes Without Spec Check

If a test reveals disagreement between implementation and docs:

1. determine which authoritative doc is correct
2. fix implementation if implementation drifted
3. if docs themselves are inconsistent, update the authoritative semantic doc deliberately
4. keep checkpoint-specific work notes in this plan/dev files

Do not casually redefine the language inside tests.

---

# 69. CI-Friendly Command

The entire pure-language conformance suite must run through normal:

```bash
pytest
```

No custom external service setup.

Optional pytest markers are acceptable for organization, but the full default suite should include the conformance tests.

---

# 70. Verification Commands

Run:

```bash
pytest
ruff check .
mypy src

kaj --version
python -m kaj --version
```

Also run representative:

```bash
kaj check
kaj run
kaj fmt
kaj ast
```

through automated tests.

---

# 71. Definition of Done

Checkpoint 18 is complete only when:

```text
[ ] comprehensive pure-language conformance suite exists
[ ] all required test categories are covered

[ ] lexer valid cases covered
[ ] lexer invalid cases assert exact codes
[ ] parser valid syntax covered
[ ] parser invalid syntax asserts exact codes
[ ] source span conventions covered

[ ] AST structure tests exist
[ ] AST JSON full round-trip coverage exists
[ ] AST JSON invalid cases assert exact codes

[ ] module/function/block scope covered
[ ] shadowing behavior covered
[ ] duplicate/unknown name diagnostics covered
[ ] forward/self/mutual function resolution covered

[ ] primitive types covered
[ ] numeric promotion matrix covered
[ ] invalid operators/conditions covered
[ ] mutability diagnostics covered

[ ] function signatures/calls/returns covered
[ ] named argument errors covered
[ ] missing-return analysis covered
[ ] recursion runtime covered

[ ] if/while/for runtime covered
[ ] short-circuit behavior covered
[ ] Python truthiness leakage prevented by tests

[ ] List typing/runtime/errors covered
[ ] Record typing/runtime/nominality/errors covered
[ ] Enum construction/runtime/errors covered
[ ] Match bindings/exhaustiveness/runtime covered
[ ] Optional semantics covered
[ ] Result semantics covered
[ ] Map typing/safe lookup/runtime/key semantics covered
[ ] Newtype nominal semantics/runtime covered

[ ] formatter exact output tests exist
[ ] formatter semantic round-trip tests exist
[ ] formatter idempotence tests exist
[ ] full-language formatter fixture exists

[ ] runtime success behavior covered
[ ] runtime error codes covered
[ ] no raw Python exception leakage covered

[ ] diagnostic-code matrix exists
[ ] every stable pure-language diagnostic code has at least one test
[ ] invalid constructs assert exact stable codes
[ ] unexpected extra diagnostics fail tests

[ ] CLI command behavior covered
[ ] CLI exit codes 0/1/2/64 covered
[ ] stdout/stderr separation covered

[ ] local modules covered
[ ] nested/transitive/shared imports covered
[ ] module initialization order/once semantics covered
[ ] missing/duplicate/cycle import codes covered
[ ] dependency compile/runtime failure covered
[ ] project-root behavior covered
[ ] cross-module nominal identity covered

[ ] one broad single-module integration program passes
[ ] one broad multi-module integration project passes
[ ] invalid cross-feature composition cases exist

[ ] tests run offline
[ ] tests deterministic
[ ] no external services required
[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes

[ ] no agentic Kaj features added
[ ] no capabilities/effects added
[ ] no AST patch/planner work added

[ ] dev/plans/pure-language-v0.md updated to mark pure-language core/conformance milestone
```

---

# 72. Completion Report

When finished, report:

```text
Checkpoint 18 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

Conformance suite structure:
- ...

Shared test helpers:
- ...

Diagnostic code inventory:
- total stable codes:
- codes covered:
- uncovered codes:

Category status:
- lexer: PASS/FAIL
- parser: PASS/FAIL
- source spans: PASS/FAIL
- AST JSON: PASS/FAIL
- scope: PASS/FAIL
- shadowing: PASS/FAIL
- types: PASS/FAIL
- numeric promotion: PASS/FAIL
- functions: PASS/FAIL
- recursion: PASS/FAIL
- control flow: PASS/FAIL
- lists: PASS/FAIL
- records: PASS/FAIL
- enums: PASS/FAIL
- match: PASS/FAIL
- Optional: PASS/FAIL
- Result: PASS/FAIL
- maps: PASS/FAIL
- newtypes: PASS/FAIL
- formatter: PASS/FAIL
- runtime: PASS/FAIL
- diagnostics: PASS/FAIL
- modules: PASS/FAIL
- CLI: PASS/FAIL

Integration:
- full single-module program: PASS/FAIL
- full multi-module project: PASS/FAIL

Verification:
- pytest: PASS/FAIL
- ruff check .: PASS/FAIL
- mypy src: PASS/FAIL

Language/spec deviations found:
- ...

Implementation bugs fixed:
- ...

Remaining gaps:
- ...

Pure-language core ready for agentic work: YES/NO
```

Do not begin agentic Kaj until this checkpoint is complete and the suite is green.
