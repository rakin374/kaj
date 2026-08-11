# Kaj Pure Language — First-Pass Implementation Plan

**Status:** Implementation plan  
**Target:** Kaj pure language core only  
**Phase:** First working compiler/interpreter  
**Date:** August 2026

---

# Implementation Status

**Current checkpoint:** Checkpoint 1 — Source Locations, Tokens, Lexer
**Status:** Complete

## Completed

- Checkpoint 0 repository bootstrap and `kaj` CLI version output.
- Immutable, half-open `SourceLocation` and `SourceSpan` value models.
- Structured lexical diagnostics with all five Checkpoint 1 diagnostic codes.
- Complete Checkpoint 1 token kinds, token values, and public lexer API.
- ASCII identifiers, exact case-sensitive keyword recognition, integers, exact decimals,
  strings and escapes, punctuation, operators, whitespace, and comments.
- Recoverable lexical errors and exactly one zero-width EOF token per tokenization.
- Conformance coverage for token meaning, source spans, recovery, and acceptance examples.

## Decisions Made During Checkpoint 1

- `\n`, `\r`, and `\r\n` are accepted as line endings. A CRLF pair is one logical line break
  while advancing the source offset by two characters.
- Tabs advance the source column by one, as required by the lexical specification.
- Malformed forms `.5`, `1.`, and `1.2.3` are consumed as one invalid numeric sequence,
  produce one `LEX_INVALID_NUMBER`, and do not emit misleading partial number tokens.
- An unknown string escape produces `LEX_INVALID_ESCAPE`, drops the escape backslash from
  the decoded value, preserves the escaped character, and continues scanning the string.
- Raw newlines terminate ordinary strings without consuming the newline, allowing normal
  whitespace handling and token recovery to continue on the next line.
- Block comments are non-nesting: the first `*/` closes the active comment.
- Reusing a `Lexer` instance restarts tokenization, so every result contains exactly one EOF.

## Known Issues

- None within the Checkpoint 1 scope.
- Parser, AST, semantic analysis, and deferred lexical forms remain intentionally unimplemented.

## Verification

- `pytest`: 97 tests passed.
- `ruff check .`: passed.
- `mypy src`: passed under strict mode.
- `kaj --version`: prints `Kaj 0.0.1`.
- `python -m kaj`: prints `Kaj 0.0.1`.

---

# 1. Goal

This document defines the first implementation pass of Kaj.

The objective is **not** to implement the full Kaj vision yet.

The objective is to get the pure, general-purpose language working well enough that Kaj has:

- a real AST,
- a JSON AST representation,
- a parser for `.kaj`,
- a type system,
- name resolution,
- functions,
- control flow,
- user-defined data types,
- collections,
- explicit mutability,
- pattern matching,
- structured diagnostics,
- an interpreter/runtime,
- a formatter,
- and a CLI.

Agentic constructs such as:

```text
task
step
goal
success
require
expect
verify
observe
ask
confirm
handoff
capabilities
asset annotations
model adapters
```

are deliberately postponed until the pure language foundation is stable.

The first milestone should prove:

```text
Human .kaj source
        ↓
      Parser
        ↓
     Kaj AST
        ↑
        │
  Kaj AST JSON
        │
        ↓
  semantic analysis
        ↓
   typed Kaj AST
        ↓
     interpreter
        ↓
      result
```

The compiler must not depend on an LLM.

---

# 2. First-Pass Language Scope

Kaj v0 pure core should initially contain the following language features.

## 2.1 Primitive values

```text
Bool
Int
Decimal
String
Bytes
None
```

Literal examples:

```kaj
true
false
10
-42
3.14
"hello"
none
```

`Int` should be arbitrary precision for ordinary Kaj arithmetic.

`Decimal` should provide exact decimal semantics rather than ordinary binary floating-point behavior.

`Float32` and `Float64` are intentionally postponed from the first minimal implementation unless they become necessary while implementing numeric abstractions.

## 2.2 Bindings

