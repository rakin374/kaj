# Kaj Checkpoint 10 — Records

**Audience:** Codex / implementation agent  
**Checkpoint:** 10  
**Goal:** Add record type declarations, construction, field access, type checking, and reference-interpreter execution.

---

# 1. Primary Instruction

Implement **Checkpoint 10 only**.

Before editing code, read:

```text
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
docs/language/records.md
```

as authoritative for Kaj record semantics.

Do not begin Checkpoint 11 Enums and Match.

---

# 2. Acceptance Target

This must parse, resolve, type-check, execute, and print:

```kaj
type User {
    name: String
    age: Int
}

let user = User {
    name: "Alice",
    age: 30
}

print(user.name)
```

Expected output:

```text
Alice
```

with one newline.

---

# 3. AST Additions

Add explicit AST nodes for record declarations and construction.

Conceptually:

```text
RecordDeclaration
RecordFieldDeclaration

RecordConstructionExpression
RecordFieldInitializer
```

Follow existing AST conventions:

```text
immutable dataclasses where practical
SourceSpan preservation
tuples for ordered child collections
syntax-only AST
```

Do not attach semantic types/symbols to AST nodes.

---

# 4. Parser — Type Declarations

Implement parsing for:

```kaj
type User {
    name: String
    age: Int
}
```

Grammar conceptually:

```text
"type" IDENTIFIER "{"
    field_declaration*
"}"
```

Field declaration:

```text
IDENTIFIER ":" type_expression
```

No commas are required between record field declarations unless existing parser conventions make optional commas desirable and the language spec explicitly allows them.

Do not invent methods/defaults/mutability syntax.

---

# 5. Parser — Record Construction

Implement expression syntax:

```kaj
User {
    name: "Alice",
    age: 30
}
```

Construction fields are:

```text
IDENTIFIER ":" expression
```

Comma-separated.

Support trailing comma only if it matches existing collection/call parser conventions.

Do not parse this as a function call.

---

# 6. Parser Disambiguation

Ensure the parser can distinguish:

```text
statement/control blocks
map literals
record construction
```

according to syntactic context.

Record construction requires a leading type-name/identifier expression form followed by a record initializer brace.

Do not destabilize existing block/map parsing.

---

# 7. AST JSON

Extend AST JSON serialization/deserialization for all new record AST nodes.

Add stable node kinds, for example:

```text
record_declaration
record_field_declaration
record_construction_expression
record_field_initializer
```

Use exact naming consistently in:

```text
serializer
deserializer
schema
tests
docs/compiler/ast-json.md
```

Preserve spans.

Do not add semantic record types to AST JSON.

---

# 8. JSON Schema

Update:

```text
schemas/ast/v1.json
```

to validate the new AST node kinds and structural placement.

Ensure:

```text
AST -> JSON -> AST
```

round-trips record declarations/constructions exactly.

---

# 9. Type Namespace

Add a module-level type namespace distinct from value symbols.

Introduce compiler-internal type symbols or equivalent.

Recommended:

```text
TypeSymbolKind.RECORD
TypeSymbol
```

Each record type needs unique nominal identity.

Do not identify record types merely by name string or field shape.

---

# 10. Type Predeclaration

Before resolving record field annotations:

1. scan top-level record declarations
2. predeclare all record type names
3. detect duplicate type names
4. resolve field types

This supports forward references between records.

---

# 11. Duplicate Type Names

Reject:

```kaj
type User {
    name: String
}

type User {
    age: Int
}
```

with:

```text
TYPE_DUPLICATE_TYPE_NAME
```

Keep the first declaration active for deterministic recovery.

---

# 12. Record Field Resolution

Resolve every declared field's type annotation using the semantic type system.

Support already implemented types:

```text
primitive types
List<T>
record types
```

Unknown types:

```text
TYPE_UNKNOWN_TYPE
```

---

# 13. Duplicate Declared Fields

Reject duplicate field names within one record declaration.

Example:

```kaj
type User {
    name: String
    name: String
}
```

→

