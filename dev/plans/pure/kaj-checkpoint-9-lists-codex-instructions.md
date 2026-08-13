# Kaj Checkpoint 9 — Lists

**Audience:** Codex / implementation agent  
**Checkpoint:** 9  
**Goal:** Implement `List<T>`, list literals, indexing, `count`, and `for` iteration.

---

# 1. Primary Instruction

Implement **Checkpoint 9 only**.

Before editing code, read:

```text
docs/language/lists.md
docs/internals/interpreter.md
docs/language/functions.md
docs/language/primitive-types.md
docs/internals/name-resolution.md
docs/internals/ast.md
dev/plans/pure-language-v0.md
```

Treat:

```text
docs/language/lists.md
```

as authoritative.

Do not begin Maps, Records, Enums, Optional/Result, or list mutation APIs.

---

# 2. Acceptance Target

This program must type-check and execute:

```kaj
let values = [1, 2, 3]

for value in values {
    print(value)
}
```

Output:

```text
1
2
3
```

---

# 3. Extend Semantic Types

Add:

```text
ListType(element_type)
```

or an equivalently explicit semantic representation.

Do not use raw strings.

Support recursive nesting:

```text
List<List<Int>>
```

Type equality compares element types recursively.

---

# 4. Type Annotation Resolution

Give semantic meaning to:

```text
List<T>
```

Rules:

```text
exactly one type argument
```

Invalid arity:

```text
TYPE_INVALID_TYPE_ARGUMENTS
```

Examples:

```kaj
let x: List<Int> = [1]
let y: List<List<String>> = [["a"]]
```

---

# 5. List Literal Inference

Without expected context:

```kaj
[1, 2, 3]
```

→ `List<Int>`

```kaj
[1, 2.5]
```

→ `List<Decimal>`

```kaj
["a", 1]
```

→ `TYPE_MISMATCH`

Use narrow common element typing:

```text
same type -> same type
Int + Decimal -> Decimal
otherwise incompatible
```

---

# 6. Empty Lists

This must fail:

```kaj
let values = []
```

with:

```text
TYPE_CANNOT_INFER_LIST_ELEMENT
```

This must pass:

```kaj
let values: List<Int> = []
```

Use expected annotation type to type the literal.

---

# 7. Contextual List Literal Checking

When expected type is:

```text
List<T>
```

check each literal element against `T`.

Example:

```kaj
let values: List<Decimal> = [1, 2, 3]
```

valid.

Record element-level Int->Decimal runtime coercions or enough expected type information for the interpreter to materialize them.

Do not globally make `List<Int>` assignable to `List<Decimal>`.

---

# 8. List Assignability

Implement invariant list assignment:

```text
List<T> -> List<T>
```

Only exact element type equality.

Do not add generic covariance.

Literal contextual typing is separate.

---

# 9. Index Typing

For:

```kaj
values[index]
```

if:

```text
values: List<T>
index: Int
```

then result:

```text
T
```

Wrong index type:

```text
TYPE_MISMATCH
```

Non-list indexing remains unsupported for this checkpoint unless already defined elsewhere.

---

# 10. `count` Member Typing

For:

```kaj
values.count
```

if:

```text
values: List<T>
```

result is:

```text
Int
```

Unknown member:

```text
TYPE_UNKNOWN_MEMBER
```

Do not implement `count()`.

Do not expose arbitrary runtime/Python members.

---

# 11. `for` Type Checking

For:

```kaj
for value in values {
    ...
}
```

type-check iterable.

It must be:

```text
List<T>
```

Otherwise:

```text
TYPE_NOT_ITERABLE
```

Assign loop-variable symbol type:

```text
T
```

Then type-check body.

---

# 12. Loop Variable Mutability

Loop variable is immutable.

Assignment to it:

```text
ASSIGN_TO_IMMUTABLE
```

Do not add mutable loop syntax.

---

# 13. Function Integration

Extend function type annotation support so:

```kaj
fn first(values: List<Int>) -> Int {
    return values[0]
}
```

works.

Calls must enforce List type compatibility.

Direct list literal arguments should use expected parameter type context if the existing type checker architecture supports expected-type propagation.

---

# 14. Runtime List Value

Implement explicit controlled runtime list value.

Recommended:

```text
KajList(elements)
```

Do not expose Python list APIs.

The implementation may internally store a tuple/list of Kaj runtime values.

---

# 15. Runtime List Literal