Kaj has two binding forms:

```kaj
let x = 10
var y = 20
```

Rules:

```text
let
    immutable binding

var
    mutable binding
```

Example:

```kaj
let x = 10
x = 20
```

must fail.

This is valid:

```kaj
var x = 10
x = 20
```

### Shadowing

Shadowing is allowed.

Example:

```kaj
let x = 10

if true {
    let x = 20
}
```

The inner `x` is a distinct binding.

The compiler may later provide a lint for suspicious shadowing, but shadowing is not a language error.

---

# 3. Static Typing

Kaj is statically typed.

The compiler must determine the type of every expression before execution.

Kaj should use aggressive local inference:

```kaj
let x = 10
let name = "Kaj"
```

infers:

```text
x: Int
name: String
```

Explicit types are also supported:

```kaj
let x: Int = 10
let name: String = "Kaj"
```

Named function parameters and return values should initially require explicit types.

---

# 4. Numeric Semantics

The first compiler should implement a small, predictable numeric model.

## 4.1 Initial types

```text
Int
Decimal
```

## 4.2 Safe implicit promotion

Allow:

```text
Int → Decimal
```

when required by an expression.

Example:

```kaj
let result = 10 + 2.5
```

produces:

```text
Decimal
```

## 4.3 Do not allow arbitrary coercion

Reject implicit conversions such as:

```text
String → Int
Int → String
Decimal → Int
Bool → Int
```

Conversions should eventually be explicit.

## 4.4 Division

Define:

```text
Int / Int → Decimal
```

Example:

```kaj
5 / 2
```

produces:

```text
2.5
```

No silent integer truncation.

Integer division can be added later through an explicit operator or function.

## 4.5 Boolean separation

`Bool` must not behave like an integer.

Reject:

```kaj
true + 1
if 1 {
}
```

Conditions must have type `Bool`.

Kaj has no implicit truthiness.

---

# 5. Operators

Implement the following initial operators.

## Arithmetic

```text
+
-
*
/
%
**
```

## Comparison

```text
==
!=
<
<=
>
>=
```

## Boolean

```text
and
or
not
```

## Assignment

```text
=
```

Compound assignment may be included after basic assignment works:

```text
+=
-=
*=
/=
```

Avoid adding bitwise operators in the first implementation.

---

# 6. Strings

Support Unicode strings:

```kaj
let name = "Kaj"
let bangla = "কাজ"
```

Support string interpolation:

```kaj
let message = "Hello, {name}"
```

Support multiline strings:

```kaj
let message = """
This is
multiple lines.
"""
```

Exact interpolation parsing can be implemented after ordinary strings if needed.

---

# 7. Bytes

Introduce a separate:

```text
Bytes
```

type.

`String` and `Bytes` are not interchangeable.

Encoding and decoding should eventually be explicit:

```kaj
utf8.encode(text)
utf8.decode(data)
```

Do not build large file APIs yet.

---

# 8. Optional Values

Kaj should not have unrestricted nullability.

Use:

```text
Optional<T>
```

Semantically:

```text
some(T) | none
```

Example:

```kaj
let user: Optional<User> = none
```

This must fail:

```kaj
let user: User = none
```

No implicit Optional unwrapping.

Access to optional values must be explicit through pattern matching initially.

---

# 9. Result Values

Expected failures should use:

```text
Result<T, E>
```

Semantically:

```text
ok(T) | err(E)
```

Example:

```kaj
fn parse_user(input: String) -> Result<User, ParseError> {
    ...
}
```

The `?` propagation operator should be postponed until ordinary `Result` handling works.

---

# 10. Lists

Support homogeneous typed lists:

```kaj
let numbers = [1, 2, 3]
```

infer:

```text
List<Int>
```

Explicit:

```kaj
let names: List<String> = ["A", "B"]
```

Initial operations:

```text
count
index access
iteration
```

Avoid a large collection API in the first compiler.

