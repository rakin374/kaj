# Kaj Checkpoint 15 — Formatter

**Audience:** Codex / implementation agent  
**Checkpoint:** 15  
**Goal:** Implement deterministic `AST -> canonical .kaj` formatting with semantic parse/format/parse preservation.

---

# 1. Primary Instruction

Implement **Checkpoint 15 only**.

Before editing code, read:

```text
docs/language/formatting.md
docs/internals/ast.md
docs/compiler/ast-json.md
docs/language/primitive-types.md
docs/language/functions.md
docs/language/lists.md
docs/language/records.md
docs/language/enums-and-match.md
docs/language/optional-and-result.md
docs/language/maps.md
docs/language/newtypes.md
dev/plans/pure-language-v0.md
```

Treat:

```text
docs/language/formatting.md
```

as authoritative.

Do not begin Checkpoint 16 CLI Completion.

---

# 2. Acceptance Target

The core invariant is:

```text
parse
format
parse
```

preserves semantic AST.

For every supported fixture:

```text
AST₁ = parse(source)
canonical = format(AST₁)
AST₂ = parse(canonical)
```

Then:

```text
semantic_ast_equal(AST₁, AST₂) == true
```

excluding source-span/location differences.

---

# 3. Formatter Architecture

Implement a dedicated AST formatter/printer.

Recommended module:

```text
src/kaj/formatter.py
```

or:

```text
src/kaj/formatting/
    __init__.py
    formatter.py
    doc.py
```

Use repository conventions.

Do not serialize AST to JSON and reconstruct source from JSON as the primary formatting architecture.

---

# 4. Input

Formatter input is the Core AST:

```text
Program
```

It must not reparse source internally.

Conceptual API:

```python
format_program(program: Program) -> str
```

A class-based API is also acceptable.

---

# 5. Output

Return canonical UTF-8-compatible Python `str`.

Rules:

```text
LF line endings
exactly one final newline for non-empty program
no trailing whitespace
4-space indentation
```

---

# 6. Span Independence

Do not use source spans to reproduce original formatting.

Spans may be used only for diagnostics/internal assertions if necessary.

Formatting must produce the same output for structurally identical ASTs with different spans.

---

# 7. Semantic AST Comparator

Add a reusable test helper that compares ASTs while ignoring:

```text
SourceSpan
SourceLocation
```

but preserving all semantic syntax structure.

Possible strategies:

- recursive structural comparison excluding spans
- normalized AST projection
- existing AST JSON projection with spans removed, if robust and deterministic

Do not mutate AST nodes to erase spans.

---

# 8. Precedence-Aware Expression Formatting

Implement precedence-aware formatting.

Do not parenthesize every binary expression.

Do not remove parentheses in a way that changes the reparsed tree.

Provide a clear internal precedence table matching the parser exactly.

Current precedence low -> high:

```text
or
and
== !=
< <= > >=
+ -
* / %
unary + - not
**
postfix call/member/index
primary
```

Respect `**` right associativity and unary/power interaction.

---

# 9. Parenthesis Algorithm

Formatter expression rendering should conceptually know:

```text
current expression precedence
parent precedence
position within parent
associativity
```

Add parentheses only when needed to preserve the AST.

Test left/right associativity explicitly.

---

# 10. Literal Formatting

Implement canonical formatting for:

```text
IntegerLiteral
DecimalLiteral
StringLiteral
BooleanLiteral
NoneLiteral
```

Integer:

```text
base-10
no unnecessary leading zeros
```

Decimal:

```text
exact decimal
no float
no scientific notation
must contain decimal point
```

String:

```text
double quoted
required escapes
Unicode preserved
```

---

# 11. Decimal Canonicalization

Be careful with semantic Decimal values.

Examples should remain parseable as Decimal literals:

```text
1.0
2.50 semantic value may canonicalize to 2.5 if scale is not semantically preserved
0.001
```

Do not emit:

```text
1
```

for a Decimal semantic value because reparsing would produce Int.

Do not emit exponent notation.

Add helper for canonical Decimal text.

---

# 12. String Escaping

Escape:

```text
"
\
\n
\r
\t
```

Use actual Unicode for other characters where valid.

Verify round-trip of:

```text
quotes
backslashes
newline
tab
carriage return
non-ASCII Unicode
```

---

# 13. Statements

Implement formatting for all currently supported statement nodes, including:

```text
BindingDeclaration
AssignmentStatement
ExpressionStatement
IfStatement
WhileStatement
ForStatement
BreakStatement
ContinueStatement
ReturnStatement
FunctionDeclaration
RecordDeclaration
EnumDeclaration
NewtypeDeclaration
MatchStatement
```

and any module wrapper/program structures.

---

# 14. Expressions

Implement formatting for all currently supported expression nodes:

```text
primitive literals
Identifier
UnaryExpression
BinaryExpression
CallExpression
MemberAccessExpression
IndexExpression
ListLiteral
MapLiteral
RecordConstructionExpression
Enum construction representation
Optional/Result standard constructors through their AST representation
newtype construction through its AST representation
```

Do not skip an existing supported AST node.

---

# 15. Type Expressions

Format:

```text
NamedType
GenericType
```

Examples:

```text
Int
User
List<Int>
Map<String, User>
Optional<User>
Result<User, String>
```

---

# 16. Block Formatting

Implement shared block rendering.

Canonical shape:

```text
header {
    statement
    statement
}
```

Outermost function body uses the same textual braces even though resolver/runtime scope semantics differ.

Formatter is purely syntactic.

---

# 17. Module Layout

Implement deterministic top-level spacing.

Use exactly one blank line between top-level declarations/statements when the canonical policy requires separation.

Avoid:

```text
multiple blank lines
leading blank lines
trailing blank lines before final newline
```

Add exact-string tests.

---

# 18. Collections and Width

Use canonical target width:

```text
88
```

Implement a deterministic strategy.

It does not need to be a sophisticated Wadler/Prettier engine if a simpler layout algorithm satisfies the spec and round-trip guarantees.

At minimum:

- simple constructs stay single-line when <= target width
- supported comma-separated constructs may switch to multiline when too long/complex
- multiline comma-separated constructs use trailing comma

---

# 19. Lists

Examples:

```kaj
[1, 2, 3]
```

Long/multiline:

```kaj
[
    expression,
    expression,
]
```

If choosing always-inline for v0 when syntactically possible, ensure width rules in the language doc are satisfied or update implementation to deterministic multiline behavior.

---

# 20. Maps

Simple:

```kaj
{"a": 1, "b": 2}
```

Multiline:

```kaj
{
    "a": expression,
    "b": expression,
}
```

Preserve entry source order.

---

# 21. Record Construction

Implement deterministic inline/multiline policy.

Recommended:

- zero/one short field may stay inline
- 2+ fields format multiline

Example:

```kaj
User {
    name: "Alice",
    age: 30,
}
```

Preserve initializer source order.

---

# 22. Calls

Simple:

```kaj
f(a, b)
```

Multiline when needed:

```kaj
f(
    long_argument,
    named: another_argument,
)
```

Preserve source argument order.

---

# 23. Function Formatting

Exact basic fixture:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

Test mutable parameters.

Test zero parameters.

Test generic parameter/return type expressions currently supported as concrete type syntax.

---

# 24. If/Else Formatting

Support:

```kaj
if condition {
    ...
} else if other {
    ...
} else {
    ...
}
```

Ensure parser reparses else-if into the same AST shape used before formatting.

If AST represents else-if as nested IfStatement, formatter should emit canonical `else if` instead of unnecessary:

```kaj
else {
    if ...
}
```

when semantic structure permits exact round-trip.

---

# 25. Loops

Format:

```kaj
while condition {
    ...
}
```

and:

```kaj
for value in values {
    ...
}
```

---

# 26. Records

Format:

```kaj
type User {
    name: String
    age: Int
}
```

Preserve field order.

No commas.

---

# 27. Enums

Format:

```kaj
enum Status {
    pending
    complete
}
```

Payload:

```kaj
enum Message {
    quit
    text(value: String)
    move(x: Int, y: Int)
}
```

Preserve variant and payload field order.

---

# 28. Match

Format unit patterns:

```kaj
match status {
    pending => print("pending")
    complete => print("complete")
}
```

Format payload bindings:

```kaj
match result {
    ok(value) => print(value)
    err(error) => print(error)
}
```

For block branches, format braces/indentation canonically.

Preserve case order.

---

# 29. Optional / Result Constructors

Whatever AST representation currently exists for:

```text
some(...)
none
ok(...)
err(...)
```

must format to canonical source forms.

Do not expose internal semantic tagged-type representation.

---

# 30. Newtypes

Format declaration:

```kaj
newtype UserId = String
```

Construction:

```kaj
UserId("abc")
```

Unwrap/member:

```kaj
id.value
```

---

# 31. No Comment Preservation

Do not add a CST or trivia model in this checkpoint.

Formatter may drop comments because current AST does not preserve them.

Add a clear regression test/documentation assertion so this is intentional rather than accidental.

Do not begin a comment-preserving architecture.

---

# 32. No Semantic Rewrites

Formatter must not:

```text
constant-fold
rename symbols
insert inferred types
reorder declarations
reorder fields
reorder arguments
rewrite match cases
simplify newtypes
change literal semantic types
```

---

# 33. Idempotence

For each formatting fixture:

```text
formatted1 = format(parse(source))
formatted2 = format(parse(formatted1))
```

Assert:

```text
formatted1 == formatted2
```

byte-for-byte.

This is mandatory.

---

# 34. Round-Trip Structural Tests

For each feature from Checkpoints 1-14, include parse-format-parse coverage.

At minimum cover:

```text
literals
unary/binary precedence
calls/named arguments
bindings/assignments
if/else/else-if
while
for
functions
lists
maps
records
enums
match/patterns
Optional/Result syntax
newtypes
nested combinations
```

---

# 35. Precedence Test Matrix

Add focused cases such as:

```text
a + b * c
(a + b) * c
a - (b - c)
(a - b) - c
a ** b ** c
(a ** b) ** c
-2 ** 2
(-2) ** 2
not a and b
not (a and b)
f(x).field[0]
```

Assert reparsed expression structure equals original.

---

# 36. Exact Canonical Output Tests

In addition to semantic round-trip, assert exact canonical strings for representative fixtures.

Examples:

```kaj
let x = 10
```

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

```kaj
type User {
    name: String
    age: Int
}
```

```kaj
enum Status {
    pending
    complete
}
```

---

# 37. Span-Insensitive Comparison

Do not require reparsed AST spans to match original.

Formatting necessarily changes:

```text
offset
line
column
end positions
```

Only syntax meaning/order/value/operators should be compared.

---

# 38. Formatter Errors

For a valid supported AST, formatting should not emit user-facing diagnostics.

If an impossible/internal AST state is encountered, fail with a clear internal formatter error rather than outputting malformed Kaj.

Recommended internal code/exception naming:

```text
FORMAT_UNSUPPORTED_NODE
FORMAT_INVALID_AST
```

These do not need to become public language diagnostics unless the current compiler architecture uses structured results everywhere.

---

# 39. Public API

Expose a simple formatter API usable later by the CLI.

Recommended:

```python
format_program(program: Program) -> str
```

Do not implement CLI commands yet unless an existing CLI hook makes a tiny non-invasive integration useful.

Checkpoint 16 owns CLI completion.

---

# 40. Optional File Helper

A pure helper may exist:

```python
format_source(source: str) -> FormatResult
```

that runs lexer/parser and formats only if parsing succeeds.

This is useful for tests and later CLI work.

But keep the canonical core:

```text
AST -> source
```

separate.

---

# 41. Suggested Files

Likely:

```text
src/kaj/formatter.py
```

or:

```text
src/kaj/formatting/__init__.py
src/kaj/formatting/formatter.py
```

Tests:

```text
tests/formatting/
├── test_formatter_literals.py
├── test_formatter_expressions.py
├── test_formatter_statements.py
├── test_formatter_functions.py
├── test_formatter_collections.py
├── test_formatter_records.py
├── test_formatter_enums_match.py
├── test_formatter_newtypes.py
├── test_formatter_roundtrip.py
├── test_formatter_idempotence.py
└── test_formatter_canonical_output.py
```

Follow current repo structure instead of forcing these exact paths if conventions differ.

---

