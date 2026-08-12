# Kaj Maps

**Status:** Authoritative for Kaj v0 map semantics  
**Scope:** `Map<K, V>`, map literals, safe lookup, and `count`  
**Not covered:** map mutation, map iteration, ordered-map APIs, merging, key/value views, comprehensions

---

# 1. Purpose

Kaj maps represent finite key/value associations with a statically known key type and value type:

```text
Map<K, V>
```

Example:

```kaj
let ages = {
    "Alice": 30,
    "Bob": 40
}
```

which infers:

```text
Map<String, Int>
```

Map lookup is safe and returns:

```text
Optional<V>
```

rather than throwing for a missing key.

---

# 2. Map Type

A map type has exactly two type arguments:

```text
Map<K, V>
```

Examples:

```text
Map<String, Int>
Map<Int, User>
Map<String, Optional<User>>
```

The first argument is the key type.

The second argument is the value type.

---

# 3. Type Arity

`Map` requires exactly two type arguments.

Valid:

```text
Map<String, Int>
```

Invalid:

```text
Map
Map<String>
Map<String, Int, Bool>
```

Invalid arity produces:

```text
TYPE_INVALID_TYPE_ARGUMENTS
```

---

# 4. Map Literal Syntax

A map literal uses braces with key/value entries:

```kaj
{
    key_expression: value_expression,
    key_expression: value_expression
}
```

Example:

```kaj
{
    "Alice": 30,
    "Bob": 40
}
```

A map literal is an expression.

Parser context distinguishes map literals from statement blocks and record construction.

---

# 5. Key and Value Evaluation Order

Map literal entries evaluate left-to-right in source order.

Within each entry:

```text
key expression first
value expression second
```

Example:

```kaj
{
    key_a(): value_a(),
    key_b(): value_b()
}
```

evaluates:

```text
key_a()
value_a()
key_b()
value_b()
```

---

# 6. Homogeneous Keys

All map keys must have one common key type.

Example:

```kaj
{
    "a": 1,
    "b": 2
}
```

has key type:

```text
String
```

Incompatible key types are rejected.

Do not introduce `Any` or union-key maps.

---

# 7. Homogeneous Values

All map values must have one common value type.

Example:

```kaj
{
    "a": 1,
    "b": 2
}
```

has value type:

```text
Int
```

Incompatible value types are rejected.

---

# 8. Numeric Common-Type Rule

Map literal inference uses the same narrow numeric common-type rule as lists:

```text
same type -> same type
Int + Decimal -> Decimal
otherwise -> incompatible
```

This is applied independently to keys and values.

Example:

```kaj
{
    1: 10,
    2.5: 20
}
```

may infer:

```text
Map<Decimal, Int>
```

if Decimal is an allowed map key type.

---

# 9. Allowed Key Types

Kaj v0 map keys must have stable value equality and hashing semantics.

The allowed key types are:

```text
Bool
Int
Decimal
String
Bytes
```

The following are not valid map key types in v0:

```text
None
List<T>
Map<K, V>
record types
enum types
Optional<T>
Result<T, E>
function types
```

Additional key types may be added later after their equality/hash semantics are defined.

Invalid key type produces:

```text
TYPE_INVALID_MAP_KEY_TYPE
```

---

# 10. Decimal Keys

`Decimal` is a valid key type.

Kaj Decimal keys use exact decimal numeric equality.

No Python `float` conversion is permitted.

A contextual `Int -> Decimal` promotion may occur when constructing a `Map<Decimal, V>`.

---

# 11. Empty Map Literal

An empty map literal:

```kaj
{}
```

does not provide enough information to infer `K` or `V`.

Therefore:

```kaj
let values = {}
```

is invalid.

Emit:

```text
TYPE_CANNOT_INFER_MAP_TYPE
```

An explicit annotation makes it valid:

```kaj
let values: Map<String, Int> = {}
```

---

# 12. Contextual Map Literal Typing

When the expected type is:

```text
Map<K, V>
```

