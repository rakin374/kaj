# Kaj Function Type Checking

**Status:** Authoritative for Kaj v0 Checkpoint 7  
**Scope:** Function signatures, parameter types, return types, call checking, named arguments, recursion, mutable `var` parameters, and missing-return analysis  
**Not covered:** user-defined generics, overloads, closures, nested named functions, collections, records, enums, Optional/Result, effects/capabilities, async/concurrency

---

## 1. Purpose

Checkpoint 7 extends Kaj's static type system from primitive expressions and bindings to functions.

The compiler pipeline remains:

```text
source
  ↓
lexer
  ↓
parser
  ↓
AST
  ↓
name resolution
  ↓
type checking
```

After this checkpoint, Kaj understands function contracts such as:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

and can verify:

- parameter types
- return types
- positional arguments
- named arguments
- argument count
- argument type compatibility
- recursive calls
- mutable `var` parameters
- missing returns in non-`None` functions

---

## 2. Function Signature

Every function declaration has a static signature:

```text
(parameter types) -> return type
```

Example:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

has signature:

```text
(Int, Int) -> Int
```

Parameter names are also part of the callable interface because Kaj supports named arguments.

Therefore a function's semantic signature must preserve:

```text
parameter order
parameter names
parameter types
parameter mutability
return type
```

---

## 3. Function Type Representation

Use an explicit semantic function type/signature representation.

Conceptually:

```text
FunctionType
    parameters: ordered ParameterType[]
    return_type: Type
```

Each parameter entry should contain at least:

```text
name
type
mutable
```

Function types/signatures must not be represented only as formatted strings.

---

## 4. Function Symbol Types

Checkpoint 5 already creates function symbols.

Checkpoint 7 assigns a function signature/type to each function symbol.

Example:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

The resolved symbol for `add` receives:

```text
FunctionType(
    parameters=[
        (a, Int, immutable),
        (b, Int, immutable)
    ],
    return_type=Int
)
```

Keep semantic function types in type-checker side tables/results.

Do not mutate the Core AST.

---

## 5. Signature Predeclaration

Function signatures must be known before any function body is type-checked.

This is required for:

- self recursion
- forward function references
- mutual recursion

Therefore module type checking conceptually performs:

```text
1. collect/validate all top-level function signatures
2. assign signatures to function symbols
3. type-check module bindings/statements and function bodies
```

Equivalent implementations are acceptable if they preserve these semantics.

---

## 6. Signature Annotation Rules

Function parameters require explicit type annotations in Kaj v0.

Function return types are also explicit.

Grammar already requires:

```kaj
fn name(parameter: Type, ...) -> ReturnType {
    ...
}
```

Checkpoint 7 resolves these annotations through the type system.

Primitive types currently supported:

```text
Bool
Int
Decimal
String
Bytes
None
```

Future composite/user-defined types are checked when their checkpoints are implemented.

Unknown type names produce:

```text
TYPE_UNKNOWN_TYPE
```

Do not silently replace unknown parameter/return types with `Any`.

---

## 7. Parameter Types

Each parameter receives exactly its declared static type.

Example:

```kaj
fn double(x: Int) -> Int {
    return x + x
}
```

Within the body:

```text
x: Int
```

Parameter types are available before body expressions are checked.

---

## 8. Immutable Parameters

Parameters are immutable by default.

Example:

```kaj
fn f(x: Int) -> Int {
    x = 2
    return x
}
```

must fail with:

```text
ASSIGN_TO_IMMUTABLE
```

This reuses the primitive assignment/mutability rule from Checkpoint 6.

---

## 9. Mutable `var` Parameters

A parameter may be declared:

```kaj
fn normalize(var value: Decimal) -> Decimal {
    value = value + 1
    return value
}
```

Inside the function, `value` is a mutable local binding.

This means:

- it may be reassigned
- it retains static type `Decimal`
- assignments must remain type-compatible

`var` parameter does **not** mean:

- pass-by-reference
- caller mutation
- `inout`
- pointer/reference semantics

Example:

```kaj
fn change(var x: Int) -> Int {
    x = 20
    return x
}
```

Calling:

```kaj
let original = 10
let result = change(original)
```

does not imply that `original` becomes `20`.

Runtime parameter passing semantics remain ordinary value/local-binding semantics in v0.

---

## 10. Return Type

Every function has an explicit return type.

