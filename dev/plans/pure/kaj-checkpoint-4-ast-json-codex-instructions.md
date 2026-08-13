# Kaj Checkpoint 4 — AST JSON

**Audience:** Codex / implementation agent  
**Repository:** Kaj  
**Checkpoint:** 4  
**Goal:** Add a canonical machine-facing JSON representation for the Kaj AST, with lossless round-trip between internal AST objects and JSON.

---

## 1. Primary Instruction

Implement **Checkpoint 4 only**.

Before changing code, read:

```text
docs/internals/ast.md
docs/language/lexical-structure.md
.dev/plans/pure-language-v0.md
```

Also inspect the completed implementations for:

```text
Checkpoint 1 — lexer/source spans
Checkpoint 2 — core AST
Checkpoint 3 — parser
```

Checkpoint 4 adds a structured JSON interchange format for ASTs.

Do not implement:

- AST patches
- agent planning
- task IR
- compiler IR
- name resolution
- type checking
- interpreter/runtime changes
- formatter
- records/enums/match/newtypes if they do not yet exist in the internal AST
- capabilities/effects
- asset semantics
- network APIs

---

# 2. Checkpoint Goal

After this checkpoint, Kaj must support:

```text
.kaj source
    ↓
Lexer
    ↓
Parser
    ↓
Internal Kaj AST
    ↓
AST JSON serialization
    ↓
JSON

and:

JSON
    ↓
AST JSON deserialization
    ↓
Internal Kaj AST
```

The critical invariant is:

```text
AST
  ↓ serialize
JSON
  ↓ deserialize
AST'
```

where:

```text
AST' == AST
```

for all supported Checkpoint 4 AST nodes.

Also validate source-driven round trip:

```text
source
  ↓
parse
  ↓
AST
  ↓
JSON
  ↓
AST
```

The AST before and after JSON must be structurally equivalent.

---

# 3. Architectural Rule

The internal AST remains the compiler's semantic syntax representation.

AST JSON is an **external interchange representation**.

Do not redesign internal AST nodes merely to make JSON convenient.

Do not make the compiler depend on JSON for normal parsing/type checking/runtime operation.

The intended relationship is:

```text
           ┌──────────── .kaj source
           │
           ↓
        Internal AST
           ↑
           │
           └──────────── Kaj AST JSON
```

Both `.kaj` source and AST JSON ultimately represent programs through the same internal AST.

---

# 4. Canonical Purpose of AST JSON

AST JSON exists primarily for:

- agents/tools generating Kaj structurally
- IDE/tooling interoperability
- tests
- debugging
- future structured editing
- future AST patch workflows
- programmatic code generation

It is not the compiler IR.

Do not put runtime lowering details into AST JSON.

---

# 5. Required Repository Structure

Add:

```text
src/kaj/
└── serialization/
    ├── __init__.py
    └── ast_json.py
```

Optionally add:

```text
src/kaj/serialization/errors.py
```

only if it materially improves clarity.

Add schemas:

```text
schemas/
└── ast/
    └── v1.json
```

Add tests:

```text
tests/
└── serialization/
    ├── test_ast_json_literals.py
    ├── test_ast_json_expressions.py
    ├── test_ast_json_statements.py
    ├── test_ast_json_types.py
    ├── test_ast_json_functions.py
    ├── test_ast_json_roundtrip.py
    ├── test_ast_json_invalid.py
    ├── test_ast_json_spans.py
    └── test_ast_json_schema.py
```

If the repo already has a better schema directory convention, follow it consistently.

---

# 6. Public Serialization API

Provide a small API conceptually equivalent to:

```python
ast_to_json_value(program: Program) -> dict[str, object]
ast_from_json_value(value: object) -> Program

ast_to_json(program: Program, *, indent: int | None = None) -> str
ast_from_json(text: str) -> Program
```

Names may differ slightly, but support both:

- Python object/dict conversion
- JSON string conversion

Do not require callers to serialize through disk.

---

# 7. Do Not Couple Internal AST to Pydantic

Do not rewrite internal AST dataclasses as Pydantic models solely for JSON support.

The internal AST should remain ordinary typed compiler data structures.

If Pydantic is used at all, it must be isolated to the external validation/serialization boundary.

Prefer implementing explicit serialization/deserialization functions unless a dependency clearly reduces complexity without leaking into the compiler core.

Do not add a major dependency unnecessarily.

---

# 8. JSON Top-Level Envelope

