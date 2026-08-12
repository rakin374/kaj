# Kaj Core AST

**Status:** Authoritative for Kaj v0 Checkpoint 2  
**Scope:** Internal compiler Abstract Syntax Tree  
**Not covered:** parsing, type checking, execution, AST JSON serialization

## 1. Purpose

The Kaj Abstract Syntax Tree (AST) is the compiler's structured representation of Kaj source code.

```text
Kaj source
    ↓
Lexer
    ↓
Tokens
    ↓
Parser       ← Checkpoint 3
    ↓
AST          ← structure defined here
```

Checkpoint 2 defines the AST data model only. It does not parse source into AST nodes.

The AST should represent source structure clearly and preserve source spans for diagnostics and future formatting/tooling.

## 2. Design Principles

The Kaj v0 AST follows these rules:

1. AST nodes are explicit typed data structures.
2. Every source-derived AST node carries a `SourceSpan`.
3. AST nodes represent syntax, not evaluated runtime values.
4. AST nodes do not perform name resolution or type checking.
5. AST nodes do not contain runtime state.
6. AST nodes should be immutable value objects where practical.
7. The AST should be easy to traverse and serialize later.
8. Do not encode parser implementation details into the AST.
9. Do not add agent, capability, task, asset, or effect nodes yet.
10. Do not design AST JSON serialization in this checkpoint.

## 3. Package Location

Implement under:

```text
src/kaj/ast/
├── __init__.py
├── base.py
├── expressions.py
├── statements.py
└── declarations.py
```

Small variations are acceptable if they improve clarity without introducing unnecessary abstraction.

## 4. Base Node

All AST nodes must have a source span.

Conceptually:

```python
@dataclass(frozen=True)
class Node:
    span: SourceSpan
```

It is acceptable for `Node` to be a protocol/base class rather than an instantiated node, but all concrete source-derived nodes must expose:

```text
span: SourceSpan
```

## 5. Program

The root of a Kaj source unit is:

```text
Program
```

Conceptually:

```python
@dataclass(frozen=True)
class Program(Node):
    statements: tuple[Statement, ...]
```

For Checkpoint 2, top-level declarations and statements may share the program body collection.

Later module semantics may refine this.

## 6. Expression and Statement Categories

Define distinct base categories:

```text
Expression
Statement
```

Declarations may either subclass `Statement` or use a declaration subtype that is accepted wherever top-level/block statements are valid.

For v0, keeping declarations within the statement hierarchy is preferred for simplicity.

Conceptually:

```text
Node
├── Expression
└── Statement
```

## 7. Literal Expressions

Define:

```text
IntegerLiteral
DecimalLiteral
StringLiteral
BooleanLiteral
NoneLiteral
```

Conceptual fields:

```python
IntegerLiteral:
    value: int

DecimalLiteral:
    value: Decimal

StringLiteral:
    value: str

BooleanLiteral:
    value: bool

NoneLiteral:
    no semantic payload beyond span
```

Numeric and string values should use the decoded token values produced by the lexer.

Do not store negative numeric literals directly. `-42` is a unary expression.

## 8. Identifier Expression

Define:

```text
Identifier
```

Conceptually:

```python
@dataclass(frozen=True)
class Identifier(Expression):
    name: str
```

The AST does not resolve what the identifier refers to. Resolution happens later.

## 9. Unary Expression

Define:

```text
UnaryExpression
```

Fields:

```text
operator
operand
span
```

Supported operator semantics will later include:

```text
-
+
not
```

Use a dedicated enum for unary operators rather than raw strings.

Example source:

```kaj
-42
```

AST:

```text
UnaryExpression
├── operator: NEGATE
└── operand:
    IntegerLiteral(42)
```

## 10. Binary Expression

Define:

```text
BinaryExpression
```

Fields:

```text
left
operator
right
span
```

Use a dedicated `BinaryOperator` enum.

The enum should be capable of representing the pure-core operators already established:

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

Do not put precedence information into each AST node. Precedence is a parser rule.

## 11. Call Expression

Define:

```text
CallExpression
```

Fields:

```text
callee
arguments
span
```

For Checkpoint 2, positional arguments are sufficient in the core node.

However, because Kaj intends to support named arguments, model call arguments in a way that can be extended cleanly without redesigning the entire call node.

