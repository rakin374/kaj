# Kaj Scope and Name Resolution

**Status:** Authoritative for Kaj v0 Checkpoint 5  
**Scope:** Value-name scopes and lexical name resolution for the pure language core  
**Not covered:** type checking, type-name resolution, modules/import loading, runtime execution

---

## 1. Purpose

Name resolution determines what each identifier reference refers to.

Example:

```kaj
let x = 10

fn f(a: Int) -> Int {
    let y = x + a
    return y
}
```

The resolver establishes that:

```text
x in `x + a`
    → module binding `x`

a in `x + a`
    → parameter `a`

y in `return y`
    → local binding `y`
```

The resolver does not determine whether the resulting expressions are type-correct.

---

## 2. Pipeline Position

Checkpoint 5 extends the frontend pipeline to:

```text
Kaj source
    ↓
Lexer
    ↓
Parser
    ↓
AST
    ↓
Name Resolution
    ↓
Resolved references + diagnostics
```

AST JSON remains another way to construct the same AST:

```text
AST JSON
    ↓
AST
    ↓
Name Resolution
```

---

## 3. Lexical Scope Model

Kaj v0 has these value scopes:

```text
module scope
function scope
block scope
```

Scopes form a lexical parent chain.

A lookup begins in the current scope and walks outward until a matching declaration is found.

If no matching declaration exists, resolution fails with an unknown-name diagnostic.

---

## 4. Module Scope

A source unit has exactly one module scope.

Module-scope declarations currently relevant to name resolution are:

```text
function declarations
let bindings
var bindings
```

Function declarations are available throughout the module, including before their textual declaration.

Module bindings are **not** forward-visible.

Therefore:

```kaj
fn first() -> Int {
    return second()
}

fn second() -> Int {
    return 2
}
```

is valid.

But:

```kaj
let x = y
let y = 10
```

contains an unknown reference to `y` in the initializer for `x`.

---

## 5. Forward Function References

All top-level function names are predeclared in module scope before function bodies are resolved.

This supports:

- calling functions declared later
- self-recursion
- mutual recursion

Example:

```kaj
fn even(n: Int) -> Bool {
    return odd(n - 1)
}

fn odd(n: Int) -> Bool {
    return even(n - 1)
}
```

Both function references resolve successfully, assuming the syntax is otherwise valid.

Forward reference behavior applies to top-level functions only.

It does not make later module bindings forward-visible.

---

## 6. Function Scope

Every function declaration creates one function scope.

The function scope contains:

```text
parameters
direct declarations in the function body
```

The outermost body block of a function does **not** create an additional block scope beyond the function scope.

This means parameters and declarations directly inside the function body share the same scope.

Example:

```kaj
fn f(x: Int) -> Int {
    let x = 10
    return x
}
```

is invalid because `x` is declared twice in the same function scope.

To intentionally shadow the parameter, use a nested block-producing construct:

```kaj
fn f(x: Int) -> Int {
    if true {
        let x = 10
        return x
    }

    return x
}
```

The inner `x` belongs to the nested block scope.

---

## 7. Parameters

Function parameters are declarations in the function scope.

Parameters are visible throughout the function body.

Duplicate parameter names are not allowed.

Example:

```kaj
fn f(x: Int, x: Int) -> Int {
    return x
}
```

must produce a duplicate-name diagnostic.

Parameter mutability does not affect name resolution.

Both immutable and `var` parameters introduce one symbol.

---

## 8. Block Scope

Nested blocks introduced by control-flow constructs create child scopes.

This includes bodies of:

```text
if
else
while
for
```

Declarations inside a block are visible from their declaration point to the end of that block and in nested child scopes.

They are not visible outside the block.

Example:

```kaj
if ready {
    let x = 10
}

x
```

The final `x` is unresolved.

---

## 9. If / Else Scopes

Each `if` branch body has its own block scope.

Each `else` block also has its own block scope.

Example:

```kaj
if condition {
    let x = 1
} else {
    let x = 2
}
```

is valid because the two `x` bindings are in different sibling scopes.

Neither is visible after the `if`.

For `else if`, the nested condition is resolved in the surrounding scope, not inside the preceding `then` block.

---

## 10. While Scope

A `while` body creates a child block scope.

The condition is resolved in the surrounding scope.

Example:

```kaj
let ready = true

while ready {
    let value = 10
}
```

`ready` resolves from the outer scope.

`value` exists only inside the loop body.

---

## 11. For Scope

For:

```kaj
for item in items {
    ...
}
```

resolution occurs in this order:

1. resolve `items` in the enclosing scope
2. create the loop body block scope
3. declare `item` in that body scope
4. resolve the body statements

The loop variable is not visible while resolving the iterable expression.

The loop variable and direct declarations inside the loop body share the same block scope.

Therefore:

```kaj
for item in items {
    let item = 10
}
```

is a duplicate declaration.

---

## 12. Declaration Visibility Begins After Initializer Resolution

For `let` and `var`, resolve the initializer **before** inserting the new binding into the current scope.

Example:

```kaj
let x = x
```

does not make the new `x` self-referential.

If no outer `x` exists, the initializer reference is unknown.

If an outer `x` exists:

```kaj
let x = 10

if true {
    let x = x
}
```

the inner initializer resolves to the outer `x`, then the inner `x` is declared.

This rule applies to both `let` and `var`.

---

## 13. Shadowing

Shadowing is allowed across nested lexical scopes.

Example:

```kaj
let x = 10

if condition {
    let x = 20
}
```

The two declarations are distinct symbols.

The inner declaration shadows the outer declaration only within the inner scope.

Shadowing does not mutate or replace the outer symbol.

A future linter may warn about suspicious shadowing, but the resolver accepts it.

---

## 14. Same-Scope Duplicates

Two declarations with the same name in the same scope are invalid.

Examples:

```kaj
let x = 1
let x = 2
```

```kaj
var x = 1
let x = 2
```

```kaj
fn f() -> None {}
fn f() -> None {}
```

```kaj
fn f(x: Int, x: Int) -> Int {
    return x
}
```

All produce:

```text
RESOLVE_DUPLICATE_NAME
```

Kaj v0 uses one value namespace for:

```text
functions
bindings
parameters
loop variables
```

Therefore a same-scope function/binding name collision is also invalid.

---

## 15. Shadowing Functions

A nested local declaration may shadow a module-level function name.

Example:

```kaj
fn compute() -> Int {
    return 1
}

fn use() -> Int {
    let compute = 10
    return compute
}
```

The local `compute` resolves to the local binding.

The function symbol remains available outside that function scope.

---

## 16. Identifier References

`Identifier` expressions are value-name references and must be resolved.

Example:

```kaj
x
```

must resolve to a visible symbol or produce:

```text
RESOLVE_UNKNOWN_NAME
```

Declaration names themselves are not references.

For example, the `x` declared here:

```kaj
let x = 10
```

creates a symbol; it does not perform a lookup.

---

## 17. Member Names Are Not Lexical References

For:

```kaj
user.name
```

the resolver resolves:

```text
user
```

through lexical scope.

It does **not** resolve:

```text
name
```

as a lexical identifier.

Member existence is checked by later type/semantic analysis.

---

## 18. Named Argument Labels Are Not Lexical References

For:

```kaj
send(message, priority: 2)
```

the resolver resolves:

```text
send
message
```

as value references.

The label:

```text
priority
```

is not looked up in lexical scope.

Matching named arguments to function parameters occurs later.

---

## 19. Assignment Targets

Assignments resolve references inside their targets.

Examples:

```kaj
x = 1
```

resolve `x`.

```kaj
user.name = "A"
```

resolve `user`; `name` remains a member name.

```kaj
items[index] = value
```

resolve:

```text
items
index
value
```

Whether the resolved binding is mutable is not enforced by name resolution.