Use a versioned top-level envelope.

Canonical shape:

```json
{
  "format": "kaj-ast",
  "version": 1,
  "program": {
    "...": "..."
  }
}
```

Required fields:

```text
format
version
program
```

Rules:

```text
format == "kaj-ast"
version == 1
```

Do not use an unversioned bare node as the canonical document format.

This gives Kaj room to evolve its public AST interchange format later.

---

# 9. Node Discriminator

Every AST node serialized to JSON must include a stable node discriminator:

```text
kind
```

Example:

```json
{
  "kind": "integer_literal",
  "value": 10,
  "span": {
    "start": {
      "offset": 8,
      "line": 1,
      "column": 9
    },
    "end": {
      "offset": 10,
      "line": 1,
      "column": 11
    }
  }
}
```

Use stable snake_case strings.

Do not serialize Python class names directly as the public format.

For example, prefer:

```text
integer_literal
binary_expression
binding_declaration
```

rather than:

```text
IntegerLiteral
BinaryExpression
BindingDeclaration
```

The JSON contract must not depend on Python naming conventions.

---

# 10. Versioning Rule

Checkpoint 4 defines:

```text
Kaj AST JSON version 1
```

The serializer emits:

```json
"version": 1
```

The deserializer must reject unsupported versions cleanly.

Do not silently accept:

```json
"version": 2
```

as version 1.

Use a structured serialization diagnostic/error.

---

# 11. AST JSON Error Model

Malformed AST JSON must produce structured errors rather than arbitrary:

```text
KeyError
TypeError
AssertionError
AttributeError
```

At minimum define stable error codes equivalent to:

```text
ASTJSON_INVALID_JSON
ASTJSON_INVALID_DOCUMENT
ASTJSON_UNSUPPORTED_VERSION
ASTJSON_UNKNOWN_NODE_KIND
ASTJSON_MISSING_FIELD
ASTJSON_INVALID_FIELD
ASTJSON_INVALID_ENUM_VALUE
```

If the project has a general diagnostic architecture that fits non-source input, reuse it carefully.

AST JSON validation errors do not necessarily have a Kaj `SourceSpan`, because the invalid input is JSON rather than `.kaj` source.

Do not fabricate Kaj source spans for JSON syntax errors.

---

# 12. SourceSpan Serialization

All source-derived AST nodes must preserve their existing spans.

Serialize:

```text
span
```

as:

```json
{
  "start": {
    "offset": 0,
    "line": 1,
    "column": 1
  },
  "end": {
    "offset": 3,
    "line": 1,
    "column": 4
  }
}
```

This must preserve the existing rules:

```text
offset: zero-based
line: one-based
column: one-based
end: exclusive
```

Deserialization must recreate equivalent `SourceLocation` and `SourceSpan` objects.

---

# 13. Source Filename

Do not embed absolute local filesystem paths into every AST node.

If the internal AST itself does not currently store filename identity, do not redesign it during this checkpoint.

The canonical AST JSON v1 format should focus on node structure and spans.

A future source-unit metadata envelope may add filename/module identity if needed.

---

# 14. Program Serialization

Serialize the root `Program` as a normal node.

Example:

```json
{
  "kind": "program",
  "statements": [
    {
      "...": "..."
    }
  ],
  "span": {
    "...": "..."
  }
}
```

The top-level document then contains it under:

```json
"program"
```

This intentionally means the JSON document has both:

```text
format/version envelope
program AST node
```

---

# 15. Canonical Node Field Ordering

JSON objects are semantically unordered, but the serializer should emit fields in a deterministic order for readability and stable tests.

Recommended order:

```text
kind
node-specific semantic fields
span
```

Top-level document:

```text
format
version
program
```

Do not rely on arbitrary dataclass field introspection order as the public contract.

Implement explicitly enough that output remains deterministic.

---

# 16. Canonical JSON Formatting

For string serialization:

- default compact output is acceptable
- support optional indentation
- use UTF-8 / normal Unicode JSON behavior
- do not ASCII-escape all Unicode unless the JSON library forces it

Prefer:

```python
json.dumps(..., ensure_ascii=False)
```

so Kaj strings remain readable:

```json
"value": "বাংলা"
```

instead of unnecessary Unicode escape sequences.

---

# 17. Decimal Serialization

This is critical.

Kaj `Decimal` is exact.

Do **not** serialize `Decimal` through JSON floating-point numbers.

For example, this is unsafe as the canonical representation:

```json
{
  "kind": "decimal_literal",
  "value": 19.99
}
```

because generic JSON consumers may interpret it as binary floating-point.

Instead serialize exact decimal values as strings:

```json
{
  "kind": "decimal_literal",
  "value": "19.99"
}
```

On deserialization:

```python
Decimal("19.99")
```

must recreate the exact value.

This is a frozen AST JSON v1 rule.

---

# 18. Integer Serialization

Kaj `Int` supports arbitrary precision.

JSON ecosystems may not safely preserve arbitrarily large integer values.

Therefore serialize Kaj integer literal values as decimal strings as well.

Canonical:

```json
{
  "kind": "integer_literal",
  "value": "999999999999999999999999999999"
}
```

Deserialize with Python `int`.

Do not rely on a JSON consumer's numeric range.

This keeps AST JSON portable across languages.

---

# 19. String Serialization

Serialize decoded Kaj string values as ordinary JSON strings.

Example:

```json
{
  "kind": "string_literal",
  "value": "hello\nworld"
}
```

AST JSON represents semantic string contents, not the original `.kaj` string lexeme.

The internal AST currently stores decoded value, not lexer token lexeme.

Do not invent raw source literal fields unless the AST already contains them.

---

# 20. Boolean and None Serialization

Serialize booleans as JSON booleans:

```json
{
  "kind": "boolean_literal",
  "value": true
}
```

Serialize `NoneLiteral` without a fake payload:

```json
{
  "kind": "none_literal",
  "span": { "...": "..." }
}
```

Do not use JSON null as the node discriminator.

The node itself must remain explicit.

---

# 21. Identifier Serialization

Example:

```json
{
  "kind": "identifier",
  "name": "price",
  "span": { "...": "..." }
}
```

---

# 22. Unary Expression Serialization

Example:

```json
{
  "kind": "unary_expression",
  "operator": "negate",
  "operand": {
    "kind": "integer_literal",
    "value": "42",
    "span": { "...": "..." }
  },
  "span": { "...": "..." }
}
```

Use stable lowercase enum strings.

Recommended unary values:

```text
positive
negate
not
```

Use the actual internal enum names only through an explicit mapping.

---

# 23. Binary Expression Serialization

Example:

```json
{
  "kind": "binary_expression",
  "operator": "add",
  "left": {
    "...": "..."
  },
  "right": {
    "...": "..."
  },
  "span": {
    "...": "..."
  }
}
```

Recommended stable operator strings:

```text
add
subtract
multiply
divide
modulo
power

equal
not_equal
less
less_equal
greater
greater_equal

and
or
```

Map explicitly from internal enums.

---

# 24. Call Arguments and Calls

Serialize `CallArgument` explicitly.

Example positional argument:

```json
{
  "kind": "call_argument",
  "name": null,
  "value": {
    "kind": "integer_literal",
    "value": "1",
    "span": { "...": "..." }
  },
  "span": { "...": "..." }
}
```

Example named argument:

```json
{
  "kind": "call_argument",
  "name": "priority",
  "value": {
    "kind": "integer_literal",
    "value": "2",
    "span": { "...": "..." }
  },
  "span": { "...": "..." }
}
```

If `CallArgument` in the internal AST does not have a span, follow the authoritative AST design rather than fabricating one. In that case omit its span in v1.

Call:

```json
{
  "kind": "call_expression",
  "callee": {
    "...": "..."
  },
  "arguments": [
    {
      "...": "..."
    }
  ],
  "span": {
    "...": "..."
  }
}
```

---

# 25. Member Access

Example:

```json
{
  "kind": "member_access_expression",
  "object": {
    "kind": "identifier",
    "name": "user",
    "span": { "...": "..." }
  },
  "member": "name",
  "span": { "...": "..." }
}
```

---

# 26. Index Expression

Example:

```json
{
  "kind": "index_expression",
  "object": {
    "...": "..."
  },
  "index": {
    "...": "..."
  },
  "span": {
    "...": "..."
  }
}
```

---

# 27. List Literal

Example:

```json
{
  "kind": "list_literal",
  "elements": [
    {
      "kind": "integer_literal",
      "value": "1",
      "span": { "...": "..." }
    }
  ],
  "span": {
    "...": "..."
  }
}
```

Preserve element order exactly.

---

# 28. Map Literal

Serialize entries explicitly rather than converting to a JSON object.

Correct:

```json
{
  "kind": "map_literal",
  "entries": [
    {
      "kind": "map_entry",
      "key": {
        "...": "..."
      },
      "value": {
        "...": "..."
      }
    }
  ],
  "span": {
    "...": "..."
  }
}
```

Do **not** serialize Kaj maps as JSON objects because:

- Kaj keys are expressions
- Kaj map keys are not necessarily strings
- source ordering should be preserved
- duplicate-key syntax may need to remain representable before semantic checking

---

# 29. Type Expressions

Serialize `NamedType`:

```json
{
  "kind": "named_type",
  "name": "Int",
  "span": {
    "...": "..."
  }
}
```

Serialize `GenericType`:

```json
{
  "kind": "generic_type",
  "base": {
    "kind": "named_type",
    "name": "List",
    "span": { "...": "..." }
  },
  "arguments": [
    {
      "kind": "named_type",
      "name": "Int",
      "span": { "...": "..." }
    }
  ],
  "span": {
    "...": "..."
  }
}
```

If the internal AST's `GenericType.base` shape differs, serialize exactly the authoritative internal structure rather than redesigning it.

---

# 30. Block Serialization

Example:

```json
{
  "kind": "block",
  "statements": [
    {
      "...": "..."
    }
  ],
  "span": {
    "...": "..."
  }
}
```

Preserve statement order.

---

# 31. Binding Declaration

Example:

```json
{
  "kind": "binding_declaration",
  "binding_kind": "let",
  "name": "x",
  "annotation": null,
  "initializer": {
    "kind": "integer_literal",
    "value": "10",
    "span": { "...": "..." }
  },
  "span": { "...": "..." }
}
```

For mutable bindings:

```json
"binding_kind": "var"
```

Do not serialize Python enum repr strings.

---

# 32. Assignment Statement

Example:

```json
{
  "kind": "assignment_statement",
  "operator": "assign",
  "target": {
    "kind": "identifier",
    "name": "x",
    "span": { "...": "..." }
  },
  "value": {
    "kind": "integer_literal",
    "value": "1",
    "span": { "...": "..." }
  },
  "span": { "...": "..." }
}
```

Recommended assignment enum strings:

```text
assign
add_assign
subtract_assign
multiply_assign
divide_assign
```

---

# 33. Expression Statement

Example:

```json
{
  "kind": "expression_statement",
  "expression": {
    "...": "..."
  },
  "span": {
    "...": "..."
  }
}
```

---

# 34. If Statement

Serialize:

```text
condition
then_branch
else_branch
span
```

`else_branch` may be:

```text
null
block node
if_statement node
```

depending on the internal AST model.

Do not flatten `else if` chains into arrays unless the internal AST already does so.

---

# 35. While and For

While:

```json
{
  "kind": "while_statement",
  "condition": { "...": "..." },
  "body": { "...": "..." },
  "span": { "...": "..." }
}
```

For:

```json
{
  "kind": "for_statement",
  "name": "item",
  "iterable": { "...": "..." },
  "body": { "...": "..." },
  "span": { "...": "..." }
}
```

---

# 36. Break / Continue / Return

Break:

```json
{
  "kind": "break_statement",
  "span": { "...": "..." }
}
```

Continue:

```json
{
  "kind": "continue_statement",
  "span": { "...": "..." }
}
```

Return:

```json
{
  "kind": "return_statement",
  "value": null,
  "span": { "...": "..." }
}
```

or with an expression value.

---

# 37. Parameter Serialization

Serialize:

```text
name
type_annotation
mutable
span
```

Example:

```json
{
  "kind": "parameter",
  "name": "value",
  "type_annotation": {
    "kind": "named_type",
    "name": "Decimal",
    "span": { "...": "..." }
  },
  "mutable": true,
  "span": { "...": "..." }
}
```

If the internal AST uses a mutability enum rather than bool, expose a stable external form. A boolean is acceptable if the semantic distinction is only mutable/immutable.

---

# 38. Function Declaration

Example:

```json
{
  "kind": "function_declaration",
  "name": "add",
  "parameters": [
    {
      "...": "..."
    }
  ],
  "return_type": {
    "kind": "named_type",
    "name": "Int",
    "span": { "...": "..." }
  },
  "body": {
    "kind": "block",
    "statements": [
      {
        "...": "..."
      }
    ],
    "span": { "...": "..." }
  },
  "span": { "...": "..." }
}
```

Do not add effect/capability fields.

---

# 39. Exact Internal AST Coverage

