# Kaj Checkpoint 2 — Core AST Implementation Instructions

**Audience:** Codex / implementation agent  
**Checkpoint:** 2  
**Goal:** Implement Kaj's internal pure-language AST data model.

## Primary instruction

Implement Checkpoint 2 only.

Read and follow:

```text
docs/internals/ast.md
```

as the authoritative AST architecture document.

Also read:

```text
docs/language/lexical-structure.md
.dev/plans/pure-language-v0.md
```

and inspect the completed Checkpoint 1 implementation before editing code.

Do not implement the parser. Do not implement AST JSON.

## Objective

Create typed immutable AST data structures that the parser can construct in Checkpoint 3.

The pipeline after this checkpoint is:

```text
source
  ↓
lexer                 IMPLEMENTED
  ↓
tokens
  ↓
parser                NOT YET IMPLEMENTED
  ↓
AST                   DATA MODEL IMPLEMENTED HERE
```

Checkpoint 2 is successful when AST nodes can be manually constructed and tested, but source text is still not parsed into them.

## Files

Create:

```text
src/kaj/ast/
├── __init__.py
├── base.py
├── expressions.py
├── statements.py
└── declarations.py
```

If a separate `types.py` or `type_expressions.py` makes the implementation materially cleaner, it is acceptable:

```text
src/kaj/ast/type_expressions.py
```

Do not create unnecessary one-class-per-file structures.

Create tests:

```text
tests/ast/
├── test_literals.py
├── test_expressions.py
├── test_types.py
├── test_statements.py
├── test_functions.py
└── test_spans.py
```

## Required implementation

Implement the node inventory specified in `docs/internals/ast.md`, including:

```text
Node
Program

Expression
IntegerLiteral
DecimalLiteral
StringLiteral
BooleanLiteral
NoneLiteral
Identifier
UnaryExpression
BinaryExpression
CallArgument
CallExpression
MemberAccessExpression
IndexExpression
ListLiteral
MapEntry
MapLiteral

TypeExpression
NamedType
GenericType

Statement
Block
BindingDeclaration
AssignmentStatement
ExpressionStatement
IfStatement
WhileStatement
ForStatement
BreakStatement
ContinueStatement
ReturnStatement
Parameter
FunctionDeclaration

BindingKind or Mutability
UnaryOperator
BinaryOperator
AssignmentOperator
```

## AST rules

Use these rules:

- all concrete source-derived nodes expose `span: SourceSpan`
- spans come from the existing Checkpoint 1 source model
- nodes are immutable value objects where practical
- use typed fields
- use tuples for ordered child collections where practical
- AST nodes contain syntax data only
- no runtime/evaluation methods
- no name resolution
- no type checking
- no parser code
- no JSON serialization
- no agent/capability/asset semantics

## Literal values

Use:

```text
IntegerLiteral.value -> int
DecimalLiteral.value -> decimal.Decimal
StringLiteral.value -> str
BooleanLiteral.value -> bool
NoneLiteral -> no value payload
```

Do not represent `-42` as `IntegerLiteral(-42)` in normal source structure. Represent it as:

```text
UnaryExpression(
    operator=NEGATE,
    operand=IntegerLiteral(42)
)
```

The lexer already separates `-` from the number.

## Operator enums

Use dedicated enums rather than strings or `TokenKind`.

Provide semantic operator categories capable of representing:

Unary:

```text
POSITIVE
NEGATE
NOT
```

Binary:

```text
ADD
SUBTRACT
MULTIPLY
DIVIDE
MODULO
POWER

EQUAL
NOT_EQUAL
LESS
LESS_EQUAL
GREATER
GREATER_EQUAL

AND
OR
```

Assignment:

```text
ASSIGN
ADD_ASSIGN
SUBTRACT_ASSIGN
MULTIPLY_ASSIGN
DIVIDE_ASSIGN
```

Names can vary slightly if they remain clear and consistent, but do not use lexer token kinds as the AST's operator representation.

## Types

Implement syntactic type expressions:

```text
NamedType
GenericType
```

Must represent:

```kaj
Int
User
List<Int>
Optional<String>
Map<String, Int>
Result<Value, Error>
Map<String, List<Int>>
```

Do not resolve whether these names exist or whether generic arity is valid.

## Bindings

Use a single binding declaration representation with explicit mutability.

Must represent:

```kaj
let x = 10
var y = 20
```

and future typed forms such as:

```kaj
let x: Int = 10
```

Required conceptual fields:

```text
name
kind/mutability
annotation: TypeExpression | None
initializer: Expression
span
```

Do not create unrelated `LetDeclaration` and `VarDeclaration` classes unless the existing architecture gives a compelling reason.

## Parameters

A parameter must preserve:

```text
name
type annotation
local mutability
span
```

This must support:

```kaj
fn normalize(var value: Decimal) -> Decimal
```

`var` means local rebinding only. Do not introduce reference/inout semantics.

## Function declarations

Represent:

```text
name
parameters
return type
body
span
```

Do not add capability/effect fields yet.

## Calls

Represent the callee as an expression.

