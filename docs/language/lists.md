# Kaj Lists

**Status:** Authoritative for Kaj v0 Checkpoint 9  
**Scope:** `List<T>`, list literals, index access, `count`, `first`, `last`, and `for` iteration
**Not covered:** list mutation APIs, slicing, comprehensions, iterators as first-class values, maps, tuples, records

`List<T>.first` and `.last` return `Optional<T>`. Empty lists return `none`; non-empty lists return `some(value)`.

---

# 1. Purpose

Checkpoint 9 introduces Kaj's first generic collection type:

```text
List<T>
```

and makes these constructs fully semantic and executable:

```kaj
let values = [1, 2, 3]

for value in values {
    print(value)
}
```

The expected output is:

```text
1
2
3
```

---

# 2. List Type

A Kaj list has one element type:

```text
List<T>
```

Examples:

```text
List<Int>
List<String>
List<Decimal>
List<Bool>
```

Lists are homogeneous.

A single list cannot contain unrelated element types.

---

# 3. List Literal Inference

For:

```kaj
[1, 2, 3]
```

infer:

```text
List<Int>
```

For:

```kaj
["a", "b"]
```

infer:

```text
List<String>
```

For:

```kaj
[1, 2.5]
```

infer:

```text
List<Decimal>
```

because `Int -> Decimal` promotion is allowed.

---

# 4. Homogeneity

All list elements must be assignable to one common element type.

Examples:

```kaj
[1, 2, 3]
```

valid → `List<Int>`

```kaj
[1, 2.5, 3]
```

valid → `List<Decimal>`

```kaj
["a", 1]
```

invalid → `TYPE_MISMATCH`

Do not introduce `Any` or union types to make heterogeneous lists legal.

---

# 5. Common Element Type

Checkpoint 9 uses a narrow common-type rule:

```text
all same type -> that type
Int + Decimal mixture -> Decimal
otherwise -> no common type
```

No broader coercion lattice is introduced.

---

# 6. Empty List Literal

An empty list literal:

```kaj
[]
```

does not contain enough information to infer an element type by itself.

Therefore this is invalid:

```kaj
let values = []
```

Emit:

```text
TYPE_CANNOT_INFER_LIST_ELEMENT
```

But an explicit annotation makes it valid:

```kaj
let values: List<Int> = []
```

The annotation supplies the element type.

---

# 7. List Annotation Syntax

The parser already supports generic type expressions.

Checkpoint 9 gives semantic meaning to:

```text
List<T>
```

Valid:

```kaj
let values: List<Int> = [1, 2, 3]
```

`List` must have exactly one type argument.

Invalid:

```text
List
List<Int, String>
```

Recommended diagnostic:

```text
TYPE_INVALID_TYPE_ARGUMENTS
```

---

# 8. Nested Lists

Lists may contain lists.

Example:

```kaj
let rows = [[1, 2], [3, 4]]
```

infers:

```text
List<List<Int>>
```

This follows recursively from normal list element typing.

---

# 9. List Value Semantics

For v0, lists are value-like runtime values.

Checkpoint 9 does not introduce list mutation operations.

There is no:

```text
append
push
remove
insert
list[index] = value
```

in this checkpoint.

Index assignment remains deferred.

---

# 10. List Runtime Representation

The Python reference interpreter may use a dedicated Kaj runtime list wrapper or a carefully controlled Python list/tuple internally.

Preferred design:

```text
KajList
    elements
```

or another explicit wrapper.

Do not expose arbitrary Python list methods as Kaj behavior.

The runtime representation must preserve Kaj semantics independently of Python.

---

# 11. List Literal Runtime

Evaluate list elements left-to-right.

Example:

```kaj
[f(), g(), h()]
```

evaluation order is:

```text
f()
g()
h()
```

Then construct the Kaj list value.

Any statically approved `Int -> Decimal` element promotion must be materialized.

Example:

```kaj
[1, 2.5]
```

runtime contents should both semantically be Decimal values.

---

# 12. Index Access

Kaj supports:

```kaj
values[index]
```

For:

```text
List<T>
```

index access has type:

```text
T
```

Example:

