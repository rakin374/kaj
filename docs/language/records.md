# Kaj Records

**Status:** Authoritative for Kaj v0 record semantics  
**Scope:** Record type declarations, record construction, field access, and record type checking  
**Not covered:** methods, inheritance, structural typing, traits, mutable fields, default values, computed properties

---

# 1. Purpose

Records define named product types with fixed fields.

Example:

```kaj
type User {
    name: String
    age: Int
}
```

A value of type `User` is constructed with:

```kaj
let user = User {
    name: "Alice",
    age: 30
}
```

Fields are accessed with:

```kaj
user.name
```

---

# 2. Record Declaration Syntax

A record type declaration uses:

```kaj
type TypeName {
    fieldName: FieldType
    ...
}
```

Example:

```kaj
type User {
    name: String
    age: Int
}
```

A record declaration introduces a nominal type named `User`.

---

# 3. Nominal Typing

Kaj records are nominally typed.

Two separately declared record types are distinct even if their fields are identical.

Example:

```kaj
type User {
    name: String
}

type Customer {
    name: String
}
```

`User` and `Customer` are different types.

A `User` value is not implicitly assignable to `Customer`.

---

# 4. Field Order

Field declarations have a stable source order.

Example:

```kaj
type User {
    name: String
    age: Int
}
```

declares fields in the order:

```text
name
age
```

Record construction uses field names, not positional order.

Field order remains useful for deterministic formatting, reflection/tooling, and runtime layout decisions.

---

# 5. Duplicate Field Names

A record type may not declare the same field name more than once.

Invalid:

```kaj
type User {
    name: String
    name: String
}
```

This is a semantic declaration error.

Recommended diagnostic:

```text
TYPE_DUPLICATE_FIELD
```

---

# 6. Record Type Names

A `type` declaration introduces a type name into the module's type namespace.

Example:

```kaj
type User {
    name: String
}
```

makes `User` available in type positions:

```kaj
let user: User = ...
```

and in record construction syntax:

```kaj
User {
    name: "Alice"
}
```

---

# 7. Separate Type Namespace

Record type names live in a type namespace, distinct from ordinary value bindings.

Therefore it is conceptually possible for a value and a type to share the same spelling without being the same declaration category.

Example:

```kaj
type User {
    name: String
}

let User = "value"
```

The exact style guidance for such naming may be addressed later, but type lookup and value lookup are distinct.

Record construction syntax explicitly resolves `User` as a type name.

---

# 8. Record Field Types

Each field has an explicit type annotation.

Example:

```kaj
type User {
    name: String
    age: Int
}
```

Field types may use semantic types already supported by Kaj.

At this checkpoint, that includes at least:

```text
Bool
Int
Decimal
String
Bytes
None
List<T>
previously declared record types
```

Nested records are valid.

Example:

```kaj
type Address {
    city: String
}

type User {
    name: String
    address: Address
}
```

---

# 9. Record Declaration Ordering

A record field type must refer to a type that is known according to Kaj's type-declaration visibility rules.

For v0, all top-level record type names are predeclared before record field types are resolved.

This permits forward references between record declarations.

Example:

```kaj
type User {
    address: Address
}

type Address {
    city: String
}
```

is valid.

This also permits recursive record type references at the type level.

Whether recursively constructed runtime values are possible depends on available value constructors and future Optional/indirection features.

---

# 10. Duplicate Type Names

Two top-level type declarations with the same name are invalid.

Example:

```kaj
type User {
    name: String
}

type User {
    age: Int
}
```

Recommended diagnostic:

```text
TYPE_DUPLICATE_TYPE_NAME
```

Kaj v0 does not overload type names.

---

# 11. Unknown Field Type

If a field references an unknown type:

```kaj
type User {
    profile: MissingType
}
```

emit:

```text
TYPE_UNKNOWN_TYPE
```

Do not silently substitute `Any`.

---

# 12. Record Construction Syntax

A record value is constructed with:

```kaj
TypeName {
    field: expression,
    ...
}
```

Example:

```kaj
User {
    name: "Alice",
    age: 30
}
```

The constructor is named by the record type.

This is not a function call.

---

# 13. Record Construction Is Named-Field Based

Construction fields are matched by name.

Example:

```kaj
User {
    age: 30,
    name: "Alice"
}
```

is valid even though the field order differs from the declaration.

Construction order does not change the resulting record type.

---

# 14. Required Fields

Every declared record field is required during construction.

Example:

```kaj
type User {
    name: String
    age: Int
}
```

This is invalid:

```kaj
User {
    name: "Alice"
}
```

because `age` is missing.

Recommended diagnostic:

```text
TYPE_MISSING_FIELD
```

Default field values are not supported in v0.

---

# 15. Unknown Construction Fields

A constructor may not provide fields that are not declared by the record type.

Invalid:

```kaj
User {
    name: "Alice",
    age: 30,
    email: "a@example.com"
}
```

if `email` is not declared.

Recommended diagnostic:

```text
TYPE_UNKNOWN_FIELD
```

---

# 16. Duplicate Construction Fields

A constructor may not provide the same field more than once.

Invalid:

```kaj
User {
    name: "Alice",
    name: "Bob",
    age: 30
}
```

Recommended diagnostic:

```text
TYPE_DUPLICATE_FIELD
```

---

# 17. Construction Field Type Checking

Each constructor field expression must be assignable to the declared field type.

Example:

```kaj
type User {
    age: Decimal
}

let user = User {
    age: 30
}
```

is valid because:

```text
Int -> Decimal
```

is allowed.

Invalid:

```kaj
type User {
    age: Int
}

let user = User {
    age: 30.5
}
```

produces:

```text
TYPE_MISMATCH
```

---

# 18. Construction Result Type

A successful record construction expression has the declared record type.

Example:

```kaj
let user = User {
    name: "Alice",
    age: 30
}
```

infers:

```text
user: User
```

---

# 19. Contextual Construction

Record construction already names its target type explicitly.

Therefore it does not depend on contextual type inference to know what record type is being created.

An annotation may still be checked:

```kaj
let user: User = User {
    name: "Alice",
    age: 30
}
```

---

# 20. Record Assignability

Record values are assignable only when the nominal record types match exactly.

Valid:

```text
User -> User
```

Invalid:

```text
User -> Customer
```

even if both declarations contain identical fields.

No structural record compatibility exists in Kaj v0.

---

# 21. Field Access

Record fields are accessed with:

```kaj
record.field
```

Example:

```kaj
user.name
```

If:

```text
user: User
```

and:

```text
User.name: String
```

then:

```text
user.name: String
```

---

# 22. Unknown Field Access

Accessing a field not declared on the record is invalid.

Example:

```kaj
user.email
```

when `User` has no `email`.

Emit:

```text
TYPE_UNKNOWN_FIELD
```

or the existing stable member diagnostic if Kaj standardizes one shared code.

For record semantics, the important rule is that unknown fields fail statically.

---

# 23. Field Names Are Not Lexical Value Lookups

For:

```kaj
user.name
```

the resolver resolves:

```text
user
```

as a value name.

`name` is resolved by record type checking against `User`'s declared fields.

This continues the existing member-access rule.

---

# 24. Record Values Are Immutable

Record values are immutable in Kaj v0.

Checkpoint 10 does not introduce mutable record fields.

Therefore:

```kaj
user.name = "Bob"
```

is not supported.

A `var` binding containing a record may be rebound:

```kaj
var user = User {
    name: "Alice",
    age: 30
}

user = User {
    name: "Bob",
    age: 31
}
```

if both values have the same record type.

But field mutation itself is not part of v0 record semantics.

---

# 25. Nested Field Access

Field access composes recursively.

Example:

```kaj
type Address {
    city: String
}

type User {
    address: Address
}

print(user.address.city)
```

is valid when the values are well-typed.

---

# 26. Records in Lists

Lists may contain records.

Example:

```kaj
type User {
    name: String
}

let users = [
    User { name: "Alice" },
    User { name: "Bob" }
]
```

infers:

```text
List<User>
```

List homogeneity remains nominal.

A list mixing different record types is invalid unless a future common supertype mechanism exists.

---

# 27. Records as Function Parameters

Record types may appear in function signatures.

Example:

```kaj
fn greet(user: User) -> String {
    return user.name
}
```

Calls require nominal type compatibility.

---

# 28. Records as Function Returns

Functions may return records.

Example:

```kaj
fn make_user() -> User {
    return User {
        name: "Alice",
        age: 30
    }
}
```

Return compatibility uses exact nominal record type matching.

---

# 29. Record Equality

Record equality is deferred.

Checkpoint 10 does not define:

```kaj
user1 == user2
```

Do not inherit Python object/dataclass equality automatically.

---

# 30. Record Printing

The minimal `print` builtin does not need to support whole-record formatting in Checkpoint 10.

The acceptance case prints:

```kaj
user.name
```

which is a String.

Therefore:

```kaj
print(user)
```

may remain unsupported until a general formatting/display design exists.

---

# 31. Runtime Representation

The reference interpreter should use an explicit controlled record runtime value.

Conceptually:

```text
KajRecord
├── type identity
└── field values keyed by declared field identity/name
```

The runtime must preserve nominal type identity.

Do not expose arbitrary Python object attributes.

---

# 32. Runtime Construction

For:

```kaj
User {
    name: expr1,
    age: expr2
}
```

evaluate constructor field expressions in source order.

Then store the resulting values under the declared record fields.

Any statically approved boundary promotions such as:

```text
Int -> Decimal
```