Support every concrete AST node that exists at the end of Checkpoint 3 and belongs to the pure Core AST.

Do not invent JSON forms for future AST nodes that do not exist yet.

The serializer should fail loudly during development if a concrete internal node is not handled rather than silently dropping it.

Tests should make coverage explicit.

---

# 40. Explicit Serialization Mapping

Prefer an explicit mapping strategy.

For example:

```python
if isinstance(node, IntegerLiteral):
    ...
elif isinstance(node, BinaryExpression):
    ...
```

or a clean registry.

Do not blindly use:

```python
dataclasses.asdict()
```

as the public serialization contract.

`asdict()` would leak:

- Python field names
- enum representations
- class structure
- future internal refactors

into the external format.

The public JSON contract must be intentionally controlled.

---

# 41. Explicit Deserialization Dispatch

Deserialize using:

```text
kind
```

as the node discriminator.

Conceptually:

```python
kind = value["kind"]

if kind == "integer_literal":
    ...
elif kind == "binary_expression":
    ...
```

A registry mapping kind strings to parser functions is acceptable.

Unknown kinds must produce:

```text
ASTJSON_UNKNOWN_NODE_KIND
```

Do not silently ignore unknown nodes.

---

# 42. Validation Strictness

AST JSON v1 should be strict enough to prevent ambiguous malformed structures.

Reject:

- missing required fields
- wrong field types
- invalid enum strings
- unknown node kinds
- unsupported document versions
- invalid span shapes
- invalid integer strings
- invalid decimal strings

Do not attempt broad coercion.

Examples:

```json
"value": true
```

is not valid for an integer literal.

```json
"value": "abc"
```

is not a valid integer literal.

---

# 43. Unknown Fields

For canonical v1 deserialization, reject unknown fields by default.

This prevents misspellings such as:

```json
{
  "kind": "identifier",
  "nam": "x"
}
```

from silently succeeding.

If a forward-compatibility extension mechanism is desired later, define it explicitly in a future version.

---

# 44. Span Validation

Validate:

```text
offset >= 0
line >= 1
column >= 1
```

and:

```text
end.offset >= start.offset
```

Do not attempt to verify that line/column are perfectly consistent with unavailable source text.

AST JSON deserialization may happen without original `.kaj` source.

---

# 45. Child Type Validation

Validate structurally meaningful child categories.

Examples:

```text
Program.statements -> statement nodes
BinaryExpression.left/right -> expression nodes
Block.statements -> statement nodes
FunctionDeclaration.return_type -> type-expression node
```

Do not merely accept any node everywhere because it carries a `kind`.

This provides a useful structural boundary before later semantic analysis.

---

# 46. Semantic Validation Is Deferred

Do not reject AST JSON because:

```text
identifier is unresolved
break is outside loop
return is outside function
types do not match
function does not exist
Map has wrong generic arity
```

Those belong to later compiler passes.

Checkpoint 4 validates **AST structure**, not Kaj semantic correctness.

---

# 47. JSON Schema

Create:

```text
schemas/ast/v1.json
```

using JSON Schema.

The schema should validate the canonical AST JSON document format.

It must cover:

- top-level envelope
- version
- program
- spans
- all currently supported node kinds
- enum strings
- required fields
- nullability
- arrays
- exact integer/decimal string representation

Do not generate a vague schema such as:

```json
{
  "type": "object"
}
```

The schema should meaningfully describe the contract.

---

# 48. JSON Schema Draft

Use a modern stable JSON Schema draft supported by the chosen test dependency.

For example:

```text
2020-12
```

If using schema validation in tests, add a lightweight development dependency only if needed.

Do not add runtime schema validation to every normal compiler operation.

---

# 49. Schema and Code Must Agree

The following must match:

```text
serializer
deserializer
schemas/ast/v1.json
tests
```

If the code emits JSON that the schema rejects, that is a bug.

If the schema accepts structures the deserializer rejects for basic shape reasons, tighten them where practical.

---

# 50. Round-Trip Invariant

For every supported AST node reachable from `Program`:

```python
decoded = ast_from_json(ast_to_json(program))
assert decoded == program
```

This is a required conformance property.

Use structural AST equality.

---

# 51. Source-to-JSON Round Trip

Add parser-backed tests.

Example:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

Test:

```text
source
→ lexer
→ parser
→ AST A
→ AST JSON
→ AST B

A == B
```

This is the first checkpoint where using the parser in serialization tests is appropriate.

---

