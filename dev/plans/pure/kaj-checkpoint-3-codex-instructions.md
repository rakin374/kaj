# Kaj Checkpoint 3 — Minimal Parser

**Audience:** Codex / implementation agent  
**Repository:** Kaj  
**Checkpoint:** 3  
**Goal:** Parse Kaj token streams into the Core AST implemented in Checkpoint 2.

---

## 1. Primary Instruction

Implement **Checkpoint 3 only**.

Before changing code, read:

```text
docs/language/lexical-structure.md
docs/internals/ast.md
.dev/plans/pure-language-v0.md
```

Also inspect the completed Checkpoint 1 lexer and Checkpoint 2 AST implementation.

Treat:

```text
docs/language/lexical-structure.md
```

as authoritative for lexical behavior, and:

```text
docs/internals/ast.md
```

as authoritative for AST structure.

This checkpoint introduces the **parser** that converts tokens into AST nodes.

Do not implement:

- name resolution,
- type checking,
- execution,
- AST JSON,
- formatter,
- records,
- enums,
- match,
- newtypes,
- module/import semantics,
- capabilities,
- tasks,
- agent semantics,
- asset semantics.

---

# 2. Checkpoint Goal

The pipeline should become:

```text
Kaj source
    ↓
Lexer
    ↓
Token stream
    ↓
Parser
    ↓
AST
```

Example source:

```kaj
let x = 10
```

must produce an AST equivalent to:

```text
Program
└── BindingDeclaration
    ├── kind: LET
    ├── name: "x"
    ├── annotation: None
    └── initializer:
        IntegerLiteral(10)
```

Another example:

```kaj
let total = price * quantity + tax
```

must preserve precedence:

```text
BindingDeclaration
└── initializer:
    BinaryExpression(ADD)
    ├── BinaryExpression(MULTIPLY)
    │   ├── Identifier("price")
    │   └── Identifier("quantity")
    └── Identifier("tax")
```

---

# 3. Scope

Implement parsing for:

- programs,
- literals,
- identifiers,
- grouping,
- unary operators,
- binary operators,
- operator precedence,
- operator associativity,
- calls,
- named call arguments,
- member access,
- indexing,
- list literals,
- map literals,
- `let`,
- `var`,
- optional binding type annotations,
- assignments,
- compound assignments,
- expression statements,
- blocks,
- `if`,
- `else`,
- `else if`,
- `while`,
- `for`,
- `break`,
- `continue`,
- `return`,
- function declarations,
- typed parameters,
- mutable parameters,
- function return types,
- simple named types,
- generic type syntax,
- parser diagnostics,
- parser error recovery.

Do not implement semantic validity checks that belong to later passes.

---

# 4. Required Repository Structure

Add:

```text
src/kaj/
└── parser/
    ├── __init__.py
    └── parser.py
```

If separating diagnostics or precedence helpers materially improves readability, small supporting files are acceptable, but avoid unnecessary fragmentation.

Tests:

```text
tests/
└── parser/
    ├── test_literals.py
    ├── test_expressions.py
    ├── test_precedence.py
    ├── test_calls.py
    ├── test_collections.py
    ├── test_bindings.py
    ├── test_assignments.py
    ├── test_control_flow.py
    ├── test_functions.py
    ├── test_types.py
    ├── test_spans.py
    ├── test_diagnostics.py
    └── test_parser.py
```

Reuse existing AST, source span, token, and diagnostic types.

Do not duplicate them.

---

# 5. Parser API

Provide a small API conceptually equivalent to:

```python
lexer_result = Lexer(source, filename="example.kaj").tokenize()

parser = Parser(
    lexer_result.tokens,
    filename="example.kaj",
)

parser_result = parser.parse()
```

The result should provide:

```text
program
diagnostics
```

A suitable shape:

```python
@dataclass(frozen=True)
class ParserResult:
    program: Program
    diagnostics: tuple[Diagnostic, ...]
```

or an equivalent existing collection convention.

The parser must not require direct filesystem access.

---

# 6. Lexer Diagnostics

The parser must not reinterpret lexer failures.

If the higher-level frontend eventually combines lexer and parser diagnostics, keep that orchestration outside the parser itself unless the existing architecture already has a clean shared result model.

The parser consumes tokens.

Do not redesign Checkpoint 1 solely for parser convenience.

---

# 7. Parser Diagnostics

Introduce stable parser diagnostic codes.