# 42. Suggested Implementation Order

### Step 1
Read `docs/language/formatting.md` and inspect every current AST node.

### Step 2
Create formatter core, indentation, line-buffer/document helpers.

### Step 3
Implement type-expression formatting.

### Step 4
Implement primitive/primary/postfix expressions.

### Step 5
Implement precedence-aware unary/binary formatting.

### Step 6
Implement calls, lists, maps, record/enum/newtype construction forms.

### Step 7
Implement statements and blocks.

### Step 8
Implement functions/control flow.

### Step 9
Implement records/enums/match/newtypes.

### Step 10
Implement deterministic width/multiline decisions.

### Step 11
Add semantic AST comparison helper.

### Step 12
Add parse-format-parse tests.

### Step 13
Add idempotence tests.

### Step 14
Add exact canonical-output tests.

### Step 15
Run full quality gates.

### Step 16
Update:

```text
dev/plans/pure-language-v0.md
```

Do not begin Checkpoint 16.

---

# 43. Verification

Run:

```bash
pytest
ruff check .
mypy src
kaj --version
python -m kaj
```

All Checkpoints 0-14 tests must remain green.

---

# 44. Definition of Done

Checkpoint 15 is complete only when:

```text
[ ] AST -> canonical source formatter implemented
[ ] formatter accepts Program directly
[ ] formatter does not reparse source internally

[ ] output uses LF
[ ] output uses 4-space indentation
[ ] non-empty output ends with exactly one newline
[ ] no trailing whitespace emitted
[ ] formatting deterministic

[ ] primitive literals format canonically
[ ] Decimal remains Decimal when reparsed
[ ] strings escape correctly
[ ] Unicode strings remain Unicode

[ ] precedence-aware binary formatting implemented
[ ] associativity preserved
[ ] unary/power precedence preserved
[ ] postfix chains format correctly
[ ] unnecessary parentheses removed where safe
[ ] required parentheses retained

[ ] bindings format
[ ] assignments format
[ ] expression statements format
[ ] return formats
[ ] break/continue format where AST supports them

[ ] functions format
[ ] named arguments format
[ ] mutable parameters format

[ ] if/else/else-if format
[ ] while formats
[ ] for formats

[ ] List literals format
[ ] Map literals format
[ ] member/index access formats
[ ] List.count / Map.count syntax preserved

[ ] record declarations format
[ ] record construction formats
[ ] field order preserved

[ ] enum declarations format
[ ] unit/payload variants format
[ ] enum construction formats
[ ] match formats
[ ] pattern bindings format
[ ] case order preserved

[ ] Optional/Result syntax formats
[ ] some/none/ok/err formats

[ ] newtype declarations format
[ ] newtype construction/unwrapping formats

[ ] generic type expressions format
[ ] Map/List/Optional/Result nested types format

[ ] source-order-sensitive AST children are never reordered
[ ] formatter does not rename anything
[ ] formatter does not insert inferred types
[ ] formatter does not constant-fold
[ ] comments intentionally not preserved

[ ] semantic AST comparator ignores spans
[ ] parse-format-parse preserves semantic AST
[ ] formatter idempotence holds
[ ] exact canonical-output tests exist

[ ] precedence matrix tests pass
[ ] nested feature round-trip tests pass

[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] Checkpoints 0-14 remain passing

[ ] no full CLI completion begun
[ ] no CST/comment-preserving formatter built
[ ] no user-configurable style options added

[ ] dev/plans/pure-language-v0.md updated
```

---

# 45. Completion Report

When finished, report:

```text
Checkpoint 15 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

Formatter architecture:
- ...

Canonical layout rules implemented:
- ...

Expression precedence handling:
- ...

Multiline/width behavior:
- ...

Semantic AST comparison:
- ...

Acceptance:
- parse -> format -> parse semantic preservation: PASS/FAIL
- idempotence: PASS/FAIL

Representative canonical output:
- ...

Verification:
- pytest: PASS/FAIL
- ruff check .: PASS/FAIL
- mypy src: PASS/FAIL
- Kaj CLI bootstrap: PASS/FAIL

Decisions/deviations:
- ...

Known issues:
- ...
```

Do not proceed to Checkpoint 16.