must be materialized before storing the field value.

---

# 33. Constructor Evaluation Order

Field expressions evaluate left-to-right in the order written in source.

Example:

```kaj
User {
    age: f(),
    name: g()
}
```

evaluates:

```text
f()
then
g()
```

even if the record declaration lists `name` before `age`.

Field mapping is by name; evaluation order is source order.

---

# 34. Runtime Field Access

For:

```kaj
user.name
```

runtime:

```text
evaluate user
verify defensively that it is the expected Kaj record value
retrieve declared field `name`
return stored Kaj runtime value
```

Do not use unrestricted Python `getattr`.

---

# 35. Record Runtime Identity

Two record values of the same declared type share the same semantic type identity but have independent field values.

Example:

```kaj
let a = User {
    name: "Alice",
    age: 30
}

let b = User {
    name: "Bob",
    age: 40
}
```

Both have type `User`, but are distinct runtime values.

---

# 36. No Methods

Checkpoint 10 records contain fields only.

Do not add:

```text
methods
constructors with code
static methods
associated functions
property getters/setters
```

---

# 37. No Inheritance

Kaj records do not use class inheritance.

Do not add:

```text
extends
super
subclasses
virtual dispatch
```

---

# 38. No Structural Typing

Matching field shapes do not make two record types interchangeable.

Nominal identity is authoritative.

---

# 39. No Default Fields

Every construction must provide every declared field.

Defaults are deferred.

---

# 40. No Optional Fields

Optionality is expressed later through:

```text
Optional<T>
```

not by omitting a required record field.

Until Optional is implemented, fields are always present in every value of that record type.

---

# 41. No Mutable Fields

Record field mutation is deferred.

This keeps initial record values simple and value-like.

---

# 42. Type Representation

Use an explicit semantic record type representation tied to the declared type symbol/identity.

Conceptually:

```text
RecordType
├── type symbol
├── name
└── ordered fields
```

Each field contains:

```text
name
type
```

Do not identify a record only by its textual field dictionary.

Nominal identity matters.

---

# 43. Type Declaration Symbols

Introduce compiler-internal type symbols or an equivalent type-declaration identity model.

Record type identity should not reuse ordinary value symbols.

A type symbol should preserve at least:

```text
unique identity
name
declaration span
```

These identities are compiler-internal and are not AST JSON node IDs.

---

# 44. Type Scope

Record type declarations in v0 are module-level.

Nested type declarations are not supported.

Record type names are visible throughout the module after the type-name predeclaration phase.

---

# 45. Type Predeclaration

Before resolving record field types:

```text
1. predeclare every top-level record type name
2. then resolve every record's field type annotations
```

This supports forward record references.

---

# 46. Recursive Type References

The type system may represent:

```kaj
type Node {
    next: Node
}
```

as a valid recursive type declaration.

However, constructing a finite value of this exact shape is not practically possible without Optional/indirection.

Do not reject recursive type declarations merely because construction is difficult.

A future cycle/size/lowering design may impose additional rules for native layout.

The Python reference interpreter can represent record values dynamically.

---

# 47. Record Construction Name Resolution

The record constructor type name:

```kaj
User {
    ...
}
```

must resolve through the type namespace, not the value namespace.

If `User` is not a known record type, emit a type diagnostic.

Recommended:

```text
TYPE_UNKNOWN_TYPE
```

---

# 48. Record Constructor vs Block Syntax

The parser distinguishes:

```kaj
User {
    name: "Alice"
}
```

as record construction in expression position when an identifier/type name is followed by a record field initializer block.

This is distinct from a statement block.

The concrete parser grammar must preserve this unambiguously.

---

# 49. Record Construction AST

The AST should represent record construction explicitly.

Conceptually:

```text
RecordConstructionExpression
├── type_name
├── fields
└── span
```

Each field initializer should preserve:

```text
field name
expression
source span where available
```

Do not encode record construction as a generic function call.

---

# 50. Record Declaration AST

The AST should represent:

```kaj
type User {
    name: String
    age: Int
}
```

explicitly.

Conceptually:

```text
RecordDeclaration
├── name
├── fields
└── span
```

Each declared field preserves:

```text
name
type annotation
span
```

---

# 51. AST JSON

Record declarations and constructions extend the public AST JSON format only when Checkpoint 10 adds those AST nodes.

The JSON representation must preserve the existing AST JSON design principles:

```text
stable snake_case kind
explicit fields
source spans
strict validation
round-trip equivalence
```

New AST JSON node kinds should be documented as part of AST JSON v1 evolution if v1 is intentionally extensible during the pre-release language phase.

Do not serialize semantic resolved record types or runtime values into AST JSON.

---

# 52. Source of Truth

For Kaj v0 records:

```text
docs/language/records.md
```

defines the enduring language semantics.

Compiler/runtime implementation must conform to it.