At minimum support:

```text
PARSE_EXPECTED_EXPRESSION
PARSE_EXPECTED_IDENTIFIER
PARSE_EXPECTED_TOKEN
PARSE_EXPECTED_TYPE
PARSE_UNEXPECTED_TOKEN
PARSE_INVALID_ASSIGNMENT_TARGET
PARSE_POSITIONAL_AFTER_NAMED_ARGUMENT
```

If the implementation naturally benefits from more specific stable codes, that is acceptable.

Do not throw arbitrary user-visible Python exceptions for malformed Kaj source.

Each diagnostic must have an accurate `SourceSpan`.

Tests should assert codes and spans more strongly than exact prose.

---

# 8. Program Grammar

A source file parses as a sequence of statements/declarations followed by EOF.

Conceptually:

```text
program
    := statement* EOF
```

Return:

```text
Program(statements=(...))
```

The `Program` span should cover the full parsed source construct.

For empty source, use a zero-width span at EOF.

---

# 9. No Semicolon Requirement

Kaj statements do not require semicolons.

Because newlines are discarded by the lexer, statement boundaries must be determined grammatically.

This means the parser must know when a statement's grammar is complete without relying on newline tokens.

Do not add semicolon insertion.

Do not make newlines semantically significant.

---

# 10. Expression Parsing Strategy

Use a precedence-aware hand-written expression parser.

A Pratt parser or precedence-climbing parser is recommended.

Do not use an external parser generator.

The parser must correctly model precedence and associativity.

---

# 11. Expression Precedence

Use the following precedence from lowest to highest:

```text
1. or
2. and
3. == !=
4. < <= > >=
5. + -
6. * / %
7. unary: + - not
8. **
9. postfix: call, member access, indexing
10. primary
```

Important:

```text
**
```

is **right-associative**.

Therefore:

```kaj
2 ** 3 ** 2
```

must parse as:

```text
2 ** (3 ** 2)
```

not:

```text
(2 ** 3) ** 2
```

All ordinary binary operators other than power are left-associative.

---

# 12. Unary Minus and Power

Freeze the following parsing behavior:

```kaj
-2 ** 2
```

must parse as:

```text
-(2 ** 2)
```

not:

```text
(-2) ** 2
```

This is consistent with power binding more tightly than unary negation.

Grouping may override it:

```kaj
(-2) ** 2
```

must parse with the unary expression inside the grouped left operand.

Make tests explicit.

---

# 13. Primary Expressions

Parse:

```text
INTEGER
DECIMAL
STRING
TRUE
FALSE
NONE
IDENTIFIER
(...)
[...]
{...}
```

into the corresponding AST nodes.

---

# 14. Literal Expressions

Map lexer tokens to AST:

```text
INTEGER -> IntegerLiteral
DECIMAL -> DecimalLiteral
STRING  -> StringLiteral
TRUE    -> BooleanLiteral(True)
FALSE   -> BooleanLiteral(False)
NONE    -> NoneLiteral
```

Use lexer-decoded token values.

Do not reparse decimal strings through `float`.

---

# 15. Identifier Expressions

Parse:

```kaj
foo
```

as:

```text
Identifier(name="foo")
```

No name resolution occurs here.

---

# 16. Grouping

Parse:

```kaj
(1 + 2)
```

as the inner expression with a span behavior consistent with the AST design.

If there is no dedicated GroupingExpression node in the authoritative AST, do not invent one.

The parser may use parentheses only to control structure.

For:

```kaj
(1 + 2) * 3
```

the AST must preserve the intended grouping through tree structure.

---

# 17. Unary Operators

Support prefix:

```text
+
-
not
```

Map to the AST `UnaryOperator` enum.

Examples:

```kaj
-42
+value
not ready
```

Unary operators may nest:

```kaj
not not ready
```

---

# 18. Binary Operators

Support:

```text
+
-
*
/
%
**

==
!=
<
<=
>
>=

and
or
```

Map lexer token kinds to the AST `BinaryOperator` enum.

Do not store raw token kinds as AST operators.

---

# 19. Postfix Expressions

Postfix operations bind tighter than arithmetic/logical operators.

Support chaining.

Examples:

```kaj
foo()
user.name
items[0]
foo().bar[0](x)
```

This should parse left-to-right as a sequence of postfix operations applied to the preceding expression.

---

# 20. Call Expressions

Parse:

```kaj
add(1, 2)
```