Examples:

```kaj
fn value() -> Int {
    return 10
}
```

```kaj
fn log() -> None {
    return
}
```

The return annotation defines the function's static return type.

---

## 11. Return Statement Compatibility

For:

```kaj
fn f() -> T {
    return expression
}
```

the expression type must be assignable to `T` using the existing assignment compatibility rules.

Therefore:

```text
T -> T
Int -> Decimal
```

are valid where appropriate.

Example:

```kaj
fn price() -> Decimal {
    return 10
}
```

is valid because:

```text
Int -> Decimal
```

is allowed.

But:

```kaj
fn count() -> Int {
    return 2.5
}
```

produces:

```text
TYPE_MISMATCH
```

---

## 12. Bare Return

A bare return:

```kaj
return
```

is valid only in a function whose return type is:

```text
None
```

Example:

```kaj
fn done() -> None {
    return
}
```

valid.

Invalid:

```kaj
fn value() -> Int {
    return
}
```

→ `TYPE_MISMATCH`

The diagnostic should indicate that an `Int` return value is required.

---

## 13. Returning a Value from `None`

A `None`-returning function may return:

```kaj
return
```

or fall through the end of the body.

Returning an expression is valid only if that expression has type `None`.

Therefore:

```kaj
fn done() -> None {
    return none
}
```

is valid.

But:

```kaj
fn done() -> None {
    return 1
}
```

→ `TYPE_MISMATCH`

---

## 14. Fallthrough for `None`

A function declared:

```kaj
fn f() -> None {
    ...
}
```

does not require an explicit return statement.

Falling off the end is semantically equivalent to returning `None`.

This rule is specific to `None` return type.

---

## 15. Non-`None` Missing Return

A function whose return type is not `None` must return a compatible value on every statically reachable path to the end of the function body.

If execution may reach the end without returning, emit:

```text
TYPE_MISSING_RETURN
```

Example:

```kaj
fn value() -> Int {
    let x = 10
}
```

→ `TYPE_MISSING_RETURN`

---

## 16. Return-Path Analysis

Checkpoint 7 uses a conservative structural return analysis.

A block is considered definitely returning if execution cannot fall through its end under the rules below.

This is not a full general control-flow graph analysis.

It is sufficient for v0 function return checking.

---

## 17. Direct Return

A statement:

```kaj
return expression
```

or:

```kaj
return
```

definitely returns from the current function.

Statements after a definite return may be unreachable, but unreachable-code diagnostics are not required in Checkpoint 7.

---

## 18. Sequential Block Return

For a block:

```text
statement 1
statement 2
...
```

the block definitely returns if some statement in sequence definitely returns and control cannot continue past that statement.

For v0, once a statement is classified as definitely returning, the block may be considered definitely returning.

Do not require unreachable-code warnings.

---

## 19. If / Else Return Analysis

An `if` statement definitely returns only when:

```text
then branch definitely returns
AND
else branch exists
AND
else branch definitely returns
```

Example:

```kaj
fn f(x: Bool) -> Int {
    if x {
        return 1
    } else {
        return 2
    }
}
```

passes.

But:

```kaj
fn f(x: Bool) -> Int {
    if x {
        return 1
    }
}
```

must produce:

```text
TYPE_MISSING_RETURN
```

because the false path reaches the end.

---

## 20. Else-If Return Analysis

An `else if` chain is treated recursively as nested `IfStatement`.

Example:

```kaj
fn f(x: Int) -> Int {
    if x == 0 {
        return 0
    } else if x == 1 {
        return 1
    } else {
        return 2
    }
}
```

definitely returns if every branch including the final `else` definitely returns.

Without a final `else`, it does not count as definitely returning.

---

## 21. While Return Analysis

Checkpoint 7 does **not** assume a `while` loop definitely executes.

Therefore:

```kaj
fn f() -> Int {
    while condition {
        return 1
    }
}
```

still produces:

```text
TYPE_MISSING_RETURN
```

unless later statements guarantee a return.

Even:

```kaj
while true {
    return 1
}
```

does not need to be recognized as definitely returning in Checkpoint 7.

Loop termination/reachability sophistication is deferred.

---

## 22. For Return Analysis

A `for` loop is not considered definitely returning because it may execute zero times.

Therefore:

```kaj
fn f() -> Int {
    for x in items {
        return 1
    }
}
```

