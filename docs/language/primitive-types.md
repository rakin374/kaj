# Kaj Primitive Type System

**Status:** Authoritative for Kaj v0 Checkpoint 6  
**Scope:** Primitive value types, local type inference, operator typing, assignment compatibility, and Bool-only conditions  
**Not covered:** functions/calls typing, collections, records, enums, Optional/Result, newtypes, imports, effects

---

## 1. Purpose

Checkpoint 6 introduces Kaj's first static type-checking rules.

The compiler pipeline becomes:

```text
source
  ↓
lexer
  ↓
parser
  ↓
AST
  ↓
name resolution
  ↓
type checking
```

This checkpoint gives meaning to:

```text
Bool
Int
Decimal
String
Bytes
None
```

and checks primitive expressions and bindings before execution.

---

## 2. Primitive Types

Kaj v0 defines these primitive semantic types:

```text
Bool
Int
Decimal
String
Bytes
None
```

These are distinct types.

Kaj does not use implicit truthiness and does not freely coerce unrelated primitive values.

---

## 3. Bool

`Bool` has two literal values:

```kaj
true
false
```

Boolean values are not integers.

Invalid implicit interchange:

```kaj
let x: Int = true
let y: Bool = 1
```

Both are type errors.

---

## 4. Int

`Int` represents arbitrary-precision integers.

Examples:

```kaj
0
10
999999999999999999999999999
```

Integer width is not constrained to machine integer sizes at the language level.

---

## 5. Decimal

`Decimal` represents exact decimal arithmetic.

Examples:

```kaj
0.5
19.99
100.125
```

It is not defined as binary floating point.

---

## 6. String

`String` is Unicode text.

Example:

```kaj
"hello"
```

String concatenation uses:

```text
String + String -> String
```

No implicit conversion from numeric or Boolean values to String occurs.

Therefore:

```kaj
"10" + 2
```

is a type error.

---

## 7. Bytes

`Bytes` is a distinct primitive type representing binary data.

Checkpoint 6 defines the type even though Kaj v0 currently has no bytes literal syntax.

Therefore `Bytes` can appear in type annotations and future APIs, but ordinary source expressions cannot construct a Bytes value yet unless an existing compiler/test fixture creates such an AST value through an approved internal mechanism.

Do not invent bytes literal syntax during this checkpoint.

`Bytes` is not implicitly convertible to or from `String`.

---

## 8. None

`None` is the type of the `none` literal and of functions that return no meaningful value.

The literal:

```kaj
none
```

has type:

```text
None
```

`None` is a real type, not absence of compiler type information.

---

## 9. Primitive Type Names

In type-expression positions, these names resolve to primitive semantic types:

```text
Bool
Int
Decimal
String
Bytes
None
```

Checkpoint 6 adds primitive type-name resolution for these names.

Unknown type names remain deferred to later user-defined type support unless the current type checker needs a structured unknown-type diagnostic.

---

## 10. Type Representation

Implement explicit semantic type objects or an enum.

A simple representation may be:

```text
PrimitiveType.BOOL
PrimitiveType.INT
PrimitiveType.DECIMAL
PrimitiveType.STRING
PrimitiveType.BYTES
PrimitiveType.NONE
```

Do not use raw strings throughout the type checker as the primary semantic type representation.

---

## 11. Expression Type Inference

The type checker infers expression types bottom-up.

Examples:

```kaj
10
```

→ `Int`

```kaj
2.5
```

→ `Decimal`

```kaj
true
```

→ `Bool`

```kaj
"hello"
```

→ `String`

```kaj
none
```

→ `None`

Identifier expression types come from the resolved symbol's declared/inferred type.

---

## 12. Binding Type Inference

For an unannotated binding:

```kaj
let x = 10
```

infer:

```text
x: Int
```

For:

```kaj
let price = 19.99
```

infer:

```text
price: Decimal
```

For:

```kaj
let enabled = true
```

infer:

```text
enabled: Bool
```

The inferred type becomes the binding's static type.

---

## 13. Annotated Bindings

For:

```kaj
let x: Int = 10
```

the initializer must be assignable to `Int`.

