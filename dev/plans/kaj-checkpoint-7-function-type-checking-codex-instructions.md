# Kaj Checkpoint 7 — Function Type Checking

**Audience:** Codex / implementation agent  
**Checkpoint:** 7  
**Goal:** Add static function signatures, calls, argument checking, return checking, recursion support, `var` parameters, and missing-return analysis.

---

## 1. Primary Instruction

Implement **Checkpoint 7 only**.

Before editing code, read:

```text
docs/language/functions.md
docs/language/primitive-types.md
docs/internals/name-resolution.md
docs/internals/ast.md
docs/compiler/ast-json.md
dev/plans/pure-language-v0.md
```

Inspect the completed Checkpoint 6 type checker and Checkpoint 5 resolver.

Treat:

```text
docs/language/functions.md
```

as authoritative for function type-checking semantics.

Do not begin Checkpoint 8 interpreter/runtime work.

---

## 2. Acceptance Target

This must pass:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

Valid calls must type-check:

```kaj
let x = add(1, 2)
```

Wrong arguments must fail:

```kaj
let x = add(1, "2")
```

Wrong returns must fail:

```kaj
fn bad() -> Int {
    return "hello"
}
```

Non-`None` functions that may fall through must fail.

---

## 3. Extend the Semantic Type Model

Add an explicit function signature/type representation.

Recommended shape:

```text
FunctionType
    parameters: tuple[FunctionParameterType, ...]
    return_type: SemanticType
```

Each parameter entry should preserve:

```text
name
type
mutable
```

Do not encode signatures as raw strings.

---

## 4. Signature Prepass

Before checking any function body:

1. walk top-level function declarations
2. resolve parameter and return type annotations
3. construct function signatures
4. assign each signature to the function's resolver symbol

This must happen for **all top-level functions first**.

Then check bodies.

Required for:

```text
self recursion
mutual recursion
forward function references
```

---

## 5. Unknown Signature Types

For unknown parameter/return annotation names, emit:

```text
TYPE_UNKNOWN_TYPE
```

Use the existing internal error type to keep the signature usable enough for recovery.

Do not use `Any`.

---

## 6. Parameter Symbol Types

When entering a function body, associate each parameter symbol with its declared semantic type.

This must happen before any body expression is checked.

Example:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

Inside the body:

```text
a -> Int
b -> Int
```

---

## 7. Parameter Mutability

Reuse Checkpoint 6 mutation rules.

Default parameter:

```kaj
fn f(x: Int) -> Int {
    x = 1
    return x
}
```

→ `ASSIGN_TO_IMMUTABLE`

Mutable parameter:

```kaj
fn f(var x: Int) -> Int {
    x = x + 1
    return x
}
```

valid.

Do not implement caller mutation/pass-by-reference.

`var` means the local parameter binding is reassignable.

---

## 8. Function Call Typing

When visiting a `CallExpression`:

1. type the callee expression
2. verify it is callable / has `FunctionType`
3. map call arguments to parameters
4. type each argument expression
5. check assignability
6. record call expression type = declared return type

Use resolver identity and existing expression-type infrastructure.

---

## 9. Positional Argument Mapping

Map positional arguments in source order to parameters in declaration order.

Example:

```kaj
fn f(a: Int, b: String) -> None {}
f(1, "x")
```

maps:

```text
1 -> a
"x" -> b
```

---

## 10. Named Argument Mapping

Map a named argument by exact parameter name.

Example:

```kaj
fn send(message: String, priority: Int) -> None {}

send(message: "hello", priority: 2)
```

valid.

Unknown labels:

```text
TYPE_UNKNOWN_NAMED_ARGUMENT
```

---

## 11. Mixed Arguments

Support:

```kaj
send("hello", priority: 2)
```

The parser already ensures positional arguments do not follow named ones.

The type checker still must correctly map all supplied arguments.

Do not reorder the AST.

---

## 12. Duplicate Argument Binding

Detect when one parameter receives more than one argument.

Example:

```kaj
send("hello", message: "again", priority: 2)
```

→

```text
TYPE_DUPLICATE_ARGUMENT
```

Keep argument checking deterministic.

---

## 13. Missing Arguments

All parameters are required.

After mapping provided arguments, any unmapped parameter produces:

```text
TYPE_MISSING_ARGUMENT
```

One diagnostic per call is acceptable if it clearly reports all missing names.

No default parameters.

---

## 14. Too Many Arguments

Extra positional arguments beyond the parameter list produce:

```text
TYPE_TOO_MANY_ARGUMENTS
```

