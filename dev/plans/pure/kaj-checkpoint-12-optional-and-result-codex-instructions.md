# Kaj Checkpoint 12 — Optional and Result

**Audience:** Codex / implementation agent  
**Checkpoint:** 12  
**Goal:** Implement language-standard `Optional<T>` and `Result<T, E>` using enum/tagged-type semantics.

---

# 1. Primary Instruction

Implement **Checkpoint 12 only**.

Before editing code, read:

```text
docs/language/optional-and-result.md
docs/language/enums-and-match.md
docs/language/records.md
docs/language/lists.md
docs/language/functions.md
docs/language/primitive-types.md
docs/internals/name-resolution.md
docs/internals/ast.md
docs/compiler/ast-json.md
docs/internals/interpreter.md
dev/plans/pure-language-v0.md
```

Treat:

```text
docs/language/optional-and-result.md
```

as authoritative.

Do not implement `?`.

Do not begin Checkpoint 13 Maps.

---

# 2. Acceptance Target

This must type-check and execute:

```kaj
match maybe_user {
    some(user) => print(user.name)
    none => print("missing")
}
```

assuming:

```text
maybe_user: Optional<User>
```

Both `some` and `none` branches must be recognized through the standard tagged-type semantics.

---

# 3. Semantic Types

Add explicit semantic types:

```text
OptionalType(value_type)
ResultType(ok_type, err_type)
```

or reuse a generic tagged-type abstraction if the enum implementation already supports it cleanly.

Do not represent them only as strings.

---

# 4. Generic Type Resolution

Recognize:

```text
Optional<T>
Result<T, E>
```

in semantic type annotations.

Validate arity:

```text
Optional -> exactly 1
Result -> exactly 2
```

Invalid:

```text
TYPE_INVALID_TYPE_ARGUMENTS
```

Support recursive type arguments using all currently known Kaj types.

---

# 5. Preserve Primitive `None`

Do not remove or redefine primitive:

```kaj
none
```

with type:

```text
None
```

The existing behavior:

```kaj
let x = none
```

must continue to infer primitive `None`.

---

# 6. Contextual Optional `none`

When an expected type is:

```text
Optional<T>
```

a `none` expression constructs:

```text
Optional<T>.none
```

Examples requiring expected-type propagation:

```kaj
let x: Optional<Int> = none
```

```kaj
fn f() -> Optional<Int> {
    return none
}
```

```kaj
use(none)
```

where parameter is `Optional<Int>`.

Do not treat uncontextualized `none` as Optional.

---

# 7. `some` Typing

Recognize:

```kaj
some(expression)
```

as the standard Optional constructor, not an ordinary function call.

Without expected type:

```text
payload type T
→ Optional<T>
```

Example:

```kaj
let x = some(10)
```

→ `Optional<Int>`.

With expected `Optional<T>`, check payload assignability to `T`.

---

# 8. `ok` Typing

Recognize:

```kaj
ok(expression)
```

as standard Result constructor.

Require expected:

```text
Result<T, E>
```

in v0 because `E` cannot be inferred from `ok` alone.

If no expected Result type:

```text
TYPE_CANNOT_INFER_RESULT_TYPE
```

With context, check payload against `T`.

---

# 9. `err` Typing

Recognize:

```kaj
err(expression)
```

as standard Result constructor.

Require expected:

```text
Result<T, E>
```

because `T` cannot be inferred from `err` alone.

Without context:

```text
TYPE_CANNOT_INFER_RESULT_TYPE
```

With context, check payload against `E`.

---

# 10. Expected-Type Propagation

Extend the type checker enough to pass expected types into these contexts:

```text
annotated binding initializer
assignment RHS
function return expression
function call argument
record field initializer
enum payload initializer
annotated/contextual list literal element
```

This is necessary for `none`, `ok`, and `err`.

Do not redesign the entire type checker into unconstrained bidirectional inference if a narrow expected-type API suffices.

---

# 11. Assignability

Implement invariant assignment:

```text
Optional<T> -> Optional<T>
Result<T,E> -> Result<T,E>
```

No generic variance.

Contextual construction/payload promotion is separate.

---

# 12. Runtime Representation

Prefer reusing the enum/tagged runtime abstraction where clean.

Conceptually support:

```text
Optional.some(payload)
Optional.none

Result.ok(payload)
Result.err(payload)
```

