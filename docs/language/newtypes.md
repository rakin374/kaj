# Kaj Newtypes

**Status:** Authoritative for Kaj v0 newtype semantics  
**Scope:** nominal wrapper declarations, construction, typing, assignability, and runtime representation  
**Not covered:** implicit unwrapping, coercion protocols, derived operators, methods, traits, zero-cost native layout guarantees

---

# 1. Purpose

A newtype creates a new nominal type backed by an existing Kaj type.

Example:

```kaj
newtype UserId = String
```

`UserId` is not interchangeable with `String`.

Newtypes are used when two values may have the same underlying representation but different semantic meaning.

Example:

```kaj
newtype UserId = String
newtype OrderId = String
```

`UserId` and `OrderId` are distinct types.

---

# 2. Declaration Syntax

A newtype declaration uses:

```kaj
newtype TypeName = UnderlyingType
```

Example:

```kaj
newtype UserId = String
```

The declaration introduces one nominal type into the module type namespace.

---

# 3. Nominal Identity

Each newtype declaration creates a unique nominal type identity.

Example:

```kaj
newtype UserId = String
newtype OrderId = String
```

Even though both wrap `String`:

```text
UserId != OrderId
```

and neither is implicitly assignable to the other.

---

# 4. Distinct from Underlying Type

A newtype is also distinct from its underlying type.

Given:

```kaj
newtype UserId = String
```

these are different static types:

```text
UserId
String
```

There is no implicit:

```text
String -> UserId
UserId -> String
```

conversion in v0.

---

# 5. Type Namespace

Newtype declarations share Kaj's module type namespace with:

```text
record types
enum types
other newtypes
```

Duplicate type names across any of these declarations are invalid.

Example:

```kaj
type UserId {
    value: String
}

newtype UserId = String
```

is invalid.

The existing duplicate type-name diagnostic applies.

---

# 6. Type Predeclaration

All top-level type declarations, including newtypes, are predeclared before underlying newtype types and record/enum field types are resolved.

This supports forward type references where semantically valid.

Example:

```kaj
newtype UserId = Identifier

newtype Identifier = String
```

may be represented by the type system because both type names are known before underlying types are resolved.

---

# 7. Underlying Type

A newtype may wrap any currently supported non-function Kaj value type.

Examples:

```text
String
Int
Decimal
Bool
Bytes
List<Int>
Map<String, Int>
User
Status
Optional<User>
Result<Int, String>
another newtype
```

Function types are not valid newtype underlying types in v0.

---

# 8. Unknown Underlying Type

If the underlying type name cannot be resolved:

```kaj
newtype UserId = MissingType
```

emit:

```text
TYPE_UNKNOWN_TYPE
```

Do not substitute `Any`.

---

# 9. Recursive Newtypes

Direct or cyclic newtype aliases are invalid.

Invalid:

```kaj
newtype A = A
```

Invalid:

```kaj
newtype A = B
newtype B = A
```

These do not create meaningful wrapper structure.

Recommended diagnostic:

```text
TYPE_RECURSIVE_NEWTYPE
```

This differs from records/enums, which may form recursive type graphs with explicit value structure.

---

# 10. Construction

A newtype value is constructed by calling the newtype name with exactly one value:

```kaj
UserId("abc123")
```

If:

```kaj
newtype UserId = String
```

then:

```kaj
UserId("abc123")
```

has type:

```text
UserId
```

---

# 11. Constructor Arity

A newtype constructor takes exactly one positional argument.

Invalid:

```kaj
UserId()
UserId("a", "b")
```

Named arguments are not supported for newtype construction in v0.

Recommended diagnostics should reuse the normal call-arity model where practical.

---

# 12. Constructor Input Type

The constructor argument must be assignable to the underlying type.

Example:

```kaj
newtype Price = Decimal

let price = Price(10)
```

is valid because:

```text
Int -> Decimal
```

is allowed.

The stored wrapped value is semantically Decimal.

Invalid:

```kaj
newtype UserId = String

let id = UserId(10)
```

produces:

```text
TYPE_MISMATCH
```

---

# 13. Construction Is Explicit

Newtype conversion is never implicit.

Given:

```kaj
newtype UserId = String
```

this is invalid:

```kaj
let id: UserId = "abc"
```

The programmer must write:

```kaj
let id: UserId = UserId("abc")
```

---

# 14. Unwrapping

A newtype value is explicitly unwrapped with the built-in property:

```kaj
value.value
```

Example:

```kaj
newtype UserId = String

let id = UserId("abc")
print(id.value)
```

prints:

```text
abc
```

If:

```text
id: UserId
```

then:

```text
id.value: String
```

---

# 15. `value` Is a Property

Use:

```kaj
id.value
```

not:

```kaj
id.value()
```

No general method system is introduced.

---

# 16. No Implicit Unwrap

A newtype is not automatically treated as its underlying value.

Invalid:

```kaj
newtype UserId = String

fn print_name(value: String) -> None {
    print(value)
}

let id = UserId("abc")
print_name(id)
```

because:

```text
UserId -> String
```

is not implicit.

The caller must explicitly unwrap:

```kaj
print_name(id.value)
```

---

# 17. Assignability

Newtype assignability is exact nominal identity.

Valid:

```text
UserId -> UserId
```

Invalid:

```text
String -> UserId
UserId -> String
OrderId -> UserId
```

even if the underlying types match.

---

# 18. Nested Newtypes

A newtype may wrap another newtype.

Example:

```kaj
newtype UserId = String
newtype ExternalUserId = UserId
```

Then:

```text
ExternalUserId
UserId
String
```

are three distinct types.

Construction must be explicit at each boundary.

Example:

```kaj
let id = ExternalUserId(UserId("abc"))
```