does not satisfy the function return requirement by itself.

---

## 23. Function Calls

For:

```kaj
add(1, 2)
```

the type checker:

1. obtains the callee's resolved symbol
2. verifies it has a known function signature
3. maps arguments to parameters
4. checks argument types
5. assigns the call expression the function return type

Example:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}

let x = add(1, 2)
```

The call has type:

```text
Int
```

and therefore:

```text
x: Int
```

---

## 24. Calling Non-Functions

If an expression resolves to a value that is not callable:

```kaj
let x = 10
x()
```

emit:

```text
TYPE_NOT_CALLABLE
```

Do not treat every identifier call as a function merely because syntax permits it.

---

## 25. Positional Arguments

Positional arguments bind to parameters by declaration order.

Example:

```kaj
fn pair(a: Int, b: String) -> None {
}

pair(1, "x")
```

maps:

```text
1   -> a
"x" -> b
```

---

## 26. Named Arguments

Named arguments use the parameter's declared name.

Example:

```kaj
fn send(message: String, priority: Int) -> None {
}

send(message: "hello", priority: 2)
```

is valid.

Named argument labels are not lexical variable references; the parser/resolver already treat them as labels.

---

## 27. Mixed Positional and Named Arguments

Kaj permits positional arguments first, then named arguments.

Example:

```kaj
send("hello", priority: 2)
```

is valid.

The parser already rejects positional arguments after named arguments.

Checkpoint 7 performs semantic mapping after parsing.

---

## 28. Named Argument Matching

A named argument must match exactly one parameter name.

Unknown argument label:

```kaj
send(message: "hello", urgency: 2)
```

produces:

```text
TYPE_UNKNOWN_NAMED_ARGUMENT
```

No fuzzy matching or aliases.

---

## 29. Duplicate Argument Binding

A parameter may not receive more than one argument.

Invalid:

```kaj
send("hello", message: "again", priority: 2)
```

because `message` is provided positionally and again by name.

Emit:

```text
TYPE_DUPLICATE_ARGUMENT
```

Likewise:

```kaj
send(message: "a", message: "b", priority: 2)
```

must fail if the parser allows such syntax to reach semantic analysis.

---

## 30. Missing Arguments

All parameters are required in Kaj v0.

Default parameter values are not implemented.

Therefore:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}

add(1)
```

produces:

```text
TYPE_MISSING_ARGUMENT
```

The diagnostic should identify missing parameter(s) where practical.

---

## 31. Too Many Positional Arguments

Example:

```kaj
add(1, 2, 3)
```

produces:

```text
TYPE_TOO_MANY_ARGUMENTS
```

Do not silently ignore extras.

---

## 32. Argument Type Compatibility

Each mapped argument expression must be assignable to the corresponding parameter type.

Use the same compatibility rules established in Checkpoint 6.

Valid:

```kaj
fn f(x: Decimal) -> Decimal {
    return x
}

let y = f(10)
```

because:

```text
Int -> Decimal
```

is allowed.

Invalid:

```kaj
fn f(x: Int) -> Int {
    return x
}

let y = f(2.5)
```

→ `TYPE_MISMATCH`

---

## 33. Parameter Mutability Does Not Affect Call Compatibility

For:

```kaj
fn f(var x: Int) -> Int {
    x += 1
    return x
}
```

the call:

```kaj
f(10)
```

is valid.

A `var` parameter does not require a mutable lvalue argument.

It receives a mutable local copy/value binding.

Therefore both are valid:

```kaj
f(10)
```

```kaj
let a = 10
f(a)
```

No caller-side mutation semantics exist.

---

## 34. Recursive Calls

Self-recursive functions must type-check using the predeclared function signature.

Example:

```kaj
fn factorial(n: Int) -> Int {
    if n == 0 {
        return 1
    } else {
        return n * factorial(n - 1)
    }
}
```

The recursive call:

```text
factorial(n - 1)
```

has type:

```text
Int
```

while the body is being checked.

Do not require the body to be fully checked before assigning the signature.

---

## 35. Mutual Recursion

Mutually recursive functions must also work.

Example:

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

Both function signatures are available before either body is checked.

---

## 36. Forward Function References

Checkpoint 5 resolves later-declared function names.

Checkpoint 7 must also make their signatures available.

Example:

```kaj
fn first() -> Int {
    return second()
}

fn second() -> Int {
    return 2
}
```

passes.

Do not type-check bodies strictly in a way that makes later function signatures unavailable.

---

## 37. Function Name Collisions

Duplicate function names remain a name-resolution error:

```text
RESOLVE_DUPLICATE_NAME
```

Checkpoint 7 does not introduce overloading.

Therefore these are invalid:

```kaj
fn f(x: Int) -> Int {
    return x
}

fn f(x: Decimal) -> Decimal {
    return x
}
```

Kaj v0 has no function overloading.

---

## 38. No User Generics

Checkpoint 7 does not support:

```kaj
fn identity<T>(x: T) -> T
```

or generic inference.

Do not add generic function syntax or type variables.

---

## 39. No Optional/Default Parameters

Not supported:

```kaj
fn f(x: Int = 10) -> Int
```

Do not invent default-argument behavior.

Every parameter is required.

---

## 40. No Variadic Parameters

Not supported:

```text
*args
...args
variadic parameter packs
```

Arity is statically fixed.

---

## 41. No Function Overloading

A name maps to one value symbol.

Kaj v0 does not select a function by argument types.

No overload sets.

---

## 42. No First-Class Function Design Expansion

Functions may currently appear as identifiers in expressions due to the general AST/resolver structure.

Checkpoint 7 only needs enough callable typing to type-check direct references to declared functions and calls.

Do not design:

- closures
- lambdas
- function-valued local variables
- higher-order generic behavior
- capture semantics

unless already structurally necessary.

A declared function identifier may have its `FunctionType` recorded as its expression type.

---

## 43. Function Identifier Type

For:

```kaj
let x = add
```

if the current AST/type system naturally permits this, the identifier `add` has its `FunctionType`.

Whether assigning/storing first-class functions becomes a supported public language feature should not be expanded in Checkpoint 7.

Do not add special syntax or runtime semantics around this.

---

## 44. Return Outside Function

If the parser permits a top-level `return` AST, name resolution may have tolerated it.

Checkpoint 7 should emit:

```text
TYPE_RETURN_OUTSIDE_FUNCTION
```

for a return statement not enclosed by a function.

This is a semantic legality check naturally associated with function typing.

---

## 45. Nested Control Flow Returns

Return type checking applies regardless of nesting:

```kaj
fn f(x: Bool) -> Int {
    if x {
        while x {
            return 1
        }
    }

    return 2
}
```

Every encountered return expression is checked against the enclosing function return type.

---

## 46. Error Type and Recovery

Reuse the internal error type/sentinel from Checkpoint 6.

Examples:

- unknown callee symbol → resolver error, call gets error type
- unknown function annotation → signature contains error type where needed
- wrong argument → diagnostic, call may still retain declared return type to reduce cascades
- wrong return expression → diagnostic, continue checking body
- duplicate/missing named args → diagnostic, continue checking other arguments where possible

Do not stop after the first function type error.

---

## 47. Call Result Type After Argument Error

If the callee is a known function and its return type is known, the call expression may retain that return type even when one argument is invalid.

Example:

```kaj
fn f(x: Int) -> String {
    return "ok"
}

let y = f("wrong")
```

Emit the argument `TYPE_MISMATCH`, but record the call expression as `String` where practical.

This reduces cascading errors in later expressions.

---

## 48. Function Body Environment

When type-checking a function body:

```text
parameter symbol types are already assigned
module symbols retain their known types
local binding types are inferred as encountered
```

Use name-resolution symbol identity.

Do not perform name lookup by raw string.

---

## 49. Module Bindings Referenced by Functions

The visibility rules from Checkpoint 5 remain authoritative.

A function may only reference module bindings that resolved successfully under source-order visibility.

Checkpoint 7 does not change hoisting rules.

---

## 50. Named Argument Evaluation Order

Argument expressions retain source order for evaluation semantics.

Checkpoint 7 maps them to parameters for type checking, but must not reorder the AST.

Runtime evaluation order will be specified by the interpreter checkpoint.

For now, preserve source ordering and only maintain a semantic mapping.

---

## 51. Parameter Mapping Side Table

Where useful, record the mapping:

```text
CallArgument -> Parameter
```

in type-checker results.

This can help later interpreter/compiler lowering, especially for named arguments.

Do not mutate the AST to reorder named arguments.

---