each key is checked against `K` and each value against `V`.

Example:

```kaj
let prices: Map<String, Decimal> = {
    "apple": 1,
    "orange": 2.5
}
```

is valid.

The `1` value is promoted from `Int` to `Decimal`.

---

# 13. Map Assignability

Map types are invariant.

Valid:

```text
Map<K, V> -> Map<K, V>
```

Do not generally allow:

```text
Map<String, Int> -> Map<String, Decimal>
```

even though `Int -> Decimal` exists for individual values.

Contextual literal construction is separate.

---

# 14. Lookup Syntax

Map lookup uses the existing index syntax:

```kaj
map[key]
```

Example:

```kaj
let ages = {
    "Alice": 30
}

let age = ages["Alice"]
```

If:

```text
ages: Map<String, Int>
```

then:

```text
age: Optional<Int>
```

---

# 15. Safe Lookup

Map lookup never assumes that a key exists.

For:

```text
Map<K, V>
```

lookup returns:

```text
Optional<V>
```

If the key exists:

```text
some(value)
```

If the key does not exist:

```text
none
```

This is the standard `Optional<V>` tagged value from the Optional/Result semantics.

---

# 16. Lookup Key Type

The lookup expression must be assignable to the map's key type.

Example:

```text
Map<String, Int>
```

requires a String key.

Invalid:

```kaj
ages[1]
```

produces:

```text
TYPE_MISMATCH
```

Existing `Int -> Decimal` promotion applies when the map key type is Decimal.

---

# 17. Lookup Does Not Throw for Missing Key

A missing map key is normal control flow.

It does not produce:

```text
RUNTIME_INDEX_OUT_OF_BOUNDS
```

or another lookup failure.

Instead:

```text
missing key -> Optional.none
```

---

# 18. Matching Lookup Results

Because lookup returns `Optional<V>`, normal Optional matching is used:

```kaj
match ages["Alice"] {
    some(age) => print(age)
    none => print("missing")
}
```

The pattern binding has type `V`.

---

# 19. `count`

A map has a built-in property:

```kaj
map.count
```

For any:

```text
Map<K, V>
```

`count` has type:

```text
Int
```

Example:

```kaj
let ages = {
    "Alice": 30,
    "Bob": 40
}

print(ages.count)
```

prints:

```text
2
```

---

# 20. `count` Is a Property

Use:

```kaj
map.count
```

not:

```kaj
map.count()
```

No general map method API is introduced in v0.

---

# 21. Unknown Map Members

No map members other than `count` are defined in this checkpoint.

Example:

```kaj
map.keys
```

is invalid in v0.

Use the existing unknown-member diagnostic:

```text
TYPE_UNKNOWN_MEMBER
```

---

# 22. Duplicate Runtime Keys

A map literal must not contain two entries that evaluate to the same key.

Example:

```kaj
{
    "a": 1,
    "a": 2
}
```

is invalid as a map value.

Because key expressions may be computed, duplicate-key detection is ultimately a runtime property.

If two evaluated keys are equal, execution fails with:

```text
RUNTIME_DUPLICATE_MAP_KEY
```

The implementation may additionally detect obviously duplicated constant literal keys statically, but runtime detection remains authoritative.

No silent "last value wins" behavior exists.

---

# 23. Map Value Semantics

Maps are value-like and immutable in Kaj v0.

There is no:

```text
map[key] = value
insert
remove
delete
clear
merge
update
```

in this checkpoint.

A `var` binding containing a map may be rebound to another compatible map value.

---

# 24. No Map Iteration Yet

Checkpoint 13 does not make `Map<K, V>` directly iterable.

This remains invalid:

```kaj
for item in map {
}
```

unless a future checkpoint defines map iteration semantics.

`for` continues to require `List<T>`.

---

# 25. No Map Ordering Contract

Kaj v0 maps do not expose iteration, so no public iteration-order contract is defined.

Internal runtime storage order must not become observable language behavior except where source evaluation order is explicitly defined during construction.