Evaluate elements left-to-right.

Materialize statically approved Int->Decimal element promotions.

Construct Kaj list runtime value.

---

# 16. Runtime Indexing

Evaluate:

```text
object
then index
```

Require Kaj list + Kaj Int according to already-approved typing.

Bounds:

```text
0 <= index < count
```

Failure:

```text
RUNTIME_INDEX_OUT_OF_BOUNDS
```

Negative Python-style indexing is forbidden.

---

# 17. Runtime `count`

For Kaj list member access:

```text
count
```

return Kaj Int length.

Do not delegate arbitrary attributes with `getattr`.

---

# 18. Runtime `for`

Implement `ForStatement`.

Steps:

1. evaluate iterable once
2. confirm runtime Kaj list defensively
3. iterate elements in order
4. for each element:
   - create fresh block environment
   - bind loop-variable symbol to element
   - execute body
5. propagate `_ReturnSignal` unchanged

Do not implement generic Python iteration.

---

# 19. Missing Return Rule

Do not change Checkpoint 7 definite-return semantics.

A `for` loop does not guarantee return.

---

# 20. Print

Do not broaden `print` to whole-list formatting unless required by existing architecture.

The acceptance test only prints list elements.

Primitive element printing already exists.

---

# 21. No Mutation

Do not implement:

```text
append
remove
push
pop
index assignment
slices
```

`var values` permits rebinding the variable, not mutating list contents.

---

# 22. No List Operators

Do not implement:

```text
list + list
list * int
list equality
truthiness
```

unless separately specified later.

Python behavior must not leak in.

---

# 23. Required Diagnostics

Add:

```text
TYPE_CANNOT_INFER_LIST_ELEMENT
TYPE_INVALID_TYPE_ARGUMENTS
TYPE_UNKNOWN_MEMBER
TYPE_NOT_ITERABLE
RUNTIME_INDEX_OUT_OF_BOUNDS
```

Reuse:

```text
TYPE_MISMATCH
ASSIGN_TO_IMMUTABLE
```

---

# 24. Error Recovery

List checking should continue after one invalid element where practical.

Use existing internal error type.

Do not produce redundant cascades from a list whose element type is already invalid.

---

# 25. Suggested Files

Likely extend:

```text
src/kaj/semantic/types.py
src/kaj/semantic/type_checker.py
src/kaj/runtime/values.py
src/kaj/runtime/interpreter.py
src/kaj/runtime/errors.py
```

Add focused tests:

```text
tests/semantic/test_lists.py
tests/semantic/test_list_indexing.py
tests/semantic/test_for_typing.py

tests/runtime/test_lists.py
tests/runtime/test_list_indexing.py
tests/runtime/test_for_iteration.py
```

Follow current repository conventions.

---

# 26. Required Tests — Inference

Test:

```kaj
let values = [1, 2, 3]
```

→ `List<Int>`

```kaj
let values = [1, 2.5]
```

→ `List<Decimal>`

```kaj
let values = ["a", 1]
```

→ `TYPE_MISMATCH`

```kaj
let values = []
```

→ `TYPE_CANNOT_INFER_LIST_ELEMENT`

```kaj
let values: List<Int> = []
```

valid.

---

# 27. Required Tests — Contextual Promotion

Test:

```kaj
let values: List<Decimal> = [1, 2, 3]
```

type-checks and runtime stores Decimal elements.

Reject:

```kaj
let values: List<Int> = [1, 2.5]
```

---

# 28. Required Tests — Indexing

Test:

```kaj
let values = [10, 20, 30]
print(values[1])
```

→ `20`

Test wrong index type.

Test negative index runtime failure.

Test index == count runtime failure.

Test large out-of-range index runtime failure.

No raw Python `IndexError`.

---

# 29. Required Tests — Count

Test:

```kaj
let values = [1, 2, 3]
print(values.count)
```

→ `3`

Test empty list count with annotation:

```kaj
let values: List<Int> = []
print(values.count)
```

→ `0`

Unknown list member must fail statically.

---

# 30. Required Tests — For

Required:

```kaj
let values = [1, 2, 3]

for value in values {
    print(value)
}
```

→

```text
1
2
3
```

Verify loop variable type is Int.

Verify loop variable unavailable after loop through resolver behavior.

Verify loop variable immutable.

Verify iteration order.

Verify iterable evaluated once where observable.

---