Represent arguments with a `CallArgument` object carrying:

```text
name: str | None
value: Expression
```

This allows positional and named arguments without redesigning the call AST later.

Do not enforce positional-before-named ordering in the AST. That belongs to parsing/semantic validation.

## Assignment

Represent assignment targets as expressions.

This preserves future support for:

```kaj
x = 1
user.name = "A"
items[0] = value
```

Whether the target is assignable is not checked in this checkpoint.

## Tests

Write direct construction tests.

At minimum verify:

1. literal nodes preserve exact values and spans
2. `Decimal` is used for decimal values
3. identifiers preserve names
4. unary/binary nodes use operator enums
5. negative values can be represented with unary negation
6. call arguments represent positional and named forms
7. list/map nodes preserve ordered children
8. `NamedType` and nested `GenericType` work
9. bindings preserve LET/VAR distinction
10. typed and untyped bindings are representable
11. assignment operators are represented
12. if/while/for nodes can be constructed
13. break/continue/return nodes can be constructed
14. function parameters preserve mutability
15. function declarations preserve parameter/return/body structure
16. AST nodes preserve source spans
17. frozen dataclasses reject mutation where applicable
18. structural equality behaves predictably

## Do not test parsing

Tests should manually instantiate AST nodes.

Do **not** write tests such as:

```python
parse("let x = 10")
```

because parsing belongs to Checkpoint 3.

Checkpoint 2 tests should look conceptually like:

```python
node = IntegerLiteral(
    span=span,
    value=10,
)

assert node.value == 10
assert node.span == span
```

## Package exports

Expose the intended AST public compiler API through:

```text
kaj.ast
```

where useful.

Avoid exporting implementation-only helpers.

Watch for circular imports between base, expression, statement, declaration, and type-expression modules. Use a clean dependency direction and `TYPE_CHECKING` only if genuinely needed.

## Existing code

Do not regress Checkpoint 1.

Run all lexer/source tests after AST work.

Do not rewrite lexer structures just to accommodate the AST unless a genuine bug is found.

If a Checkpoint 1 behavior change is required, update its authoritative spec and tests rather than silently changing it.

## Active plan

Update:

```text
.dev/plans/pure-language-v0.md
```

Set the current checkpoint to:

```text
Checkpoint 2 — Core AST
```

Record:

- completed work
- implementation decisions
- known issues
- verification commands/results

## Verification

Run:

```bash
pytest
ruff check .
mypy src
kaj --version
python -m kaj
```

All existing Checkpoint 0 and Checkpoint 1 tests must remain passing.

## Explicitly deferred

Do not implement:

```text
parser
Pratt parser / precedence parsing
AST JSON
JSON Schema
Pydantic AST models solely for serialization
name resolution
symbol tables
type checking
runtime/interpreter
formatter
records
enums
pattern matching
Optional/Result semantic lowering
newtypes
module resolution
capabilities
tasks
effects
agent semantics
asset semantics
AST patches
IR
```

If a richer node is genuinely required by the authoritative AST spec, implement only that representation—not its semantics.

## Definition of done

Checkpoint 2 is complete when:

```text
[ ] docs/internals/ast.md treated as authoritative
[ ] AST package exists

[ ] Node implemented
[ ] Program implemented

[ ] Expression category implemented
[ ] literal nodes implemented
[ ] Identifier implemented
[ ] UnaryExpression implemented
[ ] BinaryExpression implemented
[ ] CallArgument / CallExpression implemented
[ ] member access implemented
[ ] index expression implemented
[ ] list literal implemented
[ ] map literal / entries implemented

[ ] TypeExpression implemented
[ ] NamedType implemented
[ ] GenericType implemented

[ ] Statement category implemented
[ ] Block implemented
[ ] BindingDeclaration implemented
[ ] AssignmentStatement implemented
[ ] ExpressionStatement implemented
[ ] IfStatement implemented
[ ] WhileStatement implemented
[ ] ForStatement implemented
[ ] BreakStatement implemented
[ ] ContinueStatement implemented
[ ] ReturnStatement implemented
[ ] Parameter implemented
[ ] FunctionDeclaration implemented

[ ] operator enums implemented
[ ] binding mutability explicit
[ ] parameter mutability explicit

[ ] all nodes carry SourceSpan where specified
[ ] nodes immutable where practical
[ ] child sequences immutable where practical

[ ] AST construction tests added
[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] CLI bootstrap still passes
[ ] lexer/source tests still pass

[ ] no parser added
[ ] no AST JSON added
[ ] no semantic analysis added
[ ] no runtime added
[ ] no agent/capability/asset nodes added

[ ] .dev/plans/pure-language-v0.md updated
```

## Completion report

When finished, report:

```text
Checkpoint 2 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

AST nodes implemented:
- ...

Enums implemented:
- ...

Tests added:
- ...

Verification:
- pytest: PASS/FAIL
- ruff check .: PASS/FAIL
- mypy src: PASS/FAIL
- CLI: PASS/FAIL

Decisions/deviations:
- ...

Known issues:
- ...
```

Do not proceed to Checkpoint 3.