For:

```kaj
let x: Decimal = 10
```

the initializer is valid because `Int` may promote to `Decimal`.

For:

```kaj
let x: Int = 2.5
```

the initializer is invalid because `Decimal` does not implicitly narrow to `Int`.

---

## 14. Assignment Compatibility

The core compatibility rule is:

```text
T -> T
```

plus one numeric widening conversion:

```text
Int -> Decimal
```

No other implicit primitive conversion is allowed in Checkpoint 6.

Valid:

```text
Int -> Int
Decimal -> Decimal
Int -> Decimal
String -> String
Bool -> Bool
Bytes -> Bytes
None -> None
```

Invalid examples:

```text
Decimal -> Int
String -> Int
Int -> String
Bool -> Int
Int -> Bool
String -> Bytes
Bytes -> String
None -> String
```

---

## 15. Int to Decimal Promotion

Kaj permits safe implicit widening from `Int` to `Decimal`.

Example:

```kaj
let x = 10 + 2.5
```

The `10` operand is promoted for the operation.

Result:

```text
Decimal
```

Likewise:

```kaj
let x: Decimal = 10
```

is valid.

Promotion is semantic; the AST does not need to be rewritten in Checkpoint 6 unless the implementation has a clean coercion representation.

Prefer recording coercion/type information in side tables rather than mutating the Core AST.

---

## 16. No Reverse Promotion

Kaj does not implicitly convert:

```text
Decimal -> Int
```

Therefore:

```kaj
let x: Int = 10.5
```

is invalid.

A future explicit conversion API may support this intentionally.

---

## 17. Arithmetic Operators

Arithmetic typing:

### Addition

```text
Int + Int -> Int
Int + Decimal -> Decimal
Decimal + Int -> Decimal
Decimal + Decimal -> Decimal

String + String -> String
```

All other primitive combinations are invalid.

### Subtraction

```text
Int - Int -> Int
Int - Decimal -> Decimal
Decimal - Int -> Decimal
Decimal - Decimal -> Decimal
```

### Multiplication

```text
Int * Int -> Int
Int * Decimal -> Decimal
Decimal * Int -> Decimal
Decimal * Decimal -> Decimal
```

### Modulo

```text
Int % Int -> Int
Int % Decimal -> Decimal
Decimal % Int -> Decimal
Decimal % Decimal -> Decimal
```

Modulo follows the same numeric promotion rule in v0.

### Power

```text
Int ** Int -> Int
```

For any operation involving Decimal:

```text
Int ** Decimal
Decimal ** Int
Decimal ** Decimal
```

result type is:

```text
Decimal
```

Checkpoint 6 checks types only; runtime numerical edge cases are handled by execution semantics later.

---

## 18. Division

Kaj freezes:

```text
Int / Int -> Decimal
```

Therefore:

```kaj
5 / 2
```

has type:

```text
Decimal
```

Mixed numeric division also produces Decimal:

```text
Int / Decimal -> Decimal
Decimal / Int -> Decimal
Decimal / Decimal -> Decimal
```

Division never produces `Int` in v0.

Integer division syntax such as `//` is deferred.

---

## 19. Unary Operators

Unary typing:

```text
+ Int -> Int
- Int -> Int

+ Decimal -> Decimal
- Decimal -> Decimal

not Bool -> Bool
```

Invalid:

```text
not Int
-"hello"
+true
```

---

## 20. Equality Operators

Kaj supports:

```text
==
!=
```

for compatible primitive values.

Valid same-type comparisons:

```text
Bool with Bool
Int with Int
Decimal with Decimal
String with String
Bytes with Bytes
None with None
```

Numeric mixed comparison is valid via `Int -> Decimal` promotion:

```text
Int with Decimal
Decimal with Int
```

Result type is always:

```text
Bool
```

Incompatible primitive equality is a compile-time type error.

Therefore:

```kaj
10 == "10"
```

is invalid rather than evaluating to `false`.

---

## 21. Ordering Comparisons

Kaj supports:

```text
<
<=
>
>=
```

for numeric values only in Checkpoint 6.

Valid:

```text
Int with Int
Int with Decimal
Decimal with Int
Decimal with Decimal
```

Result:

```text
Bool
```

Ordering for `String`, `Bytes`, and `Bool` is not defined in this checkpoint.

Therefore:

```kaj
"a" < "b"
```

is a type error in Kaj v0 Checkpoint 6.

This may be revisited explicitly later.

---

## 22. Boolean Operators

Kaj boolean operators:

```text
and
or
not
```

require `Bool`.

Rules:

```text
Bool and Bool -> Bool
Bool or Bool -> Bool
not Bool -> Bool
```

No implicit truthiness exists.

Invalid:

```kaj
1 and 2
"hello" or "world"
not 1
```

---

## 23. Bool-Only Conditions

Conditions in:

```text
if
while
```

must have type:

```text
Bool
```

Valid:

```kaj
if ready {
    ...
}
```

when `ready: Bool`.

Invalid:

```kaj
if 1 {
    ...
}
```

Invalid:

```kaj
while "yes" {
    ...
}
```

Kaj has no truthiness conversion.

---

## 24. For Loops

Checkpoint 6 does not yet implement collection typing.

Therefore full iterable checking for:

```kaj
for item in items {
    ...
}
```

is deferred to the collections checkpoint.

The type checker should still type-check the iterable expression itself where possible, but must not invent list/iterator semantics before their type-system checkpoint.

---

## 25. Assignment Statements

For:

```kaj
x = expression
```

name resolution identifies the target symbol.

Checkpoint 6 verifies:

```text
type(expression)
```

is assignable to the symbol's static type.

Examples:

```kaj
var x = 10
x = 20
```

type-compatible.

```kaj
var x: Decimal = 1
x = 2.5
```

type-compatible.

```kaj
var x = 10
x = 2.5
```

is invalid because the binding was inferred as `Int` and `Decimal -> Int` is not allowed.

Checkpoint 6 may also reject assignment to an immutable `let` binding, since mutability information is now available and assignment checking is being introduced.

Use:

```text
ASSIGN_TO_IMMUTABLE
```

as the stable diagnostic for this case.

---

## 26. Compound Assignment

Compound assignment is typed as the corresponding binary operation followed by assignment compatibility.

Example:

```kaj
var x: Decimal = 1
x += 2
```

is valid because:

```text
Decimal + Int -> Decimal
Decimal -> Decimal
```

Example:

```kaj
var x: Int = 1
x += 2.5
```

is invalid because:

```text
Int + Decimal -> Decimal
Decimal -> Int
```

is not assignable.

Compound assignment to immutable bindings is invalid.

---

## 27. Binding Mutability

`let` bindings are immutable.

`var` bindings are mutable.

Function parameters are immutable by default.

Parameters declared with `var` are mutable local bindings.

Checkpoint 6 should enforce mutation legality for assignment statements.

No reference/inout semantics exist.

---

## 28. Symbol Types

The type checker should associate a semantic type with value symbols.

Examples:

```text
LET_BINDING -> inferred or annotated type
VAR_BINDING -> inferred or annotated type
PARAMETER -> annotated type
```

Function symbol typing is deferred to Checkpoint 7.

Loop-variable typing is deferred until collection typing provides an iterable element type.

Do not invent `Any`.

---

## 29. Error Type

Use an internal error/unknown type sentinel so type checking can continue after diagnostics.

Conceptually:

```text
ErrorType
```

This is not a Kaj source-visible type.

It prevents cascades such as:

```kaj
let x = missing
let y = x + 1
```

from producing meaningless secondary errors when name resolution/type information is already invalid.

Do not serialize this as AST JSON.

---

## 30. Type Information Side Tables

Do not mutate AST nodes to attach types.

Maintain side tables/results such as:

```text
Expression node -> inferred type
Symbol -> static type
```

The Core AST remains syntax-only.

---

## 31. Type Checker Result

A result should expose enough information for later compiler stages:

```text
expression types
symbol types
diagnostics
```

It may also preserve or reference the existing name-resolution result.

Do not merge name resolution and type checking into one opaque pass.

---

## 32. Primitive Type Annotation Resolution

