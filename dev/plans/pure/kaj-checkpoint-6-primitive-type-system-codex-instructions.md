# Kaj Checkpoint 6 — Primitive Type System

**Audience:** Codex / implementation agent  
**Checkpoint:** 6  
**Goal:** Implement Kaj's primitive static type system.

---

## 1. Primary Instruction

Implement **Checkpoint 6 only**.

Before editing code, read:

```text
docs/language/primitive-types.md
docs/internals/name-resolution.md
docs/internals/ast.md
docs/compiler/ast-json.md
dev/plans/pure-language-v0.md
```

Inspect the completed resolver and all prior frontend code.

Treat:

```text
docs/language/primitive-types.md
```

as authoritative for primitive type semantics.

Do not redesign those rules in implementation.

Do not begin Checkpoint 7 function typing.

---

## 2. Goal

Add static typing for:

```text
Bool
Int
Decimal
String
Bytes
None
```

including:

```text
literal inference
binding inference
type annotations
primitive operator typing
assignment compatibility
Int -> Decimal promotion
Bool-only conditions
mutation legality
structured diagnostics
```

Acceptance must include:

```kaj
let x = 10 + 2.5
```

→ `Decimal`

and:

```kaj
let x = "10" + 2
```

→ `TYPE_MISMATCH`

---

## 3. Suggested Structure

Add or extend:

```text
src/kaj/
└── semantic/
    ├── types.py
    └── type_checker.py
```

Reuse:

```text
symbols.py
scope.py
resolver.py
diagnostics
AST
```

Do not create a giant generic semantic framework.

Tests:

```text
tests/semantic/
├── test_primitive_types.py
├── test_type_inference.py
├── test_numeric_promotion.py
├── test_operator_typing.py
├── test_assignments.py
├── test_conditions.py
├── test_mutability.py
├── test_type_annotations.py
├── test_type_errors.py
└── test_type_checker_recovery.py
```

---

## 4. Semantic Type Model

Implement explicit semantic types.

A simple enum or singleton model is appropriate:

```text
BOOL
INT
DECIMAL
STRING
BYTES
NONE
ERROR
```

`ERROR` is compiler-internal only.

Do not represent semantic types primarily with raw strings.

Do not add `Any`.

---

## 5. TypeChecker Input

The type checker should consume:

```text
Program AST
ResolutionResult
```

Do not rerun lexical name lookup from strings.

Use the resolver's symbol associations.

---

## 6. TypeChecker Result

Return a result exposing:

```text
expression -> semantic type
symbol -> semantic type
diagnostics
```

Do not mutate AST nodes with type information.

Use side tables.

---

## 7. Primitive Annotation Resolution

Recognize:

```text
Bool
Int
Decimal
String
Bytes
None
```

in type positions.

Unknown named types produce:

```text
TYPE_UNKNOWN_TYPE
```

Generic types remain unsupported semantically in this checkpoint.

Do not silently accept them as `Any`.

---

## 8. Literal Inference

Infer:

```text
IntegerLiteral -> Int
DecimalLiteral -> Decimal
StringLiteral -> String
BooleanLiteral -> Bool
NoneLiteral -> None
```

Use existing exact `Decimal` values.

---

## 9. Identifier Types

For an identifier whose resolver symbol has a known type, return that symbol type.

If resolution failed, use internal `ERROR` and avoid redundant type errors.

Do not emit a second unknown-name diagnostic.

---

## 10. Binding Inference

For:

```kaj
let x = expression
var x = expression
```

infer expression type and assign it as the symbol's static type.

For an annotation:

```kaj
let x: T = expression
```

resolve `T`, infer expression, and check assignment compatibility.

If compatible:

```text
symbol type = T
```

If incompatible:

- emit `TYPE_MISMATCH`
- still retain declared type `T` for the symbol where possible

This improves recovery for later references.

---

## 11. Assignability

Implement:

```text
same type -> valid
Int -> Decimal -> valid
everything else -> invalid
```

Do not introduce other implicit coercions.

---

## 12. Numeric Promotion

For mixed `Int` and `Decimal` arithmetic/comparison:

```text
promote Int to Decimal
```

Result for arithmetic is generally Decimal.

Do not rewrite the Core AST merely to represent promotion.