into:

```text
CallExpression
├── callee: Identifier("add")
└── arguments:
    ├── CallArgument(name=None, value=IntegerLiteral(1))
    └── CallArgument(name=None, value=IntegerLiteral(2))
```

Calls may have zero arguments:

```kaj
run()
```

Trailing commas are **not required for Checkpoint 3**.

Do not add them unless already specified elsewhere.

---

# 21. Named Arguments

Support named arguments using:

```kaj
send(message, priority: 2)
```

Represent:

```text
CallArgument(
    name="priority",
    value=IntegerLiteral(2),
)
```

Positional arguments must come before named arguments.

Valid:

```kaj
send(message, priority: 2)
```

Invalid:

```kaj
send(priority: 2, message)
```

Emit:

```text
PARSE_POSITIONAL_AFTER_NAMED_ARGUMENT
```

Do not resolve whether the function actually has such a parameter yet.

---

# 22. Member Access

Parse:

```kaj
user.name
```

as:

```text
MemberAccessExpression
├── object: Identifier("user")
└── member: "name"
```

After a dot, require an identifier.

Support chaining:

```kaj
user.profile.name
```

---

# 23. Indexing

Parse:

```kaj
items[0]
```

as:

```text
IndexExpression
├── object: Identifier("items")
└── index: IntegerLiteral(0)
```

Require a closing `]`.

Support chained indexing/calls/member access.

---

# 24. List Literals

Parse:

```kaj
[]
[1]
[1, 2, 3]
```

as `ListLiteral`.

Do not check element type homogeneity.

No spread syntax.

No comprehensions.

---

# 25. Map Literals

Parse:

```kaj
{}
{"Alice": 30}
{"a": 1, "b": 2}
```

as `MapLiteral` with `MapEntry` children.

Map entry grammar:

```text
expression ":" expression
```

Do not check whether key expressions have legal map-key types yet.

Do not add shorthand property syntax.

---

# 26. Ambiguity Between Block and Map Literal

A `{` in expression position starts a map literal.

A `{` where a statement grammar requires a body starts a block.

Examples:

```kaj
let x = {"a": 1}
```

is a map literal.

```kaj
if ready {
    run()
}
```

contains a block.

The parser context resolves the distinction.

---

# 27. Binding Declarations

Parse:

```kaj
let x = 10
var y = 20
```

into `BindingDeclaration`.

Support optional explicit annotations:

```kaj
let x: Int = 10
var values: List<Int> = [1, 2, 3]
```

Grammar:

```text
binding
    := ("let" | "var")
       IDENTIFIER
       (":" type_expression)?
       "=" expression
```

Initializer is required in Checkpoint 3.

Do not allow:

```kaj
let x
var y: Int
```

unless the authoritative language docs are changed later.

---

# 28. Assignment Statements

Support:

```kaj
x = 1
x += 1
x -= 1
x *= 2
x /= 2
```

and structurally:

```kaj
user.name = "Alice"
items[0] = value
```

Assignment is a **statement**, not a general expression, in Kaj v0.

Do not make assignment expressions return values.

A valid assignment target must structurally be one of:

```text
Identifier
MemberAccessExpression
IndexExpression
```

If the parser sees:

```kaj
1 + 2 = 3
```

emit:

```text
PARSE_INVALID_ASSIGNMENT_TARGET
```

Do not defer this particular syntactic restriction to type checking.

---

# 29. Expression Statements

Expressions may appear as statements.

Examples:

```kaj
print("hello")
foo()
user.refresh()
```

Represent as `ExpressionStatement`.

The parser should first parse an expression and then determine whether an assignment operator follows.

If so, convert to `AssignmentStatement` after validating the target shape.

Otherwise, emit `ExpressionStatement`.

---

# 30. Blocks

Parse:

```kaj
{
    statement1
    statement2
}
```

into:

```text
Block(statements=(...))
```

A block begins with `{` and ends with `}`.

If EOF occurs before `}`, emit an appropriate expected-token diagnostic.

Do not create lexical scopes here; scope construction belongs to name resolution.

---

# 31. If Statements

Parse:

```kaj
if condition {
    ...
}
```

and:

```kaj
if condition {
    ...
} else {
    ...
}
```

and:

```kaj
if a {
    ...
} else if b {
    ...
} else {
    ...
}
```

Use the existing AST's `else_branch` representation.

Condition syntax does not use parentheses:

```kaj
if x > 10 {
    ...
}
```

Do not require:

```kaj
if (x > 10)
```

though parenthesized expressions remain valid as ordinary grouping:

```kaj
if (x > 10) {
    ...
}
```

---

# 32. While Statements

Parse:

```kaj
while condition {
    ...
}
```

into `WhileStatement`.

Do not validate that condition has type `Bool` yet.

---

# 33. For Statements

Parse only the initial simple form:

```kaj
for item in items {
    ...
}
```

Grammar:

```text
for_statement
    := "for" IDENTIFIER "in" expression block
```

Do not implement:

- destructuring patterns,
- ranges as special grammar,
- C-style loops.

Whether the iterable is iterable belongs to type checking.

---

# 34. Break and Continue

Parse:

```kaj
break
continue
```

into their AST nodes.

Do not check whether they appear inside a loop yet.

That belongs to semantic validation/name-control-flow analysis.

---

# 35. Return Statements

Parse:

```kaj
return
```

and:

```kaj
return expression
```

The AST supports `Expression | None`.

Because Kaj has no newline tokens or semicolons, bare `return` must only be recognized when the next token clearly closes the current statement context, such as:

```text
RIGHT_BRACE
EOF
```

Do not use source newlines for this decision.

Example:

```kaj
return x
```

must parse with value `x`.

Example:

```kaj
return
}
```

must parse as bare return.

This is one reason Kaj's no-semicolon grammar should remain explicit and conservative.

---

# 36. Function Declarations

Parse:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

Grammar:

```text
function_declaration
    := "fn"
       IDENTIFIER
       "(" parameter_list? ")"
       "->"
       type_expression
       block
```

Function return type is required.

Do not infer it in Checkpoint 3.

---

# 37. Parameters

Parse ordinary parameters:

```kaj
a: Int
b: String
```

and mutable local parameters:

```kaj
var value: Decimal
```

Grammar:

```text
parameter
    := "var"? IDENTIFIER ":" type_expression
```

The absence of `var` means immutable parameter binding.

Do not support `let` before parameters.

Do not implement pass-by-reference or `inout`.

---

# 38. Parameter Lists

Parse:

```kaj
fn f() -> None {}
fn f(x: Int) -> Int {}
fn f(x: Int, y: String) -> None {}
```

Do not implement default parameter values yet.

Do not implement variadic parameters.

Do not implement generic function declarations.

---

# 39. Type Expressions

Parse `NamedType`:

```kaj
Int
String
User
```

and `GenericType`:

```kaj
List<Int>
Map<String, Int>
Optional<User>
Result<Value, Error>
Map<String, List<Int>>
```

Grammar conceptually:

```text
type_expression
    := IDENTIFIER
       ("<" type_expression ("," type_expression)* ">")?
```

Important: `<` and `>` tokens are also comparison operators in expression parsing.

In type-expression context, interpret them as generic delimiters.

The lexer does not need separate generic-angle tokens.

---

# 40. Type Parsing Scope

Type expressions are syntax only.

Do not validate:

- whether a named type exists,
- generic arity,
- whether `Map` accepts two type parameters,
- whether recursive forms are valid semantically.

That belongs to later type analysis.

---

# 41. Statements Recognized by Leading Keyword

At statement position:

```text
LET       -> binding declaration
VAR       -> binding declaration
FN        -> function declaration
IF        -> if statement
WHILE     -> while statement
FOR       -> for statement
BREAK     -> break statement
CONTINUE  -> continue statement
RETURN    -> return statement
```

Everything else begins as an expression statement or assignment statement.

Do not parse `TYPE`, `ENUM`, `NEWTYPE`, `MATCH`, or `IMPORT` yet.

If encountered, produce a parser diagnostic rather than inventing incomplete behavior.

---

# 42. Deferred Keyword Constructs

The lexer already recognizes some future pure-language keywords:

```text
type
enum
newtype
match
import
```

Checkpoint 3 does **not** parse these constructs yet.

Encountering them at statement position should produce a clear unsupported/unexpected parser diagnostic.

Do not remove them from the lexer.

They are reserved for their later checkpoints.

---

# 43. Source Spans

Every parser-created AST node must have a correct `SourceSpan`.

General rule:

```text
node span = from first token/child belonging to construct
            through end of final token/child
```

Examples:

```kaj
1 + 2
```

Binary expression span covers `1 + 2`.

```kaj
let x = 10
```