Decide collection mutation after value semantics are working. The safest first implementation is to treat collection values as immutable values even when held by `var`, and support rebinding instead of internal mutation.

---

# 11. Maps

Support:

```text
Map<K, V>
```

Example:

```kaj
let ages = {
    "Alice": 30,
    "Bob": 25
}
```

infer:

```text
Map<String, Int>
```

Initial operations:

```text
construction
lookup
count
iteration later
```

For the first pass, prefer an explicit lookup operation returning:

```text
Optional<V>
```

rather than unsafe missing-key behavior.

---

# 12. User-Defined Record Types

Use:

```kaj
type User {
    id: String
    name: String
    age: Int
    active: Bool
}
```

Construction:

```kaj
let user = User {
    id: "u_1",
    name: "Alice",
    age: 30,
    active: true
}
```

Field access:

```kaj
user.name
```

Rules:

- record values are value types,
- no classes,
- no inheritance,
- no hidden constructors,
- no methods in the first pass.

Updated-value syntax can be added:

```kaj
let updated = user with {
    age = 31
}
```

but it may be implemented after the initial record system.

---

# 13. Enums

Support simple enums:

```kaj
enum OrderStatus {
    pending
    paid
    shipped
    cancelled
}
```

Usage:

```kaj
let status = OrderStatus.pending
```

Also support enums with typed payloads:

```kaj
enum PaymentResult {
    success(receipt: Receipt)
    declined(reason: String)
    unavailable
}
```

Payload enums are important because they form the basis of:

```text
Optional<T>
Result<T,E>
```

---

# 14. Newtypes

Kaj should support nominal wrappers:

```kaj
newtype UserId = String
newtype OrderId = String
```

These are distinct types.

Reject:

```kaj
fn load_order(id: OrderId) -> Order {
    ...
}

let user_id = UserId("u_123")
load_order(user_id)
```

even though both newtypes are backed by `String`.

This is valuable for correctness and should be part of the first type-system architecture, although implementation may follow records/enums.

---

# 15. Type Aliases

If needed, support aliases separately:

```kaj
type UserName = String
```

An alias is not a new nominal type.

Distinguish:

```text
type X = Y
    alias

newtype X = Y
    distinct type
```

The exact syntax can be revisited before implementation.

---

# 16. Pattern Matching

Implement:

```kaj
match value {
    pattern => expression_or_block
}
```

For enums:

```kaj
match status {
    pending => print("Pending")
    paid => print("Paid")
    shipped => print("Shipped")
    cancelled => print("Cancelled")
}
```

Payload binding:

```kaj
match result {
    ok(value) => print(value)
    err(error) => handle(error)
}
```

Requirements:

- typed patterns,
- exhaustiveness checking,
- scoped pattern bindings,
- compiler diagnostics for missing cases.

Advanced record destructuring and match guards should be postponed.

---

# 17. Functions

Initial named function syntax:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

Rules:

- named function parameters require types,
- return type required,
- recursion supported,
- forward function references supported,
- no user-defined overloading initially,
- no nested named functions initially.

---

# 18. Function Parameter Mutability

Parameters are immutable by default.

```kaj
fn calculate(value: Int) -> Int {
    value = 10
}
```

must fail.

A parameter can explicitly be locally mutable:

```kaj
fn normalize(var value: Decimal) -> Decimal {
    if value < 0 {
        value = 0
    }

    if value > 1 {
        value = 1
    }

    return value
}
```

Important:

```text
var parameter
    means mutable local binding

var parameter
    does NOT mean pass-by-reference
```

No `inout`, references, or caller mutation in the first implementation.

---

# 19. Function Calls

Support positional calls:

```kaj
add(10, 20)
```

Named arguments should also be supported:

```kaj
create_user(
    name: "Alice",
    age: 30,
    active: true
)
```

Rules should prevent ambiguous argument binding.

Suggested rule:

```text
positional arguments first
named arguments afterward
```

Named arguments are useful enough for agent-generated and human-readable Kaj that they should be designed early.

