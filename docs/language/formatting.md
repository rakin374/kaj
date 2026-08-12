# Kaj Canonical Formatting

**Status:** Authoritative for Kaj v0 source formatting semantics  
**Scope:** canonical `.kaj` rendering from AST  
**Not covered:** comment preservation, source-to-source minimal diffs, user-configurable style profiles, CST formatting

---

# 1. Purpose

Kaj defines a canonical source representation for its AST.

The formatter performs:

```text
AST
 ↓
canonical .kaj source
```

The canonical formatter is deterministic.

Equivalent supported ASTs must format the same way regardless of their original whitespace.

---

# 2. Semantic Preservation

Formatting must preserve the semantic AST.

For supported source:

```text
source
  ↓ parse
AST₁
  ↓ format
canonical source
  ↓ parse
AST₂
```

`AST₁` and `AST₂` must be semantically equivalent.

Source spans are not required to be identical after formatting because formatting changes textual positions.

---

# 3. Canonical, Not Lossless

The formatter is AST-based, not CST-based.

Therefore it does not preserve:

```text
original whitespace
original line breaks
original indentation
original redundant parentheses
comments
original literal lexeme spelling where semantic value is preserved
```

Comments are not represented in the semantic AST and are therefore not preserved in v0.

---

# 4. Determinism

Formatting the same AST repeatedly must produce byte-for-byte identical UTF-8 source.

Also:

```text
format(parse(format(parse(source))))
```

must stabilize after the first formatting pass.

---

# 5. Encoding

Canonical Kaj source is UTF-8.

Unicode string contents are emitted directly where valid.

Do not force ASCII escape output for ordinary Unicode text.

---

# 6. Newlines

Canonical output uses:

```text
LF (`\n`)
```

line endings.

Do not emit CRLF as canonical output.

A non-empty formatted program ends with exactly one newline.

---

# 7. Indentation

Canonical indentation is:

```text
4 spaces per nesting level
```

Tabs are not emitted by the formatter.

---

# 8. Trailing Whitespace

Canonical output contains no trailing spaces or tabs at line ends.

---

# 9. Blank Lines

Use blank lines sparingly and deterministically.

At module level:

- separate top-level type/function declarations from adjacent top-level declarations/statements with one blank line where needed for readability
- do not emit multiple consecutive blank lines
- do not place blank lines purely due to original source layout

The formatter owns the final layout.

---

# 10. Braces

Opening braces stay on the same line as the construct header.

Example:

```kaj
if condition {
    ...
}
```

Not:

```kaj
if condition
{
    ...
}
```

The same applies to:

```text
fn
if
else
while
for
match
type
enum
record construction
```

---

# 11. Empty Blocks

An empty block formats as:

```kaj
{
}
```

within its surrounding construct.

Example:

```kaj
fn noop() -> None {
}
```

Do not emit `{ }`.

---

# 12. Statements

One statement is emitted per logical line.

Semicolons are not emitted.

---

# 13. Bindings

Canonical binding format:

```kaj
let name = expression
var name = expression
```

With annotation:

```kaj
let name: Type = expression
var name: Type = expression
```

Exactly one space around `=`.

---

# 14. Assignment

Canonical assignment:

```kaj
x = value
x += value
x -= value
x *= value
x /= value
```

Exactly one space around the assignment operator.

---

# 15. Function Declarations

Canonical function format:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

Rules:

- one space after commas
- no space before comma
- one space around `->`
- no extra spaces inside parameter parentheses
- parameter `var` appears immediately before parameter name

Example:

```kaj
fn bump(var value: Int) -> Int {
    value += 1
    return value
}
```

---

# 16. Calls

Canonical call format:

```kaj
add(1, 2)
send("hello", priority: 2)
```

Rules:

- comma followed by one space
- named argument uses `name: value`
- no spaces immediately inside parentheses

---

# 17. Literals

Integer literals format in canonical base-10 form.

Decimal literals format as canonical decimal text preserving exact numeric value.

Boolean literals:

```text
true
false
```

None literal:

```text
none
```

String literals use double quotes.

---

# 18. String Escaping

Canonical String output uses double-quoted literals.

The formatter must escape at least:

```text
"
\
newline
carriage return
tab
```

as:

```text
\"
\\
\n
\r
\t
```

Other Unicode characters should remain directly encoded unless escaping is required for valid syntax.

