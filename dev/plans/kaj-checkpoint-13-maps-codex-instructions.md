# Kaj Checkpoint 13 — Maps

**Audience:** Codex / implementation agent  
**Checkpoint:** 13  
**Goal:** Implement `Map<K,V>`, map literals, safe lookup returning `Optional<V>`, and `count`.

---

# 1. Primary Instruction

Implement **Checkpoint 13 only**.

Before editing code, read:

```text
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
docs/language/maps.md
```

as authoritative.

Do not add map mutation or map iteration.

Do not begin Checkpoint 14 Newtypes.

---

# 2. Acceptance Target

This should type-check and execute:

```kaj
let ages = {
    "Alice": 30,
    "Bob": 40
}

match ages["Alice"] {
    some(age) => print(age)
    none => print("missing")
}
```

Expected output:

```text
30
```

And:

```kaj
match ages["Charlie"] {
    some(age) => print(age)
    none => print("missing")
}
```

must output:

```text
missing
```

---

# 3. Semantic Map Type

Add:

```text
MapType(key_type, value_type)
```

or equivalent explicit semantic representation.

Do not represent `Map<K,V>` as a string.

Support nested forms such as:

```text
Map<String, List<User>>
Map<String, Optional<User>>
```

---

# 4. Type Resolution

Give semantic meaning to:

```text
Map<K, V>
```

Validate exactly two type arguments.

Invalid:

```text
TYPE_INVALID_TYPE_ARGUMENTS
```

Resolve both type arguments recursively.

---

# 5. Key Type Validation

Allow only:

```text
Bool
Int
Decimal
String
Bytes
```

as v0 map key types.

Reject:

```text
None
List
Map
RecordType
EnumType
Optional
Result
FunctionType
```

with:

```text
TYPE_INVALID_MAP_KEY_TYPE
```

Apply this validation both to explicit annotations and inferred map literals.

---

# 6. Map Literal Inference

For non-empty map literal:

```kaj
{
    "a": 1,
    "b": 2
}
```

infer key type and value type independently.

Use:

```text
same type -> same type
Int + Decimal -> Decimal
otherwise mismatch
```

Construct:

```text
Map<K, V>
```

---

# 7. Heterogeneous Keys

Reject incompatible keys:

```kaj
{
    "a": 1,
    2: 2
}
```

with:

```text
TYPE_MISMATCH
```

unless an already-defined common type exists.

Do not introduce union types or Any.

---

# 8. Heterogeneous Values

Reject incompatible values:

```kaj
{
    "a": 1,
    "b": "two"
}
```

with:

```text
TYPE_MISMATCH
```

---

# 9. Numeric Common Type

Test key and value promotion independently.

Examples:

```kaj
{
    1: "a",
    2.5: "b"
}
```

→ `Map<Decimal, String>`

```kaj
{
    "a": 1,
    "b": 2.5
}
```

→ `Map<String, Decimal>`

---

# 10. Empty Map

Without expected type:

```kaj
let values = {}
```

emit:

```text
TYPE_CANNOT_INFER_MAP_TYPE
```

With annotation:

```kaj
let values: Map<String, Int> = {}
```

valid.

---

# 11. Contextual Map Literal Typing

When expected:

```text
Map<K, V>
```

check each key against `K` and value against `V`.

Example:

```kaj
let prices: Map<String, Decimal> = {
    "a": 1,
    "b": 2.5
}
```

valid.

Record enough expected-type/coercion metadata for runtime promotions.

---

# 12. Map Assignability

Implement invariant assignability:

```text
Map<K,V> -> Map<K,V>
```

Do not add covariance.

Specifically reject general:

```text
Map<String, Int> -> Map<String, Decimal>
```

Contextual literals remain allowed to construct directly as the expected type.

---

# 13. Index Expression Typing

Extend `IndexExpression`.

Existing:

```text
List<T>[Int] -> T
```

must continue unchanged.

Add:

```text
Map<K,V>[K] -> Optional<V>
```

Use existing expected/assignability rules for the key expression.

---

# 14. Safe Lookup

Map lookup always has type:

```text
Optional<V>
```