Binding span covers from `let` through `10`.

```kaj
if ready {
    run()
}
```

If statement span covers from `if` through the closing `}`.

```kaj
foo(1, 2)
```

Call span covers from `foo` through `)`.

Use the existing half-open span convention.

Do not invent inclusive end spans.

---

# 44. Comments and Whitespace

The parser never sees comments or whitespace because the lexer skips them.

Do not add parser logic for comments/newlines.

Do not attempt formatting preservation here.

---

# 45. Error Recovery

The parser should report multiple syntax errors where practical.

Implement statement-level synchronization.

A reasonable recovery strategy is to advance until reaching:

```text
LET
VAR
FN
IF
WHILE
FOR
BREAK
CONTINUE
RETURN
RIGHT_BRACE
EOF
```

or another clear statement boundary.

Because Kaj has no newline tokens or semicolons, recovery must be conservative.

The parser must always make progress after an error.

Never infinite-loop on malformed input.

---

# 46. Missing Tokens

For malformed constructs such as:

```kaj
fn add(a: Int -> Int {
```

emit an expected-token diagnostic.

Do not crash with `IndexError`, `AssertionError`, or similar internal failures.

Malformed source is normal compiler input.

---

# 47. Parser Helpers

A hand-written parser may use helpers conceptually like:

```text
current
previous
peek
advance
check
match
consume
error
synchronize
parse_statement
parse_expression
parse_precedence
parse_primary
parse_postfix
parse_type_expression
parse_block
```

Names are not mandatory.

Keep state management centralized and understandable.

---

# 48. No Semantic Checks

Do not reject these during parsing solely because they are semantically invalid:

```kaj
break
continue
return 1
x = "hello"
1 + true
foo(unknown: 1)
```

unless the syntax itself is invalid.

Later compiler passes handle:

- scope,
- symbol existence,
- type compatibility,
- return legality,
- loop-context legality,
- function call argument matching.

The parser's job is structural syntax.

---

# 49. One Important Syntactic Check

Assignment targets are syntactically restricted.

Valid:

```text
Identifier
MemberAccessExpression
IndexExpression
```

Invalid:

```kaj
1 = 2
(a + b) = c
foo() = x
```

These should produce:

```text
PARSE_INVALID_ASSIGNMENT_TARGET
```

This belongs in the parser because it is part of the assignment grammar shape.

---

# 50. No User-Defined Operator Overloading

Do not add syntax for:

- custom operators,
- operator declarations,
- precedence declarations.

Operator grammar is fixed for Kaj v0.

---

# 51. Required Precedence Tests

Explicitly test:

```kaj
1 + 2 * 3
```

as:

```text
1 + (2 * 3)
```

Test:

```kaj
1 * 2 + 3
```

as:

```text
(1 * 2) + 3
```

Test:

```kaj
a or b and c
```

as:

```text
a or (b and c)
```

Test:

```kaj
a == b < c
```

according to the frozen precedence table:

```text
a == (b < c)
```

The later type checker may reject nonsensical chained forms.

Test:

```kaj
2 ** 3 ** 2
```

as right-associative:

```text
2 ** (3 ** 2)
```

Test:

```kaj
-2 ** 2
```

as:

```text
-(2 ** 2)
```

Test:

```kaj
(-2) ** 2
```

with negation grouped on the left.

---

# 52. Required Postfix Tests

Test:

```kaj
foo()
foo(1, 2)
foo(a: 1)
user.name
items[0]
foo().bar[0](x)
```

Ensure chaining builds the correct nested AST.

---

# 53. Required Collection Tests

Test:

```kaj
[]
[1]
[1, 2, 3]

{}
{"a": 1}
{"a": 1, "b": 2}
```

Do not check list homogeneity or map key types.

---

# 54. Required Binding Tests

Test:

```kaj
let x = 10
var y = 20
let x: Int = 10
var items: List<Int> = [1, 2]
```

Also test malformed forms:

```kaj
let = 10
let x
let x: = 10
```

with appropriate parser diagnostics.

---

# 55. Required Assignment Tests

Test:

```kaj
x = 1
x += 1
x -= 1
x *= 2
x /= 2
user.name = "Alice"
items[0] = value
```

Invalid:

```kaj
1 = 2
foo() = 3
(a + b) = c
```

must emit `PARSE_INVALID_ASSIGNMENT_TARGET`.

---

# 56. Required Control Flow Tests