---

# 19. Integer Formatting

Canonical Int rendering:

```text
base-10 digits
no leading zeros except zero itself
```

Examples:

```text
0
1
42
1000
```

Negative integers are represented structurally through unary `-`:

```kaj
-10
```

---

# 20. Decimal Formatting

Canonical Decimal rendering must preserve exact semantic value and remain parseable as a Kaj Decimal literal.

Examples:

```text
1.0
2.5
0.125
```

Do not emit scientific notation in v0.

Do not emit a trailing decimal point such as:

```text
1.
```

because that syntax is invalid in Kaj v0.

---

# 21. Unary Expressions

Canonical:

```kaj
-x
+x
not ready
```

For word operator `not`, emit one space after the operator.

For symbolic unary `+`/`-`, do not emit a space.

Parenthesize the operand only when required to preserve AST meaning.

---

# 22. Binary Operator Spacing

Use exactly one space around binary operators.

Examples:

```kaj
a + b
a - b
a * b
a / b
a % b
a ** b
a == b
a != b
a < b
a <= b
a > b
a >= b
a and b
a or b
```

---

# 23. Precedence Preservation

The formatter must preserve AST grouping using operator precedence and associativity.

Parentheses are emitted only when required to ensure reparsing produces the same expression tree.

Example AST:

```text
(a + b) * c
```

must format:

```kaj
(a + b) * c
```

But:

```text
a + (b * c)
```

may canonically format as:

```kaj
a + b * c
```

because reparsing preserves the same tree.

---

# 24. Power Associativity

`**` is right-associative.

The formatter must respect the parser's precedence rules.

Examples must be parenthesized as needed to distinguish:

```text
(a ** b) ** c
a ** (b ** c)
```

The latter may canonicalize to:

```kaj
a ** b ** c
```

if reparsing is right-associative.

---

# 25. Unary vs Power

Kaj parses:

```kaj
-2 ** 2
```

as:

```text
-(2 ** 2)
```

The formatter must preserve this rule.

If the AST means:

```text
(-2) ** 2
```

the formatter must emit:

```kaj
(-2) ** 2
```

---

# 26. Postfix Expressions

Canonical postfix formatting has no unnecessary spaces:

```kaj
f(x)
user.name
values[index]
```

Postfix chains remain compact:

```kaj
rows[1][0]
user.address.city
```

---

# 27. List Literals

Short/simple list literals format inline:

```kaj
[1, 2, 3]
```

The formatter may choose multiline layout for sufficiently complex/nested elements, but the rule must be deterministic.

For v0, preferring a simple width-based strategy is acceptable if the width is fixed by the formatter specification/implementation.

---

# 28. Map Literals

Simple map literals format:

```kaj
{"Alice": 30, "Bob": 40}
```

For complex or sufficiently long maps, multiline canonical formatting is allowed:

```kaj
{
    "Alice": 30,
    "Bob": 40,
}
```

If multiline collection formatting is implemented, use trailing commas consistently.

The choice between inline/multiline must be deterministic.

---

# 29. Canonical Line Width

Canonical formatter target line width is:

```text
88 columns
```

This is a formatting target, not a hard semantic limit.

Long indivisible tokens such as long strings may exceed it.

The formatter may break supported composite constructs to stay near this width.

---

# 30. Trailing Commas

For multiline comma-separated constructs, emit a trailing comma.

Examples include multiline:

```text
calls
list literals
map literals
record constructions
enum payload constructor arguments
```

For single-line forms, no trailing comma is emitted.

---

# 31. Type Expressions

Canonical named type:

```text
Int
User
```

Generic type:

```text
List<Int>
Map<String, User>
Optional<User>
Result<User, String>
```

Rules:

- no spaces immediately inside `<` or `>`
- one space after commas between type arguments

---

# 32. If Statements

Canonical:

```kaj
if condition {
    ...
}
```

With else:

```kaj
if condition {
    ...
} else {
    ...
}
```

Else-if:

```kaj
if a {
    ...
} else if b {
    ...
} else {
    ...
}
```

Do not insert unnecessary nesting braces around an `else if`.

---

# 33. While Loops

Canonical:

```kaj
while condition {
    ...
}
```

---

# 34. For Loops

Canonical:

```kaj
for value in values {
    ...
}
```