---

# 20. Return Semantics

Functions must return the declared type on all reachable paths.

Example:

```kaj
fn classify(x: Int) -> String {
    if x > 0 {
        return "positive"
    }
}
```

must produce:

```text
MISSING_RETURN
```

Functions returning no meaningful value use:

```text
None
```

Example:

```kaj
fn greet(name: String) -> None {
    print("Hello, {name}")
}
```

A bare `return` may be allowed inside `-> None` functions.

---

# 21. Control Flow

Implement:

```text
if
else
for
while
match
break
continue
return
```

## If

```kaj
if condition {
    ...
} else {
    ...
}
```

Condition must be `Bool`.

## While

```kaj
while condition {
    ...
}
```

## For

Initial form:

```kaj
for item in items {
    ...
}
```

Range iteration can be added after list iteration unless it is easy to implement cleanly.

---

# 22. Scope

Kaj should use lexical block scope.

Every `{ ... }` creates a scope.

Examples:

```text
function body
if block
else block
while block
for block
match arm
```

Names declared in an inner block are unavailable outside that block.

Function declarations exist at module scope in the first implementation.

Module-level mutable variables should be prohibited initially.

Module-level immutable values may be supported after basic module execution semantics are established.

---

# 23. Shadowing

Shadowing is legal.

Example:

```kaj
let value = "10"

if condition {
    let value = 10
}
```

These are distinct bindings.

A later linter can warn about suspicious shadowing.

Do not mix shadowing semantics with reassignment semantics.

---

# 24. Comments

Support:

```kaj
// line comment
```

and:

```kaj
/*
multiline
comment
*/
```

---

# 25. Braces and Semicolons

Kaj is brace-based.

```kaj
if condition {
    ...
}
```

Whitespace does not define block structure.

Semicolons are not required and should not be part of canonical formatting.

---

# 26. Modules and Imports

Implement ordinary module imports only after single-file execution works.

Syntax direction:

```kaj
import math
import my_project.models
```

`import` means:

```text
bring ordinary code/types into scope
```

Capabilities and `use` are NOT part of this first pure-language implementation.

The module system should initially support:

- local modules,
- symbol resolution,
- cycle detection,
- public/private semantics later.

Do not build a package registry yet.

---

# 27. Pure Functions

Ordinary `fn` should be pure from the perspective of external effects.

During the pure-language first pass, this is naturally true because capabilities are not implemented.

Later, Kaj will distinguish:

```text
pure fn
```

from functions that explicitly declare external effects.

Do not add the capability/effect syntax until the core language is stable.

---

# 28. First-Class Functions

Do not implement first-class functions in the earliest checkpoint.

Design for them, but postpone:

```text
function values
lambda expressions
closures
generic higher-order functions
```

until named functions and the basic runtime work.

Potential future syntax:

```kaj
x => x * 2
```

but it is out of scope for the first pass.

---

# 29. Generics

Built-in generic types are required:

```text
Optional<T>
List<T>
Map<K,V>
Result<T,E>
```

User-defined generics can be postponed.

Future:

```kaj
type Pair<A, B> {
    first: A
    second: B
}
```

The initial compiler architecture should avoid making user generics impossible later.

---

# 30. AST Architecture

The AST is the canonical semantic representation of Kaj programs.

Both:

```text
.kaj source
```

and:

```text
Kaj AST JSON
```

must produce the same AST.

The AST should be typed internally and support stable serialization.

Initial top-level structure:

```text
Program
    metadata
    declarations
    statements
```

Suggested core node families:

```text
Program

Declarations
    FunctionDeclaration
    TypeDeclaration
    EnumDeclaration
    NewtypeDeclaration
    ImportDeclaration

Statements
    LetBinding
    VarBinding
    Assignment
    IfStatement
    WhileStatement
    ForStatement
    MatchStatement
    ReturnStatement
    BreakStatement
    ContinueStatement
    ExpressionStatement

Expressions
    Literal
    Reference
    UnaryExpression
    BinaryExpression
    CallExpression
    MemberAccess
    IndexExpression
    RecordConstruction
    EnumConstruction
    ListLiteral
    MapLiteral
```

