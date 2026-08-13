# Kaj Checkpoint 11 — Enums and Match

**Audience:** Codex / implementation agent  
**Checkpoint:** 11  
**Goal:** Implement nominal enums, payload variants, construction, exhaustive `match`, pattern binding, and interpreter execution.

---

# 1. Primary Instruction

Implement **Checkpoint 11 only**.

Before editing code, read:

```text
docs/language/enums-and-match.md
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
docs/language/enums-and-match.md
```

as authoritative.

Do not begin Checkpoint 12 Optional and Result.

---

# 2. Acceptance Target

This must parse, resolve, type-check, execute, and print:

```kaj
enum Status {
    pending
    complete
}

let status = Status.pending

match status {
    pending => print("pending")
    complete => print("complete")
}
```

Expected output:

```text
pending
```

A missing variant must produce:

```text
NON_EXHAUSTIVE_MATCH
```

---

# 3. AST Additions

Add explicit AST nodes for:

```text
EnumDeclaration
EnumVariantDeclaration
EnumPayloadField

EnumConstructionExpression
EnumConstructorArgument

MatchStatement
MatchCase
EnumPattern
PatternBinding
```

Use the repository's existing AST naming/style conventions where reasonable.

Preserve:

```text
SourceSpan
ordered child collections
syntax-only AST
immutability where practical
```

Do not store semantic symbols/types on AST nodes.

---

# 4. Parser — Enum Declarations

Parse:

```kaj
enum Status {
    pending
    complete
}
```

and payload enums:

```kaj
enum Message {
    quit
    text(value: String)
    move(x: Int, y: Int)
}
```

Payload fields use:

```text
IDENTIFIER ":" type_expression
```

comma-separated inside parentheses.

Do not add generic enum syntax.

---

# 5. Parser — Enum Construction

Support unit construction:

```kaj
Status.pending
```

Support payload construction:

```kaj
Message.text(value: "hello")
Message.move(x: 1, y: 2)
```

Constructor arguments are named.

Do not treat payload variant construction as a normal function call semantically, even if parser reuse is convenient internally.

---

# 6. Parser — Match

Parse:

```kaj
match status {
    pending => print("pending")
    complete => print("complete")
}
```

Support payload patterns:

```kaj
match message {
    quit => print("quit")
    text(value) => print(value)
}
```

Branch bodies may use the existing statement/block model.

Keep syntax deterministic and compatible with existing `=>` token.

---

# 7. Parser — Pattern Restrictions

Checkpoint 11 patterns support only:

```text
unit enum variant
payload enum variant with simple binding identifiers
```

Do not parse:

```text
wildcards
guards
nested destructuring
literal patterns
record patterns
or-patterns
```

unless the parser architecture requires a general base node but semantics remain restricted.

---

# 8. AST JSON

Extend serializer/deserializer and:

```text
schemas/ast/v1.json
docs/compiler/ast-json.md
```

for the new enum/match AST nodes.

Add stable snake_case kinds.

Round-trip tests must cover:

```text
unit enum
payload enum
unit construction
payload construction
match
payload pattern bindings
```

Do not include semantic exhaustiveness/type info in JSON.

---

# 9. Type Namespace Integration

Reuse/extend the module type namespace introduced for Records.

Enums and records share one type-name namespace.

Add an enum type symbol kind if the type-symbol model distinguishes kinds.

Detect collisions across all type declarations.

---

# 10. Enum Predeclaration

Before resolving enum payload types:

1. scan top-level enum declarations
2. predeclare enum type names
3. preserve existing record predeclaration
4. reject duplicate type names
5. resolve enum payload field types

All record+enum type names should be visible during type-definition resolution.

---

# 11. Semantic EnumType

Add nominal semantic type representation.

Conceptually:

```text
EnumType
├── type_symbol
├── name
└── ordered variants
```

Each variant:

```text
name
ordered payload fields
```

Each payload field:

```text
name
semantic type
span
```

Type equality is nominal by type-symbol identity.

---

# 12. Duplicate Variants

Reject repeated variant names within one enum.

Diagnostic:

```text
TYPE_DUPLICATE_VARIANT
```

Keep first variant active for deterministic recovery.

---

# 13. Duplicate Payload Fields

Reject duplicate payload field names within one variant.

Reuse:

```text
TYPE_DUPLICATE_FIELD
```

or another existing field-declaration diagnostic consistently.

---

# 14. Payload Type Resolution

Resolve payload field annotations using the existing type namespace.

Support:

```text
primitive
List
record
enum
```

Unknown types:

```text
TYPE_UNKNOWN_TYPE
```

Forward references must work.

---

# 15. Unit Variant Typing

For:

```kaj
Status.pending
```

resolve:

```text
Status -> EnumType
pending -> declared unit variant
```

Result type:

```text
Status
```

Unknown variant:

```text
TYPE_UNKNOWN_VARIANT
```

---

# 16. Payload Variant Typing

For:

```kaj
Message.text(value: "hello")
```

perform:

1. resolve enum type
2. resolve variant
3. verify variant has payload
4. map constructor arguments by payload field name
5. detect unknown/missing/duplicate fields
6. type-check argument expressions
7. check assignability
8. result type = enum type

Use existing field diagnostics where appropriate:

```text
TYPE_MISSING_FIELD
TYPE_UNKNOWN_FIELD
TYPE_DUPLICATE_FIELD
TYPE_MISMATCH
```

---

# 17. Invalid Unit/Payload Construction Forms

Reject:

```kaj
Message.text
```

if `text` requires payload.

Reject:

```kaj
Status.pending()
```

if `pending` has no payload, if this syntax reaches semantic analysis.

Use a clear deterministic type diagnostic.

A dedicated code such as:

```text
TYPE_INVALID_VARIANT_CONSTRUCTION
```

is acceptable.

---

# 18. Match Scrutinee Typing

Type-check the scrutinee.

It must be:

```text
EnumType
```

Otherwise:

```text
TYPE_MATCH_REQUIRES_ENUM
```

Continue safely with internal error type handling.

---

# 19. Match Case Variant Resolution

Each case pattern variant name is looked up against the scrutinee's enum declaration.

Do not lexical-lookup it as an ordinary value name.

Unknown:

```text
TYPE_UNKNOWN_VARIANT
```

---

# 20. Pattern Arity

For payload variant:

```text
declared payload count == pattern binding count
```

Otherwise:

```text
TYPE_PATTERN_ARITY_MISMATCH
```

Unit variant must have zero bindings.

---

# 21. Pattern Binding Symbols

Each binding identifier in a pattern introduces a new value symbol in that case's branch scope.

Either extend resolver support for match scopes/pattern declarations or perform a clean coordinated semantic phase extension.

Preferred approach:

- resolver understands `MatchStatement`
- creates one child block scope per case
- declares pattern binding symbols before resolving case body
- type checker later assigns payload types to those symbols

Do not bypass symbol identity by storing branch locals only by string.

---

# 22. Pattern Binding Types

Assign pattern-bound symbols according to payload declaration order.

Example:

```kaj
enum Pair {
    pair(left: Int, right: String)
}

match value {
    pair(a, b) => ...
}
```

inside branch:

```text
a: Int
b: String
```

---

# 23. Duplicate Pattern Bindings

Reject:

```kaj
pair(x, x)
```

as duplicate declarations in the same pattern/branch scope.

Reuse:

```text
RESOLVE_DUPLICATE_NAME
```

where appropriate, since these are value declarations in one lexical scope.

---

# 24. Case Scopes

Each match case gets an independent child block scope.

Pattern bindings exist only inside their own case body.

Shadowing outer names is allowed.

Sibling cases do not share bindings.

---

# 25. Duplicate Match Cases

Track variants covered by the match.

If the same variant occurs more than once:

```text
TYPE_DUPLICATE_MATCH_CASE
```

Continue checking branch contents.

---

# 26. Exhaustiveness

After validating case patterns, compare covered valid enum variants with the full declaration.

If any are missing:

```text
NON_EXHAUSTIVE_MATCH
```

The diagnostic should identify missing variant names where practical.

