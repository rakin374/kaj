# Kaj Checkpoint 5 — Scope and Name Resolution

**Audience:** Codex / implementation agent  
**Checkpoint:** 5  
**Goal:** Implement lexical scopes, symbol tables, duplicate detection, and identifier resolution.

---

## 1. Primary Instruction

Implement **Checkpoint 5 only**.

Before editing code, read:

```text
docs/internals/name-resolution.md
docs/internals/ast.md
docs/compiler/ast-json.md
docs/language/lexical-structure.md
dev/plans/pure-language-v0.md
```

Inspect the completed lexer, AST, parser, and AST JSON implementations.

Treat:

```text
docs/internals/name-resolution.md
```

as authoritative for Checkpoint 5 behavior.

Do not invent different scope semantics.

Do not begin the primitive type system or interpreter.

---

## 2. Goal

After this checkpoint, Kaj must know what value declaration each identifier refers to.

Example:

```kaj
let x = 10

fn f(a: Int) -> Int {
    let y = x + a
    return y
}
```

Resolution must establish:

```text
x → module binding x
a → parameter a
y → local binding y
```

Unknown names and duplicate same-scope declarations must produce structured diagnostics.

---

## 3. Required Scope Semantics

Implement exactly:

```text
module scope
function scope
block scope
```

Lookup walks from current scope outward.

Shadowing across nested scopes is legal.

Duplicates within the same scope are illegal.

---

## 4. Function Body Scope Rule

This rule is important:

> Function parameters and declarations directly inside the function body belong to the same function scope.

Do not create an extra block scope for the outer function body.

Therefore this is invalid:

```kaj
fn f(x: Int) -> Int {
    let x = 1
    return x
}
```

Nested control-flow bodies do create child block scopes.

---

## 5. Module Visibility Rule

Top-level functions are forward-visible throughout the module.

Top-level `let`/`var` bindings are visible only after their declaration.

Therefore:

```kaj
fn a() -> None {
    b()
}

fn b() -> None {}
```

resolves.

But:

```kaj
let x = y
let y = 1
```

does not.

Likewise:

```kaj
fn f() -> Int {
    return x
}

let x = 10
```

must report `x` as unresolved.

Do not accidentally make all module declarations hoisted.

---

## 6. Recommended Repository Structure

Add:

```text
src/kaj/
└── semantic/
    ├── __init__.py
    ├── symbols.py
    ├── scope.py
    └── resolver.py
```

If the repository already has a `semantic/` package, extend it.

Do not create a generic compiler-pass framework solely for this checkpoint.

Add tests:

```text
tests/
└── semantic/
    ├── test_module_scope.py
    ├── test_function_scope.py
    ├── test_block_scope.py
    ├── test_shadowing.py
    ├── test_duplicates.py
    ├── test_unknown_names.py
    ├── test_forward_functions.py
    ├── test_for_scope.py
    ├── test_resolution_map.py
    └── test_resolver_recovery.py
```

---

## 7. Symbol Model

Implement explicit compiler-internal symbols.

Recommended enum:

```text
SymbolKind
    FUNCTION
    LET_BINDING
    VAR_BINDING
    PARAMETER
    LOOP_VARIABLE
```

Each symbol should contain at least:

```text
id
name
kind
declaration span
```

A scope identity/reference may also be stored if useful.

Symbol IDs must uniquely distinguish shadowed declarations.

They are internal compiler IDs only.

Do not add them to AST JSON v1.

---

## 8. Scope Model

Implement:

```text
ScopeKind
    MODULE
    FUNCTION
    BLOCK
```

A scope contains conceptually:

```text
kind
parent
symbols_by_name
```

Provide operations such as:

```text
declare
lookup_local
lookup
```

`lookup` walks parents.

`declare` checks same-scope duplicates only.

---

## 9. Duplicate Behavior

Stable diagnostic:

```text
RESOLVE_DUPLICATE_NAME
```

When a duplicate is encountered:

- report the duplicate declaration
- keep the original symbol active
- do not replace it

Example:

```kaj
let x = 1
let x = 2
x
```

The second declaration is diagnosed.

The final `x` resolves to the first symbol.

---

## 10. Unknown Name Behavior

Stable diagnostic:

```text
RESOLVE_UNKNOWN_NAME
```

Example:

```kaj
let x = missing
```

The diagnostic span must point at the `missing` identifier expression.

Continue resolving after the error.

---

## 11. Resolution Result

Do not mutate AST nodes.

Return a resolution result containing enough data for the future type checker.

It should conceptually expose:

```text
module scope
symbols
identifier-reference → symbol associations
diagnostics
```

A dedicated `ResolutionResult` is recommended.

The exact side-table implementation may vary.

Avoid keying public behavior only by identifier text because shadowing requires symbol identity.

If identity-based node lookup is used internally, keep it encapsulated behind the resolution result API.

---

## 12. Function Predeclaration

Before normal module resolution, scan top-level statements and predeclare all top-level function symbols.

This supports:

```text
forward function references
self recursion
mutual recursion
```

Do not predeclare module `let`/`var` bindings.

---

## 13. Top-Level Traversal

Resolve module statements in source order.

For a top-level binding:

```text
1. resolve initializer
2. declare binding
```

For a function declaration:

```text
1. function symbol already exists from predeclaration
2. create function scope
3. declare parameters
4. resolve direct body statements in same function scope
```

---

## 14. Binding Resolution

For:

```kaj
let x: Int = expression
```

or:

```kaj
var x = expression
```

perform:

```text
resolve expression
declare x
```

Do not resolve the type annotation in Checkpoint 5.

This preserves the rule:

```kaj
let x = x
```

resolves the initializer to an outer `x`, or reports unknown if no outer `x` exists.

---

## 15. Function Parameters

Declare parameters before resolving the body.

Duplicate parameters produce:

```text
RESOLVE_DUPLICATE_NAME
```

Direct body declarations share the same function scope and therefore also conflict with parameter names.

Parameter mutability does not change resolution behavior.

---

## 16. Nested Blocks

For bodies of:

```text
if
else
while
for
```

create a new block scope.

Resolve child statements inside it.

Sibling blocks do not share declarations.

---

## 17. For Loop

For:

```kaj
for item in items {
    body
}
```

perform:

```text
resolve `items` in enclosing scope
create body block scope
declare `item` as LOOP_VARIABLE
resolve body in that block scope
```

The loop variable is not visible in the iterable expression.

A direct body declaration named `item` is a same-scope duplicate.

---

## 18. If / Else If

Resolve the condition in the current/enclosing scope.

Resolve the `then` block in a new block scope.

Resolve an `else` block in its own block scope.

For `else if`, resolve the nested `IfStatement` in the original surrounding scope, not in the `then` block scope.

---

## 19. While

Resolve the condition in the surrounding scope.

Resolve the body in a new block scope.

---

## 20. Expressions

Resolve recursively.

### Identifier

Lookup through the lexical scope chain and associate the identifier with the resulting symbol.

If missing, emit `RESOLVE_UNKNOWN_NAME`.

### Unary/Binary

Resolve operand/children.

### Call

Resolve:

```text
callee
argument values
```

Do not resolve named argument labels.

### Member Access

Resolve the object expression.

Do not resolve the member string as a lexical name.

### Index

Resolve object and index expressions.

### List

Resolve every element.

### Map

Resolve every key and value expression.

---

## 21. Assignments

Resolve the target expression and right-hand value.

For:

```kaj
user.name = value
```

resolve `user` and `value`.

Do not lexically resolve `name`.

Do not enforce `let` vs `var` assignment legality yet.

---

## 22. Return

Resolve its value expression when present.

Do not check function-return legality in this checkpoint.