In type positions, recognize exactly:

```text
Bool
Int
Decimal
String
Bytes
None
```

for Checkpoint 6.

Generic types such as:

```text
List<Int>
Map<String, Int>
Optional<Int>
Result<Int, String>
```

are not semantically implemented yet.

If encountered in a binding/parameter annotation during Checkpoint 6, emit a structured unsupported/unknown-type diagnostic rather than pretending the type is valid.

Recommended code:

```text
TYPE_UNKNOWN_TYPE
```

for names not currently known to the type system.

---

## 33. Unknown Type Names

Example:

```kaj
let x: Foo = 10
```

produces:

```text
TYPE_UNKNOWN_TYPE
```

until user-defined records/newtypes are introduced.

Do not treat unknown type names as `Any`.

---

## 34. Core Type Diagnostics

Stable codes required for Checkpoint 6:

```text
TYPE_MISMATCH
TYPE_INVALID_OPERATOR
TYPE_CONDITION_NOT_BOOL
TYPE_UNKNOWN_TYPE
ASSIGN_TO_IMMUTABLE
```

The implementation may add more specific codes later, but these must be sufficient for the checkpoint acceptance behavior.

---

## 35. TYPE_MISMATCH

Use for assignment/annotation compatibility failures and other places where a value has a known incompatible type.

Example:

```kaj
let x: Int = "hello"
```

→ `TYPE_MISMATCH`

Example acceptance case:

```kaj
let x = "10" + 2
```

may be reported as `TYPE_MISMATCH` or internally as an operator mismatch, but **for Checkpoint 6 conformance the externally asserted diagnostic must be `TYPE_MISMATCH`**.

Therefore use `TYPE_MISMATCH` for incompatible operand type pairs in the primitive operator checker unless a later diagnostic refinement explicitly changes the public contract.

---

## 36. TYPE_INVALID_OPERATOR

Use when an operator is structurally known but unsupported for a single operand category or otherwise more appropriate than a binary mismatch.

Example:

```kaj
not 1
```

may produce:

```text
TYPE_INVALID_OPERATOR
```

However, keep diagnostics deterministic and tests aligned with the chosen rule.

---

## 37. Condition Diagnostic

For:

```kaj
if 1 {
}
```

emit:

```text
TYPE_CONDITION_NOT_BOOL
```

Point at the condition expression.

Likewise for `while`.

---

## 38. Assignment to Immutable

Example:

```kaj
let x = 1
x = 2
```

emit:

```text
ASSIGN_TO_IMMUTABLE
```

Point at the assignment target.

The resolver has already identified the symbol.

---

## 39. Type Checking Order

For a binding:

```text
1. resolve/interpret annotation if present
2. infer initializer expression type
3. check assignability
4. assign resulting static type to symbol
```

For no annotation:

```text
symbol type = initializer inferred type
```

For annotation:

```text
symbol type = annotation type
```

even when the initializer mismatch is diagnosed, so later references can continue against the declared type.

---

## 40. Module Binding Order

Type checking follows resolved source order.

A reference to an earlier binding can use that binding's known static type.

Unknown-name errors remain resolver diagnostics.

Do not rerun name lookup independently in the type checker.

---

## 41. Function Bodies

Full function type checking is Checkpoint 7.

Checkpoint 6 should not attempt to validate:

- parameter types beyond primitive annotation recognition needed for symbols
- function call signatures
- return statements against return type
- function body completeness

If implementation architecture needs primitive parameter symbols to have types available, it may resolve primitive parameter annotations, but function semantic checking remains deferred.

Keep Checkpoint 6 centered on primitive expressions/bindings/control conditions/assignments.

---

## 42. Function Calls

Call expression typing is deferred to Checkpoint 7.

Do not invent a dynamic `Any` return type.

Use an internal error/unknown type sentinel when a call expression cannot yet be typed due solely to deferred function typing.

Avoid cascading errors from this deferred capability.

---

## 43. Member and Index Expressions

Member access and indexing are not typeable from primitive-only rules in the general case.

Their full semantics are deferred to records/collections checkpoints.

Use the internal error/unknown/deferred type handling without inventing semantics.