---

# 19. Newtypes in Functions

Newtypes may appear in parameter and return types.

Example:

```kaj
newtype UserId = String

fn lookup(id: UserId) -> UserId {
    return id
}
```

Passing a raw String is invalid.

---

# 20. Newtypes in Records

Record fields may use newtypes.

Example:

```kaj
newtype UserId = String

type User {
    id: UserId
    name: String
}
```

Construction requires a `UserId` value:

```kaj
User {
    id: UserId("abc"),
    name: "Alice"
}
```

A raw String does not satisfy the field type.

---

# 21. Newtypes in Enums

Enum payloads may use newtypes.

Example:

```kaj
enum Event {
    user_found(id: UserId)
}
```

Payload checking uses nominal newtype identity.

---

# 22. Newtypes in Lists

Lists may contain newtypes.

Example:

```kaj
let ids = [
    UserId("a"),
    UserId("b")
]
```

infers:

```text
List<UserId>
```

A raw String in the same list is incompatible.

---

# 23. Newtypes in Maps

A newtype may be used as a map value.

Whether a newtype may be used as a map key depends on the underlying type.

For Kaj v0, a newtype is a valid map key iff its fully unwrapped underlying type is one of the existing valid map-key primitive types:

```text
Bool
Int
Decimal
String
Bytes
```

Example:

```kaj
newtype UserId = String
```

may be used as:

```text
Map<UserId, User>
```

The nominal newtype identity remains part of key semantics.

`UserId("1")` and raw `"1"` are not interchangeable keys.

---

# 24. Newtypes in Optional and Result

Newtypes may appear normally:

```text
Optional<UserId>
Result<UserId, String>
```

Pattern binding preserves the newtype type.

---

# 25. Operators

A newtype does not automatically inherit operators from its underlying type.

Example:

```kaj
newtype Count = Int
```

does not automatically make this valid:

```kaj
Count(1) + Count(2)
```

Operator derivation is deferred.

Programmers may explicitly unwrap:

```kaj
Count(1).value + Count(2).value
```

which produces `Int`.

---

# 26. Equality

Checkpoint 23 defines newtype equality when the underlying type supports equality. Both operands must have the same nominal newtype; comparison recursively uses Kaj equality rather than Python equality.

---

# 27. Ordering

Newtypes do not automatically inherit ordering from the underlying type.

---

# 28. Truthiness

Newtypes do not inherit truthiness.

Kaj conditions remain Bool-only.

---

# 29. `print`

`print` displays an entire newtype deterministically, for example `UserId("abc")`. Programmers may also explicitly print the underlying value:

```kaj
id.value
```

Display does not imply implicit unwrapping or operator inheritance.

---

# 30. Runtime Representation

The reference interpreter should represent newtype values explicitly.

Conceptually:

```text
KajNewtypeValue
├── newtype identity
└── wrapped value
```

Do not represent a newtype solely as its raw underlying Python value.

Otherwise nominal distinctions would be lost at runtime.

---

# 31. Runtime Construction

For:

```kaj
UserId(expression)
```

runtime:

```text
evaluate expression once
materialize any statically approved promotion to underlying type
wrap in KajNewtypeValue with UserId identity
```

---

# 32. Runtime Unwrap

For:

```kaj
id.value
```

runtime returns the stored underlying Kaj runtime value.

No copy/coercion beyond ordinary value semantics is required.

---

# 33. Runtime Identity

Two different newtype declarations wrapping the same underlying runtime representation remain distinct.

Example:

```kaj
newtype UserId = String
newtype OrderId = String
```

their runtime values must preserve different nominal type identities.

---

# 34. Map-Key Runtime Semantics

When a newtype is allowed as a map key, key canonicalization must include the newtype identity.

Conceptually:

```text
(NewtypeIdentity(UserId), underlying canonical key)
```

This prevents:

```text
UserId("abc")
OrderId("abc")
"abc"
```

from collapsing into the same map-key identity.

---

# 35. Type Representation

Use an explicit semantic type representation.

Conceptually:

```text
NewtypeType
├── type_symbol
├── name
└── underlying_type
```

Type equality is by newtype nominal identity, not by underlying type equality.

---

# 36. Type Symbols

Newtypes use the same compiler-internal type-symbol system as records/enums.

They must have unique type identity.

Do not reuse ordinary value symbols.

---

# 37. Constructor Name Resolution

In expression position:

```kaj
UserId(...)
```

when `UserId` resolves to a newtype in the type namespace, it is a newtype-construction expression.

It is not an ordinary function call.

Type names and value names remain separate namespaces.

---

# 38. `value` Member Typing

For:

```text
NewtypeType(U)
```

member:

```text
value
```

has type:

```text
U
```

No other built-in newtype members are defined in v0.

Unknown members produce:

```text
TYPE_UNKNOWN_MEMBER
```

---

# 39. AST Representation

A newtype declaration should have an explicit AST node.

Conceptually:

```text
NewtypeDeclaration
├── name
├── underlying_type
└── span
```

Construction may use a dedicated expression node or an unambiguous existing call-like syntax, provided semantic analysis distinguishes newtype construction from ordinary calls.

Do not store resolved semantic types in the AST.

---

# 40. AST JSON

If a new `NewtypeDeclaration` AST node is introduced, extend AST JSON consistently:

```text
stable snake_case kind
source span
name
underlying type expression
strict validation
round-trip equivalence
```

If construction reuses generic call syntax, no new constructor JSON node is required.

Do not serialize nominal type symbols or runtime wrappers.

---

# 41. Source of Truth

For Kaj v0 newtype semantics:

```text
docs/language/newtypes.md
```

defines the enduring language behavior.

Compiler/runtime implementation must conform to it.