---

# 26. No Map Truthiness

Maps are not implicitly Boolean.

Invalid:

```kaj
if map {
}
```

Conditions still require `Bool`.

---

# 27. No Map Arithmetic

Do not define:

```text
map + map
map - map
```

or other arithmetic operators.

---

# 28. Map Equality

Map equality is deferred.

Do not inherit Python dictionary equality automatically.

---

# 29. Maps in Lists

Maps may be list elements.

Example:

```kaj
let values: List<Map<String, Int>> = [
    {"a": 1},
    {"b": 2}
]
```

when contextual typing provides the map types.

---

# 30. Maps in Records

Record fields may use map types.

Example:

```kaj
type UserIndex {
    users: Map<String, User>
}
```

---

# 31. Maps in Enums

Enum payloads may use map types.

Example:

```kaj
enum Response {
    success(values: Map<String, Int>)
    failure(message: String)
}
```

---

# 32. Maps in Optional and Result

Map types may appear inside standard tagged types:

```text
Optional<Map<String, User>>
Result<Map<String, User>, String>
```

and map values may themselves contain Optional/Result values.

---

# 33. Maps in Functions

Map types may appear in parameters and returns.

Example:

```kaj
fn find_age(ages: Map<String, Int>, name: String) -> Optional<Int> {
    return ages[name]
}
```

---

# 34. Runtime Representation

The reference interpreter should use a controlled Kaj map runtime representation.

Conceptually:

```text
KajMap
├── key type
├── value type
└── entries
```

It may use an internal Python dictionary only if Kaj key equality/hash semantics are explicitly preserved and no Python dictionary APIs leak into Kaj.

---

# 35. Runtime Key Representation

Runtime map keys must remain Kaj values.

Particular care is required because Python treats:

```text
True == 1
```

as true and gives them compatible hashes.

Kaj does not equate Bool and Int.

Therefore the runtime must not let Python dictionary key semantics collapse distinct Kaj key types.

Use typed/wrapped key identity or another explicit strategy.

---

# 36. Runtime Decimal Keys

Decimal keys must use exact Kaj Decimal semantics.

Never convert Decimal keys through Python float.

---

# 37. Runtime Literal Construction

Evaluate each key/value entry in source order.

Apply contextual promotions.

Validate the key's runtime type defensively.

Detect duplicate evaluated keys under Kaj equality semantics.

Construct the Kaj map value.

---

# 38. Runtime Lookup

For:

```kaj
map[key]
```

runtime:

```text
evaluate map
evaluate key
materialize approved key promotion if needed
look up using Kaj key semantics
```

If present:

```text
return Optional<V>.some(value)
```

If absent:

```text
return Optional<V>.none
```

---

# 39. Runtime `count`

`map.count` returns the number of key/value entries as Kaj `Int`.

Do not expose arbitrary Python dictionary attributes.

---

# 40. Lookup Evaluation Order

For:

```kaj
map_expression[key_expression]
```

evaluate:

```text
map expression first
key expression second
```

This matches existing index-expression evaluation order.

---

# 41. AST Representation

`MapLiteral` and map entries already exist in the Core AST.

Checkpoint 13 gives them full semantic and runtime meaning.

`Map<K, V>` uses the existing generic type-expression syntax.

Map lookup reuses `IndexExpression`.

`count` reuses `MemberAccessExpression`.

No new AST node type is required unless the current implementation lacks one of these forms.

---

# 42. AST JSON

If the existing MapLiteral, MapEntry, IndexExpression, GenericType, and MemberAccessExpression are already represented in AST JSON, no new AST JSON syntax is required.

Checkpoint 13 should preserve those representations and add semantic/runtime behavior only.

Do not serialize inferred Map types or lookup Optional types into AST JSON.

---

# 43. Source of Truth

For Kaj v0 map semantics:

```text
docs/language/maps.md
```

defines the enduring language behavior.

Compiler/runtime implementation must conform to it.