```kaj
let values = [10, 20]
let x = values[0]
```

infers:

```text
x: Int
```

---

# 13. Index Type

List indices must have type:

```text
Int
```

Invalid:

```kaj
values[1.5]
values["0"]
```

must produce:

```text
TYPE_MISMATCH
```

Do not implicitly convert Decimal/String to Int.

---

# 14. Zero-Based Indexing

Kaj list indexing is zero-based.

Example:

```kaj
let values = [10, 20, 30]

print(values[0])
```

prints:

```text
10
```

---

# 15. Negative Indices

Negative indices are invalid in Kaj v0.

Unlike Python:

```text
values[-1]
```

does not mean the last element.

It produces a runtime bounds error.

The static type is still valid because `-1` is Int; bounds are checked at runtime.

---

# 16. Bounds Checking

Index access must perform bounds checks.

For a list of length `n`, valid indices satisfy:

```text
0 <= index < n
```

Out-of-bounds access produces:

```text
RUNTIME_INDEX_OUT_OF_BOUNDS
```

Do not expose Python `IndexError`.

---

# 17. `count`

Checkpoint 9 adds:

```text
list.count
```

as a built-in list property.

Example:

```kaj
let values = [1, 2, 3]
print(values.count)
```

prints:

```text
3
```

The type of:

```text
List<T>.count
```

is:

```text
Int
```

---

# 18. `count` Is a Property

Use:

```kaj
values.count
```

not:

```kaj
values.count()
```

for v0.

`count` returns the number of elements in the list.

This avoids prematurely designing a collection method-call model.

---

# 19. Other List Members

No other list members are defined in Checkpoint 9.

Therefore:

```kaj
values.foo
```

must produce a semantic type/member error.

Recommended code:

```text
TYPE_UNKNOWN_MEMBER
```

Do not expose Python list attributes or methods.

---

# 20. Member Typing

For a `MemberAccessExpression` whose object has type:

```text
List<T>
```

and member is:

```text
count
```

infer:

```text
Int
```

No lexical lookup is performed for `count`.

---

# 21. `for` Iteration

Checkpoint 9 gives full semantics to:

```kaj
for value in values {
    ...
}
```

where:

```text
values: List<T>
```

The loop variable has type:

```text
T
```

Example:

```kaj
let values = [1, 2, 3]

for value in values {
    print(value)
}
```

Inside the loop:

```text
value: Int
```

---

# 22. `for` Iterable Requirement

The iterable expression must have type:

```text
List<T>
```

in Checkpoint 9.

Invalid:

```kaj
for x in 10 {
}
```

Recommended diagnostic:

```text
TYPE_NOT_ITERABLE
```

Do not make arbitrary Python values iterable.

---

# 23. Loop Variable Type

The resolver already creates a loop-variable symbol.

Checkpoint 9 assigns that symbol the list element type.

Example:

```kaj
let values: List<Decimal> = [1, 2.5]

for value in values {
}
```

Inside the loop:

```text
value: Decimal
```

---

# 24. Loop Variable Mutability

The `for` loop variable is immutable in Kaj v0.

Example:

```kaj
for value in values {
    value = 10
}
```

must produce:

```text
ASSIGN_TO_IMMUTABLE
```

Do not introduce `for var value in ...` syntax in this checkpoint.

---

# 25. Loop Runtime Semantics

For:

```kaj
for value in values {
    body
}
```

runtime semantics:

```text
evaluate iterable expression once
iterate elements from first to last
for each element:
    create a fresh loop-body block environment
    bind loop-variable symbol to current element
    execute body
```

The iterable expression is not reevaluated each iteration.

---

# 26. Iteration Order

Lists iterate in stored element order.

Example:

```kaj
[1, 2, 3]
```

iterates:

```text
1
2
3
```

This is deterministic.

---

# 27. Fresh Scope Per Iteration

Each iteration creates a fresh block environment.

This matches the runtime model established for scoped loop bodies.

Bindings declared inside one iteration do not leak into another or outside the loop.

---

# 28. Return Through `for`

If a function executes `return` inside a `for` body, it exits the function immediately.