Do not return bare `V`.

Do not add a missing-key runtime exception.

This is a core Checkpoint 13 requirement.

---

# 15. Lookup Key Promotion

If:

```text
map: Map<Decimal, V>
```

then:

```kaj
map[10]
```

is valid because:

```text
Int -> Decimal
```

The runtime must materialize Decimal key conversion before lookup.

---

# 16. `count` Member Typing

Extend member dispatch:

```text
List<T>.count -> Int
Map<K,V>.count -> Int
Record.field -> declared field type
```

Unknown map members:

```text
TYPE_UNKNOWN_MEMBER
```

Do not introduce `count()`.

---

# 17. Function Integration

Support Map types in parameters and returns.

Example:

```kaj
fn find(
    values: Map<String, Int>,
    key: String
) -> Optional<Int> {
    return values[key]
}
```

must type-check.

---

# 18. Record/Enum/Optional Integration

Verify Map types work in:

```text
record fields
enum payloads
Optional
Result
List elements
function params/returns
```

Do not add special cases beyond normal recursive type support.

---

# 19. Runtime KajMap

Add a controlled map runtime value.

Recommended:

```text
KajMap
├── key_type
├── value_type
└── entries
```

Do not expose Python dict methods.

---

# 20. Critical Python Key Hazard

Python considers:

```python
True == 1
```

and hashes them compatibly.

Kaj does not.

Therefore do **not** use raw Python primitive keys in a way that lets:

```text
Bool true
Int 1
```

collide.

Use a typed map-key wrapper or an equivalent canonical Kaj key representation, for example conceptually:

```text
(RuntimeTypeTag, normalized_value)
```

This is mandatory for correct Kaj semantics.

---

# 21. Decimal Runtime Keys

Use `decimal.Decimal`.

No float conversion.

If a map is `Map<Decimal,V>`, contextual Int keys must be converted to Decimal before insertion/lookup.

---

# 22. Runtime Literal Construction

For every map entry in source order:

1. evaluate key
2. apply contextual key promotion
3. evaluate value
4. apply contextual value promotion
5. canonicalize key according to Kaj key semantics
6. reject duplicate evaluated key
7. store entry

Preserve source evaluation order.

---

# 23. Duplicate Keys

If two evaluated keys are equal under Kaj semantics:

```text
RUNTIME_DUPLICATE_MAP_KEY
```

Do not silently overwrite.

Example:

```kaj
{
    "a": 1,
    "a": 2
}
```

must fail at runtime if not already rejected statically.

Static detection of obvious constant duplicates is optional.

---

# 24. Runtime Lookup

For Map indexing:

1. evaluate map expression
2. evaluate key expression
3. apply approved key promotion
4. canonicalize key
5. look up

If found:

```text
Optional<V>.some(value)
```

If missing:

```text
Optional<V>.none
```

Reuse the Optional runtime/tagged-value representation from Checkpoint 12.

---

# 25. Runtime Count

`map.count` returns Kaj Int number of entries.

Do not use generic Python `getattr`.

---

# 26. No Map Assignment

Do not implement:

```kaj
map[key] = value
```

If parser permits it structurally, type checking must reject map index assignment for v0.

Do not expose mutating runtime operations.

---

# 27. No Map Iteration

Do not extend `for` to maps.

Existing:

```text
for iterable must be List<T>
```

remains authoritative for now.

---

# 28. No Map Equality / Arithmetic / Truthiness

Do not implement:

```text
map == map
map + map
if map
```

Python behavior must not leak into Kaj.

---

# 29. AST / Parser

Prefer using existing nodes already planned since Core AST:

```text
MapLiteral
MapEntry
GenericType
IndexExpression
MemberAccessExpression
```

Inspect parser support first.

If map literals are already parsed, do not redesign syntax.

If parser support is incomplete, complete it according to `docs/language/maps.md`.

---

# 30. AST JSON

If existing map AST nodes are already covered by AST JSON v1, do not change the external format unnecessarily.

Add/adjust tests only as needed to prove map literal round-trip and schema validity.

---

# 31. Required Diagnostics

Add:

```text
TYPE_CANNOT_INFER_MAP_TYPE
TYPE_INVALID_MAP_KEY_TYPE
RUNTIME_DUPLICATE_MAP_KEY
```

Reuse:

```text
TYPE_INVALID_TYPE_ARGUMENTS
TYPE_MISMATCH
TYPE_UNKNOWN_MEMBER
```

No missing-key runtime diagnostic should exist for ordinary map lookup.

---

# 32. Error Recovery

Type-check all map entries where practical even if one key/value is invalid.

Use internal ERROR type to avoid cascades.

Runtime duplicate-key failure terminates execution under current runtime-error semantics.

---

# 33. Required Tests — Type Resolution

Test:

```text
Map<String, Int>
Map<Int, User>
Map<String, Optional<User>>
Map<String, List<Int>>
```

Test invalid arities.

Test invalid key types.

---

# 34. Required Tests — Literal Inference

Test:

```kaj
let x = {"a": 1, "b": 2}
```

→ `Map<String, Int>`.

Test mixed numeric values → Decimal.

Test mixed numeric keys → Decimal.

Test incompatible key types.

Test incompatible value types.

---

# 35. Required Tests — Empty Map

Test:

```kaj
let x = {}
```

→ `TYPE_CANNOT_INFER_MAP_TYPE`.

Test:

```kaj
let x: Map<String, Int> = {}
```

valid and `x.count == 0`.

---

# 36. Required Tests — Contextual Promotion

Test:

```kaj
let values: Map<String, Decimal> = {
    "a": 1,
    "b": 2.5
}
```

runtime values are Decimal.

Test:

```kaj
let values: Map<Decimal, String> = {
    1: "one",
    2.5: "two"
}
```

runtime keys use Decimal semantics.

---

# 37. Required Tests — Lookup Typing

For:

```text
Map<String, Int>
```

verify:

```kaj
values["a"]
```

has type:

```text
Optional<Int>
```

Wrong key type → `TYPE_MISMATCH`.

Decimal key contextual promotion works.

---

# 38. Required Tests — Lookup Runtime

Test present key:

```kaj
match values["a"] {
    some(value) => print(value)
    none => print("missing")
}
```

prints stored value.

Test missing key prints `missing`.

No runtime exception for absence.

---

# 39. Required Tests — Count

Test:

```kaj
print(values.count)
```

for empty and non-empty maps.

Unknown map member must fail statically.

Verify existing `List.count` and record field access still work.

---

# 40. Required Tests — Duplicate Keys

Test obvious duplicate literal:

```kaj
{
    "a": 1,
    "a": 2
}
```

must produce `RUNTIME_DUPLICATE_MAP_KEY` if frontend does not reject earlier.

Also test computed keys that evaluate equal.

No silent overwrite.

---

# 41. Required Tests — Bool vs Int Keys

This is critical.

Verify these are semantically distinct in separate appropriately typed maps.

Ensure runtime infrastructure does not accidentally treat:

```text
true
1
```

as the same raw Python dictionary key.

Do not rely on Python's default bool/int key equality.

---

# 42. Required Tests — Function Integration

Test:

```kaj
fn lookup(
    values: Map<String, Int>,
    key: String
) -> Optional<Int> {
    return values[key]
}
```

and exercise both present/missing cases.

---

# 43. Required Tests — Nested Types

Test:

```text
Map<String, List<Int>>
List<Map<String, Int>>
Optional<Map<String, User>>
Result<Map<String, User>, String>
```

as applicable.

---

# 44. Acceptance Fixture

Use an end-to-end fixture such as:

```kaj
let ages = {
    "Alice": 30,
    "Bob": 40
}

match ages["Alice"] {
    some(age) => print(age)
    none => print("missing")
}

match ages["Charlie"] {
    some(age) => print(age)
    none => print("missing")
}

print(ages.count)
```

Expected output:

```text
30
missing
2
```

---

# 45. Suggested Files

Likely extend:

```text
src/kaj/semantic/types.py
src/kaj/semantic/type_checker.py
src/kaj/runtime/values.py
src/kaj/runtime/interpreter.py
src/kaj/runtime/errors.py
```

Potential helper:

```text
src/kaj/runtime/map_keys.py
```

if typed key canonicalization deserves isolation.

Avoid unnecessary fragmentation.

---

# 46. Suggested Implementation Order

### Step 1
Read `docs/language/maps.md` and inspect existing Map AST/parser support.

### Step 2
Add `MapType`.

### Step 3
Implement Map generic type resolution and key-type validation.

### Step 4
Implement map literal inference.

### Step 5
Implement contextual/empty map typing.

### Step 6
Implement invariant map assignability.

### Step 7
Extend index typing to `Map<K,V> -> Optional<V>`.

### Step 8
Extend `.count`.

### Step 9
Add controlled `KajMap` runtime representation.

### Step 10
Implement typed/canonical runtime keys.

### Step 11
Implement map literal runtime and duplicate-key detection.

### Step 12
Implement safe lookup returning Optional.

### Step 13
Implement runtime count.

### Step 14
Add integration and regression tests.

### Step 15
Run full repository validation.

### Step 16
Update:

```text
dev/plans/pure-language-v0.md
```

Do not proceed to Checkpoint 14.

---

# 47. Verification

Run:

```bash
pytest
ruff check .
mypy src
kaj --version
python -m kaj
```

If `kaj run` exists, run the Map acceptance fixture.

All previous checkpoints must remain green.

---

# 48. Definition of Done

Checkpoint 13 is complete only when:

```text
[ ] MapType implemented
[ ] Map requires exactly two type arguments
[ ] nested Map types supported
[ ] invalid map key types rejected

[ ] map literal inference implemented
[ ] homogeneous key inference implemented
[ ] homogeneous value inference implemented
[ ] Int/Decimal common-type promotion works for keys
[ ] Int/Decimal common-type promotion works for values
[ ] incompatible keys rejected
[ ] incompatible values rejected

[ ] empty map without context rejected
[ ] annotated empty map supported
[ ] contextual map literal checking implemented
[ ] contextual key/value promotions implemented

[ ] Map assignability invariant
[ ] no implicit Map<String,Int> -> Map<String,Decimal>

[ ] Map index typing implemented
[ ] lookup key checked against K
[ ] lookup result type is Optional<V>
[ ] missing key is not a runtime error
[ ] Decimal key promotion supported

[ ] Map.count typed as Int
[ ] Map.count executes
[ ] unknown members rejected
[ ] List.count remains working
[ ] record field access remains working

[ ] controlled KajMap runtime representation implemented
[ ] Kaj key semantics do not leak Python bool/int equality
[ ] Decimal keys remain exact
[ ] map literal expressions evaluate in specified order
[ ] duplicate evaluated keys rejected
[ ] RUNTIME_DUPLICATE_MAP_KEY implemented

[ ] runtime lookup returns Optional.some when present
[ ] runtime lookup returns Optional.none when absent
[ ] Optional runtime representation reused

[ ] Maps work in functions
[ ] Maps work in records
[ ] Maps work in enums
[ ] Maps work in Lists
[ ] Maps work in Optional/Result

[ ] TYPE_CANNOT_INFER_MAP_TYPE implemented
[ ] TYPE_INVALID_MAP_KEY_TYPE implemented

[ ] acceptance present lookup works
[ ] acceptance missing lookup works
[ ] count works

[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] Checkpoints 0-12 remain passing

[ ] no map mutation implemented
[ ] no map index assignment implemented
[ ] no map iteration implemented
[ ] no map equality implemented
[ ] no map arithmetic implemented
[ ] no map truthiness implemented
[ ] no Newtypes work begun

[ ] dev/plans/pure-language-v0.md updated
```

---

# 49. Completion Report

When finished, report:

```text
Checkpoint 13 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

Map type model:
- ...

Literal inference:
- ...

Key restrictions:
- ...

Safe lookup:
- ...

Count:
- ...

Runtime representation:
- ...

Duplicate-key handling:
- ...

Diagnostics:
- ...

Acceptance:
- present lookup: PASS/FAIL
- missing lookup returns none: PASS/FAIL
- count: PASS/FAIL

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

Do not proceed to Checkpoint 14.