Optional/Result values can initially lower to enum construction semantics internally.

---

# 31. AST JSON

The machine representation should contain language/schema metadata.

Example:

```json
{
  "language": "kaj",
  "language_version": "0.1",
  "ast_schema_version": 1,
  "kind": "program",
  "body": []
}
```

AST JSON should be:

- schema validated,
- deterministic,
- round-trippable,
- suitable for future LLM structured output,
- independent from runtime IR.

The compiler should accept:

```text
.kaj
```

or:

```text
Kaj AST JSON
```

as front ends into the same semantic pipeline.

---

# 32. Parser

The parser should target the AST directly.

Recommended architecture:

```text
source
  ↓
lexer
  ↓
parser
  ↓
AST
```

Do not implement semantic logic inside the parser.

Parser responsibilities:

```text
syntax
source spans
node construction
syntax diagnostics
```

Semantic analysis happens later.

---

# 33. Source Spans

Every AST node originating from source should optionally contain a source span:

```text
file
start line
start column
end line
end column
```

This is essential for good diagnostics.

AST JSON created directly by agents may not always have ordinary source spans.

The compiler should support nodes without source spans.

---

# 34. Name Resolution

Create a dedicated resolver pass.

Responsibilities:

- declare module symbols,
- resolve local bindings,
- resolve function names,
- resolve type names,
- resolve enum cases,
- detect duplicate definitions,
- handle lexical scopes,
- support forward function references.

Do not combine name resolution with interpretation.

---

# 35. Type Checker

Build a separate type-checking pass after name resolution.

Responsibilities:

- literal typing,
- binding inference,
- assignment compatibility,
- operator typing,
- call argument typing,
- return checking,
- Boolean condition enforcement,
- enum construction checking,
- record construction checking,
- Optional/Result checking,
- match pattern checking,
- exhaustiveness checking,
- safe Int→Decimal promotion.

The result should be a typed/annotated AST or a side table keyed by node ID.

---

# 36. Semantic Validation

Some checks are neither parsing nor simple type checking.

Examples:

```text
break outside loop
continue outside loop
return outside function
duplicate enum cases
invalid `var` placement
module-level mutable state
non-exhaustive match
unreachable cases
```

Keep semantic validation explicit.

---

# 37. Structured Diagnostics

Diagnostics are a first-class compiler output.

Suggested structure:

```json
{
  "code": "TYPE_MISMATCH",
  "severity": "error",
  "message": "Expected Int, received String",
  "file": "main.kaj",
  "span": {
    "start_line": 4,
    "start_column": 12,
    "end_line": 4,
    "end_column": 18
  },
  "expected": "Int",
  "actual": "String"
}
```

Initial diagnostic codes should include:

```text
SYNTAX_ERROR

UNKNOWN_NAME
DUPLICATE_NAME
UNKNOWN_TYPE

TYPE_MISMATCH
INVALID_OPERATOR
INVALID_ARGUMENT
INVALID_RETURN_TYPE
MISSING_RETURN

ASSIGN_TO_IMMUTABLE
INVALID_ASSIGNMENT

INVALID_CONDITION_TYPE

INVALID_BREAK
INVALID_CONTINUE
INVALID_RETURN

NON_EXHAUSTIVE_MATCH
INVALID_PATTERN

INVALID_RECORD_FIELD
MISSING_RECORD_FIELD
UNKNOWN_RECORD_FIELD

UNKNOWN_ENUM_CASE

MODULE_NOT_FOUND
IMPORT_CYCLE
```

Diagnostic code stability matters because future agents may consume these codes.

---

# 38. Interpreter

The first runtime should be a straightforward interpreter.

Do not build bytecode or native code yet.

Architecture:

```text
typed AST
   ↓
interpreter
   ↓
runtime values
```