The existing return-control mechanism must propagate through loop execution.

---

# 29. Break / Continue

Checkpoint 19 implements `break` and `continue` for list loops and all other supported loops. Each targets the nearest enclosing loop.

---

# 30. Missing Return Analysis

Checkpoint 7's conservative rule remains:

A `for` loop is **not** considered definitely returning, because a list may be empty.

Example:

```kaj
fn f(values: List<Int>) -> Int {
    for value in values {
        return value
    }
}
```

still requires a return after the loop.

---

# 31. Function Parameters With List Types

Checkpoint 9 extends function annotation support to:

```text
List<T>
```

Example:

```kaj
fn first(values: List<Int>) -> Int {
    return values[0]
}
```

This must type-check.

Function call argument compatibility includes recursive list type compatibility.

---

# 32. List Assignability

List assignability is invariant except for element-level safe widening during literal construction.

Canonical assignment rule:

```text
List<T> -> List<T>
```

Do **not** generally define:

```text
List<Int> -> List<Decimal>
```

as implicit assignment compatibility in v0.

Example:

```kaj
let ints: List<Int> = [1, 2]
let decimals: List<Decimal> = ints
```

is not implicitly allowed.

This keeps generic container variance simple and safe.

However:

```kaj
let decimals: List<Decimal> = [1, 2]
```

is valid because the literal can be contextually constructed as `List<Decimal>` with element promotions.

---

# 33. Contextual List Literal Typing

When a list literal has an expected type:

```text
List<T>
```

each element is checked for assignability to `T`.

Example:

```kaj
let values: List<Decimal> = [1, 2, 3]
```

valid.

Each Int element is promoted to Decimal at runtime construction.

Example:

```kaj
let values: List<Int> = [1, 2.5]
```

invalid.

---

# 34. Empty List With Context

This is valid:

```kaj
let values: List<String> = []
```

The empty literal receives type:

```text
List<String>
```

from context.

Likewise a function argument may provide context if the type checker already supports expected-type propagation cleanly.

At minimum annotated binding context is required.

---

# 35. Equality

List equality is deferred in Checkpoint 9.

Do not define:

```kaj
[1, 2] == [1, 2]
```

yet unless explicitly added by a later semantic decision.

Primitive equality rules remain unchanged.

---

# 36. Arithmetic

Lists have no arithmetic operators in Checkpoint 9.

Invalid:

```kaj
[1] + [2]
[1] * 3
```

Do not inherit Python list concatenation/repetition.

---

# 37. Truthiness

Lists are not truthy/falsy.

Invalid:

```kaj
if values {
}
```

Conditions still require `Bool`.

---

# 38. `print` and Lists

Checkpoint 23 extends deterministic display to entire lists. Therefore:

```kaj
print(values)
```

prints a deterministic bracketed representation, recursively using Kaj display for elements.

---

# 39. Type Representation

Extend the semantic type model with an explicit parameterized list type.

Conceptually:

```text
ListType(element_type)
```

or:

```text
GenericTypeInstance(
    constructor=List,
    arguments=(T,)
)
```

For the current compiler, a dedicated `ListType` is acceptable and simpler.

Do not represent `List<Int>` as a raw string.

---

# 40. Type Equality

Two list types are equal iff their element types are equal.

Examples:

```text
List<Int> == List<Int>
List<Int> != List<Decimal>
List<List<Int>> == List<List<Int>>
```

---

# 41. Error Type Propagation

If one list element already has internal `ERROR` type, avoid producing cascades when possible.

Still type-check remaining elements.

Do not stop at the first invalid element.

---

# 42. List Literal Diagnostics

Required stable diagnostic:

```text
TYPE_CANNOT_INFER_LIST_ELEMENT
```

for context-free:

```kaj
[]
```

Use:

```text
TYPE_MISMATCH
```

for incompatible element types.

---

# 43. Index Diagnostics

Wrong index type:

```text
TYPE_MISMATCH
```

Out of bounds at runtime:

```text
RUNTIME_INDEX_OUT_OF_BOUNDS
```

Unknown list member:

```text
TYPE_UNKNOWN_MEMBER
```