## 52. Function Signature Side Table

The type-checker result should expose:

```text
Function symbol -> FunctionType
```

and continue exposing:

```text
Expression -> Type
Value symbol -> Type
```

from Checkpoint 6.

---

## 53. Diagnostics

Checkpoint 7 requires these stable diagnostic codes:

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

Existing:

```text
TYPE_UNKNOWN_TYPE
ASSIGN_TO_IMMUTABLE
```

continue to apply.

Implementations may add more specific diagnostics later, but these are the v0 contract for this checkpoint.

---

## 54. Wrong Return Type

Example:

```kaj
fn f() -> Int {
    return "hello"
}
```

must produce:

```text
TYPE_MISMATCH
```

The diagnostic span should point to the returned expression or return statement in a consistent way.

---

## 55. Wrong Argument Type

Example:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}

let x = add(1, "2")
```

must produce:

```text
TYPE_MISMATCH
```

Prefer pointing at the incompatible argument expression.

---

## 56. Return Type Inference Is Not Implemented

Kaj v0 does not infer function return types from bodies.

This is required:

```kaj
fn f() -> Int {
    return 1
}
```

A syntax such as:

```kaj
fn f() {
    return 1
}
```

is not part of the current grammar.

---

## 57. Parameter Type Inference Is Not Implemented

Parameters remain explicitly typed.

No inference from call sites.

---

## 58. Function Signature Independence from Body Success

A function's declared signature exists even if its body has type errors.

This is necessary for deterministic recursive and cross-function checking.

Example:

```kaj
fn f() -> Int {
    return "bad"
}

fn g() -> Int {
    return f()
}
```

`f` still has declared return type `Int` for purposes of checking `g`.

`f` receives its own return mismatch diagnostic.

---

## 59. Missing Return Examples

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

Valid:

```kaj
fn f(x: Bool) -> None {
    if x {
        return
    }
}
```

because `None` functions may fall through.

---

## 60. Source of Truth

For Kaj v0 function typing:

```text
docs/language/functions.md
        +
type-checker tests
        +
type-checker implementation
```

must agree.

This document defines the intended language semantics.

---

## 61. Checkpoint 7 Definition of Done

Checkpoint 7 is complete when:

```text
[ ] function signature semantic representation implemented
[ ] parameter order preserved
[ ] parameter names preserved
[ ] parameter types represented
[ ] parameter mutability represented
[ ] return type represented

[ ] function signatures predeclared before body checking
[ ] function symbols receive signatures
[ ] primitive parameter annotations resolved
[ ] primitive return annotations resolved
[ ] unknown function type annotations diagnosed

[ ] parameter symbol types available in body
[ ] immutable parameters reject assignment
[ ] var parameters permit compatible reassignment
[ ] var parameters do not imply pass-by-reference

[ ] call expressions type-checked
[ ] positional arguments mapped by order
[ ] named arguments mapped by name
[ ] mixed positional-then-named arguments supported
[ ] unknown named arguments diagnosed
[ ] duplicate argument binding diagnosed
[ ] missing arguments diagnosed
[ ] too many arguments diagnosed
[ ] argument types checked
[ ] Int -> Decimal allowed at call boundary
[ ] incompatible argument types produce TYPE_MISMATCH
[ ] call result receives function return type
[ ] non-callable values diagnosed

[ ] return expressions checked
[ ] Int -> Decimal allowed at return boundary
[ ] incompatible return types produce TYPE_MISMATCH
[ ] bare return allowed only for None
[ ] return value in None function checked
[ ] return outside function diagnosed

[ ] non-None missing-return analysis implemented
[ ] direct return recognized
[ ] if/else both-return recognized
[ ] if without else not considered total
[ ] else-if chains handled recursively
[ ] loops not assumed to definitely return
[ ] None functions may fall through

[ ] self recursion type-checks
[ ] mutual recursion type-checks
[ ] forward function calls type-check

[ ] no overloads implemented
[ ] no default args implemented
[ ] no variadics implemented
[ ] no user generics implemented
[ ] no pass-by-reference semantics implemented

[ ] type information remains in side tables/results
[ ] AST remains unmodified
[ ] call argument -> parameter mapping available where useful
[ ] error recovery continues after function type errors

[ ] required diagnostics implemented
[ ] tests pass
[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] Checkpoints 0-6 remain passing
```