The interpreter should execute only programs that successfully pass semantic analysis.

Initial runtime values:

```text
IntValue
DecimalValue
BoolValue
StringValue
BytesValue
NoneValue
ListValue
MapValue
RecordValue
EnumValue
FunctionValue
```

Even if implementation uses Python values internally, keep explicit Kaj runtime semantics.

---

# 39. Built-in Functions

Keep the first standard environment tiny.

Potential initial built-ins:

```text
print
String(...)
Int(...)
Decimal(...)
len/count through members if preferred
```

Avoid building a large standard library until the language core stabilizes.

If possible, implement most library functionality as Kaj code later rather than compiler magic.

---

# 40. Formatter

Build a canonical formatter after the AST and parser stabilize enough to round-trip programs.

The formatter should produce one official Kaj style.

Example:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

Properties:

- deterministic,
- no optional styles initially,
- stable output,
- useful for agent-generated AST,
- AST → human-readable `.kaj`.

---

# 41. CLI

The first CLI should support:

```bash
kaj check file.kaj
kaj run file.kaj
kaj fmt file.kaj
```

Eventually:

```bash
kaj ast file.kaj
kaj ast --json file.kaj
```

Possible first commands:

## `kaj check`

```text
parse
resolve
type check
semantic validate
print diagnostics
```

## `kaj run`

```text
check
then interpret
```

## `kaj fmt`

```text
parse
format
write or stdout
```

## `kaj ast`

```text
show normalized AST / AST JSON
```

---

# 42. Repository Structure

Recommended initial structure:

```text
kaj/
├── README.md
├── LICENSE
├── pyproject.toml
├── docs/
│
├── src/
│   └── kaj/
│       ├── __init__.py
│       │
│       ├── ast/
│       │   ├── base.py
│       │   ├── nodes.py
│       │   ├── declarations.py
│       │   ├── statements.py
│       │   └── expressions.py
│       │
│       ├── lexer/
│       │   ├── token.py
│       │   └── lexer.py
│       │
│       ├── parser/
│       │   └── parser.py
│       │
│       ├── types/
│       │   ├── base.py
│       │   ├── primitive.py
│       │   ├── composite.py
│       │   └── relations.py
│       │
│       ├── semantic/
│       │   ├── scopes.py
│       │   ├── resolver.py
│       │   ├── type_checker.py
│       │   └── validator.py
│       │
│       ├── diagnostics/
│       │   ├── diagnostic.py
│       │   └── codes.py
│       │
│       ├── serialization/
│       │   ├── ast_json.py
│       │   └── schema.py
│       │
│       ├── runtime/
│       │   ├── values.py
│       │   ├── environment.py
│       │   └── interpreter.py
│       │
│       ├── formatter/
│       │   └── formatter.py
│       │
│       └── cli/
│           └── main.py
│
├── tests/
│   ├── lexer/
│   ├── parser/
│   ├── ast/
│   ├── resolver/
│   ├── types/
│   ├── semantics/
│   ├── runtime/
│   ├── formatter/
│   └── fixtures/
│
├── examples/
└── schemas/
    └── ast/
```

Keep implementation modular, but avoid premature abstraction.

---

# 43. Recommended Implementation Language

Use Python for the first compiler/runtime implementation.

Reasons:

- fast iteration,
- easy AST/schema work,
- good testing ecosystem,
- suitable for early LLM/schema integration,
- compiler performance is not yet the bottleneck.

Recommended dependencies:

```text
Python 3.12+
pytest
ruff
mypy
```

Pydantic may be useful for AST JSON/schema validation, but avoid making the internal compiler AST inseparable from Pydantic if it complicates compiler design.

A good compromise:

```text
external JSON schema/model
        ↓
validated DTO
        ↓
internal compiler AST
```

or use Pydantic directly during the prototype and refactor later if necessary.

---

# 44. Implementation Checkpoints

The implementation should proceed in deliberate checkpoints.

## Checkpoint 0 — Repository Bootstrap