# 52. Representative Round-Trip Programs

Test at least:

```kaj
let x = 10
```

```kaj
var price: Decimal = 19.99
```

```kaj
let x = -42
```

```kaj
let items = [1, 2, 3]
```

```kaj
let ages = {"Alice": 30}
```

```kaj
if ready {
    run()
} else {
    wait()
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
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

```kaj
fn normalize(var value: Decimal) -> Decimal {
    return value
}
```

Also include chained expression/call/member/index behavior that exists in Checkpoint 3.

---

# 53. Large Integer Round Trip

Explicitly test an integer beyond safe JavaScript integer range.

For example:

```kaj
let x = 999999999999999999999999999999999999
```

Ensure AST JSON stores it as a string and deserialization recovers exactly the same Python `int`.

---

# 54. Decimal Round Trip

Explicitly test:

```kaj
let x = 0.1
```

and:

```kaj
let x = 19.99
```

Ensure the JSON representation is a string and the resulting AST contains exact `Decimal` values.

Never compare via binary float.

---

# 55. Unicode Round Trip

Test:

```kaj
let greeting = "বাংলা 你好 👋"
```

Ensure JSON string output preserves readable Unicode and deserializes exactly.

---

# 56. Deterministic Output

For the same AST and serializer options, output must be deterministic.

Test:

```python
ast_to_json(program, indent=2)
```

twice and verify exact string equality.

Do not include timestamps, random IDs, memory addresses, or unstable ordering.

---

# 57. Stable Node Kinds

Node kind strings are part of the public AST JSON v1 contract.

Do not casually rename them.

Document them in:

```text
docs/compiler/ast-json.md
```

Create that documentation as part of this checkpoint.

---

# 58. Required Documentation

Create:

```text
docs/compiler/ast-json.md
```

It should explain:

- what AST JSON is
- that it represents the same internal AST as `.kaj` source
- top-level envelope
- versioning
- node `kind`
- spans
- exact integer/decimal string representation
- round-trip guarantee
- JSON Schema location
- that AST JSON is not compiler IR
- that semantic validation still occurs after loading
- that AST JSON from agents/tools is untrusted input

Keep it user/tooling-facing rather than documenting Python implementation internals.

---

# 59. Security / Trust Boundary

Treat AST JSON as untrusted external input.

Do not use:

```python
eval()
exec()
pickle
```

or dynamic class loading based on JSON data.

Node dispatch must use an explicit allowlist of supported kinds.

Deserialization itself must not execute Kaj code.

It only constructs AST data.

---

# 60. No AST Patch Format Yet

Do not implement:

```text
kaj patch JSON
node replacement operations
stable node IDs
insert/remove/reorder operations
```

Those are future agent tooling concerns.

Checkpoint 4 is full AST document serialization only.

---

# 61. No Stable Node IDs Yet

Do not add synthetic IDs to every AST node just because future patching may need them.

Stable IDs require their own design.

AST JSON v1 should serialize the AST structure currently present.

---

# 62. No Comments/Trivia Preservation

The lexer currently skips comments.

AST JSON therefore does not preserve comments.

Do not redesign lexer/AST trivia solely for this checkpoint.

Formatter/trivia work remains deferred.

---

# 63. No Original Source Lexemes

AST JSON represents semantic syntax structure.

Do not add original token lexemes for:

- integer formatting
- decimal formatting
- string escape spelling
- identifier spelling beyond the identifier name itself

unless the internal AST already preserves them.

For example:

```kaj
"hello\nworld"
```

and an equivalent future literal spelling may produce the same semantic string value.

AST JSON v1 is AST representation, not a lossless concrete syntax tree.

---

# 64. AST vs CST

Do not turn the AST into a Concrete Syntax Tree.

AST JSON does not need to preserve:

- whitespace
- comments
- exact parentheses
- token trivia
- original escape spellings

It must preserve semantic syntax structure and source spans.

---

# 65. Error API

Choose one clean deserialization failure API.

For example:

```python
class ASTJSONError(Exception):
    code: str
    message: str
    path: tuple[str | int, ...]