Preserve semantic tagged type identity.

Do not encode Optional as Python `None`.

---

# 13. Primitive None Distinction

Add tests proving these runtime values are distinct:

```kaj
let primitive = none
let optional: Optional<Int> = none
```

The first is Kaj primitive None.

The second is Optional.none.

Do not collapse them internally.

---

# 14. Runtime `some`

Evaluate payload once.

Materialize expected-type promotion where required.

Construct Optional tagged value.

---

# 15. Runtime `none`

When statically typed as primitive `None`, produce primitive None runtime value.

When statically typed as `Optional<T>`, produce Optional.none tagged value.

Use type-checker semantic metadata to distinguish these cases.

Do not guess from syntax alone at runtime.

---

# 16. Runtime `ok` / `err`

Evaluate payload once.

Apply approved target payload promotion.

Construct Result tagged value with correct variant.

---

# 17. Match Integration

Reuse enum match infrastructure for:

```text
Optional<T>:
    some
    none

Result<T,E>:
    ok
    err
```

The match checker should treat these as standard variants.

Do not duplicate a completely separate matching engine.

---

# 18. Pattern Binding Types

For Optional:

```text
some(value) -> value: T
none -> no binding
```

For Result:

```text
ok(value) -> value: T
err(error) -> error: E
```

Use normal branch lexical scopes.

---

# 19. Exhaustiveness

Require:

```text
Optional:
some + none

Result:
ok + err
```

Missing one produces:

```text
NON_EXHAUSTIVE_MATCH
```

Reuse enum exhaustiveness machinery where practical.

---

# 20. Duplicate/Unknown Cases

Reuse existing enum/match diagnostics:

```text
TYPE_DUPLICATE_MATCH_CASE
TYPE_UNKNOWN_VARIANT
TYPE_PATTERN_ARITY_MISMATCH
```

for standard tagged types.

---

# 21. Definite Return

An exhaustive Optional/Result match whose every branch definitely returns must count as definitely returning using the same rule as enum matches.

---

# 22. Parser

`Optional<T>` and `Result<T,E>` already use generic type-expression grammar.

`none` already exists.

If `some(...)`, `ok(...)`, `err(...)` parse as normal call expressions, semantic recognition may reuse that AST shape.

Only introduce dedicated constructor AST nodes if required for clarity/stability.

Do not add `?` syntax.

---

# 23. AST JSON

If no new AST node kinds are needed, preserve existing AST JSON unchanged.

If dedicated standard-constructor nodes are introduced, update:

```text
docs/compiler/ast-json.md
schemas/ast/v1.json
serializer/deserializer/tests
```

Do not serialize inferred generic type arguments.

---

# 24. Standard Constructor Resolution

Do not make `some`, `ok`, or `err` ordinary user-overridable value functions.

Recognize these source forms semantically as language-standard constructors.

Do not introduce generic builtin function overload infrastructure just for them.

---

# 25. Required Diagnostics

Add:

```text
TYPE_CANNOT_INFER_RESULT_TYPE
```

Reuse:

```text
TYPE_INVALID_TYPE_ARGUMENTS
TYPE_MISMATCH
TYPE_UNKNOWN_TYPE
TYPE_UNKNOWN_VARIANT
TYPE_PATTERN_ARITY_MISMATCH
TYPE_DUPLICATE_MATCH_CASE
NON_EXHAUSTIVE_MATCH
```

---

# 26. Error Recovery

Bad tagged constructors should produce internal error type and allow surrounding checking to continue.

Examples:

- wrong `some` payload under context
- uncontextualized `ok`
- uncontextualized `err`
- invalid Optional/Result arity
- malformed match pattern

Avoid cascades.

---

# 27. Required Tests — Type Resolution

Test:

```text
Optional<Int>
Optional<List<User>>
Result<Int, String>
Result<User, ErrorRecord>
```

Test invalid arities.

Test nested forms:

```text
Optional<Result<Int, String>>
Result<Optional<User>, String>
```

---

# 28. Required Tests — `some`

Test:

```kaj
let x = some(10)
```

→ `Optional<Int>`.

Test:

```kaj
let x: Optional<Decimal> = some(10)
```

valid with promotion.

Test incompatible contextual payload.

---

# 29. Required Tests — `none`

Test:

```kaj
let x = none
```

→ primitive `None`.

Test:

```kaj
let x: Optional<Int> = none
```

→ `Optional<Int>`.

Test function return context.

Test function argument context.

Test record field context.

---

# 30. Required Tests — `ok`

Test:

```kaj
let result: Result<Int, String> = ok(10)
```

valid.

Test:

```kaj
let result = ok(10)
```

→ `TYPE_CANNOT_INFER_RESULT_TYPE`.

Test Int->Decimal success payload promotion.

---

# 31. Required Tests — `err`

Test:

```kaj
let result: Result<Int, String> = err("failed")
```

valid.

Test uncontextualized err inference failure.

Test Int->Decimal error payload promotion where expected error type is Decimal.

---

# 32. Required Tests — Assignability

Verify exact Optional type assignment.

Reject:

```text
Optional<Int> -> Optional<Decimal>
```

as general assignment.

Verify exact Result type assignment.

Reject differing success/error type parameters.

---

# 33. Required Tests — Optional Match

Required pattern:

```kaj
match maybe_user {
    some(user) => print(user.name)
    none => print("missing")
}
```

Test both runtime variants.

Verify `user` has type `User`.

Verify `user` is scoped only to `some` branch.

---

# 34. Required Tests — Optional Exhaustiveness

Missing `none`:

```text
NON_EXHAUSTIVE_MATCH
```

Missing `some`:

```text
NON_EXHAUSTIVE_MATCH
```

Duplicate cases rejected.

Wrong pattern arity rejected.

---

# 35. Required Tests — Result Match

Test:

```kaj
match result {
    ok(value) => print(value)
    err(error) => print(error)
}
```

with suitable printable primitive payload types.

Test both runtime variants.

Verify binding types.

---

# 36. Required Tests — Result Exhaustiveness

Missing `ok` or `err` must emit:

```text
NON_EXHAUSTIVE_MATCH
```

---

# 37. Required Tests — Return Context

Test:

```kaj
fn find() -> Optional<Int> {
    return none
}
```

valid.

Test:

```kaj
fn find() -> Optional<Int> {
    return some(10)
}
```

valid.

Test:

```kaj
fn parse() -> Result<Int, String> {
    return ok(10)
}
```

valid.

Test:

```kaj
fn parse() -> Result<Int, String> {
    return err("bad")
}
```

valid.

---

# 38. Required Tests — Call Context

Test:

```kaj
fn use(value: Optional<Int>) -> None {
}

use(none)
```

valid.

Test:

```kaj
fn handle(value: Result<Int, String>) -> None {
}

handle(ok(10))
handle(err("bad"))
```

valid.

---

# 39. Required Tests — Lists

Test:

```kaj
let values: List<Optional<Int>> = [
    some(1),
    none
]
```

valid.

Test:

```kaj
let results: List<Result<Int, String>> = [
    ok(1),
    err("bad")
]
```

valid.

Verify runtime tags preserved.

---

# 40. Required Tests — Records

Test:

```kaj
type User {
    nickname: Optional<String>
}
```

with:

```kaj
User {
    nickname: none
}
```

valid due field expected type.

Test Result field similarly.

---

# 41. Required Tests — Runtime Distinction

Prove:

```text
primitive None
Optional.none
```

are distinct runtime representations.

No Python `None` shortcut may erase this distinction.

---

# 42. Required Tests — Definite Return

Test:

```kaj
fn unwrap(value: Optional<Int>) -> Int {
    match value {
        some(x) => return x
        none => return 0
    }
}
```

passes missing-return analysis.

Test equivalent Result function.

---

# 43. Acceptance Fixture

Create an end-to-end fixture such as:

```kaj
type User {
    name: String
}

let maybe_user: Optional<User> = some(
    User {
        name: "Alice"
    }
)

match maybe_user {
    some(user) => print(user.name)
    none => print("missing")
}
```

Expected:

```text
Alice
```

Also execute the `none` variant and expect:

```text
missing
```

---

# 44. Suggested Files

Likely extend:

```text
src/kaj/semantic/types.py
src/kaj/semantic/type_checker.py
src/kaj/runtime/values.py
src/kaj/runtime/interpreter.py
```

Possibly:

```text
src/kaj/semantic/tagged_types.py
```

if it allows clean reuse with enums.

Do not fragment unnecessarily.

---

# 45. Suggested Implementation Order

### Step 1
Read Optional/Result and enum specs.