A reasonable representation is:

```text
CallArgument
├── name: str | None
└── value: Expression
```

Then:

```text
CallExpression
├── callee: Expression
└── arguments: tuple[CallArgument, ...]
```

This supports both:

```kaj
add(1, 2)
```

and future/current parser support for:

```kaj
send(message, priority: 2)
```

without separate call node types.

## 12. Member Access

Define:

```text
MemberAccessExpression
```

Fields:

```text
object
member
span
```

Example:

```kaj
user.name
```

Conceptually:

```text
MemberAccessExpression
├── object: Identifier("user")
└── member: "name"
```

Do not resolve the member in Checkpoint 2.

## 13. Index Expression

Define:

```text
IndexExpression
```

Fields:

```text
object
index
span
```

Example:

```kaj
items[0]
```

No bounds/type behavior belongs in the AST.

## 14. List Literal

Define:

```text
ListLiteral
```

Fields:

```text
elements: tuple[Expression, ...]
```

Example:

```kaj
[1, 2, 3]
```

No homogeneity/type checking belongs in this checkpoint.

## 15. Map Literal

Define:

```text
MapLiteral
MapEntry
```

Conceptually:

```text
MapEntry
├── key: Expression
└── value: Expression

MapLiteral
└── entries: tuple[MapEntry, ...]
```

Example:

```kaj
{"Alice": 30}
```

Whether a key type is valid belongs to type checking.

## 16. Block

Define:

```text
Block
```

A block contains ordered statements:

```python
@dataclass(frozen=True)
class Block(Node):
    statements: tuple[Statement, ...]
```

Blocks carry their own span, including their source braces when created by the parser.

## 17. Binding Declarations

Kaj has:

```kaj
let x = 10
var y = 20
```

Represent this with one binding declaration node plus mutability information.

Preferred:

```text
BindingDeclaration
├── name
├── mutability
├── annotation
├── initializer
└── span
```

Define a `BindingKind` or `Mutability` enum:

```text
LET
VAR
```

Suggested fields:

```text
name: str
kind: BindingKind
annotation: TypeExpression | None
initializer: Expression
```

The initializer is required for the initial v0 binding form unless a later language specification says otherwise.

Do not represent `let` and `var` using unrelated AST node classes unless there is a strong implementation reason.

## 18. Type References

Checkpoint 2 needs a minimal syntactic representation of type annotations because functions and bindings may contain types before type checking exists.

Define:

```text
TypeExpression
```

and initially:

```text
NamedType
```

Conceptually:

```python
@dataclass(frozen=True)
class NamedType(TypeExpression):
    name: str
```

Examples:

```kaj
Int
String
User
```

Also provide a generic/application form now because core types such as:

```kaj
List<Int>
Map<String, Int>
Optional<User>
Result<Value, Error>
```

need syntax representation later.

Define:

```text
GenericType
├── base: NamedType
└── arguments: tuple[TypeExpression, ...]
```

This is syntax only. It does not validate that `List` exists or accepts one parameter.

## 19. Assignment Statement

Define:

```text
AssignmentStatement
```

Fields:

```text
target
operator
value
span
```

The target should be an expression because future valid assignment targets can include:

```kaj
x
user.name
items[0]
```

Use an `AssignmentOperator` enum capable of representing:

```text
=
+=
-=
*=
/=
```

Whether a target is assignable is semantic analysis, not AST construction.

## 20. Expression Statement

Define:

```text
ExpressionStatement
```

Fields:

```text
expression
span
```

Example:

```kaj
print("hello")
```

## 21. If Statement

Define:

```text
IfStatement
```

Fields:

```text
condition
then_branch
else_branch
span
```

Preferred:

```text
condition: Expression
then_branch: Block
else_branch: Block | IfStatement | None
```

This allows normal `else` and `else if` structure without inventing another representation.

## 22. While Statement

Define:

```text
WhileStatement
```

Fields:

```text
condition
body
span
```

## 23. For Statement

Define:

```text
ForStatement
```

For initial Kaj:

```kaj
for item in items {
    ...
}
```

Fields:

```text
name: str
iterable: Expression
body: Block
span
```

Destructuring loop patterns are deferred.

## 24. Break and Continue

Define:

```text
BreakStatement
ContinueStatement
```

No additional payload is required beyond span in v0.

Whether these occur inside a valid loop is semantic validation.

## 25. Return Statement

Define:

```text
ReturnStatement
```

Fields:

```text
value: Expression | None
span
```

This supports both:

```kaj
return value
```

and potential:

```kaj
return
```

for `None`-returning functions.

Whether bare return is legal is checked later.

## 26. Function Parameters

Define:

```text
Parameter
```

Fields should represent the already-decided semantics:

```text
name
type_annotation
mutable
span
```

Example:

```kaj
fn normalize(var value: Decimal) -> Decimal
```

The parameter AST must be able to preserve that `value` is locally mutable.

Preferred field:

```text
mutable: bool
```

or a small enum if it improves consistency.

Do not model pass-by-reference or `inout`; Kaj does not have that semantics here.

## 27. Function Declaration

Define:

```text
FunctionDeclaration
```

Fields:

```text
name
parameters
return_type
body
span
```

Conceptually:

```python
FunctionDeclaration:
    name: str
    parameters: tuple[Parameter, ...]
    return_type: TypeExpression
    body: Block
```

Parameter and return types are explicit in Kaj v0 function declarations.

Do not add effects/capabilities to function nodes yet.

## 28. Deferred Declaration Nodes

Do not implement record, enum, match, newtype, or import AST nodes in Checkpoint 2 unless required by the existing Checkpoint 2 plan.

The minimal parser checkpoint is intended to start with core expressions/statements/functions.

These richer constructs will be added in their dedicated checkpoints.

If the active implementation plan explicitly requires a broader AST now, keep the design modular, but do not silently expand scope.

## 29. Operators as Enums

Do not represent operators internally as arbitrary strings.

Define enums such as:

```text
UnaryOperator
BinaryOperator
AssignmentOperator
```

Example conceptual mapping:

```text
TokenKind.PLUS  -> BinaryOperator.ADD
TokenKind.MINUS -> BinaryOperator.SUBTRACT
```

The parser will perform this mapping in Checkpoint 3.

The AST should describe semantic syntax categories rather than retain lexer token kinds as its primary operator representation.

## 30. Source Spans

Every concrete source-derived AST node must contain a span.

For compound nodes, the parser will later create spans covering the full construct.

Examples:

```kaj
1 + 2
```

The binary expression span should eventually cover from `1` through `2`.

```kaj
fn add(...) -> Int { ... }
```

The function declaration span should eventually cover the complete declaration.

Checkpoint 2 only defines the field; Checkpoint 3 will populate spans.

## 31. Immutability

Prefer:

```python
@dataclass(frozen=True)
```

for AST value objects.

AST mutation is not needed in the pure initial compiler.

Future AST patching for agent workflows must not drive the internal v0 AST design yet.

## 32. Collections

Prefer immutable ordered collections such as tuples inside AST nodes:

```text
tuple[Statement, ...]
tuple[Expression, ...]
tuple[Parameter, ...]
```

This reduces accidental mutation.

If implementation ergonomics require lists temporarily, document the choice, but tuples are preferred for frozen nodes.

## 33. Equality

Dataclass structural equality is desirable for AST tests.

Tests should be able to construct expected nodes and compare them directly where practical.

## 34. No Behavior in AST Nodes

AST nodes should primarily be data.

Do not add:

- evaluation methods
- type-checking methods
- name-resolution methods
- lexer/parser methods
- runtime mutation
- provider/effect behavior

Those belong to later compiler/runtime components.

## 35. No Visitor Framework Yet

Do not build a generalized visitor framework during Checkpoint 2.

A visitor may become useful once multiple compiler passes exist, but introducing it now adds machinery without a consumer.

## 36. No AST JSON Yet

Checkpoint 4 will introduce AST JSON.

Do not:

- add Pydantic solely for AST JSON
- define JSON discriminator strings
- create JSON schema files
- freeze serialization field names
- create `.kaj.json` fixtures

during Checkpoint 2.

The internal AST should be clean first.

## 37. Minimum Node Inventory

Checkpoint 2 should provide, at minimum:

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