# 31. Required Tests — Scope

Test:

```kaj
let value = 100
let values = [1, 2]

for value in values {
    print(value)
}

print(value)
```

Output:

```text
1
2
100
```

This proves loop-variable shadowing and runtime symbol identity.

---

# 32. Required Tests — Nested Lists

If parser/index chaining supports it:

```kaj
let rows = [[1, 2], [3, 4]]
print(rows[1][0])
```

→ `3`

Verify inferred type:

```text
List<List<Int>>
```

---

# 33. Required Tests — Function Integration

Test:

```kaj
fn first(values: List<Int>) -> Int {
    return values[0]
}

print(first([7, 8]))
```

→ `7`

Test wrong list element type at call.

Test annotated empty-list argument if contextual typing supports it.

---

# 34. Required Tests — Rebinding

Test:

```kaj
var values = [1, 2]
values = [3, 4]
print(values[0])
```

→ `3`

Reject rebind with incompatible List type.

---

# 35. End-to-End Acceptance

Run the entire pipeline:

```text
source
→ lexer
→ parser
→ resolver
→ type checker
→ interpreter
```

with:

```kaj
let values = [1, 2, 3]

for value in values {
    print(value)
}
```

Captured output must be exactly:

```text
1
2
3
```

with one newline after each item.

---

# 36. Suggested Implementation Order

### Step 1
Read `docs/language/lists.md` and inspect current type/runtime architecture.

### Step 2
Add `ListType`.

### Step 3
Implement `List<T>` annotation resolution and arity checking.

### Step 4
Implement list literal inference.

### Step 5
Implement contextual list literal typing and empty lists.

### Step 6
Implement invariant List assignability.

### Step 7
Implement index expression typing.

### Step 8
Implement list `.count` member typing.

### Step 9
Implement `for` iterable and loop-variable typing.

### Step 10
Implement Kaj runtime list value.

### Step 11
Implement list literal runtime and promotions.

### Step 12
Implement runtime indexing/bounds errors.

### Step 13
Implement runtime `.count`.

### Step 14
Implement runtime `for`.

### Step 15
Add function integration tests.

### Step 16
Run complete tests and quality gates.

### Step 17
Update:

```text
dev/plans/pure-language-v0.md
```

Do not proceed to Checkpoint 10.

---

# 37. Verification

Run:

```bash
pytest
ruff check .
mypy src
kaj --version
python -m kaj
```

If a minimal `kaj run` exists, run the acceptance program through it too.

All prior checkpoint tests must remain green.

---

# 38. Definition of Done

Checkpoint 9 is complete only when:

```text
[ ] docs/language/lists.md treated as authoritative

[ ] ListType implemented
[ ] nested List types supported
[ ] List annotation arity validated

[ ] homogeneous list inference works
[ ] Int/Decimal common element promotion works
[ ] heterogeneous list mismatch diagnosed
[ ] empty list inference error implemented
[ ] typed empty lists work
[ ] contextual List literal typing works

[ ] List assignability invariant
[ ] no implicit List<Int> -> List<Decimal>

[ ] index typing implemented
[ ] index requires Int
[ ] index result type correct
[ ] zero-based indexing works
[ ] negative indices rejected at runtime
[ ] bounds errors structured

[ ] count property typed as Int
[ ] count runtime implemented
[ ] unknown member diagnostic implemented

[ ] for requires List
[ ] loop variable gets element type
[ ] loop variable immutable
[ ] for executes in order
[ ] iterable evaluated once
[ ] fresh body environment each iteration
[ ] return propagates through loop

[ ] function annotations/calls support List<T>

[ ] explicit controlled runtime list representation
[ ] Python list APIs do not leak
[ ] Python negative indexing does not leak
[ ] Python truthiness does not leak

[ ] no list mutation APIs
[ ] no index assignment
[ ] no list concatenation/repetition
[ ] no list equality
[ ] no Maps checkpoint work

[ ] acceptance output is 1 / 2 / 3
[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] Checkpoints 0-8 remain passing

[ ] dev/plans/pure-language-v0.md updated
```

---

# 39. Completion Report

When finished, report:

```text
Checkpoint 9 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

List type model:
- ...

Literal inference:
- ...

Indexing:
- ...

Count:
- ...

For iteration:
- ...

Runtime representation:
- ...

Diagnostics:
- ...

Acceptance output:
- ...

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

Do not proceed to Checkpoint 10.