Do not silently discard them.

Still type-check their expressions where practical so nested errors can be found.

---

## 15. Argument Type Checking

Use Checkpoint 6 assignability:

```text
same type -> valid
Int -> Decimal -> valid
everything else -> invalid
```

Wrong type:

```text
TYPE_MISMATCH
```

Example:

```kaj
fn f(x: Int) -> Int {
    return x
}

f(2.5)
```

→ `TYPE_MISMATCH`

---

## 16. Call Result Type

For a known validly declared function:

```text
CallExpression type = function return type
```

Even if an argument mismatch exists, retaining the known return type is recommended to prevent cascades.

Example:

```kaj
fn f(x: Int) -> String {
    return "ok"
}

let y = f("bad")
```

Report the argument mismatch, but `f(...)` may remain statically `String`.

---

## 17. Non-Callable Call

Example:

```kaj
let x = 10
x()
```

→

```text
TYPE_NOT_CALLABLE
```

Do not infer a fake function type.

---

## 18. Return Checking Context

Track the currently enclosing function while checking its body.

For every `ReturnStatement`, compare against that function's declared return type.

Do not use raw function names for this; retain semantic function context/signature.

---

## 19. Return With Value

For:

```kaj
fn f() -> T {
    return expr
}
```

infer `expr` and check assignability to `T`.

Use existing promotion rules.

Valid:

```kaj
fn f() -> Decimal {
    return 10
}
```

Invalid:

```kaj
fn f() -> Int {
    return 2.5
}
```

→ `TYPE_MISMATCH`

---

## 20. Bare Return

Bare return:

```kaj
return
```

valid only when enclosing return type is `None`.

For non-`None`, emit:

```text
TYPE_MISMATCH
```

Do not invent a separate required diagnostic unless the project already has one.

---

## 21. Return Value in None Function

Valid:

```kaj
fn f() -> None {
    return none
}
```

Invalid:

```kaj
fn f() -> None {
    return 1
}
```

→ `TYPE_MISMATCH`

---

## 22. Return Outside Function

If a return exists outside a function:

```kaj
return 1
```

emit:

```text
TYPE_RETURN_OUTSIDE_FUNCTION
```

Do not crash due to missing function context.

---

## 23. Missing Return

For every function with return type other than `None`, perform conservative structural definite-return analysis.

If the body may reach its end, emit:

```text
TYPE_MISSING_RETURN
```

---

## 24. Definite Return Rules

Implement:

### Return statement

```text
return ...
```

→ definitely returns.

### Sequential block

A block definitely returns if traversal reaches a statement that definitely returns.

No unreachable-code diagnostic required.

### If

Definitely returns iff:

```text
then branch definitely returns
AND
else branch exists
AND
else branch definitely returns
```

### Else-if

Treat recursively.

### While

Never assume definitely returning in Checkpoint 7.

### For

Never assume definitely returning in Checkpoint 7.

### None function

No definite return required.

Do not build a full CFG solely for this checkpoint.

---

## 25. Required Missing-Return Tests

Valid:

```kaj
fn f() -> Int {
    return 1
}
```

Valid:

```kaj
fn f(x: Bool) -> Int {
    if x {
        return 1
    } else {
        return 2
    }
}
```

Invalid:

```kaj
fn f(x: Bool) -> Int {
    if x {
        return 1
    }
}
```

→ `TYPE_MISSING_RETURN`

Invalid:

```kaj
fn f() -> Int {
    while true {
        return 1
    }
}
```

may still produce `TYPE_MISSING_RETURN` under the frozen conservative v0 rule.

Valid:

```kaj
fn f() -> None {
}
```

---

## 26. Recursion

Self recursion must work:

```kaj
fn factorial(n: Int) -> Int {
    if n == 0 {
        return 1
    } else {
        return n * factorial(n - 1)
    }
}
```

The function signature must exist before body checking.

---

## 27. Mutual Recursion

Test:

```kaj
fn even(n: Int) -> Bool {
    if n == 0 {
        return true
    } else {
        return odd(n - 1)
    }
}

fn odd(n: Int) -> Bool {
    if n == 0 {
        return false
    } else {
        return even(n - 1)
    }
}
```

Both must type-check.

---

## 28. Forward Function Reference

Test:

```kaj
fn first() -> Int {
    return second()
}

fn second() -> Int {
    return 2
}
```

must pass.

This depends on both:

```text
Checkpoint 5 function name predeclaration
Checkpoint 7 function signature predeclaration
```

