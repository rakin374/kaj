# Kaj Optional and Result

**Status:** Authoritative for Kaj v0 `Optional<T>` and `Result<T, E>` semantics  
**Scope:** language-standard tagged types, construction, typing, matching, and runtime behavior  
**Not covered:** `?`, automatic propagation, unwrap operators, combinators, error conversions, generic user-defined enums

---

# 1. Purpose

Kaj provides two language-standard tagged types:

```text
Optional<T>
Result<T, E>
```

They use the same semantic model as enums:

```text
Optional<T>
    some(T)
    none

Result<T, E>
    ok(T)
    err(E)
```

They are built into the language type system rather than declared in user source.

---

# 2. Optional

`Optional<T>` represents either:

```text
some(T)
```

or:

```text
none
```

Example:

```kaj
let maybe_name: Optional<String> = some("Alice")
```

and:

```kaj
let maybe_name: Optional<String> = none
```

---

# 3. Result

`Result<T, E>` represents either:

```text
ok(T)
```

or:

```text
err(E)
```

Example:

```kaj
let result: Result<Int, String> = ok(10)
```

and:

```kaj
let result: Result<Int, String> = err("failed")
```

---

# 4. Tagged-Type Semantics

`Optional<T>` and `Result<T, E>` behave like nominal language-standard enum types.

Conceptually:

```kaj
enum Optional<T> {
    some(value: T)
    none
}
```

and:

```kaj
enum Result<T, E> {
    ok(value: T)
    err(error: E)
}
```

This is a semantic model only.

Users do not redeclare these types.

---

# 5. Type Arity

`Optional` requires exactly one type argument.

Valid:

```text
Optional<Int>
Optional<User>
Optional<List<String>>
```

Invalid:

```text
Optional
Optional<Int, String>
```

`Result` requires exactly two type arguments.

Valid:

```text
Result<Int, String>
Result<User, ErrorRecord>
```

Invalid:

```text
Result
Result<Int>
Result<Int, String, Bool>
```

Invalid arity produces:

```text
TYPE_INVALID_TYPE_ARGUMENTS
```

---

# 6. Type Arguments

Type arguments may use any currently supported Kaj type.

Examples:

```text
Optional<Int>
Optional<User>
Optional<List<User>>

Result<Int, String>
Result<User, String>
Result<List<User>, ErrorRecord>
```

Type arguments are checked recursively through the normal type system.

---

# 7. `some`

`some(expression)` constructs an `Optional<T>` value containing one payload.

If no expected type exists, `T` is inferred from the expression.

Example:

```kaj
let value = some(10)
```

infers:

```text
value: Optional<Int>
```

Example:

```kaj
let value = some("hello")
```

infers:

```text
value: Optional<String>
```

---

# 8. Contextual `some`

When an expected type is available:

```text
Optional<T>
```

the payload expression must be assignable to `T`.

Example:

```kaj
let value: Optional<Decimal> = some(10)
```

is valid through:

```text
Int -> Decimal
```

The runtime payload is materialized as Decimal.

Invalid:

```kaj
let value: Optional<Int> = some(2.5)
```

produces:

```text
TYPE_MISMATCH
```

---

# 9. `none`

Kaj already has the primitive literal:

```kaj
none
```

with primitive type:

```text
None
```

Checkpoint 12 preserves that behavior.

When `none` occurs in a context that explicitly expects:

```text
Optional<T>
```

it is contextually interpreted as the `none` variant of that `Optional<T>`.

Therefore:

```kaj
let value: Optional<Int> = none
```

constructs:

```text
Optional<Int>.none
```

But:

```kaj
let value = none
```

still infers:

```text
None
```

This distinction is intentional.

---

# 10. `none` Without Optional Context

A bare `none` does not infer an `Optional<T>` because no `T` can be determined.

Example:

```kaj
let value = none
```

remains:

```text
value: None
```

To construct an empty Optional, provide an expected Optional type:

```kaj
let value: Optional<Int> = none
```

---

# 11. `ok`

`ok(expression)` constructs the success variant of a `Result<T, E>`.

The payload determines `T`.

However, the error type `E` cannot be inferred from `ok` alone.

Therefore `ok(...)` requires an expected `Result<T, E>` context in Kaj v0.

Valid:

```kaj
let result: Result<Int, String> = ok(10)
```

Invalid without sufficient context:

```kaj
let result = ok(10)
```

because the error type cannot be inferred.

Emit:

```text
TYPE_CANNOT_INFER_RESULT_TYPE
```

---

# 12. `err`

`err(expression)` constructs the error variant of a `Result<T, E>`.

The payload determines `E`.

However, the success type `T` cannot be inferred from `err` alone.

Therefore `err(...)` requires an expected `Result<T, E>` context in Kaj v0.

Valid:

```kaj
let result: Result<Int, String> = err("failed")
```

Invalid:

```kaj
let result = err("failed")
```

Emit:

```text
TYPE_CANNOT_INFER_RESULT_TYPE
```

---

# 13. Contextual `ok`

For expected:

```text
Result<T, E>
```

the `ok` payload must be assignable to `T`.

Example:

```kaj
let result: Result<Decimal, String> = ok(10)
```

is valid through:

```text
Int -> Decimal
```

---

# 14. Contextual `err`

For expected:

```text
Result<T, E>
```

the `err` payload must be assignable to `E`.

Example:

```kaj
let result: Result<Int, Decimal> = err(10)
```

is valid through:

```text
Int -> Decimal
```

---

# 15. Optional Assignability

`Optional<T>` is invariant.

Valid:

```text
Optional<T> -> Optional<T>
```

Do not generally allow:

```text
Optional<Int> -> Optional<Decimal>
```

implicitly.

Contextual construction remains separate:

```kaj
let value: Optional<Decimal> = some(10)
```

is valid because the payload is checked directly against `Decimal`.

---

# 16. Result Assignability

`Result<T, E>` is invariant in both type arguments.

Valid:

```text
Result<T, E> -> Result<T, E>
```

Do not generally allow:

```text
Result<Int, String> -> Result<Decimal, String>
```

or:

```text
Result<Int, SubError> -> Result<Int, Error>
```

implicitly.

No variance rules are introduced in v0.

---

# 17. Matching Optional

`Optional<T>` uses normal enum-style match syntax.

Example:

```kaj
match maybe_user {
    some(user) => print(user.name)
    none => print("missing")
}
```

The match is exhaustive when both variants are covered:

```text
some
none
```

---

# 18. Optional Pattern Binding

For:

```text
Optional<T>
```

the pattern:

```kaj
some(value)
```

introduces:

```text
value: T
```

inside that case.

Example:

```kaj
match maybe_name {
    some(name) => print(name)
    none => print("missing")
}
```

`name` is scoped only to the `some` branch.

---

# 19. Optional `none` Pattern

Inside a match whose scrutinee type is `Optional<T>`:

```kaj
none
```

means the `Optional.none` variant pattern.

It is not interpreted as a pattern for the primitive `None` type.

Pattern meaning is determined by the scrutinee's tagged type.

---

# 20. Matching Result

`Result<T, E>` uses:

```kaj
match result {
    ok(value) => ...
    err(error) => ...
}
```

The match is exhaustive when both variants are covered:

```text
ok
err
```

---

# 21. Result Pattern Binding Types

For:

```text
Result<T, E>
```

pattern:

```kaj
ok(value)
```

binds:

```text
value: T
```

Pattern:

```kaj
err(error)
```

binds:

```text
error: E
```

Each binding exists only in its branch scope.

---

# 22. Exhaustiveness

`Optional<T>` and `Result<T, E>` use the same exhaustiveness rules as ordinary enums.

Missing an Optional variant:

```kaj
match value {
    some(x) => ...
}
```

produces:

```text
NON_EXHAUSTIVE_MATCH
```

Missing a Result variant likewise produces:

```text
NON_EXHAUSTIVE_MATCH
```

---

# 23. Duplicate Cases

Duplicate `some`, `none`, `ok`, or `err` cases are invalid under the same duplicate-match-case rules as ordinary enums.

---

# 24. Pattern Arity

Patterns must match the standard variant payload arity.

Valid:

```text
some(value)
none
ok(value)
err(error)
```

Invalid:

```text
some
some(a, b)
none(x)
ok
ok(a, b)
err
err(a, b)
```

These use normal:

```text
TYPE_PATTERN_ARITY_MISMATCH
```

semantics.

---

# 25. Constructors Are Language-Standard Forms

The identifiers:

```text
some
ok
err
```

are language-standard tagged constructors.

They are not ordinary user-defined functions.

Their typing is handled directly by the type system.

`none` remains the existing keyword/literal with contextual Optional construction behavior.

---

# 26. Constructor Namespace

User value bindings do not redefine the meaning of the language-standard constructor forms:

```text
some(...)
ok(...)
err(...)
```

These forms are recognized semantically as standard tagged constructors.

They are not resolved through ordinary function overloading.

This avoids requiring generic builtin function machinery.

---

# 27. No Qualified Syntax Required

The standard construction syntax is:

```kaj
some(value)
none
ok(value)
err(error)
```

Users do not need:

```text
Optional.some(...)
Optional.none
Result.ok(...)
Result.err(...)
```

in v0.

Qualified standard tagged construction may be considered later if useful.

---

# 28. Runtime Optional Representation

The interpreter should represent Optional values explicitly.

Conceptually:

```text
KajOptionalValue
├── variant: some | none
└── payload: T when some
```

or reuse the same controlled tagged-value runtime representation as enums.

Do not represent Optional merely as Python `None` versus arbitrary Python value.

That would lose semantic type identity and confuse primitive Kaj `None` with `Optional.none`.

---

# 29. Runtime Result Representation

Represent Result explicitly:

```text
KajResultValue
├── variant: ok | err
└── payload
```

or reuse a generic tagged-value runtime representation.

Preserve:

```text
Result<T, E> semantic type
variant identity
payload value
```

---

# 30. Primitive None vs Optional None at Runtime

Primitive:

```kaj
none
```

with type `None`

and:

```kaj
let value: Optional<Int> = none
```

must be distinguishable runtime values.

Conceptually:

```text
Kaj None
```

versus:

```text
Optional<Int>.none
```

Do not collapse them into the same untyped Python `None`.

---

# 31. Constructor Evaluation Order

`some`, `ok`, and `err` each have exactly one payload expression.

Evaluate that expression once.

Materialize any statically approved boundary promotion before storing it in the tagged value.

---

# 32. Runtime Match

Optional/Result matching reuses enum-style runtime match semantics:

```text
evaluate scrutinee once
inspect tag
select branch
bind payload if present
execute selected branch
```

Only one branch executes.

---

# 33. Optional in Records and Lists

Optional types may appear anywhere ordinary types are allowed.

Examples:

```kaj
type User {
    nickname: Optional<String>
}
```

```kaj
let values: List<Optional<Int>> = [
    some(1),
    none
]
```

Contextual typing determines the Optional type of `none` in the list where sufficient expected type exists.

---

# 34. Result in Records and Lists

Likewise:

```kaj
type Response {
    value: Result<String, String>
}
```

and:

```kaj
let results: List<Result<Int, String>> = [
    ok(1),
    err("bad")
]
```

are valid with contextual typing.

---

# 35. Functions

Optional and Result may be used in parameter and return positions.

Examples:

```kaj
fn find_user() -> Optional<User> {
    return none
}
```

```kaj
fn parse() -> Result<Int, String> {
    return ok(10)
}
```

Return-type context supplies the tagged type.

---

# 36. Return Context

A return expression receives the enclosing function's declared return type as expected type.

Therefore:

```kaj
fn find() -> Optional<Int> {
    return none
}
```

constructs `Optional<Int>.none`.

And:

```kaj
fn parse() -> Result<Int, String> {
    return ok(10)
}
```

is valid even though standalone `ok(10)` would not determine the error type.

---

# 37. Call Argument Context

A function parameter type may provide expected type to a tagged constructor.

Example:

```kaj
fn use(value: Optional<Int>) -> None {
}

use(none)
```

is valid.

Likewise:

```kaj
fn handle(result: Result<Int, String>) -> None {
}

handle(ok(10))
```

is valid because the parameter supplies the missing Result type information.

---

# 38. List Literal Context

An annotated list element type may provide context.

Example:

```kaj
let values: List<Optional<Int>> = [
    some(1),
    none
]
```

Both elements have type:

```text
Optional<Int>
```

Likewise:

```kaj
let results: List<Result<Int, String>> = [
    ok(1),
    err("bad")
]
```

---

# 39. No `?` Operator

Checkpoint 12 does not introduce:

```text
?
```

for propagation, unwrapping, chaining, or optional access.

Examples such as:

```text
value?
result?
foo()?.bar
```

have no Kaj v0 semantics yet.

Do not implement them.

---

# 40. No Implicit Unwrap

An `Optional<T>` is not implicitly assignable to `T`.

A `Result<T, E>` is not implicitly assignable to `T` or `E`.

Values must be inspected through `match` in v0.

---

# 41. No Nullability Shortcut

Kaj does not treat every type as nullable.

This is invalid conceptually:

```text
String + implicit absence
```

Optionality is explicit:

```text
Optional<String>
```

Primitive `None` remains a distinct type.

---

# 42. No Exceptions from Result

`Result<T, E>` is an explicit tagged value.

`err(...)` does not throw.

Matching `err` does not catch an exception.

No exception semantics are introduced.

---

# 43. No Automatic Error Conversion

There is no implicit conversion between different error types.

Example:

```text
Result<Int, String>
```

is not implicitly assignable to:

```text
Result<Int, ErrorRecord>
```

---

# 44. AST Representation

`Optional<T>` and `Result<T, E>` use the existing generic type-expression syntax in the AST.

The semantic type checker recognizes these names as language-standard generic tagged types.

Standard constructor forms may use dedicated AST nodes or an unambiguous existing call/literal representation, provided semantic behavior is explicit and stable.

Do not encode runtime values in AST.

---

# 45. AST JSON

AST JSON should represent the source-level syntax used for:

```text
Optional<T>
Result<T, E>
some(...)
none
ok(...)
err(...)
match patterns
```

according to existing AST node representations.

If dedicated constructor AST nodes are introduced, extend AST JSON consistently.

Do not serialize inferred type arguments, runtime tags, or semantic constructor resolution into AST JSON.

---

# 46. Source of Truth

For Kaj v0 Optional and Result semantics:

```text
docs/language/optional-and-result.md
```

defines the enduring language behavior.

Compiler/runtime implementation must conform to it.
