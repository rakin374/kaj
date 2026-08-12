# Kaj Enums and Match

**Status:** Authoritative for Kaj v0 enum and pattern-matching semantics  
**Scope:** enum declarations, payload variants, enum construction, `match`, pattern binding, and exhaustiveness  
**Not covered:** guards, nested/destructuring patterns beyond enum payloads, wildcard patterns, generic enums, methods, traits, inheritance

---

# 1. Purpose

Enums define nominal sum types with a fixed set of variants.

Example:

```kaj
enum Status {
    pending
    complete
}
```

A value is constructed with:

```kaj
Status.pending
```

and inspected with:

```kaj
match status {
    pending => print("pending")
    complete => print("complete")
}
```

Kaj requires enum matches to be exhaustive.

---

# 2. Enum Declaration Syntax

An enum declaration uses:

```kaj
enum TypeName {
    variant
    variant(field: Type, ...)
}
```

Examples:

```kaj
enum Status {
    pending
    complete
}
```

and:

```kaj
enum Result {
    success(value: Int)
    failure(message: String)
}
```

Each enum declaration introduces one nominal enum type.

---

# 3. Nominal Typing

Enums are nominally typed.

Two enum declarations with identical variant names are still distinct types.

Example:

```kaj
enum Status {
    pending
    complete
}

enum JobState {
    pending
    complete
}
```

`Status` and `JobState` are not interchangeable.

---

# 4. Variant Names

Variant names are unique within one enum declaration.

Invalid:

```kaj
enum Status {
    pending
    pending
}
```

This is a semantic declaration error.

Recommended diagnostic:

```text
TYPE_DUPLICATE_VARIANT
```

---

# 5. Payload Variants

A variant may carry zero or more named payload fields.

Example:

```kaj
enum Message {
    quit
    text(value: String)
    move(x: Int, y: Int)
}
```

The payload field order is the source declaration order.

Payload field names must be unique within that variant.

---

# 6. Payload Field Types

Payload fields use normal Kaj type annotations.

Supported types include already available semantic types such as:

```text
primitive types
List<T>
record types
enum types
```

Forward enum type references are allowed through type-name predeclaration.

Unknown payload field types produce:

```text
TYPE_UNKNOWN_TYPE
```

---

# 7. Type Namespace

Enum type names live in Kaj's type namespace alongside record types.

A top-level enum declaration introduces one nominal type symbol.

Duplicate type names across records/enums are invalid.

Example:

```kaj
type Status {
    value: Int
}

enum Status {
    pending
}
```

is invalid because the same type name is declared twice in the module type namespace.

---

# 8. Enum Type Predeclaration

All top-level enum and record type names are predeclared before their internal field/payload types are resolved.

This supports:

```kaj
enum A {
    next(value: B)
}

enum B {
    back(value: A)
}
```

at the type level.

---

# 9. Unit Variant Construction

A zero-payload variant is constructed as:

```kaj
Status.pending
```

This expression has type:

```text
Status
```

The syntax is enum-type-qualified.

---

# 10. Payload Variant Construction

A payload variant is constructed with:

```kaj
TypeName.variant(
    field: expression,
    ...
)
```

Example:

```kaj
Message.text(value: "hello")
```

or:

```kaj
Message.move(x: 10, y: 20)
```

Payload construction is named-field based.

---

# 11. Payload Argument Rules

Each declared payload field is required.

Unknown fields are invalid.

Duplicate payload fields are invalid.

Field expressions must be assignable to the declared payload field types.

Existing promotion rules such as:

```text
Int -> Decimal
```

apply.

---

# 12. Payload Construction Result

Every variant constructor expression has the enum type.

Example:

```kaj
let message = Message.text(value: "hello")
```

infers:

```text
message: Message
```

The static type is not a separate per-variant subtype.

---

# 13. Enum Variant Identity

A runtime enum value contains:

```text
enum type identity
variant identity
payload values
```

Two variants with the same name in different enum types are distinct.

---

# 14. Match Syntax

A match expression/statement uses:

```kaj
match expression {
    pattern => body
    pattern => body
}
```

For v0, each branch body is a single statement or block according to parser design.

Canonical examples:

```kaj
match status {
    pending => print("pending")
    complete => print("complete")
}
```

and:

```kaj
match message {
    quit => print("quit")
    text(value) => print(value)
}
```

---

# 15. Match Scrutinee

The expression after `match` is evaluated/type-checked once.

For Checkpoint 11, exhaustive semantic matching is defined for enum-typed scrutinees.