---

## 29. No Overloads

Do not implement overload resolution.

Duplicate function declarations remain resolver errors.

---

## 30. No Defaults / Variadics / Generics

Do not add:

```text
default parameter values
variadic parameters
generic functions
type variables
overload sets
```

These are out of scope.

---

## 31. Function Identifier Expressions

A resolved declared function identifier may have its semantic `FunctionType`.

This is enough for call checking.

Do not expand Checkpoint 7 into a full higher-order function design.

---

## 32. Call Argument → Parameter Mapping

Add a semantic side table if useful:

```text
CallArgument node -> parameter descriptor/index
```

This is especially valuable for named arguments and later lowering/runtime.

Do not rewrite or reorder AST argument lists.

---

## 33. Diagnostics

Required codes:

```text
TYPE_MISMATCH
TYPE_NOT_CALLABLE
TYPE_UNKNOWN_NAMED_ARGUMENT
TYPE_DUPLICATE_ARGUMENT
TYPE_MISSING_ARGUMENT
TYPE_TOO_MANY_ARGUMENTS
TYPE_MISSING_RETURN
TYPE_RETURN_OUTSIDE_FUNCTION
```

Continue existing:

```text
TYPE_UNKNOWN_TYPE
ASSIGN_TO_IMMUTABLE
TYPE_INVALID_OPERATOR
TYPE_CONDITION_NOT_BOOL
```

Keep diagnostics deterministic and span-aware.

---

## 34. Error Recovery

Continue checking after function errors.

Examples:

- bad argument does not stop remaining argument checks
- bad return does not stop remaining function body checks
- bad function body does not prevent later functions from being checked
- bad signature annotation does not crash recursion handling
- non-callable expression yields error type and continues

Use the existing internal error type.

---

## 35. Suggested Files

Likely extend:

```text
src/kaj/semantic/types.py
src/kaj/semantic/type_checker.py
```

Optionally add:

```text
src/kaj/semantic/function_types.py
```

only if it materially improves organization.

Do not fragment the implementation unnecessarily.

Tests may include:

```text
tests/semantic/
├── test_function_signatures.py
├── test_function_calls.py
├── test_named_arguments.py
├── test_function_returns.py
├── test_missing_returns.py
├── test_recursion.py
├── test_mutable_parameters.py
└── test_function_type_errors.py
```

Follow existing repository conventions.

---

## 36. Required Tests — Signature Formation

Verify:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

produces a function signature preserving:

```text
a / Int / immutable
b / Int / immutable
return Int
```

Test:

```kaj
fn normalize(var value: Decimal) -> Decimal {
    return value
}
```

preserves parameter mutability.

---

## 37. Required Tests — Calls

Valid positional call.

Valid all-named call.

Valid mixed positional + named call.

Wrong argument type.

Missing argument.

Too many positional arguments.

Unknown named argument.

Duplicate parameter binding.

Call to non-function.

Call result type.

---

## 38. Required Tests — Promotion

Test:

```kaj
fn f(x: Decimal) -> Decimal {
    return x
}

let y = f(10)
```

valid.

Test:

```kaj
fn f() -> Decimal {
    return 10
}
```

valid.

Reject Decimal -> Int at both argument and return boundaries.

---

## 39. Required Tests — Parameters

Immutable parameter assignment rejected.

`var` parameter compatible reassignment accepted.

`var` parameter incompatible reassignment rejected by normal assignment typing.

Calling a `var` parameter with a literal is allowed.

Calling a `var` parameter with an immutable binding is allowed because there is no pass-by-reference behavior.

---

## 40. Required Tests — Return Analysis

Test direct return.

Test both if/else branches returning.

Test only one branch returning.

Test else-if with final else.

Test else-if without final else.

Test while-return does not count as total.

Test for-return does not count as total once for-loop typing is available; if collections remain deferred, construct the AST manually if necessary rather than implementing collection semantics.

Test None function fallthrough.

---

## 41. Required Tests — Recursion

Test:

```text
self recursion
mutual recursion
forward call to later declaration
```

No special recursion diagnostic should be needed when signatures are valid.

---

## 42. Integration With Checkpoint 6

All primitive operator and assignment behavior must continue unchanged.

Function bodies use the same expression inference rules.

Do not duplicate primitive typing tables in separate inconsistent logic.

Reuse the existing type checker operations.

---

## 43. Integration With Name Resolution

Use existing resolved function symbols.

Do not implement a separate function-name lookup table by raw source text.

Parameter and local identifier expressions must continue resolving through symbol identity.