```text
TYPE_DUPLICATE_FIELD
```

Preserve the first field declaration for deterministic recovery.

---

# 14. Semantic RecordType

Add explicit nominal `RecordType`.

Recommended structure:

```text
RecordType
├── type_symbol
└── fields
```

Each field descriptor:

```text
name
semantic type
declaration span
```

Field order follows source declaration order.

Type equality is nominal:

```text
same type symbol -> equal
different type symbol -> not equal
```

---

# 15. Record Type Registration

After field types resolve, associate:

```text
type symbol -> RecordType
```

in semantic results/type environment.

Do not mutate AST declarations with semantic information.

---

# 16. Record Construction Type Checking

For:

```kaj
User {
    name: "Alice",
    age: 30
}
```

perform:

1. resolve `User` in type namespace
2. verify it is a record type
3. map initializer fields by exact name
4. detect duplicates
5. detect unknown fields
6. detect missing required fields
7. type-check each initializer expression
8. check assignability against declared field type
9. record construction expression type = `User`

---

# 17. Missing Fields

Reject:

```kaj
User {
    name: "Alice"
}
```

when `age` is required.

Diagnostic:

```text
TYPE_MISSING_FIELD
```

One diagnostic may report all missing field names if deterministic and readable.

---

# 18. Unknown Fields

Reject constructor fields not declared by the type.

Diagnostic:

```text
TYPE_UNKNOWN_FIELD
```

Point to the offending field initializer name/span where practical.

---

# 19. Duplicate Constructor Fields

Reject:

```kaj
User {
    name: "Alice",
    name: "Bob",
    age: 30
}
```

with:

```text
TYPE_DUPLICATE_FIELD
```

Continue checking other fields where practical.

---

# 20. Field Type Compatibility

Use existing assignability rules recursively.

Examples:

```text
Int -> Decimal allowed
User -> User allowed
User -> Customer rejected
List<User> -> List<User> allowed
```

No structural compatibility.

---

# 21. Contextual Field Promotion

If a field is:

```text
Decimal
```

and initializer expression is `Int`, permit it.

The interpreter must materialize the approved promotion when storing the field.

---

# 22. Field Access Typing

For:

```kaj
user.name
```

1. type-check `user`
2. require a `RecordType`
3. look up `name` in its declared fields
4. result type = field type

Unknown field:

```text
TYPE_UNKNOWN_FIELD
```

---

# 23. List Member Compatibility

Existing:

```kaj
values.count
```

must continue to work.

Member access dispatch should distinguish semantic object types:

```text
ListType -> known list members
RecordType -> declared record fields
```

Do not replace the list-specific logic with unrestricted dynamic member lookup.

---

# 24. Nested Field Access

Ensure:

```kaj
user.address.city
```

type-checks recursively when `address` is a record.

---

# 25. Field Assignment

Do not implement record field mutation.

If parser already permits:

```kaj
user.name = "Bob"
```

type checker should reject it as unsupported/invalid assignment target semantics for v0.

Use a stable existing assignment diagnostic if one fits, or add:

```text
TYPE_FIELD_ASSIGNMENT_NOT_SUPPORTED
```

Do not silently mutate record runtime storage.

---

# 26. Record Assignability

Implement nominal assignment.

Exact same record type only.

Test two identical-shape declarations remain incompatible.

---

# 27. Functions

Extend function annotations and call/return compatibility for record types.

Required examples:

```kaj
fn greet(user: User) -> String {
    return user.name
}
```

and:

```kaj
fn make_user() -> User {
    return User {
        name: "Alice",
        age: 30
    }
}
```

---

# 28. Lists of Records

Ensure existing `List<T>` can use `RecordType` as element type.

Example:

```kaj
let users = [
    User { name: "Alice", age: 30 },
    User { name: "Bob", age: 40 }
]
```

→ `List<User>`

Mixing distinct record types should fail list homogeneity.

---

# 29. Runtime KajRecord

Add controlled runtime representation.

Recommended:

```text
KajRecord
├── record_type identity
└── fields
```