Test:

```kaj
if ready {
    run()
}
```

```kaj
if ready {
    run()
} else {
    wait()
}
```

```kaj
if a {
    one()
} else if b {
    two()
} else {
    three()
}
```

```kaj
while ready {
    run()
}
```

```kaj
for item in items {
    print(item)
}
```

```kaj
break
continue
```

Do not semantically reject standalone break/continue yet.

---

# 57. Required Function Tests

Test:

```kaj
fn noop() -> None {
    return
}
```

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

```kaj
fn normalize(var value: Decimal) -> Decimal {
    return value
}
```

Test nested generic parameter/return types where the AST supports them.

Malformed cases should report diagnostics, not crash.

---

# 58. Required Type Tests

Test parsing:

```text
Int
User
List<Int>
Map<String, Int>
Optional<User>
Result<Value, Error>
Map<String, List<Int>>
```

Do not test semantic resolution.

---

# 59. Required Diagnostic Tests

Include malformed sources for:

```text
missing identifier
missing expression
missing closing parenthesis
missing closing bracket
missing closing brace
missing colon in parameter
missing return arrow
missing return type
unexpected token
invalid assignment target
positional argument after named argument
unsupported reserved construct such as `type`
```

Assert:

- stable diagnostic code,
- useful span,
- parser continues where practical.

---

# 60. Required Recovery Test

Use one source containing multiple errors, for example conceptually:

```kaj
let = 10
let y = 20

fn add(a Int) -> Int {
    return a
}

let z = @
```

Note that `@` is a lexer error; parser recovery should still behave predictably with the tokens it receives.

The overall compiler orchestration may eventually combine both lexer and parser diagnostics.

Do not make parser error recovery depend on raw source text.

---

# 61. AST Equality Tests

Use direct AST comparisons where practical.

The AST was deliberately designed as structural immutable data.

Do not write tests that only compare pretty-printed strings.

---

# 62. No AST JSON

Do not serialize parser output to JSON in this checkpoint.

Do not add:

```text
to_json()
from_json()
schema generation
Pydantic serialization models
.kaj.json fixtures
```

Checkpoint 4 owns that work.

---

# 63. No Interpreter

Do not evaluate AST nodes.

This checkpoint ends after AST construction.

There should be no:

```text
eval()
execute()
run_program()
```

behavior added to AST or parser packages.

---

# 64. No Name Resolution

The parser may happily create:

```kaj
foo(bar)
```

without knowing what `foo` or `bar` refer to.

Do not create symbol tables.

Checkpoint 5 handles scope/name resolution.

---

# 65. CLI

Do not redesign the CLI.

If there is already an appropriate internal debug hook, it may be used in tests, but do not add the final:

```bash
kaj ast
```

command yet unless the active project plan explicitly assigns it to this checkpoint.

AST JSON and user-facing AST output belong later.

Preserve:

```bash
kaj --version
python -m kaj
```

behavior.

---

# 66. Update Development Plan

Update:

```text
.dev/plans/pure-language-v0.md
```

to record:

```text
Current checkpoint:
Checkpoint 3 — Minimal Parser

Status:
...

Completed:
...

Decisions:
...

Known issues:
...

Verification:
...
```

Do not treat `.dev` as authoritative language documentation.

If parser implementation forces a new public syntax decision, update the relevant authoritative language documentation rather than hiding it in the plan.

---

# 67. Suggested Implementation Order

Use this order unless repository structure makes a small variation clearly better.

### Step 1 — Inspect existing implementation

Read:

```text
docs/language/lexical-structure.md
docs/internals/ast.md
.dev/plans/pure-language-v0.md
src/kaj/lexer/
src/kaj/ast/
tests/lexer/
tests/ast/
```

### Step 2 — Parser result and cursor

Implement parser state, token navigation, result model, diagnostics, and EOF handling.

### Step 3 — Primary expressions

Implement literals, identifiers, grouping, list literals, map literals.

### Step 4 — Postfix expressions

Implement calls, named arguments, member access, indexing, chaining.

### Step 5 — Unary and binary precedence

Implement the full precedence table, right-associative power, and the frozen `-2 ** 2` behavior.

### Step 6 — Type expressions

Implement named and nested generic types.

### Step 7 — Bindings and expression/assignment statements

Implement `let`, `var`, annotations, assignment operators, assignment-target validation.

### Step 8 — Blocks

Implement `{ ... }`.