No wildcard/default behavior.

---

# 27. Exhaustiveness With Invalid Cases

Unknown or malformed cases do not count toward exhaustiveness.

Example:

```kaj
enum Status {
    pending
    complete
}

match status {
    pending => ...
    missing => ...
}
```

should still report `complete` as missing, in addition to unknown variant.

Avoid crashing or marking the match exhaustive because case count equals variant count.

---

# 28. Match Body Type Checking

Type-check every branch body using its case scope and pattern symbol types.

Do not require a common branch result type if `match` is represented as a statement.

---

# 29. Definite Return Integration

Extend Checkpoint 7 structural return analysis.

An exhaustive `match` definitely returns iff every branch definitely returns.

Example:

```kaj
fn code(status: Status) -> Int {
    match status {
        pending => return 0
        complete => return 1
    }
}
```

must satisfy missing-return analysis.

If any branch can fall through, the match does not definitely return.

---

# 30. Runtime Enum Value

Add explicit controlled runtime representation:

```text
KajEnumValue
├── enum type identity
├── variant identity
└── payload values
```

Do not represent nominal enums only as strings.

---

# 31. Runtime Unit Construction

`Status.pending` creates an enum value with no payload.

---

# 32. Runtime Payload Construction

Evaluate constructor argument expressions left-to-right in source order.

Map values to payload fields by semantic argument mapping.

Materialize approved `Int -> Decimal` promotions.

Construct `KajEnumValue`.

---

# 33. Runtime Match

For:

```kaj
match value {
    ...
}
```

1. evaluate scrutinee once
2. inspect runtime enum + variant identity
3. select matching case
4. create fresh branch environment
5. bind payload values to pattern symbols
6. execute branch
7. propagate return control normally

Only one branch executes.

---

# 34. Runtime Pattern Bindings

Bind payload values according to the semantic variant payload ordering and pattern binding mapping.

Do not re-resolve variant structure by raw field names at runtime if semantic metadata already exists.

---

# 35. Runtime Defensive Errors

A statically valid exhaustive match should always find a branch.

If runtime enum/branch metadata is inconsistent due to an internal compiler bug, return a structured:

```text
RUNTIME_INTERNAL_ERROR
```

Do not silently fall through.

---

# 36. Records/Lists Integration

Ensure:

```text
record fields may use enum types
lists may contain enums
enum payloads may contain records/lists/enums
```

Existing nominal/type rules must remain intact.

---

# 37. Functions Integration

Ensure enum types work in:

```text
parameters
returns
calls
return checking
```

Recursive functions using match should type-check and execute.

---

# 38. Print

Do not broaden `print` to whole enum values.

Acceptance prints Strings from branches.

---

# 39. Required Diagnostics

Add:

```text
TYPE_DUPLICATE_VARIANT
TYPE_UNKNOWN_VARIANT
TYPE_PATTERN_ARITY_MISMATCH
TYPE_DUPLICATE_MATCH_CASE
TYPE_MATCH_REQUIRES_ENUM
NON_EXHAUSTIVE_MATCH
```

Optionally:

```text
TYPE_INVALID_VARIANT_CONSTRUCTION
```

Reuse existing:

```text
TYPE_DUPLICATE_TYPE_NAME
TYPE_DUPLICATE_FIELD
TYPE_MISSING_FIELD
TYPE_UNKNOWN_FIELD
TYPE_UNKNOWN_TYPE
TYPE_MISMATCH
RESOLVE_DUPLICATE_NAME
```

where appropriate.

---

# 40. Required Tests — Parsing

Parse:

```kaj
enum Status {
    pending
    complete
}
```

Parse payload enum.

Parse unit construction.

Parse payload construction.

Parse unit match patterns.

Parse payload match patterns.

Verify spans.

---

# 41. Required Tests — AST JSON

Round-trip all new enum/match node forms.

Validate against updated schema.

Reject malformed enum/match JSON structures.

---

# 42. Required Tests — Enum Declarations

Test:

```text
unit variants
payload variants
multiple payload fields
duplicate variants
duplicate payload fields
unknown payload type
forward enum type references
record <-> enum type references
```

