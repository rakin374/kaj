# Kaj Checkpoint 14 — Newtypes

**Audience:** Codex / implementation agent  
**Checkpoint:** 14  
**Goal:** Implement nominal wrapper types such as `newtype UserId = String`, including explicit construction/unwrapping and strict incompatibility.

---

# 1. Primary Instruction

Implement **Checkpoint 14 only**.

Before editing code, read:

```text
docs/language/newtypes.md
docs/language/maps.md
docs/language/optional-and-result.md
docs/language/enums-and-match.md
docs/language/records.md
docs/language/lists.md
docs/language/functions.md
docs/language/primitive-types.md
docs/internals/ast.md
docs/compiler/ast-json.md
docs/internals/interpreter.md
dev/plans/pure-language-v0.md
```

Treat:

```text
docs/language/newtypes.md
```

as authoritative.

Do not begin Checkpoint 15 Formatter.

---

# 2. Acceptance Target

This must type-check:

```kaj
newtype UserId = String

let id = UserId("abc")
print(id.value)
```

Expected output:

```text
abc
```

And distinct newtypes must remain incompatible:

```kaj
newtype UserId = String
newtype OrderId = String

let user_id = UserId("u1")
let order_id: OrderId = user_id
```

must fail with:

```text
TYPE_MISMATCH
```

---

# 3. AST — Newtype Declaration

Add explicit AST support for:

```kaj
newtype UserId = String
```

Recommended:

```text
NewtypeDeclaration
├── name
├── underlying_type: TypeExpression
└── span
```

Follow existing AST conventions.

Do not attach semantic type symbols to AST nodes.

---

# 4. Parser

Implement parsing for:

```text
"newtype" IDENTIFIER "=" type_expression
```

Example:

```kaj
newtype UserId = String
```

Do not add methods, constructor blocks, attributes, or generic newtype parameters.

---

# 5. AST JSON

Extend serializer/deserializer/schema/docs for `NewtypeDeclaration`.

Use a stable kind such as:

```text
newtype_declaration
```

Preserve spans and underlying `TypeExpression`.

Round-trip tests are required.

Construction may reuse existing call-expression AST syntax if semantic resolution cleanly identifies the callee type name as a newtype.

---

# 6. Type Namespace Integration

Reuse the module type-symbol namespace.

Newtypes share it with:

```text
records
enums
other newtypes
```

Duplicate names across all type declarations remain invalid.

Reuse:

```text
TYPE_DUPLICATE_TYPE_NAME
```

---

# 7. Type Predeclaration

Extend the existing type predeclaration pass so all top-level newtype names are registered before underlying types are resolved.

This should happen together with records/enums.

---

# 8. Semantic NewtypeType

Add an explicit semantic type:

```text
NewtypeType
├── type_symbol
└── underlying_type
```

Type equality is nominal by type-symbol identity.

Do not collapse it to the underlying type.

---

# 9. Underlying Type Resolution

Resolve the RHS type annotation:

```kaj
newtype UserId = String
```

through the normal semantic type resolver.

Support existing value types.

Reject unknown types:

```text
TYPE_UNKNOWN_TYPE
```

Reject function types if function types can appear syntactically in type position.

---

# 10. Recursive Newtype Detection

Detect direct and cyclic newtype definitions.

Reject:

```kaj
newtype A = A
```

and:

```kaj
newtype A = B
newtype B = A
```

with:

```text
TYPE_RECURSIVE_NEWTYPE
```

Do not reject legitimate record/enum recursion.

This check applies specifically to chains of newtype aliases/wrappers that never reach a non-newtype base.

---

# 11. Newtype Construction Typing

Recognize:

```kaj
UserId(expression)
```

as newtype construction when `UserId` resolves in the type namespace to a `NewtypeType`.

Do not resolve this as an ordinary function symbol call.

Require exactly one positional argument.

No named arguments.

---

# 12. Constructor Type Compatibility

Check the constructor argument against the newtype's underlying type.

Example:

```kaj
newtype Price = Decimal

let p = Price(10)
```

valid via:

```text
Int -> Decimal
```

Result type:

```text
Price
```

---

# 13. Explicit Conversion Only

Do not add implicit assignability between:

```text
underlying -> newtype
newtype -> underlying
different newtypes
```

Examples that must fail:

```kaj
newtype UserId = String

let id: UserId = "abc"
```

and:

```kaj
let raw: String = UserId("abc")
```

Both:

```text
TYPE_MISMATCH
```

---

# 14. Newtype Assignability

Only:

```text
same NewtypeType -> same NewtypeType
```

is assignable.

Distinct declarations wrapping identical underlying types remain incompatible.

This is the core acceptance requirement.

---

# 15. `.value` Typing

Extend member access:

```text
NewtypeType(U).value -> U
```

Example:

```kaj
let id = UserId("abc")
let raw = id.value
```

`raw: String`.

No other newtype members.

Unknown:

```text
TYPE_UNKNOWN_MEMBER
```

---

# 16. Member Dispatch Regression

Existing member typing must continue:

```text
List.count
Map.count
Record.field
Newtype.value
```

Ensure dispatch is based on semantic object type and does not break earlier behavior.

---

# 17. Functions

Support newtypes in function signatures.

Test:

```kaj
fn lookup(id: UserId) -> UserId {
    return id
}
```

Raw String arguments must fail.

`UserId(...)` arguments pass.

---

# 18. Records

Support newtype fields.

Example:

```kaj
type User {
    id: UserId
}
```

Raw underlying values must not be accepted for the field.

---

# 19. Enums

Support newtypes in enum payloads.

Payload typing remains nominal.

---

# 20. Lists

Support:

```text
List<UserId>
```

Literal inference:

```kaj
[UserId("a"), UserId("b")]
```

→ `List<UserId>`.

Mixing:

```kaj
[UserId("a"), "b"]
```

must fail.

---

# 21. Optional / Result

Support:

```text
Optional<UserId>
Result<UserId, String>
```

Pattern bindings preserve NewtypeType.

---

# 22. Maps — Values

Support newtypes as map values normally.

---

# 23. Maps — Keys

Allow a NewtypeType as a Map key iff recursively unwrapping its underlying newtype chain reaches one of:

```text
Bool
Int
Decimal
String
Bytes
```

Examples:

```kaj
newtype UserId = String
Map<UserId, User>
```

valid.

```kaj
newtype UserList = List<Int>
Map<UserList, String>
```

invalid:

```text
TYPE_INVALID_MAP_KEY_TYPE
```

---

# 24. Runtime Newtype Value

Add explicit runtime representation:

```text
KajNewtypeValue
├── newtype type identity
└── wrapped Kaj runtime value
```

Do not store only the raw underlying Python value.

---

# 25. Runtime Construction

For:

```kaj
UserId(expr)
```

1. evaluate `expr` once
2. materialize approved conversion to underlying type
3. wrap in `KajNewtypeValue`

---

# 26. Runtime Unwrap

For:

```kaj
id.value
```

return the wrapped Kaj runtime value.

Do not remove nested wrappers automatically.

Example:

```kaj
newtype UserId = String
newtype ExternalUserId = UserId

let x = ExternalUserId(UserId("a"))
```

Then:

```text
x.value -> UserId
x.value.value -> String
```

---

# 27. Runtime Nominal Identity

Ensure:

```text
UserId("x")
OrderId("x")
```

remain distinct runtime tagged wrapper types.

No accidental equality/coercion behavior should erase the declaration identity.

---

# 28. Runtime Map-Key Canonicalization

Extend map-key canonicalization for newtypes.

Include newtype identity in the canonical key.

Conceptually:

```text
("newtype", TypeSymbolID(UserId), canonical_underlying_value)
```

Do not canonicalize a newtype directly to its raw underlying key.

---

# 29. No Inherited Operators

Do not make a newtype participate automatically in primitive operators.

Example:

```kaj
newtype Count = Int

Count(1) + Count(2)
```

must remain invalid unless future semantics explicitly derive operators.

Do not unwrap automatically during operator typing/runtime.

---

# 30. No Equality Derivation

Do not add automatic:

```text
==
!=
```

for newtypes in this checkpoint.

If equality implementation currently falls through to underlying runtime values, prevent that leak.

---

# 31. No Print Derivation

Do not make `print(UserId("x"))` valid automatically.