```

or a result object.

A JSON path is useful because source spans may not exist for malformed external JSON.

Example:

```text
program.statements[0].initializer.value
```

Do not expose an unreadable stack trace for normal invalid JSON input.

---

# 66. Error Paths

Where practical, include a structured field path for invalid documents.

Examples:

```text
$.version
$.program.kind
$.program.statements[0].initializer.value
```

Exact path syntax may be chosen by implementation, but keep it stable and useful.

---

# 67. Invalid JSON Tests

Test:

- syntactically invalid JSON
- missing `format`
- wrong `format`
- missing `version`
- unsupported version
- missing `program`
- unknown node kind
- missing required node field
- wrong field type
- invalid enum string
- invalid span
- invalid integer string
- invalid decimal string
- unknown extra field

These must fail cleanly.

---

# 68. Schema Tests

Validate emitted AST JSON against:

```text
schemas/ast/v1.json
```

for representative programs.

Also verify known-invalid documents fail schema validation.

Schema tests are part of Checkpoint 4 acceptance.

---

# 69. Avoid Code Generation for Now

Do not generate Python serializers from JSON Schema or vice versa unless there is already a stable project convention.

For v1, explicit serializer/deserializer code plus a hand-maintained schema is acceptable and easier to audit.

Keep tests ensuring they stay synchronized.

---

# 70. Performance

AST JSON is not currently a performance-critical runtime format.

Optimize for:

- correctness
- determinism
- clarity
- stable interoperability

Do not prematurely add binary encodings, streaming protocols, compression, or custom parsers.

---

# 71. CLI Scope

Do not redesign the CLI.

If the original pure-language implementation plan assigns a future:

```bash
kaj ast example.kaj
```

command to Checkpoint 4, it is acceptable to add a minimal command that emits canonical AST JSON for a valid source file.

However, only do so if it fits the current CLI architecture cleanly.

If implemented:

```bash
kaj ast example.kaj
```

should:

1. read source
2. lex
3. parse
4. report lexical/parser diagnostics if present
5. emit AST JSON only when an AST can be produced according to current frontend policy

Do not add `kaj run`, type checking, or semantic validation here.

If the active plan reserves CLI completion for later, leave the CLI unchanged.

---

# 72. Suggested Implementation Order

### Step 1 — Inspect

Read:

```text
docs/internals/ast.md
docs/language/lexical-structure.md
.dev/plans/pure-language-v0.md
src/kaj/ast/
src/kaj/parser/
src/kaj/source/
src/kaj/diagnostics/
```

### Step 2 — Freeze external kind/enums mapping

Define stable JSON v1 strings for:

```text
node kinds
binding kind
unary operators
binary operators
assignment operators
```

Keep these mappings explicit.

### Step 3 — Span conversion

Implement:

```text
SourceLocation ↔ JSON value
SourceSpan ↔ JSON value
```

with validation.

### Step 4 — Expression serialization

Implement literals, identifier, unary, binary, calls, member, index, lists, maps.

### Step 5 — Type expression serialization

Implement named/generic types.

### Step 6 — Statement/declaration serialization

Implement blocks, bindings, assignments, control flow, returns, functions, parameters.

### Step 7 — Program/document envelope

Implement:

```text
Program node
format/version envelope
```

### Step 8 — Deserialization

Implement strict inverse reconstruction.

### Step 9 — Error handling

Implement clean structured AST JSON errors and paths.

### Step 10 — JSON string helpers

Implement deterministic UTF-8-friendly JSON serialization/parsing.

### Step 11 — JSON Schema

Create:

```text
schemas/ast/v1.json
```

### Step 12 — Documentation

Create:

```text
docs/compiler/ast-json.md
```

### Step 13 — Round-trip tests

Test all major AST shapes.

### Step 14 — Parser-driven round trips

Test source → AST → JSON → AST.

### Step 15 — Invalid input/schema tests

Complete strict validation coverage.

### Step 16 — Quality gates

Run full repository validation.

### Step 17 — Update active plan

Update `.dev/plans/pure-language-v0.md`.

Do not proceed to Checkpoint 5.

---

# 73. Quality Requirements

All new Python must:

- use type annotations
- pass mypy
- pass Ruff
- pass pytest
- avoid arbitrary `Any` where practical
- avoid unsafe dynamic deserialization
- keep public JSON mappings explicit

Do not weaken mypy configuration to make serialization easier.

---

# 74. Existing Checkpoints Must Not Regress

All prior behavior must remain passing:

```text
Checkpoint 0 — bootstrap
Checkpoint 1 — lexer/source spans
Checkpoint 2 — AST
Checkpoint 3 — parser
```

Do not rewrite parser/AST semantics merely to fit JSON.

---

# 75. Update Active Development Plan

Update:

```text
.dev/plans/pure-language-v0.md
```

Record:

```text
Current checkpoint:
Checkpoint 4 — AST JSON