Fields may be stored by field name or internal field descriptor identity, provided nominal record type identity is retained.

Do not use arbitrary Python objects with dynamic attributes.

---

# 30. Runtime Construction

Evaluate constructor field expressions left-to-right in source order.

Then map them to declared fields.

Materialize any approved type promotions.

Construct `KajRecord`.

Do not evaluate in declaration-field order if source order differs.

---

# 31. Runtime Field Access

Evaluate object expression.

Require `KajRecord` defensively.

Retrieve the declared field explicitly.

Do not use `getattr` on arbitrary Python values.

---

# 32. Runtime Immutability

Do not expose runtime field mutation APIs.

A `var` binding containing a record can be rebound to another same-type record.

---

# 33. Print

Do not broaden `print` to whole-record values.

Acceptance only requires:

```kaj
print(user.name)
```

which prints a String.

---

# 34. Recursive Record Types

Permit type-level recursive references if the type predeclaration architecture supports them.

Do not attempt finite-size/native-layout analysis.

Do not invent pointer/Optional behavior.

The Python reference runtime does not need to construct impossible infinitely recursive values.

---

# 35. Required Diagnostics

Add:

```text
TYPE_DUPLICATE_TYPE_NAME
TYPE_DUPLICATE_FIELD
TYPE_MISSING_FIELD
TYPE_UNKNOWN_FIELD
```

Reuse:

```text
TYPE_UNKNOWN_TYPE
TYPE_MISMATCH
```

If field assignment is explicitly rejected, add/use one stable diagnostic consistently.

---

# 36. Error Recovery

Continue after record declaration/construction errors where practical.

Examples:

- unknown one field type should not prevent checking later declarations
- duplicate constructor field should not prevent checking unrelated fields
- missing fields should not crash construction typing
- unknown member should yield internal error type and continue

Do not produce unnecessary cascades.

---

# 37. Required Tests — Parsing

Parse:

```kaj
type User {
    name: String
    age: Int
}
```

Parse:

```kaj
User {
    name: "Alice",
    age: 30
}
```

Verify spans and ordered fields.

Test record construction alongside blocks and map literals to guard disambiguation.

---

# 38. Required Tests — AST JSON

Round-trip record declarations and constructors.

Validate emitted AST JSON against updated schema.

Reject malformed record AST JSON.

---

# 39. Required Tests — Type Declarations

Test primitive fields.

Test `List<T>` field.

Test record field referencing later-declared record.

Test duplicate type names.

Test duplicate declared field names.

Test unknown field type.

---

# 40. Required Tests — Construction

Valid exact construction.

Fields in different source order.

Missing field.

Unknown field.

Duplicate field.

Wrong field type.

Int->Decimal field promotion.

Construction result type.

---

# 41. Required Tests — Nominal Typing

Use:

```kaj
type User {
    name: String
}

type Customer {
    name: String
}
```

Verify `User` is not assignable to `Customer`.

Verify list homogeneity also respects nominal identity.

---

# 42. Required Tests — Field Access

Test:

```kaj
user.name
```

returns String type.

Test nested access.

Test unknown field fails statically.

Test existing `List.count` still works.

---

# 43. Required Tests — Functions

Test record parameter.

Test record return.

Test wrong nominal record argument.

Test record construction returned from function.

---

# 44. Required Tests — Runtime

Acceptance:

```kaj
type User {
    name: String
    age: Int
}

let user = User {
    name: "Alice",
    age: 30
}

print(user.name)
```

→

```text
Alice
```

Also test:

- two independent values of same record type
- nested records
- list of records
- `var` binding rebinding same record type

---

# 45. Required Tests — Evaluation Order

Use field initializer expressions with observable effects and verify constructor fields evaluate left-to-right in source order.

Do not reorder evaluation to declaration order.

---

# 46. Suggested Files

Likely extend/add:

```text
src/kaj/ast/
src/kaj/parser/
src/kaj/serialization/
src/kaj/semantic/types.py
src/kaj/semantic/type_checker.py
src/kaj/runtime/values.py
src/kaj/runtime/interpreter.py
```