---

## 23. Type Expressions

Do not resolve:

```text
NamedType
GenericType
```

during Checkpoint 5.

Do not report:

```text
Int
String
Decimal
List
Map
Optional
Result
User
```

as unknown value names merely because they occur in type positions.

Type-name resolution belongs to the upcoming type-system work.

---

## 24. No Implicit Builtins

Do not hard-code:

```text
print
len
range
```

or other names into the resolver.

If an optional externally supplied prelude/builtin scope fits cleanly, it may be supported, but tests for core Checkpoint 5 should not depend on speculative builtins.

Unknown ordinary identifiers remain errors.

---

## 25. Resolver Diagnostics

Use the project's existing diagnostic model.

Required stable codes:

```text
RESOLVE_DUPLICATE_NAME
RESOLVE_UNKNOWN_NAME
```

If the diagnostic system supports related locations, duplicate diagnostics should reference the original declaration.

Do not redesign all diagnostics just for this feature.

---

## 26. Error Recovery

Collect multiple diagnostics.

Example:

```kaj
let a = missing_a
let b = missing_b
```

should report both.

Resolver traversal must continue after unknown names and duplicates.

Never crash because a referenced symbol is absent.

---

## 27. Required Tests — Module Scope

Test:

```kaj
let x = 1
let y = x
```

passes.

Test:

```kaj
let y = x
let x = 1
```

reports `RESOLVE_UNKNOWN_NAME`.

Test same-scope top-level duplicates.

Test top-level function/binding name collision.

---

## 28. Required Tests — Functions

Test forward reference:

```kaj
fn a() -> None {
    b()
}

fn b() -> None {}
```

Test recursion:

```kaj
fn a() -> None {
    a()
}
```

Test mutual recursion.

Test parameter resolution.

Test duplicate parameters.

Test direct-body local conflicting with parameter.

Test function referencing earlier module binding.

Test function referencing later module binding and confirm it is unresolved.

---

## 29. Required Tests — Shadowing

Test:

```kaj
let x = 1

if true {
    let x = 2
    x
}

x
```

The two references must resolve to different symbols.

Test parameter shadowing in nested block is valid.

Test same-scope duplicate remains invalid.

---

## 30. Required Tests — Binding Initializer Order

Test:

```kaj
let x = x
```

with no outer `x` → unknown.

Test:

```kaj
let x = 1

if true {
    let x = x
}
```

The initializer's `x` must resolve to the outer symbol.

---

## 31. Required Tests — Block Escape

Test:

```kaj
if true {
    let hidden = 1
}

hidden
```

The final name must be unresolved.

Likewise for `while` and `for` body locals.

---

## 32. Required Tests — For Loop

Test iterable lookup happens outside body scope.

Test loop variable resolves in body.

Test loop variable is unavailable after loop.

Test same-scope redeclaration of loop variable in body produces duplicate diagnostic.

Test an outer symbol with the same name may be shadowed by the loop variable.

---

## 33. Required Tests — Member and Named Arguments

For member access:

```kaj
user.name
```

only `user` is a lexical reference.

For named call:

```kaj
send(message, priority: value)
```

resolve:

```text
send
message
value
```

Do not attempt lexical lookup for `priority`.

---

## 34. Required Tests — Resolution Identity

Construct a shadowing program and assert identifier references bind to the correct distinct symbol IDs.

Do not merely assert that both resolved names equal `"x"`.

The resolver must preserve declaration identity.

---

## 35. Required Tests — Multiple Errors

Use a program with several independent unknown names and duplicates.

Verify the resolver collects multiple diagnostics in deterministic traversal order.

---

## 36. AST JSON Compatibility

Resolution must work equally on an AST produced by:

```text
parser
```

and the structurally equivalent AST produced by:

```text
AST JSON deserializer
```

A focused integration test should round-trip source through AST JSON, then resolve it and confirm equivalent symbol relationships/diagnostics.