Do not report unrelated primitive errors merely because these constructs exist in AST.

---

## 44. Bytes Operations

Checkpoint 6 defines no primitive operators for `Bytes`.

Therefore operations such as:

```text
Bytes + Bytes
Bytes == Bytes
```

follow these rules:

- equality `==` / `!=` is valid for same-type Bytes values
- arithmetic/concatenation operations are not defined
- ordering is not defined

Future standard-library operations may handle binary data explicitly.

---

## 45. None Operations

`None` supports:

```text
None == None -> Bool
None != None -> Bool
```

No arithmetic or ordering operations are defined.

---

## 46. No Implicit String Conversion

Kaj never turns:

```text
Int
Decimal
Bool
Bytes
None
```

into `String` implicitly during primitive operator checking.

Thus:

```kaj
"count: " + 10
```

is invalid.

Future explicit formatting/interpolation rules may perform intentional conversions.

---

## 47. No Truthiness

These are invalid conditions:

```kaj
if 1 {}
if 0 {}
if "" {}
if "hello" {}
if none {}
```

Only `Bool` is accepted.

---

## 48. Acceptance Examples

### Mixed numeric arithmetic

```kaj
let x = 10 + 2.5
```

must infer:

```text
x: Decimal
```

### Integer arithmetic

```kaj
let x = 10 + 2
```

must infer:

```text
x: Int
```

### Integer division

```kaj
let x = 5 / 2
```

must infer:

```text
x: Decimal
```

### String concatenation

```kaj
let x = "hello" + " world"
```

must infer:

```text
x: String
```

### Invalid string/numeric addition

```kaj
let x = "10" + 2
```

must produce:

```text
TYPE_MISMATCH
```

### Bool condition

```kaj
let ready = true

if ready {
}
```

must type-check.

### Invalid condition

```kaj
if 1 {
}
```

must produce:

```text
TYPE_CONDITION_NOT_BOOL
```

---

## 49. Source of Truth

For Kaj v0 primitive typing:

```text
docs/language/primitive-types.md
        +
type-checker tests
        +
type-checker implementation
```

must agree.

---

## 50. Definition of Done

Checkpoint 6 is complete when:

```text
[ ] Bool implemented
[ ] Int implemented
[ ] Decimal implemented
[ ] String implemented
[ ] Bytes implemented
[ ] None implemented

[ ] primitive type names recognized
[ ] unknown type names diagnosed

[ ] literal type inference implemented
[ ] identifier type lookup from symbol types implemented
[ ] unannotated binding inference implemented
[ ] annotated binding checking implemented

[ ] Int -> Decimal promotion implemented
[ ] Decimal -> Int implicit conversion rejected
[ ] unrelated primitive coercions rejected

[ ] arithmetic operator typing implemented
[ ] String + String implemented
[ ] mixed numeric arithmetic implemented
[ ] Int / Int -> Decimal implemented
[ ] equality typing implemented
[ ] numeric comparison typing implemented
[ ] boolean operators implemented
[ ] unary operator typing implemented

[ ] Bool-only if conditions enforced
[ ] Bool-only while conditions enforced

[ ] assignment typing implemented
[ ] compound assignment typing implemented
[ ] let immutability enforced
[ ] var assignment supported
[ ] var parameter mutation representable/enforceable where checked

[ ] expression type side table/result implemented
[ ] symbol type side table/result implemented
[ ] AST remains unmodified
[ ] error type/sentinel prevents cascades

[ ] TYPE_MISMATCH implemented
[ ] TYPE_INVALID_OPERATOR implemented
[ ] TYPE_CONDITION_NOT_BOOL implemented
[ ] TYPE_UNKNOWN_TYPE implemented
[ ] ASSIGN_TO_IMMUTABLE implemented

[ ] `10 + 2.5` infers Decimal
[ ] `"10" + 2` produces TYPE_MISMATCH

[ ] tests pass
[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes

[ ] Checkpoints 1-5 remain passing
[ ] function call/return typing not implemented beyond minimal primitive support
[ ] collections/records/enums/Optional/Result not implemented
[ ] no interpreter work added