If later lowering needs explicit coercions, record promotion/coercion metadata in a side table or defer it to IR.

---

## 13. Arithmetic Typing

Implement exactly the authoritative table.

### `+`

```text
Int + Int -> Int
Int + Decimal -> Decimal
Decimal + Int -> Decimal
Decimal + Decimal -> Decimal
String + String -> String
```

All other combinations → `TYPE_MISMATCH`.

### `-`

numeric only, using promotion.

### `*`

numeric only, using promotion.

### `%`

numeric only, using promotion.

### `**`

numeric only.

```text
Int ** Int -> Int
otherwise numeric combination -> Decimal
```

### `/`

all numeric combinations -> `Decimal`.

In particular:

```text
Int / Int -> Decimal
```

---

## 14. Unary Typing

Implement:

```text
+Int -> Int
-Int -> Int
+Decimal -> Decimal
-Decimal -> Decimal
not Bool -> Bool
```

Invalid operand categories produce a structured type diagnostic.

---

## 15. Equality

Implement:

```text
same primitive type ==/!= same primitive type -> Bool
Int compared with Decimal -> Bool
Decimal compared with Int -> Bool
```

Incompatible primitive pairs produce `TYPE_MISMATCH`.

Thus:

```kaj
10 == "10"
```

is invalid.

---

## 16. Ordering

Implement `< <= > >=` for numeric operands only.

Mixed Int/Decimal is valid.

Result is Bool.

Do not implement String ordering.

---

## 17. Boolean Operators

Implement:

```text
Bool and Bool -> Bool
Bool or Bool -> Bool
not Bool -> Bool
```

No truthiness.

---

## 18. Conditions

For `if` and `while`, infer the condition type.

If it is not Bool and not internal ERROR, emit:

```text
TYPE_CONDITION_NOT_BOOL
```

Do not coerce integers, strings, None, or Decimal to Bool.

---

## 19. Assignment Statements

For a resolved target symbol:

1. check mutability
2. infer RHS type
3. check assignability against symbol type

If immutable:

```text
ASSIGN_TO_IMMUTABLE
```

If type-incompatible:

```text
TYPE_MISMATCH
```

Avoid suppressing one diagnostic solely because another exists unless it would create meaningless cascades.

---

## 20. Compound Assignments

For:

```kaj
x += y
```

type as:

```text
binary_result = type(x + y)
then check binary_result assignable to type(x)
```

Apply corresponding binary operator rules for:

```text
+=
-=
*=
/=
```

Also enforce mutability.

Example:

```kaj
var x: Int = 1
x += 2.5
```

must fail because the operation produces Decimal and Decimal cannot be assigned back to Int.

---

## 21. Mutation Rules

Enforce:

```text
let -> immutable
var -> mutable
parameter -> immutable unless declared var
```

Loop-variable mutation semantics can remain deferred if its static type is not available yet due to collections not being implemented.

Do not invent reference semantics.

---

## 22. Bytes

Implement `Bytes` as a semantic primitive type and valid annotation.

Do not add bytes literal syntax.

Equality/inequality for same-type Bytes is valid.

Do not define arithmetic/concatenation/order operations for Bytes.

---

## 23. None

`none` has type `None`.

Allow:

```text
None == None
None != None
```

Do not define arithmetic/order operations.

---

## 24. Deferred Constructs

Function call return typing is Checkpoint 7.

Collections are later checkpoints.

For expressions whose typing fundamentally depends on deferred features:

```text
CallExpression
ListLiteral
MapLiteral
MemberAccessExpression
IndexExpression
```

do not invent `Any`.

Use a controlled internal ERROR/deferred handling strategy so Checkpoint 6 tests can coexist with parser coverage without cascades.

Do not emit misleading primitive type errors solely because a future construct is not implemented yet.

---

## 25. Function Boundary

Do not implement full function typing yet.

Checkpoint 7 owns:

```text
function signatures
call checking
return checking
missing return
recursion typing
named argument checking
```

Checkpoint 6 may resolve primitive annotation names where needed for parameter symbols, but do not expand scope into call/return semantics.

---

## 26. Diagnostic Codes

Required:

```text
TYPE_MISMATCH
TYPE_INVALID_OPERATOR
TYPE_CONDITION_NOT_BOOL
TYPE_UNKNOWN_TYPE
ASSIGN_TO_IMMUTABLE
```

Important conformance rule:

```kaj
let x = "10" + 2
```

must emit:

```text
TYPE_MISMATCH
```

Do not change that acceptance case to another code.

---

## 27. Error Recovery

Use internal `ERROR` type to continue after failures.

Examples:

- unresolved identifier -> ERROR without duplicate unknown-name type diagnostic
- unknown annotation -> TYPE_UNKNOWN_TYPE, continue safely
- invalid operator -> diagnostic + ERROR result
- incompatible initializer -> diagnostic but preserve declared symbol type if one exists

Avoid diagnostic cascades.

---

## 28. Required Tests — Primitive Literals

Test:

```kaj
let a = true
let b = 10
let c = 19.99
let d = "hello"
let e = none
```

Verify symbol types:

```text
Bool
Int
Decimal
String
None
```

For Bytes, test annotation/type representation directly since no source literal exists.

---

## 29. Required Tests — Numeric Promotion

Test:

```kaj
let x = 10 + 2.5
```

→ Decimal

```kaj
let x = 2.5 + 10
```

→ Decimal

```kaj
let x = 10 + 2
```

→ Int

Test `-`, `*`, `%`, `**`, `/`.

Explicitly test:

```kaj
let x = 5 / 2
```

→ Decimal

---

## 30. Required Tests — String

Test:

```kaj
let x = "hello" + " world"
```

→ String

Test:

```kaj
let x = "10" + 2
```

→ `TYPE_MISMATCH`

Test no implicit numeric/string coercions.

---

## 31. Required Tests — Equality/Comparison

Test:

```kaj
let x = 1 == 2
```

→ Bool

```kaj
let x = 1 == 2.0
```

→ Bool

```kaj
let x = "a" == "b"
```

→ Bool

```kaj
let x = 10 == "10"
```

→ TYPE_MISMATCH

Numeric `< <= > >=` → Bool.

String ordering → error.

---

## 32. Required Tests — Boolean Operators

Test:

```kaj
let x = true and false
let y = true or false
let z = not true
```

all → Bool.

Invalid numeric/string boolean operators must fail.

---

## 33. Required Tests — Conditions

Test valid:

```kaj
let ready = true

if ready {
}
```

Test invalid:

```kaj
if 1 {
}
```

→ `TYPE_CONDITION_NOT_BOOL`

Likewise for `while`.

---

## 34. Required Tests — Annotations

Test:

```kaj
let x: Int = 10
```

valid.

```kaj
let x: Decimal = 10
```

valid via promotion.

```kaj
let x: Int = 10.5
```

→ TYPE_MISMATCH.

```kaj
let x: Foo = 10
```

→ TYPE_UNKNOWN_TYPE.

Test `Bytes` annotation is recognized even though no bytes literal exists.

---

## 35. Required Tests — Assignment and Mutability

Test:

```kaj
var x = 10
x = 20
```

valid.

```kaj
var x: Decimal = 10
x = 20.5
```

valid.

```kaj
var x = 10
x = 20.5
```

→ TYPE_MISMATCH.

```kaj
let x = 10
x = 20
```

→ ASSIGN_TO_IMMUTABLE.

Test compound assignments.

---

## 36. Required Tests — Recovery

Create a program with several independent type failures and verify multiple deterministic diagnostics are collected.

Do not stop after first type error.

---

## 37. Integration With Name Resolution

Add tests showing shadowed symbols receive independent types.

Example:

```kaj
let x = 1

if true {
    let x = "hello"
}
```

Outer symbol type:

```text
Int
```

Inner symbol type:

```text
String
```

This verifies type data is keyed by symbol identity rather than name string.

---

## 38. AST JSON Compatibility

A source program parsed normally and the same program round-tripped through AST JSON should receive equivalent primitive type results after name resolution/type checking.

Do not add types to AST JSON v1.

---

## 39. Suggested Implementation Order

### Step 1

Inspect:

```text
docs/language/primitive-types.md
src/kaj/semantic/
src/kaj/ast/
src/kaj/parser/
src/kaj/serialization/
dev/plans/pure-language-v0.md
```