### Step 9 — Control flow

Implement `if`, `else`, `else if`, `while`, `for`, `break`, `continue`.

### Step 10 — Return

Implement value and bare-return forms.

### Step 11 — Functions

Implement declarations, parameters, `var` parameters, return types.

### Step 12 — Recovery

Implement statement-level synchronization and ensure malformed input cannot stall.

### Step 13 — Tests

Complete all parser test categories.

### Step 14 — Quality gates

Run all tests and tooling.

### Step 15 — Update `.dev` plan

Record completion and decisions.

Do not start Checkpoint 4.

---

# 68. Verification Commands

Run:

```bash
pytest
ruff check .
mypy src
kaj --version
python -m kaj
```

All prior tests must remain passing:

```text
Checkpoint 0 bootstrap
Checkpoint 1 source/lexer
Checkpoint 2 AST
Checkpoint 3 parser
```

---

# 69. Definition of Done

Checkpoint 3 is complete only when:

```text
[ ] authoritative lexer and AST docs were read and followed

[ ] parser package exists
[ ] Parser API implemented
[ ] ParserResult or equivalent implemented
[ ] parser diagnostics implemented

[ ] Program parsing implemented

[ ] integer literals parsed
[ ] decimal literals parsed
[ ] string literals parsed
[ ] bool literals parsed
[ ] none literal parsed
[ ] identifiers parsed
[ ] grouping parsed

[ ] unary + parsed
[ ] unary - parsed
[ ] not parsed

[ ] binary arithmetic parsed
[ ] comparisons parsed
[ ] equality parsed
[ ] and/or parsed
[ ] precedence correct
[ ] ordinary binary associativity correct
[ ] power right-associative
[ ] -2 ** 2 behavior correct

[ ] calls parsed
[ ] zero-argument calls parsed
[ ] positional arguments parsed
[ ] named arguments parsed
[ ] positional-after-named diagnosed
[ ] member access parsed
[ ] indexing parsed
[ ] postfix chaining parsed

[ ] list literals parsed
[ ] map literals parsed

[ ] NamedType parsed
[ ] GenericType parsed
[ ] nested generic types parsed

[ ] let bindings parsed
[ ] var bindings parsed
[ ] optional type annotations parsed
[ ] initializer required

[ ] assignment parsed
[ ] compound assignment parsed
[ ] assignment-target shape validated
[ ] expression statements parsed

[ ] blocks parsed
[ ] if parsed
[ ] else parsed
[ ] else-if parsed
[ ] while parsed
[ ] for-in parsed
[ ] break parsed
[ ] continue parsed
[ ] return value parsed
[ ] bare return parsed

[ ] function declarations parsed
[ ] typed parameters parsed
[ ] var parameters parsed
[ ] explicit return types parsed

[ ] all created AST nodes carry correct spans
[ ] malformed source produces structured parser diagnostics
[ ] parser recovery implemented
[ ] parser cannot infinite-loop on malformed input

[ ] parser tests added
[ ] precedence tests added
[ ] diagnostic tests added
[ ] recovery tests added

[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] bootstrap CLI still works
[ ] lexer tests still pass
[ ] AST tests still pass

[ ] no name resolution added
[ ] no type checking added
[ ] no interpreter added
[ ] no AST JSON added
[ ] no formatter added
[ ] no records/enums/match/newtypes/import semantics added
[ ] no agent/capability/asset features added

[ ] .dev/plans/pure-language-v0.md updated
```

---

# 70. Completion Report

When finished, report:

```text
Checkpoint 3 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

Grammar implemented:
- ...

Parser diagnostics:
- ...

Tests added:
- ...

Verification:
- pytest: PASS/FAIL
- ruff check .: PASS/FAIL
- mypy src: PASS/FAIL
- Kaj bootstrap CLI: PASS/FAIL

Precedence behavior:
- power right-associative: PASS/FAIL
- unary minus vs power: PASS/FAIL
- postfix precedence: PASS/FAIL

Decisions/deviations:
- ...

Known issues:
- ...
```

If any required behavior remains incomplete, say so explicitly.

---

# 71. Final Constraint

Do **not** proceed to Checkpoint 4.

Checkpoint 3 ends with:

```text
Kaj source
    ↓
Lexer
    ↓
Tokens
    ↓
Parser
    ↓
Core AST
```

The next checkpoint will add the machine-facing AST JSON representation and round-trip support separately.