---

# 43. Required Tests — Construction

Test:

```kaj
Status.pending
```

type = Status.

Test payload construction.

Test wrong payload type.

Test missing payload field.

Test unknown payload field.

Test duplicate payload field.

Test unknown variant.

Test Int->Decimal payload promotion.

---

# 44. Required Tests — Match Exhaustiveness

Required:

```kaj
enum Status {
    pending
    complete
}

match status {
    pending => ...
    complete => ...
}
```

passes.

Missing one:

```kaj
match status {
    pending => ...
}
```

→

```text
NON_EXHAUSTIVE_MATCH
```

Test three+ variant enum and report all missing variants where implementation supports it.

---

# 45. Required Tests — Duplicate/Unknown Cases

Test duplicate variant cases.

Test unknown variant case.

Verify invalid case does not satisfy exhaustiveness.

---

# 46. Required Tests — Pattern Binding

Example:

```kaj
enum Message {
    text(value: String)
}

let message = Message.text(value: "hello")

match message {
    text(value) => print(value)
}
```

→ `hello`

Verify pattern binding type = String.

Verify binding unavailable outside branch.

Verify shadowing outer value works.

Verify duplicate binding identifiers fail.

---

# 47. Required Tests — Pattern Arity

Test payload variant with:

```text
too few bindings
too many bindings
```

Both produce:

```text
TYPE_PATTERN_ARITY_MISMATCH
```

Test unit variant with binding also fails.

---

# 48. Required Tests — Runtime Match

Acceptance:

```kaj
enum Status {
    pending
    complete
}

let status = Status.pending

match status {
    pending => print("pending")
    complete => print("complete")
}
```

Output:

```text
pending
```

Verify only selected branch executes.

---

# 49. Required Tests — Payload Runtime

Test:

```kaj
enum Message {
    text(value: String)
    quit
}

let message = Message.text(value: "hello")

match message {
    text(value) => print(value)
    quit => print("quit")
}
```

→

```text
hello
```

---

# 50. Required Tests — Definite Return

Test:

```kaj
fn code(status: Status) -> Int {
    match status {
        pending => return 0
        complete => return 1
    }
}
```

passes missing-return analysis.

Test one branch without return → `TYPE_MISSING_RETURN`.

---

# 51. Required Tests — Nominal Typing

Use two identical-shape enum declarations.

Verify values are not assignable across types.

Verify `List<EnumA>` is not `List<EnumB>`.

---

# 52. Required Tests — Evaluation Order

For payload variant construction with observable argument expressions, verify evaluation is left-to-right in source order.

Verify match scrutinee evaluates exactly once.

---

# 53. Suggested Files

Likely extend/add:

```text
src/kaj/ast/
src/kaj/parser/
src/kaj/serialization/
src/kaj/semantic/type_symbols.py
src/kaj/semantic/types.py
src/kaj/semantic/resolver.py
src/kaj/semantic/type_checker.py
src/kaj/runtime/values.py
src/kaj/runtime/interpreter.py
```

Potential focused files:

```text
src/kaj/semantic/enums.py
```

only if useful.

Follow existing repository conventions.

---

# 54. Suggested Implementation Order

### Step 1
Read `docs/language/enums-and-match.md`.

### Step 2
Add enum/match AST nodes.

### Step 3
Implement parser support.

### Step 4
Extend AST JSON/schema/docs.

### Step 5
Extend type predeclaration for enums.

### Step 6
Implement `EnumType`, variants, payload descriptors.

### Step 7
Resolve payload field types and declaration diagnostics.

### Step 8
Implement enum construction typing.

### Step 9
Extend resolver for match cases and pattern-bound symbols.

### Step 10
Implement match pattern typing and binding types.

### Step 11
Implement duplicate-case and exhaustiveness checking.

### Step 12
Integrate match with definite-return analysis.

### Step 13
Add `KajEnumValue`.

### Step 14
Implement enum construction runtime.

### Step 15
Implement match runtime.

### Step 16
Add full unit/integration/end-to-end tests.