### Step 2

Implement primitive semantic type representation plus internal ERROR type.

### Step 3

Implement type-checker result/side tables.

### Step 4

Implement primitive annotation resolution.

### Step 5

Implement literal and identifier inference.

### Step 6

Implement binding inference/annotation checking.

### Step 7

Implement unary operators.

### Step 8

Implement binary arithmetic and Int->Decimal promotion.

### Step 9

Implement equality/comparisons/boolean operators.

### Step 10

Implement Bool-only conditions.

### Step 11

Implement assignment compatibility and immutability.

### Step 12

Implement compound assignment.

### Step 13

Implement recovery/cascade suppression.

### Step 14

Complete unit and integration tests.

### Step 15

Run quality gates.

### Step 16

Update:

```text
dev/plans/pure-language-v0.md
```

Do not begin Checkpoint 7.

---

## 40. Verification

Run:

```bash
pytest
ruff check .
mypy src
kaj --version
python -m kaj
```

All earlier checkpoint tests must remain passing.

---

## 41. Definition of Done

Checkpoint 6 is complete only when:

```text
[ ] docs/language/primitive-types.md treated as authoritative

[ ] primitive semantic type model implemented
[ ] Bool implemented
[ ] Int implemented
[ ] Decimal implemented
[ ] String implemented
[ ] Bytes implemented
[ ] None implemented
[ ] internal ERROR type implemented

[ ] primitive annotation resolution implemented
[ ] unknown types diagnosed

[ ] literal inference implemented
[ ] identifier type lookup via resolved symbol implemented
[ ] binding inference implemented
[ ] annotated binding compatibility implemented

[ ] symbol-type side table implemented
[ ] expression-type side table implemented
[ ] AST remains unmodified

[ ] Int -> Decimal promotion implemented
[ ] reverse implicit promotion rejected
[ ] unrelated implicit conversions rejected

[ ] + typing implemented
[ ] - typing implemented
[ ] * typing implemented
[ ] / typing implemented
[ ] % typing implemented
[ ] ** typing implemented
[ ] String + String implemented
[ ] Int / Int -> Decimal implemented

[ ] equality typing implemented
[ ] numeric ordering implemented
[ ] boolean operators implemented
[ ] unary typing implemented

[ ] if condition Bool enforcement implemented
[ ] while condition Bool enforcement implemented

[ ] assignment type checking implemented
[ ] compound assignment type checking implemented
[ ] let immutability enforced
[ ] var mutability enforced
[ ] var parameter mutability supported where applicable

[ ] TYPE_MISMATCH implemented
[ ] TYPE_INVALID_OPERATOR implemented
[ ] TYPE_CONDITION_NOT_BOOL implemented
[ ] TYPE_UNKNOWN_TYPE implemented
[ ] ASSIGN_TO_IMMUTABLE implemented

[ ] `let x = 10 + 2.5` infers Decimal
[ ] `let x = "10" + 2` emits TYPE_MISMATCH

[ ] shadowed symbols can hold different types
[ ] resolver errors do not create redundant type cascades
[ ] multiple type errors are collected

[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] Checkpoints 0-5 remain passing

[ ] no full function/call typing implemented
[ ] no collection typing implemented
[ ] no record/enum/Optional/Result typing implemented
[ ] no types added to AST JSON v1
[ ] no interpreter work added

[ ] dev/plans/pure-language-v0.md updated
```

---

## 42. Completion Report

When finished, report:

```text
Checkpoint 6 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

Primitive types:
- ...

Promotion rules:
- ...

Operator typing:
- ...

Assignment/mutability:
- ...

Diagnostics:
- ...

Tests added:
- ...

Acceptance:
- `10 + 2.5` -> Decimal: PASS/FAIL
- `"10" + 2` -> TYPE_MISMATCH: PASS/FAIL
- `5 / 2` -> Decimal: PASS/FAIL
- Bool-only conditions: PASS/FAIL

Verification:
- pytest: PASS/FAIL
- ruff check .: PASS/FAIL
- mypy src: PASS/FAIL
- Kaj bootstrap CLI: PASS/FAIL

Decisions/deviations:
- ...

Known issues:
- ...
```

Do not proceed to Checkpoint 7.