Potential new semantic files if useful:

```text
src/kaj/semantic/type_symbols.py
src/kaj/semantic/records.py
```

Avoid unnecessary fragmentation.

---

# 47. Suggested Implementation Order

### Step 1
Read `docs/language/records.md` and inspect current AST/parser/type/runtime designs.

### Step 2
Add record declaration/construction AST nodes.

### Step 3
Implement parser support.

### Step 4
Extend AST JSON and schema.

### Step 5
Add module type-symbol namespace and record type predeclaration.

### Step 6
Resolve record field types.

### Step 7
Implement nominal `RecordType`.

### Step 8
Implement construction type checking.

### Step 9
Implement field access type checking.

### Step 10
Integrate record types with functions and lists.

### Step 11
Add `KajRecord` runtime value.

### Step 12
Implement runtime record construction.

### Step 13
Implement runtime field access.

### Step 14
Add diagnostics/recovery tests.

### Step 15
Run full repository verification.

### Step 16
Update:

```text
dev/plans/pure-language-v0.md
```

Do not proceed to Checkpoint 11.

---

# 48. Verification

Run:

```bash
pytest
ruff check .
mypy src
kaj --version
python -m kaj
```

If `kaj run` exists, execute the acceptance program through it.

All previous checkpoints must remain green.

---

# 49. Definition of Done

Checkpoint 10 is complete only when:

```text
[ ] record declaration AST implemented
[ ] record field declaration AST implemented
[ ] record construction AST implemented
[ ] record field initializer AST implemented

[ ] type declaration parsing implemented
[ ] record construction parsing implemented
[ ] block/map/record syntax remains unambiguous

[ ] AST JSON supports record nodes
[ ] JSON schema updated
[ ] record AST JSON round-trip tests pass

[ ] module type namespace implemented
[ ] type symbols have nominal identity
[ ] record type names predeclared
[ ] forward record type references resolve

[ ] RecordType implemented
[ ] field order preserved
[ ] field semantic types resolved
[ ] duplicate type names rejected
[ ] duplicate declared fields rejected
[ ] unknown field types rejected

[ ] record construction type checking implemented
[ ] missing fields rejected
[ ] unknown fields rejected
[ ] duplicate constructor fields rejected
[ ] field type mismatches rejected
[ ] Int->Decimal field promotion supported
[ ] construction expression type = declared record type

[ ] nominal record assignability implemented
[ ] structurally identical different records remain incompatible

[ ] record field access typing implemented
[ ] unknown field access rejected
[ ] nested field access works
[ ] existing List.count behavior remains correct

[ ] record types work in function parameters
[ ] record types work as function returns
[ ] List<Record> works

[ ] KajRecord runtime value implemented
[ ] record construction executes
[ ] constructor expressions evaluate left-to-right
[ ] runtime field promotions materialized
[ ] field access executes
[ ] arbitrary Python attributes do not leak
[ ] record field mutation not implemented
[ ] var record bindings can rebind same-type values

[ ] TYPE_DUPLICATE_TYPE_NAME implemented
[ ] TYPE_DUPLICATE_FIELD implemented
[ ] TYPE_MISSING_FIELD implemented
[ ] TYPE_UNKNOWN_FIELD implemented
[ ] TYPE_UNKNOWN_TYPE reused correctly
[ ] TYPE_MISMATCH reused correctly

[ ] acceptance program prints Alice
[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] Checkpoints 0-9 remain passing

[ ] no methods implemented
[ ] no inheritance implemented
[ ] no structural typing implemented
[ ] no default fields implemented
[ ] no mutable record fields implemented
[ ] no Enums/Match work begun

[ ] dev/plans/pure-language-v0.md updated
```

---

# 50. Completion Report

When finished, report:

```text
Checkpoint 10 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

AST/parser:
- ...

Type namespace:
- ...

RecordType model:
- ...

Construction checking:
- ...

Field access:
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

Do not proceed to Checkpoint 11.