A non-enum scrutinee is invalid.

Recommended diagnostic:

```text
TYPE_MATCH_REQUIRES_ENUM
```

---

# 16. Unit Variant Pattern

A zero-payload variant is matched by its variant name:

```kaj
pending
```

inside a match on `Status`.

Because the scrutinee type is already known, the enum type qualifier is omitted in patterns.

Example:

```kaj
match status {
    pending => ...
    complete => ...
}
```

---

# 17. Payload Variant Pattern

A payload variant pattern uses positional binding names corresponding to payload declaration order.

Example declaration:

```kaj
enum Message {
    text(value: String)
    move(x: Int, y: Int)
}
```

Patterns:

```kaj
text(value)
move(x, y)
```

The names in the pattern create new local value bindings.

They do not need to match the payload field declaration names.

Example:

```kaj
text(message)
```

is valid and binds the payload value to local name `message`.

---

# 18. Pattern Binding Types

Pattern bindings receive the declared payload field types.

Example:

```kaj
enum Message {
    text(value: String)
}

match message {
    text(value) => print(value)
}
```

Inside that branch:

```text
value: String
```

---

# 19. Pattern Binding Scope

Bindings introduced by a match pattern are visible only in that match branch.

Each branch has its own lexical block scope.

Example:

```kaj
match message {
    text(value) => {
        print(value)
    }
    quit => {
        // value is not visible here
    }
}
```

Pattern bindings may shadow outer names according to normal nested-scope shadowing rules.

Duplicate bindings within one pattern are invalid.

---

# 20. Pattern Arity

A payload pattern must bind exactly the number of payload values declared by that variant.

Example:

```kaj
enum Message {
    move(x: Int, y: Int)
}
```

Valid:

```kaj
move(a, b)
```

Invalid:

```kaj
move(a)
move(a, b, c)
```

Recommended diagnostic:

```text
TYPE_PATTERN_ARITY_MISMATCH
```

---

# 21. Unit Variant Pattern Arity

A zero-payload variant must not use payload bindings.

Invalid:

```kaj
pending(x)
```

when `pending` has no payload.

---

# 22. Unknown Variant Pattern

A branch naming a variant not declared by the scrutinee enum is invalid.

Example:

```kaj
match status {
    pending => ...
    cancelled => ...
}
```

if `cancelled` does not exist.

Recommended diagnostic:

```text
TYPE_UNKNOWN_VARIANT
```

---

# 23. Duplicate Match Cases

A match may not provide the same enum variant more than once.

Invalid:

```kaj
match status {
    pending => ...
    pending => ...
    complete => ...
}
```

Recommended diagnostic:

```text
TYPE_DUPLICATE_MATCH_CASE
```

---

# 24. Exhaustiveness

A match over an enum must cover every declared enum variant exactly once or at least once under future pattern extensions.

In v0, with no wildcard patterns, this means every variant must appear explicitly.

Example:

```kaj
enum Status {
    pending
    complete
}
```

This is exhaustive:

```kaj
match status {
    pending => ...
    complete => ...
}
```

This is not:

```kaj
match status {
    pending => ...
}
```

and must produce:

```text
NON_EXHAUSTIVE_MATCH
```

---

# 25. Exhaustiveness Uses Enum Declaration

Exhaustiveness is checked against the complete set of variants declared on the enum type.

Branch source order does not matter.

---

# 26. No Wildcard Pattern in v0

Checkpoint 11 does not introduce:

```text
_
default
else
```

as a catch-all match pattern.

All variants must be listed explicitly.

A wildcard may be designed later.

---

# 27. No Pattern Guards

Patterns such as:

```kaj
case(x) if x > 0 => ...
```

are not supported in v0.

Do not add guards.

---

# 28. No Nested Destructuring Patterns

Checkpoint 11 supports enum variant patterns with direct payload bindings only.

Do not add nested matching such as:

```text
some(User { name })
some(other_enum.variant(...))
```

Those can be designed later.

---

# 29. Match Branch Result

For Checkpoint 11, `match` is primarily a control-flow construct.

Do not require match branches to produce a common expression result type unless the existing AST specifically models `match` as an expression.

The acceptance use case is statement-oriented:

```kaj
match status {
    pending => print("pending")
    complete => print("complete")
}
```

If implemented as an AST statement, keep it a statement in v0.

---

# 30. Return Through Match

A `return` inside a match branch exits the enclosing function normally.

Example:

```kaj
fn code(status: Status) -> Int {
    match status {
        pending => return 0
        complete => return 1
    }
}
```