Mutability checking belongs to later semantic/type checking.

---

## 20. Function Calls

For:

```kaj
add(x, y)
```

the resolver resolves:

```text
add
x
y
```

It does not yet check:

- whether `add` is callable
- argument count
- argument types
- named argument compatibility
- return type

Those are later type-checker responsibilities.

---

## 21. Collection Literals

All expressions inside list and map literals are resolved normally.

Example:

```kaj
[key, value]
```

resolves both names.

For:

```kaj
{key: value}
```

both key and value expressions are resolved.

---

## 22. Control-Flow Conditions

Conditions and iterable expressions resolve in the scope surrounding their body.

Examples:

```kaj
if ready { ... }
while ready { ... }
for item in items { ... }
```

resolve:

```text
ready
ready
items
```

before entering the corresponding body scope.

---

## 23. Return Expressions

If a return has a value:

```kaj
return result
```

resolve `result` in the current lexical scope.

Whether `return` is valid in the current control-flow context is not a name-resolution concern.

---

## 24. Type Names Are Deferred

Checkpoint 5 resolves **value names only**.

It does not resolve names appearing in:

```text
NamedType
GenericType
function parameter type annotations
function return types
binding type annotations
```

Therefore:

```kaj
fn f(x: Int) -> UnknownType {
    return x
}
```

must not produce a value-name resolution error for `Int` or `UnknownType`.

Type-name resolution begins with the type-system checkpoints.

This separation prevents primitive types and future user-defined types from being incorrectly treated as value symbols.

---

## 25. No Implicit Builtins Yet

Checkpoint 5 defines no implicit value names such as:

```text
print
len
range
```

Unless a symbol is explicitly introduced by the current compilation environment, it is unresolved.

A future prelude/standard-library design may provide builtins.

The resolver implementation may support an optional injected outer/builtin scope if this can be done cleanly, but Checkpoint 5 must not silently hard-code speculative builtins.

---

## 26. Function Declaration Location

Named function declarations are module-level only in Kaj v0.

Nested named functions are not supported.

The resolver does not need to define nested-function declaration semantics during Checkpoint 5.

---

## 27. Symbol Model

The resolver should represent declarations with explicit symbols.

A symbol should contain enough information for later compiler passes.

Recommended information:

```text
symbol id
name
kind
declaration span
scope
```

Useful symbol kinds:

```text
FUNCTION
LET_BINDING
VAR_BINDING
PARAMETER
LOOP_VARIABLE
```

Symbol IDs are compiler-internal identities.

They are not AST JSON node IDs and are not part of the public Kaj AST JSON v1 format.

---

## 28. Symbol Identity

Two shadowing declarations with the same text name are distinct symbols.

Example:

```kaj
let x = 1

if condition {
    let x = 2
}
```

The module `x` and block `x` must have different symbol identities.

Identifier references should resolve to symbol identity, not merely to name strings.

This is necessary for later type checking and diagnostics.

---

## 29. Scope Model

A scope should contain conceptually:

```text
kind
parent
symbols_by_name
```

Scope kinds:

```text
MODULE
FUNCTION
BLOCK
```

Implementation may also track child scopes or numeric scope IDs for diagnostics/debugging.

Do not expose mutable symbol tables through public user-facing APIs.

---

## 30. Resolution Result

Name resolution must return both:

```text
resolved symbol information
diagnostics
```

A useful result may include:

```text
module scope
all symbols
identifier-reference → symbol associations
diagnostics
```

Do not mutate AST nodes to attach resolved symbols.

The Core AST remains syntax-only.

Use side tables or resolver-owned associations.

The type checker in later checkpoints should be able to consume these results.

---

## 31. Resolver Must Not Depend on Object Serialization

Do not use AST JSON as the internal resolution mechanism.

Whether the AST originated from `.kaj` parsing or AST JSON deserialization, the resolver operates on internal AST nodes.

---

## 32. Duplicate Diagnostic