`print(id.value)` remains the intended v0 form.

---

# 32. Diagnostics

Add:

```text
TYPE_RECURSIVE_NEWTYPE
```

Reuse:

```text
TYPE_DUPLICATE_TYPE_NAME
TYPE_UNKNOWN_TYPE
TYPE_MISMATCH
TYPE_UNKNOWN_MEMBER
TYPE_INVALID_MAP_KEY_TYPE
```

Constructor arity/named-argument errors may reuse existing call diagnostics where clean.

---

# 33. Error Recovery

A malformed newtype declaration should not prevent unrelated later type declarations from being checked.

A bad constructor expression should produce internal error type and allow surrounding checking to continue.

Recursive newtype cycles should be reported deterministically without infinite recursion.

---

# 34. Required Tests — Parsing

Parse:

```kaj
newtype UserId = String
```

Parse nested underlying type:

```kaj
newtype UserIndex = Map<String, User>
```

Verify spans.

---

# 35. Required Tests — AST JSON

Round-trip NewtypeDeclaration.

Validate schema.

Reject malformed newtype declaration JSON.

---

# 36. Required Tests — Type Identity

Critical:

```kaj
newtype UserId = String
newtype OrderId = String
```

Verify:

```text
UserId != OrderId
UserId != String
OrderId != String
```

---

# 37. Required Tests — Construction

Test:

```kaj
let id = UserId("abc")
```

→ `UserId`.

Test wrong argument type.

Test exactly-one-argument rule.

Test named-argument rejection.

Test `Int -> Decimal` constructor promotion.

---

# 38. Required Tests — Explicit Conversion

Reject:

```kaj
let id: UserId = "abc"
```

Reject:

```kaj
let raw: String = UserId("abc")
```

Accept:

```kaj
let raw: String = UserId("abc").value
```

---

# 39. Required Tests — Distinct Newtypes

Acceptance-critical:

```kaj
newtype UserId = String
newtype OrderId = String

let user = UserId("x")
let order: OrderId = user
```

must emit:

```text
TYPE_MISMATCH
```

Also test wrong function argument across newtypes.

---

# 40. Required Tests — `.value`

Test primitive underlying type.

Test record/list/map/newtype underlying types.

Nested newtype unwrap must remove exactly one wrapper per `.value`.

---

# 41. Required Tests — Recursion

Reject direct:

```kaj
newtype A = A
```

Reject indirect:

```kaj
newtype A = B
newtype B = A
```

Accept:

```kaj
newtype UserId = String
```

and valid chains terminating in a concrete non-newtype type.

---

# 42. Required Tests — Function Integration

Test parameter and return types.

Reject raw underlying argument.

Accept explicitly constructed newtype.

---

# 43. Required Tests — Record Integration

Test:

```kaj
type User {
    id: UserId
}
```

Construction with `UserId(...)` passes.

Raw String field fails.

---

# 44. Required Tests — List Integration

Test homogeneous list of one newtype.

Reject mixing underlying and wrapper.

Reject mixing two distinct newtypes with same underlying type.

---

# 45. Required Tests — Optional/Result Integration

Test:

```text
Optional<UserId>
Result<UserId, String>
```

and match payload bindings.

---

# 46. Required Tests — Map Keys

Test:

```kaj
newtype UserId = String
```

as valid map key.

Verify present/missing lookup.

Verify:

```text
UserId("x")
```

does not collide semantically with another distinct newtype's `"x"`.

Reject newtype wrapping invalid map-key type.

---

# 47. Required Tests — Operators

Verify newtypes do not inherit:

```text
+
-
*
/
%
**
ordering
equality
```

from underlying type.

Explicit `.value` operations remain legal according to underlying type rules.

---

# 48. Runtime Acceptance Fixture

Use:

```kaj
newtype UserId = String

let id = UserId("abc")
print(id.value)
```

Expected:

```text
abc
```

---

# 49. Suggested Files

Likely extend:

```text
src/kaj/ast/
src/kaj/parser/
src/kaj/serialization/
src/kaj/semantic/type_symbols.py
src/kaj/semantic/types.py
src/kaj/semantic/type_checker.py
src/kaj/runtime/values.py
src/kaj/runtime/interpreter.py
src/kaj/runtime/map_keys.py
```