Exactly one space around `in`.

---

# 35. Return

Bare:

```kaj
return
```

With value:

```kaj
return expression
```

---

# 36. Break and Continue

Canonical:

```kaj
break
continue
```

where these syntax nodes exist.

---

# 37. Record Declarations

Canonical:

```kaj
type User {
    name: String
    age: Int
}
```

One field per line.

No commas after record field declarations.

Preserve declared field order.

---

# 38. Record Construction

Short form may be inline when simple:

```kaj
User { name: "Alice", age: 30 }
```

Multiline form:

```kaj
User {
    name: "Alice",
    age: 30,
}
```

For readability, canonical formatter may prefer multiline record construction whenever it has more than one field.

Whichever policy is implemented must be deterministic.

Preserve source initializer order because expression evaluation order is semantically observable.

---

# 39. Enum Declarations

Canonical:

```kaj
enum Status {
    pending
    complete
}
```

Payload variants:

```kaj
enum Message {
    quit
    text(value: String)
    move(x: Int, y: Int)
}
```

One variant per line.

No commas between variants.

---

# 40. Enum Construction

Unit:

```kaj
Status.pending
```

Payload:

```kaj
Message.text(value: "hello")
```

Use standard call-like comma spacing for payload arguments.

---

# 41. Match

Canonical:

```kaj
match status {
    pending => print("pending")
    complete => print("complete")
}
```

For branch blocks:

```kaj
match message {
    text(value) => {
        print(value)
    }
    quit => {
        print("quit")
    }
}
```

One case per line/block.

---

# 42. Match Patterns

Unit variant:

```text
pending
```

Payload variant:

```text
some(value)
ok(value)
err(error)
```

Use comma-space rules for multiple bindings:

```text
move(x, y)
```

---

# 43. Optional and Result

Canonical type syntax:

```text
Optional<User>
Result<User, String>
```

Canonical constructors:

```kaj
some(value)
none
ok(value)
err(error)
```

No special formatting beyond their existing expression/pattern forms.

---

# 44. Newtype Declarations

Canonical:

```kaj
newtype UserId = String
```

Exactly one space around `=`.

---

# 45. Newtype Construction and Unwrap

Canonical:

```kaj
UserId("abc")
id.value
```

---

# 46. Comments

Comments are not preserved by the v0 AST formatter.

Given:

```kaj
// comment
let x = 1
```

the parser's semantic AST contains no comment node, so formatting may produce:

```kaj
let x = 1
```

Comment-preserving formatting requires a CST/trivia model and is deferred.

---

# 47. Source Spans

The formatter ignores original source spans for layout.

Generated text naturally creates new locations/spans when reparsed.

Semantic comparison for formatter round-trip must ignore span differences.

---

# 48. Semantic AST Equivalence

Formatter round-trip comparison should compare structural syntax meaning, excluding fields whose purpose is source location.

Conceptually:

```text
same node kinds
same operator enums
same declaration names
same field/variant order
same literal semantic values
same type expressions
same expression grouping
same statement structure
```

Spans are excluded.

---

# 49. No Semantic Reordering

The formatter must not reorder constructs whose source order has semantic or declared significance.

Do not reorder:

```text
module statements
function declarations relative to source
record fields
enum variants
function parameters
call arguments
list elements
map entries
record constructor fields
enum constructor arguments
match cases
```

Even when some constructs could theoretically be reordered without changing static types, canonical formatting preserves AST order.

---

# 50. No Name Rewriting

The formatter does not rename:

```text
variables
parameters
functions
types
fields
variants
pattern bindings
```

---

# 51. No Type Insertion

The formatter does not add inferred type annotations.

Example:

```kaj
let x = 10
```

must not become:

```kaj
let x: Int = 10
```

Formatting is syntactic rendering, not source elaboration.

---

# 52. No Semantic Simplification

The formatter does not perform constant folding or optimization.

Example:

```kaj
1 + 2
```

remains an addition expression.

It must not become:

```kaj
3
```

---

# 53. Idempotence

Canonical formatting is idempotent:

```text
format(parse(format(parse(source))))
==
format(parse(source))
```

for supported source.

---

# 54. Source of Truth

For Kaj v0 canonical source formatting:

```text
docs/language/formatting.md
```

defines the enduring formatter behavior.

The formatter implementation must conform to it.