### Step 2
Add semantic OptionalType and ResultType or generalized tagged types.

### Step 3
Implement generic type-name/arity resolution.

### Step 4
Add expected-type plumbing needed for standard constructors.

### Step 5
Implement `some`.

### Step 6
Implement contextual Optional `none` while preserving primitive None.

### Step 7
Implement contextual `ok` and `err`.

### Step 8
Integrate assignability.

### Step 9
Reuse enum match/pattern/exhaustiveness logic.

### Step 10
Implement runtime tagged values.

### Step 11
Implement runtime constructor execution.

### Step 12
Implement runtime match reuse.

### Step 13
Add function/list/record integration tests.

### Step 14
Run complete repository validation.

### Step 15
Update:

```text
dev/plans/pure-language-v0.md
```

Do not proceed to Checkpoint 13.

---

# 46. Verification

Run:

```bash
pytest
ruff check .
mypy src
kaj --version
python -m kaj
```

If `kaj run` exists, run Optional and Result end-to-end fixtures.

All previous checkpoints must remain green.

---

# 47. Definition of Done

Checkpoint 12 is complete only when:

```text
[ ] OptionalType implemented
[ ] ResultType implemented
[ ] Optional requires exactly one type argument
[ ] Result requires exactly two type arguments
[ ] nested Optional/Result types supported

[ ] primitive None semantics preserved
[ ] `let x = none` remains type None
[ ] contextual Optional none implemented
[ ] primitive None and Optional.none distinguished at runtime

[ ] some(...) implemented
[ ] some infers Optional<T> without context
[ ] contextual some payload checking implemented
[ ] Int->Decimal Optional payload promotion supported

[ ] ok(...) implemented
[ ] err(...) implemented
[ ] ok/err require Result context in v0
[ ] uncontextualized ok/err emit TYPE_CANNOT_INFER_RESULT_TYPE
[ ] contextual ok payload checked against T
[ ] contextual err payload checked against E
[ ] Int->Decimal Result payload promotion supported

[ ] expected-type propagation works for:
    [ ] annotated bindings
    [ ] assignments
    [ ] returns
    [ ] call arguments
    [ ] record fields
    [ ] contextual list elements

[ ] Optional assignability invariant
[ ] Result assignability invariant

[ ] Optional matching supports some/none
[ ] Result matching supports ok/err
[ ] pattern binding types correct
[ ] branch scopes correct
[ ] pattern arity checking reused
[ ] duplicate match checking reused
[ ] exhaustiveness reused
[ ] missing Optional/Result cases emit NON_EXHAUSTIVE_MATCH

[ ] exhaustive Optional/Result matches integrate with definite return

[ ] runtime Optional representation implemented
[ ] runtime Result representation implemented
[ ] some/none/ok/err runtime construction implemented
[ ] payload promotion materialized
[ ] runtime match dispatch works

[ ] Optional works in records
[ ] Optional works in lists
[ ] Optional works in function params/returns
[ ] Result works in records
[ ] Result works in lists
[ ] Result works in function params/returns

[ ] TYPE_CANNOT_INFER_RESULT_TYPE implemented

[ ] acceptance Optional match works
[ ] some case executes correctly
[ ] none case executes correctly

[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] Checkpoints 0-11 remain passing

[ ] no `?` implemented
[ ] no implicit unwrap implemented
[ ] no Result exception behavior implemented
[ ] no wildcard patterns added
[ ] no Maps work begun

[ ] dev/plans/pure-language-v0.md updated
```

---

# 48. Completion Report

When finished, report:

```text
Checkpoint 12 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

Optional type model:
- ...

Result type model:
- ...

Contextual constructor typing:
- ...

Primitive None distinction:
- ...

Match/exhaustiveness integration:
- ...

Runtime representation:
- ...

Diagnostics:
- ...

Acceptance:
- some branch: PASS/FAIL
- none branch: PASS/FAIL
- missing case -> NON_EXHAUSTIVE_MATCH: PASS/FAIL
- uncontextualized ok/err rejection: PASS/FAIL

Verification:
- pytest: PASS/FAIL
- ruff check .: PASS/FAIL
- mypy src: PASS/FAIL
- Kaj CLI: PASS/FAIL

Decisions/deviations:
- ...

Known issues:
- ...
```

Do not proceed to Checkpoint 13.