Status:
...

Completed:
...

AST JSON v1 decisions:
...

Known issues:
...

Verification:
...
```

Any public interchange decision established here should also be documented in:

```text
docs/compiler/ast-json.md
```

---

# 76. Verification Commands

Run:

```bash
pytest
ruff check .
mypy src
kaj --version
python -m kaj
```

If a `kaj ast` command is implemented, also verify it with a representative `.kaj` file.

All previous checkpoint tests must remain green.

---

# 77. Definition of Done

Checkpoint 4 is complete only when:

```text
[ ] serialization package exists
[ ] AST JSON v1 envelope implemented
[ ] format == "kaj-ast"
[ ] version == 1

[ ] every supported AST node has a stable `kind`
[ ] stable enum string mappings implemented

[ ] SourceLocation serialization implemented
[ ] SourceSpan serialization implemented
[ ] span validation implemented

[ ] integers serialize as decimal strings
[ ] arbitrary-precision integers round-trip exactly
[ ] decimals serialize as exact strings
[ ] Decimal round-trips exactly
[ ] Unicode strings round-trip exactly
[ ] booleans round-trip
[ ] NoneLiteral round-trips

[ ] expression nodes serialize/deserialize
[ ] list/map nodes serialize/deserialize
[ ] type-expression nodes serialize/deserialize
[ ] statement nodes serialize/deserialize
[ ] function/parameter nodes serialize/deserialize
[ ] Program serializes/deserializes

[ ] AST -> JSON value implemented
[ ] JSON value -> AST implemented
[ ] AST -> JSON text implemented
[ ] JSON text -> AST implemented

[ ] unknown node kinds rejected
[ ] unsupported versions rejected
[ ] missing fields rejected
[ ] invalid field types rejected
[ ] invalid enum values rejected
[ ] unknown extra fields rejected
[ ] malformed spans rejected
[ ] malformed integer/decimal strings rejected

[ ] structured AST JSON error model implemented
[ ] error paths included where practical

[ ] deterministic JSON output verified
[ ] no unsafe eval/pickle/dynamic class loading

[ ] schemas/ast/v1.json exists
[ ] schema covers all current node kinds
[ ] emitted documents validate against schema
[ ] invalid schema fixtures rejected

[ ] docs/compiler/ast-json.md exists
[ ] docs explain AST JSON is not compiler IR
[ ] docs explain versioning and exact number representation
[ ] docs explain untrusted-input boundary

[ ] direct AST round-trip tests pass
[ ] parser-driven source -> AST -> JSON -> AST tests pass
[ ] large integer round-trip test passes
[ ] decimal exactness test passes
[ ] Unicode round-trip test passes
[ ] invalid-document tests pass

[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] existing lexer/AST/parser tests remain passing
[ ] bootstrap CLI remains working

[ ] no AST patches implemented
[ ] no stable node IDs added
[ ] no compiler IR implemented
[ ] no name resolution implemented
[ ] no type checking implemented
[ ] no interpreter changes implemented
[ ] no agent/capability/asset features implemented

[ ] .dev/plans/pure-language-v0.md updated
```

---

# 78. Completion Report

When finished, report:

```text
Checkpoint 4 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

AST JSON version:
- 1

Node kinds supported:
- ...

Serialization implemented:
- ...

Deserialization implemented:
- ...

Validation/error model:
- ...

Schema:
- PASS/FAIL

Round-trip tests:
- direct AST: PASS/FAIL
- source -> AST -> JSON -> AST: PASS/FAIL
- large Int: PASS/FAIL
- Decimal exactness: PASS/FAIL
- Unicode: PASS/FAIL

Verification:
- pytest: PASS/FAIL
- ruff check .: PASS/FAIL
- mypy src: PASS/FAIL
- Kaj bootstrap CLI: PASS/FAIL

Decisions/deviations:
- ...

Known issues:
- ...
```

Do not declare Checkpoint 4 complete if any supported AST node cannot round-trip.

---

# 79. Final Constraint

Do **not** proceed to Checkpoint 5.

Checkpoint 4 ends with:

```text
.kaj source
    ↓
Lexer
    ↓
Parser
    ↓
Internal AST
    ⇅
AST JSON v1
```

The next checkpoint will add scope and name resolution separately.

AST JSON is an interchange representation of the AST.

It is **not** compiler IR, not runtime state, and not an AST patch protocol.