An exhaustive match whose every branch definitely returns may count as definitely returning for missing-return analysis.

---

# 31. Definite Return Through Match

For an exhaustive enum match:

```text
match definitely returns
iff every branch definitely returns
```

Example:

```kaj
fn code(status: Status) -> Int {
    match status {
        pending => return 0
        complete => return 1
    }
}
```

passes missing-return analysis.

If one branch falls through its branch body, the match is not definitely returning.

A non-exhaustive match is already invalid.

---

# 32. Runtime Match Semantics

Runtime execution:

```text
evaluate scrutinee once
inspect enum type/variant identity
select matching branch
create fresh branch environment
bind payload values if any
execute branch
```

Exactly one branch executes for a valid exhaustive enum match.

---

# 33. Runtime Payload Binding

For:

```kaj
match message {
    text(value) => print(value)
}
```

if runtime value is:

```text
Message.text("hello")
```

the selected branch receives:

```text
value -> "hello"
```

with the statically declared payload type.

---

# 34. Branch Evaluation Order

Only the selected branch executes.

Other branches are not evaluated.

---

# 35. Enum Runtime Representation

Use an explicit controlled runtime enum value.

Conceptually:

```text
KajEnumValue
├── enum type identity
├── variant identity
└── payload values
```

Do not encode variants as arbitrary Python strings/tuples alone without preserving nominal enum identity.

---

# 36. Unit Variant Runtime Value

`Status.pending` creates a `KajEnumValue` with:

```text
enum = Status
variant = pending
payload = empty
```

---

# 37. Payload Variant Runtime Value

`Message.text(value: "hello")` creates:

```text
enum = Message
variant = text
payload = ["hello"]
```

or an equivalent field-aware representation.

Payload values are stored in declared field order after name mapping.

---

# 38. Constructor Evaluation Order

Payload expressions evaluate left-to-right in source order.

Mapping remains by declared payload field name.

Do not reorder evaluation to declaration order.

---

# 39. Enum Assignability

Enum values are assignable only to the exact same nominal enum type.

Valid:

```text
Status -> Status
```

Invalid:

```text
Status -> JobState
```

even if variants are identical.

---

# 40. Enums in Lists

Lists may contain enum values.

Example:

```kaj
let statuses = [Status.pending, Status.complete]
```

infers:

```text
List<Status>
```

---

# 41. Enums in Records

Record fields may use enum types.

Example:

```kaj
type Task {
    status: Status
}
```

---

# 42. Enums in Functions

Enum types may appear in function parameter and return positions.

Example:

```kaj
fn is_complete(status: Status) -> Bool {
    match status {
        pending => return false
        complete => return true
    }
}
```

---

# 43. Enum Equality

Checkpoint 23 defines enum equality within the same nominal enum when every payload type supports equality. Tags and corresponding payloads are compared with Kaj equality. Different enum declarations remain incomparable. Pattern matching remains the primary decomposition mechanism.

---

# 44. Variant Access Outside Construction

`Status.pending` is a variant-construction expression.

Do not interpret `.pending` as ordinary record field access.

Type checking must distinguish enum type-qualified variant construction from value member access.

---

# 45. Type-Qualified Variant Syntax

For unit variants:

```kaj
Status.pending
```

is valid construction.

For payload variants:

```kaj
Message.text(value: "hello")
```

is valid construction.

Using a payload variant without payload arguments is invalid.

Using call syntax on a unit variant is invalid.

---

# 46. AST Representation

The AST should represent enum declarations explicitly.

Conceptually:

```text
EnumDeclaration
EnumVariantDeclaration
EnumPayloadField
```

Variant construction should also be explicit or unambiguously represented so semantic analysis can distinguish it from ordinary member access/calls.

Match requires explicit AST nodes such as:

```text
MatchStatement
MatchCase
EnumPattern
PatternBinding
```

Follow existing AST conventions:

```text
source spans
immutable syntax data
ordered tuples
no semantic annotations stored in AST
```

---

# 47. AST JSON

Enum/match AST nodes extend the public AST JSON representation according to the existing AST JSON design:

```text
stable snake_case kind values
explicit child fields
source spans
strict validation
round-trip equivalence
```

Do not serialize resolved enum symbols, exhaustiveness results, or runtime values into AST JSON.

---

# 48. Source of Truth

For Kaj v0 enum and match semantics:

```text
docs/language/enums-and-match.md
```

defines the enduring language behavior.

Compiler/runtime implementation must conform to it.