Stable code:

```text
RESOLVE_DUPLICATE_NAME
```

The diagnostic should point to the duplicate declaration.

Where supported by the diagnostic framework, also include or reference the original declaration span.

Exact wording may vary.

Example message:

```text
Name 'x' is already declared in this scope.
```

---

## 33. Unknown Name Diagnostic

Stable code:

```text
RESOLVE_UNKNOWN_NAME
```

The diagnostic span must point to the unresolved identifier reference.

Example:

```kaj
let x = missing
```

The diagnostic should point to:

```text
missing
```

---

## 34. Resolution Continues After Errors

The resolver should collect multiple diagnostics where practical.

Example:

```kaj
let x = missing1
let y = missing2
```

should report both unresolved names rather than stopping after the first.

Duplicate declarations should also not crash or abort the entire pass.

---

## 35. Duplicate Recovery

After a duplicate declaration, keep the original symbol as the active symbol for that scope.

Do not silently replace it with the duplicate.

This provides deterministic behavior for subsequent references and prevents later declarations from rewriting symbol identity.

Example:

```kaj
let x = 1
let x = 2
x
```

produces a duplicate diagnostic for the second declaration.

The final `x` resolves to the first declaration's symbol.

---

## 36. Unknown-Name Recovery

An unresolved identifier produces a diagnostic but resolution continues into subsequent expressions/statements.

Do not create a fake ordinary user declaration to hide the error.

If a dedicated unresolved/error symbol is useful internally for later passes, it must be clearly distinguished from valid symbols.

---

## 37. Function Predeclaration Pass

Resolution of a module uses at least these conceptual stages:

```text
1. create module scope

2. scan top-level statements for function declarations
   and predeclare function symbols

3. resolve top-level statements in source order

4. resolve function bodies with their function scopes
   according to source traversal
```

Equivalent implementations are acceptable if they preserve the defined visibility rules:

```text
functions: forward-visible
bindings: visible only after declaration
```

---

## 38. Module Binding Ordering

For module bindings:

```kaj
let a = 1
let b = a
```

`a` resolves successfully in `b`.

For:

```kaj
let b = a
let a = 1
```

the first `a` is unknown.

The same source-order rule applies to `var`.

---

## 39. Function Access to Module Bindings

A function body may reference module bindings that are already visible according to module source order at the function declaration point.

Example:

```kaj
let x = 10

fn f() -> Int {
    return x
}
```

is valid.

For:

```kaj
fn f() -> Int {
    return x
}

let x = 10
```

`x` is not forward-visible merely because it is module-level.

Therefore the reference inside `f` is unresolved in Kaj v0.

This preserves the explicit rule that only functions receive forward-reference behavior.

---

## 40. Recursion

A function may resolve its own name:

```kaj
fn factorial(n: Int) -> Int {
    return factorial(n - 1)
}
```

because all top-level function symbols are predeclared.

---

## 41. Mutual Recursion

Mutual recursion is valid:

```kaj
fn a() -> None {
    b()
}

fn b() -> None {
    a()
}
```

Both names resolve through module function predeclaration.

---

## 42. Function Parameter Resolution

When resolving a function:

```text
1. create function scope whose parent is the module scope
2. declare all parameters
3. resolve the function body's direct statements in that same function scope
4. create child block scopes only for nested blocks/control-flow bodies
```

This rule is authoritative for v0.

---

## 43. Resolution of Binding Initializers

For:

```kaj
let name: Type = initializer
```

Checkpoint 5:

1. ignores `Type` for value-name resolution
2. resolves `initializer` in the current scope
3. attempts to declare `name`

If `name` duplicates an existing same-scope declaration, emit `RESOLVE_DUPLICATE_NAME`.

---

## 44. Resolution of Function Declarations at Top Level

A top-level function declaration's name is already present from predeclaration.

When the source-order traversal reaches the function declaration:

- do not redeclare it as a second symbol
- resolve its body using the existing function symbol
- create its function scope
- declare its parameters
- resolve its statements