---

## 44. AST JSON Compatibility

Do not add semantic function signatures to AST JSON v1.

A parsed AST and an AST JSON round-tripped equivalent must produce equivalent function typing results.

Add a focused integration test if practical.

---

## 45. Suggested Implementation Order

### Step 1
Read authoritative docs and inspect type checker/resolver.

### Step 2
Add semantic `FunctionType` / parameter descriptor representation.

### Step 3
Add signature collection/predeclaration pass.

### Step 4
Associate parameter symbol types.

### Step 5
Type function identifiers/callees.

### Step 6
Implement positional argument mapping.

### Step 7
Implement named argument mapping and argument diagnostics.

### Step 8
Implement argument type compatibility.

### Step 9
Implement return-context tracking and return type checks.

### Step 10
Implement `var` parameter mutation behavior through existing assignment checks.

### Step 11
Implement structural definite-return analysis.

### Step 12
Verify self/mutual/forward recursion.

### Step 13
Add recovery tests.

### Step 14
Run full quality gates.

### Step 15
Update:

```text
dev/plans/pure-language-v0.md
```

Do not proceed to Checkpoint 8.

---

## 46. Verification

Run:

```bash
pytest
ruff check .
mypy src
kaj --version
python -m kaj
```

All previous checkpoint tests must remain green.

---

## 47. Definition of Done

Checkpoint 7 is complete only when:

```text
[ ] docs/language/functions.md treated as authoritative

[ ] semantic FunctionType exists
[ ] parameter descriptors preserve name/type/mutability/order
[ ] return type preserved
[ ] function symbols receive signatures

[ ] signatures created before body checking
[ ] forward function calls type-check
[ ] self recursion type-checks
[ ] mutual recursion type-checks

[ ] parameter types assigned to parameter symbols
[ ] default parameters immutable
[ ] var parameters mutable locally
[ ] var parameters do not require mutable call arguments
[ ] no pass-by-reference behavior added

[ ] calls typed
[ ] non-callables rejected
[ ] positional arguments checked
[ ] named arguments checked
[ ] mixed positional/named checked
[ ] missing args rejected
[ ] too many args rejected
[ ] unknown named args rejected
[ ] duplicate argument binding rejected
[ ] argument type compatibility enforced
[ ] Int -> Decimal promotion works at calls
[ ] call expression receives return type

[ ] return expressions checked against declared return type
[ ] Int -> Decimal promotion works at returns
[ ] wrong returns produce TYPE_MISMATCH
[ ] bare return valid only for None
[ ] None functions may fall through
[ ] return outside function rejected

[ ] non-None definite-return analysis implemented
[ ] direct return recognized
[ ] if/else total return recognized
[ ] one-sided if rejected as potentially falling through
[ ] else-if chains handled
[ ] loops not assumed definitely returning

[ ] TYPE_NOT_CALLABLE implemented
[ ] TYPE_UNKNOWN_NAMED_ARGUMENT implemented
[ ] TYPE_DUPLICATE_ARGUMENT implemented
[ ] TYPE_MISSING_ARGUMENT implemented
[ ] TYPE_TOO_MANY_ARGUMENTS implemented
[ ] TYPE_MISSING_RETURN implemented
[ ] TYPE_RETURN_OUTSIDE_FUNCTION implemented

[ ] errors recover without compiler crashes
[ ] AST remains syntax-only
[ ] no semantic data added to AST JSON v1

[ ] acceptance function passes
[ ] wrong argument type fails
[ ] wrong return type fails

[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] Checkpoints 0-6 remain passing

[ ] no interpreter/runtime implemented
[ ] no overloads implemented
[ ] no defaults implemented
[ ] no variadics implemented
[ ] no user generics implemented
[ ] no closures/lambdas implemented

[ ] dev/plans/pure-language-v0.md updated
```

---

## 48. Completion Report

When finished, report:

```text
Checkpoint 7 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

Function signature model:
- ...

Call checking:
- ...

Named arguments:
- ...

Return checking:
- ...

Missing-return analysis:
- ...

Recursion:
- ...

Mutable parameters:
- ...

Diagnostics:
- ...

Acceptance:
- add(Int, Int) -> Int declaration: PASS/FAIL
- valid call: PASS/FAIL
- wrong argument type: PASS/FAIL
- wrong return type: PASS/FAIL
- missing return: PASS/FAIL
- self recursion: PASS/FAIL
- mutual recursion: PASS/FAIL

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

Do not proceed to Checkpoint 8.