### Step 17
Run all quality gates.

### Step 18
Update:

```text
dev/plans/pure-language-v0.md
```

Do not begin Checkpoint 12.

---

# 55. Verification

Run:

```bash
pytest
ruff check .
mypy src
kaj --version
python -m kaj
```

If `kaj run` exists, run the acceptance program.

All previous checkpoint tests must remain green.

---

# 56. Definition of Done

Checkpoint 11 is complete only when:

```text
[ ] enum declaration AST implemented
[ ] enum variant AST implemented
[ ] payload field AST implemented
[ ] enum construction AST implemented
[ ] match AST implemented
[ ] enum pattern/binding AST implemented

[ ] enum declarations parse
[ ] payload variants parse
[ ] unit variant construction parses
[ ] payload construction parses
[ ] match parses
[ ] payload patterns parse

[ ] AST JSON supports enum/match nodes
[ ] JSON schema updated
[ ] enum/match AST round trips pass

[ ] enum type names share module type namespace
[ ] enum names predeclared
[ ] forward enum references supported
[ ] duplicate type names still rejected

[ ] EnumType implemented
[ ] nominal enum identity implemented
[ ] duplicate variants rejected
[ ] duplicate payload fields rejected
[ ] payload field types resolved
[ ] unknown payload types rejected

[ ] unit variant construction typed
[ ] payload construction typed
[ ] unknown variants rejected
[ ] missing payload fields rejected
[ ] unknown payload fields rejected
[ ] duplicate payload fields rejected
[ ] payload type mismatch rejected
[ ] Int->Decimal payload promotion supported

[ ] match requires enum scrutinee
[ ] case variants resolved against scrutinee enum
[ ] pattern arity checked
[ ] pattern symbols created
[ ] pattern symbols receive payload types
[ ] pattern binding scope correct
[ ] duplicate pattern bindings rejected

[ ] duplicate match cases rejected
[ ] exhaustiveness implemented
[ ] missing cases emit NON_EXHAUSTIVE_MATCH
[ ] invalid/unknown cases do not falsely satisfy exhaustiveness
[ ] no wildcard/default behavior added

[ ] exhaustive all-return match counts as definitely returning
[ ] incomplete branch return does not

[ ] KajEnumValue runtime representation implemented
[ ] unit variant construction executes
[ ] payload variant construction executes
[ ] constructor arguments evaluate left-to-right
[ ] match scrutinee evaluates once
[ ] correct branch selected
[ ] only selected branch executes
[ ] payload values bound into branch scope
[ ] return propagates through match

[ ] records/lists/functions interoperate with enum types
[ ] nominal enum assignability enforced

[ ] TYPE_DUPLICATE_VARIANT implemented
[ ] TYPE_UNKNOWN_VARIANT implemented
[ ] TYPE_PATTERN_ARITY_MISMATCH implemented
[ ] TYPE_DUPLICATE_MATCH_CASE implemented
[ ] TYPE_MATCH_REQUIRES_ENUM implemented
[ ] NON_EXHAUSTIVE_MATCH implemented

[ ] acceptance program prints pending
[ ] missing-case acceptance emits NON_EXHAUSTIVE_MATCH

[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] Checkpoints 0-10 remain passing

[ ] no Optional/Result work begun
[ ] no wildcard patterns implemented
[ ] no pattern guards implemented
[ ] no nested destructuring implemented
[ ] no generic enums implemented
[ ] no enum methods implemented

[ ] dev/plans/pure-language-v0.md updated
```

---

# 57. Completion Report

When finished, report:

```text
Checkpoint 11 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

AST/parser:
- ...

Enum type model:
- ...

Variant construction:
- ...

Match/pattern binding:
- ...

Exhaustiveness:
- ...

Definite-return integration:
- ...

Runtime representation:
- ...

Diagnostics:
- ...

Acceptance:
- enum match output: PASS/FAIL
- expected output `pending`: PASS/FAIL
- missing case -> NON_EXHAUSTIVE_MATCH: PASS/FAIL

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

Do not proceed to Checkpoint 12.