Do not put resolution information into AST JSON.

---

## 37. Suggested Implementation Order

### Step 1

Inspect:

```text
docs/internals/name-resolution.md
src/kaj/ast/
src/kaj/parser/
src/kaj/serialization/
src/kaj/diagnostics/
dev/plans/pure-language-v0.md
```

### Step 2

Implement symbol and scope enums/data structures.

### Step 3

Implement same-scope declaration and lexical lookup.

### Step 4

Implement `ResolutionResult` / side-table API.

### Step 5

Implement module function predeclaration.

### Step 6

Implement module source-order traversal and binding declaration ordering.

### Step 7

Implement function scopes and parameter declaration.

### Step 8

Implement nested block scope handling.

### Step 9

Implement expression/reference traversal.

### Step 10

Implement `for` loop special ordering.

### Step 11

Implement duplicate/unknown diagnostics and recovery.

### Step 12

Add complete unit/conformance tests.

### Step 13

Add AST JSON integration resolution test.

### Step 14

Run all quality gates.

### Step 15

Update:

```text
dev/plans/pure-language-v0.md
```

Do not begin Checkpoint 6.

---

## 38. Verification

Run:

```bash
pytest
ruff check .
mypy src
kaj --version
python -m kaj
```

All earlier checkpoint tests must remain green.

---

## 39. Definition of Done

Checkpoint 5 is complete only when:

```text
[ ] docs/internals/name-resolution.md treated as authoritative

[ ] semantic resolver package exists
[ ] SymbolKind implemented
[ ] ScopeKind implemented
[ ] Symbol implemented
[ ] unique symbol IDs implemented
[ ] Scope implemented
[ ] local duplicate detection implemented
[ ] parent-chain lookup implemented

[ ] ResolutionResult / equivalent implemented
[ ] identifier-reference → symbol association available
[ ] AST nodes remain syntax-only and unmodified

[ ] module scope implemented
[ ] function scope implemented
[ ] block scope implemented

[ ] top-level function predeclaration implemented
[ ] forward function references resolve
[ ] self recursion resolves
[ ] mutual recursion resolves

[ ] top-level let/var remain source-order visible
[ ] later module binding is not forward-visible
[ ] function cannot see later module binding solely due to hoisting

[ ] binding initializer resolves before declaration
[ ] parameter declaration occurs before body resolution
[ ] function body shares parameter scope
[ ] nested control-flow bodies create scopes

[ ] for iterable resolves before loop variable declaration
[ ] loop variable scoped to body
[ ] loop-variable duplicates detected

[ ] nested shadowing works
[ ] same-scope duplicates diagnosed
[ ] duplicate recovery keeps original symbol

[ ] unknown identifiers diagnosed
[ ] multiple diagnostics collected
[ ] member labels are not lexical lookups
[ ] named argument labels are not lexical lookups
[ ] type names are ignored by value-name resolver

[ ] module scope tests pass
[ ] function scope tests pass
[ ] block scope tests pass
[ ] shadowing tests pass
[ ] duplicate tests pass
[ ] unknown-name tests pass
[ ] forward-function tests pass
[ ] symbol identity tests pass
[ ] AST JSON integration test passes

[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] bootstrap CLI remains working
[ ] all Checkpoints 1–4 tests remain passing

[ ] no type checking added
[ ] no runtime/interpreter work added
[ ] no module loader/import resolution added
[ ] no builtins hard-coded
[ ] no resolution data added to AST JSON
[ ] no agent/capability/asset features added

[ ] dev/plans/pure-language-v0.md updated
```

---

## 40. Completion Report

When finished, report:

```text
Checkpoint 5 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

Scope model:
- ...

Symbol kinds:
- ...

Forward reference behavior:
- ...

Diagnostics:
- ...

Tests added:
- ...

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

Do not proceed to Checkpoint 6.