Create:

```text
pyproject.toml
src/kaj
tests
README
LICENSE
```

Configure:

```text
pytest
ruff
mypy
```

Add:

```bash
python -m kaj
```

and eventually:

```bash
kaj
```

Acceptance:

```bash
kaj --version
```

works.

## Checkpoint 1 — Source Locations, Tokens, Lexer

Implement:

```text
SourceLocation
SourceSpan
TokenKind
Token
Lexer
```

Support tokens for:

```text
identifiers
keywords
numbers
strings
operators
braces
parentheses
brackets
commas
colons
newlines if needed
comments
EOF
```

Acceptance examples:

```kaj
let x = 10
```

and:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

tokenize correctly.

## Checkpoint 2 — Core AST

Implement internal AST nodes for:

```text
Program
Literal
Reference
UnaryExpression
BinaryExpression
CallExpression
MemberAccess
ListLiteral

LetBinding
VarBinding
Assignment
ExpressionStatement

IfStatement
WhileStatement
ReturnStatement

FunctionDeclaration
```

Do not add the entire language at once.

Acceptance:

AST can be built manually and serialized/debug-printed.

## Checkpoint 3 — Parser for Minimal Kaj

Parse:

```text
literals
let
var
assignment
operators
parentheses
if/else
while
function declarations
calls
return
```

Acceptance program:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}

let x = add(10, 20)

if x > 20 {
    print(x)
}
```

produces the expected AST.

## Checkpoint 4 — AST JSON

Create canonical AST JSON serialization and deserialization.

Acceptance:

```text
source
↓
AST
↓
JSON
↓
AST
```

preserves meaning.

Also accept AST JSON as compiler input.

## Checkpoint 5 — Scope and Name Resolution

Implement:

```text
module scope
function scope
block scope
symbol tables
duplicate detection
unknown-name errors
forward function references
shadowing
```

Acceptance:

valid lexical scope succeeds and invalid references fail with structured diagnostics.

## Checkpoint 6 — Primitive Type System

Implement:

```text
Bool
Int
Decimal
String
Bytes
None
```

Add:

```text
type inference
operator typing
assignment typing
Bool-only conditions
Int→Decimal promotion
```

Acceptance includes:

```kaj
let x = 10 + 2.5
```

→ Decimal

and:

```kaj
let x = "10" + 2
```

→ TYPE_MISMATCH.

## Checkpoint 7 — Function Type Checking

Implement:

```text
parameter types
return types
argument checking
named arguments
missing returns
recursion
mutable `var` parameters
```

Acceptance:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

passes.

Wrong argument and return types fail.

## Checkpoint 8 — Interpreter Core

Execute:

```text
literals
bindings
assignment
operators
if
while
functions
return
```

Acceptance:

```kaj
fn factorial(n: Int) -> Int {
    if n <= 1 {
        return 1
    }

    return n * factorial(n - 1)
}

print(factorial(5))
```

prints:

```text
120
```

## Checkpoint 9 — Lists

Add:

```text
List<T>
list literals
index access
count
for iteration
```

Acceptance:

```kaj
let values = [1, 2, 3]