---

## 45. Source Spans

Symbols should preserve declaration spans.

Resolved references preserve the original AST identifier spans.

All resolver diagnostics use existing AST/source spans.

Do not invent new coordinate conventions.

Checkpoint 1 remains authoritative:

```text
offset zero-based
line/column one-based
end exclusive
```

---

## 46. No Mutation Analysis Yet

Name resolution does not reject:

```kaj
let x = 1
x = 2
```

because determining whether assignment is allowed based on mutability is a later semantic check.

The resolver only establishes that assignment target `x` refers to the `let` symbol.

---

## 47. No Type Checking Yet

Name resolution does not reject:

```kaj
let x = 1
let y = x + "hello"
```

if all names resolve.

Type compatibility is handled later.

---

## 48. No Control-Flow Legality Yet

Name resolution does not reject:

```kaj
break
continue
return 1
```

based solely on context.

Those checks belong to later semantic/control-flow analysis.

---

## 49. No Module Import Resolution Yet

Although `import` is lexically reserved, full import/module resolution is deferred.

Checkpoint 5's "module scope" means the lexical top-level scope of one source unit.

It does not load other files/packages.

---

## 50. Source of Truth

For Kaj v0 name resolution:

```text
docs/internals/name-resolution.md
        +
resolver tests
        +
resolver implementation
```

must agree.

If they disagree, that inconsistency is a project bug.

---

## 51. Conformance Cases

The resolver must accept:

```kaj
let x = 10
let y = x
```

It must reject:

```kaj
let y = x
let x = 10
```

It must accept:

```kaj
fn first() -> Int {
    return second()
}

fn second() -> Int {
    return 2
}
```

It must accept recursion:

```kaj
fn recurse() -> None {
    recurse()
}
```

It must accept nested shadowing:

```kaj
let x = 1

if true {
    let x = 2
}
```

It must reject same-scope duplicates:

```kaj
let x = 1
let x = 2
```

It must reject parameter/direct-body duplication:

```kaj
fn f(x: Int) -> Int {
    let x = 1
    return x
}
```

It must accept shadowing inside a nested control-flow block:

```kaj
fn f(x: Int) -> Int {
    if true {
        let x = 1
        return x
    }

    return x
}
```

---

## 52. Checkpoint 5 Definition of Done

Checkpoint 5 is complete when:

```text
[ ] module scope implemented
[ ] function scope implemented
[ ] block scope implemented
[ ] lexical parent lookup implemented

[ ] symbol model implemented
[ ] unique compiler-internal symbol identity implemented
[ ] function symbols implemented
[ ] let/var symbols implemented
[ ] parameter symbols implemented
[ ] loop-variable symbols implemented

[ ] top-level functions predeclared
[ ] forward function references resolve
[ ] self recursion resolves
[ ] mutual recursion resolves
[ ] module bindings remain source-order visible only

[ ] binding initializer resolves before declaration
[ ] function parameters declared before body resolution
[ ] function body direct declarations share parameter scope
[ ] nested control-flow bodies create block scopes
[ ] for iterable resolved before loop variable declaration
[ ] for loop variable scoped to body

[ ] same-scope duplicates diagnosed
[ ] nested shadowing allowed
[ ] duplicate recovery keeps original symbol
[ ] unknown names diagnosed
[ ] multiple resolver errors can be collected

[ ] identifier expressions resolve to symbol identity
[ ] member names are not lexical lookups
[ ] named argument labels are not lexical lookups
[ ] assignment targets resolve contained value references
[ ] type names are not resolved in Checkpoint 5

[ ] AST is not mutated with semantic information
[ ] resolution side tables/results available for later passes

[ ] resolver tests pass
[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes

[ ] lexer/parser/AST JSON tests remain passing
[ ] no type checker implemented
[ ] no interpreter work added
[ ] no import loader added
[ ] no agent/capability/asset behavior added
```