BindingKind / Mutability
UnaryOperator
BinaryOperator
AssignmentOperator
```

If the minimal parser plan does not need one of the collection/member nodes immediately, it is still acceptable to include it because these are already-established pure-core expression forms and require no semantic behavior.

Do not expand beyond this list without a concrete need.

## 38. Tests

Create focused AST construction tests under:

```text
tests/ast/
```

Suggested files:

```text
tests/ast/
├── test_literals.py
├── test_expressions.py
├── test_types.py
├── test_statements.py
├── test_functions.py
└── test_spans.py
```

Tests should verify:

- nodes can be constructed with expected fields
- nodes preserve spans
- frozen nodes cannot be mutated
- tuples preserve ordering
- operators use enums
- negative numeric values are represented as unary expressions rather than negative literal nodes
- function parameters preserve local mutability
- call arguments can represent positional and named forms
- generic type syntax can represent nested generic types

## 39. Representative AST Shapes

### Binding

Source concept:

```kaj
let x = 10
```

AST:

```text
BindingDeclaration
├── kind: LET
├── name: "x"
├── annotation: None
└── initializer:
    IntegerLiteral(10)
```

### Unary expression

```kaj
-42
```

```text
UnaryExpression
├── operator: NEGATE
└── operand:
    IntegerLiteral(42)
```

### Function

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

```text
FunctionDeclaration
├── name: "add"
├── parameters
│   ├── Parameter("a", NamedType("Int"))
│   └── Parameter("b", NamedType("Int"))
├── return_type: NamedType("Int")
└── body:
    Block
      └── ReturnStatement
          └── BinaryExpression
              ├── Identifier("a")
              ├── ADD
              └── Identifier("b")
```

### Generic type

```kaj
List<Int>
```

```text
GenericType
├── base: NamedType("List")
└── arguments:
    NamedType("Int")
```

### Nested generic type

```kaj
Map<String, List<Int>>
```

must be representable recursively.

## 40. Source of Truth

For Checkpoint 2 AST architecture:

```text
docs/internals/ast.md
        +
AST tests
        +
AST implementation
```

must agree.

`docs/language/` remains authoritative for user-visible Kaj semantics.

This AST document is authoritative for compiler representation only.

## 41. Definition of Done

Checkpoint 2 is complete when:

```text
[ ] base Node model exists
[ ] every concrete AST node carries SourceSpan
[ ] Program exists

[ ] Expression hierarchy exists
[ ] primitive literal nodes exist
[ ] Identifier exists
[ ] UnaryExpression exists
[ ] BinaryExpression exists
[ ] CallExpression / CallArgument exist
[ ] member/index expressions exist
[ ] list/map literal nodes exist

[ ] TypeExpression exists
[ ] NamedType exists
[ ] GenericType exists

[ ] Statement hierarchy exists
[ ] Block exists
[ ] BindingDeclaration exists
[ ] AssignmentStatement exists
[ ] ExpressionStatement exists
[ ] IfStatement exists
[ ] WhileStatement exists
[ ] ForStatement exists
[ ] BreakStatement exists
[ ] ContinueStatement exists
[ ] ReturnStatement exists
[ ] Parameter exists
[ ] FunctionDeclaration exists

[ ] operator categories use enums
[ ] binding mutability is explicit
[ ] parameter local mutability is representable
[ ] AST nodes are immutable where practical
[ ] ordered child collections are immutable where practical

[ ] AST tests pass
[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes

[ ] lexer behavior remains passing
[ ] no parser was implemented
[ ] no type checker was implemented
[ ] no AST JSON serialization was implemented
[ ] no agent/capability/asset nodes were added
```

Checkpoint 3 may then implement the parser that produces these nodes.
# Checkpoint 10 Record Extension

Checkpoint 10 adds these immutable, syntax-only Core AST nodes:

```text
RecordDeclaration(Statement)
    name: str
    fields: tuple[RecordFieldDeclaration, ...]

RecordFieldDeclaration(Node)
    name: str
    type_annotation: TypeExpression

RecordConstructionExpression(Expression)
    type_name: str
    fields: tuple[RecordFieldInitializer, ...]

RecordFieldInitializer(Node)
    name: str
    value: Expression
```

Field tuples preserve source order. These nodes carry source spans and no resolved type symbols,
semantic field mappings, or runtime values. Record declarations are module-level statements;
record construction is an explicit expression and is not represented as a function call.

---