Non-list iterable:

```text
TYPE_NOT_ITERABLE
```

Invalid `List` arity:

```text
TYPE_INVALID_TYPE_ARGUMENTS
```

---

# 44. Runtime Index Access

For:

```kaj
values[index]
```

runtime:

```text
evaluate values
evaluate index
bounds-check
return element
```

Evaluation order is object first, then index expression.

---

# 45. Runtime `count`

For:

```kaj
values.count
```

evaluate the object once and return its element count as Kaj Int.

Do not call arbitrary Python attributes.

Dispatch explicitly on Kaj list runtime value and member name `count`.

---

# 46. Runtime `for`

Evaluate the list expression once.

Then iterate over a stable snapshot/reference according to the list's value semantics.

Since mutation is not introduced, concurrent structural modification is not a concern in Checkpoint 9.

---

# 47. No List Mutation Yet

Do not implement:

```text
append
extend
remove
pop
clear
sort
reverse
index assignment
slice assignment
```

A `var` binding containing a list means the variable may later be rebound to another list, not that the list object itself exposes mutation APIs.

Example:

```kaj
var values = [1, 2]
values = [3, 4]
```

may be valid if both sides have type `List<Int>`.

But:

```kaj
values[0] = 3
```

remains unsupported.

---

# 48. Nested Runtime Lists

Nested lists must preserve element structure.

Example:

```kaj
let rows = [[1, 2], [3, 4]]
print(rows[1][0])
```

prints:

```text
3
```

if chained indexing is already supported by the AST/parser.

---

# 49. Function Call Compatibility

Examples:

```kaj
fn sum(values: List<Int>) -> Int {
    ...
}

sum([1, 2, 3])
```

valid.

```kaj
sum(["a"])
```

→ `TYPE_MISMATCH`

A list literal passed directly to a function parameter may use the expected parameter type as contextual typing where implemented.

---

# 50. Source of Truth

For Kaj v0 list semantics:

```text
docs/language/lists.md
        +
type-checker tests
        +
runtime tests
        +
implementation
```

must agree.

---

# 51. Acceptance Example

This program:

```kaj
let values = [1, 2, 3]

for value in values {
    print(value)
}
```

must produce:

```text
1
2
3
```

with one newline after each value.

---

# 52. Definition of Done

Checkpoint 9 is complete when:

```text
[ ] semantic List<T> type implemented
[ ] List requires exactly one type argument
[ ] nested List types supported

[ ] list literal inference implemented
[ ] homogeneous same-type lists inferred
[ ] Int/Decimal list literals promote to Decimal
[ ] heterogeneous incompatible lists rejected
[ ] empty list without context rejected
[ ] annotated empty list supported
[ ] contextual annotated list checking implemented

[ ] list assignability implemented
[ ] List<Int> -> List<Decimal> not generally implicit
[ ] literal elements may promote under List<Decimal> context

[ ] index expression typing implemented
[ ] list index requires Int
[ ] index expression result type = element type
[ ] zero-based indexing implemented
[ ] negative index runtime rejected
[ ] runtime bounds checking implemented
[ ] RUNTIME_INDEX_OUT_OF_BOUNDS implemented

[ ] List<T>.count typing implemented
[ ] count returns Int
[ ] count runtime implemented
[ ] unknown list members rejected

[ ] for-loop iterable must be List<T>
[ ] loop variable receives T
[ ] loop variable immutable
[ ] for runtime implemented
[ ] iterable evaluated once
[ ] iteration order deterministic
[ ] fresh body environment per iteration
[ ] return propagates through for loop

[ ] function annotations support List<T>
[ ] function parameters/calls support List<T>

[ ] explicit Kaj list runtime representation or controlled equivalent exists
[ ] no arbitrary Python list methods exposed
[ ] no Python truthiness leakage
[ ] no Python negative indexing semantics leak

[ ] list mutation APIs not implemented
[ ] index assignment not implemented
[ ] list arithmetic not implemented
[ ] list equality not implemented
[ ] print(list) not required

[ ] acceptance program prints 1, 2, 3
[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] Checkpoints 0-8 remain passing
```