for value in values {
    print(value)
}
```

works.

## Checkpoint 10 — Records

Add:

```text
type declarations
record construction
field access
record type checking
```

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

works.

## Checkpoint 11 — Enums and Match

Add:

```text
enum declarations
payload enums
enum construction
match
pattern binding
exhaustiveness
```

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

works.

Missing a case produces:

```text
NON_EXHAUSTIVE_MATCH
```

## Checkpoint 12 — Optional and Result

Implement as language-standard tagged types using enum semantics.

Support:

```text
Optional<T>
Result<T,E>
some
none
ok
err
```

Acceptance:

```kaj
match maybe_user {
    some(user) => print(user.name)
    none => print("missing")
}
```

works.

Do not add `?` yet.

## Checkpoint 13 — Maps

Add:

```text
Map<K,V>
map literals
lookup
count
```

Prefer safe lookup returning Optional.

## Checkpoint 14 — Newtypes

Add nominal wrapper semantics:

```kaj
newtype UserId = String
```

Ensure distinct newtypes are incompatible.

## Checkpoint 15 — Formatter

Implement:

```text
AST → canonical .kaj
```

Acceptance:

```text
parse
format
parse
```

preserves semantic AST.

## Checkpoint 16 — CLI Completion

Support:

```bash
kaj check
kaj run
kaj fmt
kaj ast
kaj --version
```

Exit codes should distinguish:

```text
success
compile error
runtime error
CLI misuse
```

## Checkpoint 17 — Module Imports

After single-file behavior is solid, implement local imports.

Support:

```kaj
import foo
import foo.bar
```

Initial scope:

```text
local project modules only
```

Do not implement remote packages or package registry resolution yet.

## Checkpoint 18 — Pure Language Test Suite

Before starting agentic Kaj, create a comprehensive language conformance suite.

Test categories:

```text
lexer
parser
source spans
AST JSON
scope
shadowing
types
numeric promotion
functions
recursion
control flow
lists
records
enums
match
Optional
Result
maps
newtypes
formatter
runtime behavior
diagnostics
modules
```

For every invalid construct, assert the stable diagnostic code.

---

# 45. What Is Explicitly Deferred

Do NOT implement during this pass:

```text
task
step
goal
success
require
expect
verify
observe
learn

ask
choose
confirm
inform
handoff

use capability
capability providers
effect checking

planning
replanning
AST patches
task persistence
Task IR

asset language
Asset<T>
annotations
asset patches
selections
preservation constraints

audio/image/geometry profiles
Kaj model adapters

world models

async
concurrency
parallel steps

classes
inheritance
traits/interfaces
macros

user-defined generics
closures/lambdas
function overloading

remote package registry
package signing
IDE/LSP
native compiler
bytecode VM
```

These should come after the language foundation is proven.

---

# 46. First-Pass Definition of Done

The pure Kaj language first pass is complete when this program can be parsed, checked, formatted, serialized to AST JSON, and executed:

```kaj
type User {
    name: String
    age: Int
}

enum LookupResult {
    found(user: User)
    missing
}

fn classify_age(age: Int) -> String {
    if age >= 18 {
        return "adult"
    }

    return "minor"
}

fn describe(result: LookupResult) -> None {
    match result {
        found(user) => {
            let category = classify_age(user.age)
            print("{user.name}: {category}")
        }

        missing => {
            print("User not found")
        }
    }
}

let users = [
    User {
        name: "Alice",
        age: 30
    },
    User {
        name: "Bob",
        age: 16
    }
]

for user in users {
    describe(LookupResult.found(user))
}
```

The toolchain should support:

```bash
kaj check example.kaj
kaj fmt example.kaj
kaj ast example.kaj
kaj run example.kaj
```

and AST JSON should also be accepted as an equivalent machine representation.

---

# 47. What Comes Immediately After

Once this pure core passes its conformance suite, begin the second major language phase:

```text
Kaj Agent Semantics
```

in roughly this order:

```text
1. capability contracts
2. effect system
3. task
4. step
5. goal / success / invariant
6. require / expect / verify
7. observe
8. human interaction
9. Task IR
10. execution state
11. planning and constrained AST patching
12. recovery
13. capability providers
```

Only after those foundations are working should Kaj Asset semantics and model adapters be implemented.

---

# 48. Immediate Next Action

Start only with:

```text
Checkpoint 0 — repository bootstrap
Checkpoint 1 — lexer
Checkpoint 2 — minimal AST
```

Do not implement the type checker, interpreter, or full grammar before the syntax/AST foundations are reviewed.

For each checkpoint, define:

```text
syntax
AST shape
invariants
diagnostics
tests
acceptance examples
```

before coding it.

This keeps the implementation aligned with the evolving Kaj specification and avoids cementing accidental semantics into the compiler.