Potential helper:

```text
src/kaj/semantic/newtypes.py
```

only if it improves organization.

---

# 50. Suggested Implementation Order

### Step 1
Read `docs/language/newtypes.md`.

### Step 2
Add `NewtypeDeclaration` AST and parser support.

### Step 3
Extend AST JSON/schema/docs.

### Step 4
Extend type predeclaration.

### Step 5
Add semantic `NewtypeType`.

### Step 6
Resolve underlying types.

### Step 7
Detect recursive newtype chains.

### Step 8
Implement constructor typing.

### Step 9
Implement strict nominal assignability.

### Step 10
Implement `.value` member typing.

### Step 11
Integrate with functions/records/enums/lists/Optional/Result.

### Step 12
Extend Map key validation for eligible newtypes.

### Step 13
Add `KajNewtypeValue`.

### Step 14
Implement runtime construction/unwrapping.

### Step 15
Extend map-key canonicalization.

### Step 16
Add regression and acceptance tests.

### Step 17
Run full repository quality gates.

### Step 18
Update:

```text
dev/plans/pure-language-v0.md
```

Do not proceed to Checkpoint 15.

---

# 51. Verification

Run:

```bash
pytest
ruff check .
mypy src
kaj --version
python -m kaj
```

If `kaj run` exists, run the newtype acceptance fixture.

All previous checkpoint tests must remain green.

---

# 52. Definition of Done

Checkpoint 14 is complete only when:

```text
[ ] NewtypeDeclaration AST implemented
[ ] parser supports newtype declarations
[ ] AST JSON/schema supports newtype declarations

[ ] newtypes share module type namespace
[ ] newtype names predeclared
[ ] semantic NewtypeType implemented
[ ] newtype type identity is nominal
[ ] underlying type resolved correctly
[ ] unknown underlying types rejected
[ ] recursive newtype chains rejected

[ ] newtype construction implemented
[ ] constructor requires exactly one positional argument
[ ] named constructor arguments rejected
[ ] constructor input checked against underlying type
[ ] Int->Decimal constructor promotion supported
[ ] constructor result type is newtype type

[ ] underlying -> newtype implicit conversion rejected
[ ] newtype -> underlying implicit conversion rejected
[ ] distinct newtype -> newtype conversion rejected

[ ] `.value` typed as underlying type
[ ] runtime `.value` unwrap implemented
[ ] nested unwrap removes one layer only
[ ] unknown newtype member rejected

[ ] functions support newtypes
[ ] records support newtypes
[ ] enums support newtypes
[ ] lists support newtypes
[ ] Optional/Result support newtypes

[ ] eligible newtypes supported as map keys
[ ] invalid underlying map-key types rejected
[ ] map-key canonicalization includes newtype identity

[ ] KajNewtypeValue runtime representation implemented
[ ] runtime construction preserves nominal identity
[ ] runtime unwrap preserves underlying Kaj value

[ ] newtypes do not inherit operators
[ ] newtypes do not inherit equality
[ ] newtypes do not inherit truthiness
[ ] print(newtype) not added implicitly

[ ] TYPE_RECURSIVE_NEWTYPE implemented

[ ] acceptance unwrap prints abc
[ ] distinct UserId/OrderId assignment emits TYPE_MISMATCH

[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] Checkpoints 0-13 remain passing

[ ] no formatter work begun
[ ] no methods/traits implemented
[ ] no implicit unwrap/coercion protocols implemented
[ ] no derived operators implemented

[ ] dev/plans/pure-language-v0.md updated
```

---

# 53. Completion Report

When finished, report:

```text
Checkpoint 14 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

AST/parser:
- ...

Newtype semantic model:
- ...

Construction:
- ...

Assignability:
- ...

Unwrapping:
- ...

Map-key integration:
- ...

Runtime representation:
- ...

Diagnostics:
- ...

Acceptance:
- UserId("abc").value output: PASS/FAIL
- UserId vs String incompatibility: PASS/FAIL
- UserId vs OrderId incompatibility: PASS/FAIL
- recursive newtype rejection: PASS/FAIL

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

Do not proceed to Checkpoint 15.
