# Kaj Reference Interpreter Core

**Status:** Authoritative for Kaj v0 Checkpoint 8  
**Scope:** Reference execution of primitive literals, bindings, assignment, operators, `if`, `while`, functions, calls, and `return`  
**Implementation:** Python reference interpreter  

**Current extensions:** `break` and `continue` use control-flow signals consumed by the nearest loop. `range` uses lazy `KajRange`; map iteration yields controlled `KajMapEntry` values. Structured display and equality are Kaj-defined and do not delegate to Python representation or identity.
**Not covered:** lists/maps execution, records, enums, Optional/Result, imports, effects/capabilities, concurrency, native code generation

---

# 1. Purpose

Checkpoint 8 gives Kaj its first executable runtime.

Before this checkpoint, Kaj can:

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

Checkpoint 8 adds:

```text
type-checked AST
  ↓
reference interpreter
  ↓
runtime values / observable output
```

The interpreter is written in Python, but **Kaj semantics are authoritative**.

Python is the implementation substrate, not the language specification.

---

# 2. Execution Requirement

The reference interpreter executes only programs that have successfully passed the required frontend stages.

Normal execution pipeline:

```text
source
  ↓
lex
  ↓
parse
  ↓
resolve
  ↓
type check
  ↓
interpret
```

If lexical, parse, resolution, or type diagnostics contain errors, normal execution must not proceed.

The interpreter should not be used to bypass Kaj's static rules.

---

# 3. Checkpoint 8 Acceptance Program

This program must execute:

```kaj
fn factorial(n: Int) -> Int {
    if n <= 1 {
        return 1
    }

    return n * factorial(n - 1)
}

print(factorial(5))
```

and produce:

```text
120
```

followed by the host's normal line termination.

---

# 4. Reference Interpreter

Checkpoint 8 implements a **reference interpreter**.

Conceptually:

```text
AST node
   ↓
evaluate / execute
   ↓
Kaj runtime value or control-flow outcome
```

The interpreter exists to:

- establish executable Kaj semantics early
- test frontend correctness end to end
- provide a reference for future compiled backends
- make Kaj usable before native code generation exists

It is not intended to make Kaj semantically equivalent to Python.

---

# 5. Runtime Value Representation

Kaj primitive runtime values may initially use Python values internally.

Recommended mapping:

```text
Kaj Bool     -> Python bool
Kaj Int      -> Python int
Kaj Decimal  -> decimal.Decimal
Kaj String   -> Python str
Kaj Bytes    -> Python bytes
Kaj None     -> dedicated Kaj runtime sentinel or carefully controlled Python None
```

The implementation must preserve Kaj semantics regardless of Python behavior.

Examples:

```text
Python: True + 1 is legal
Kaj:    true + 1 is illegal
```

The type checker prevents such invalid Kaj operations before execution.

---

# 6. Runtime Value Semantics

Kaj values are semantic language values.

Do not expose arbitrary Python objects as ordinary Kaj values.

Do not use:

```text
eval
exec
Python globals()
Python locals()
```

to implement Kaj bindings or expressions.

---

# 7. Runtime Environments

Bindings are stored in explicit Kaj runtime environments.

Conceptually:

```text
Environment
├── parent
└── values
    ├── Symbol #1 -> runtime value
    ├── Symbol #2 -> runtime value
    └── ...
```

Environment lookup should use resolved compiler symbol identity where practical.

Do not key execution solely by source-name strings, because shadowing creates distinct symbols with the same name.

---

# 8. Environment Hierarchy

Runtime environments mirror Kaj lexical scope.

Conceptually:

```text
module environment
    ↓
function-call environment
    ↓
nested block environments
```

A nested environment references its parent.

A runtime binding belongs to the environment corresponding to its lexical declaration.

---

# 9. Module Environment

Each execution creates one module environment.

It contains:

```text
module-level let/var bindings
top-level function runtime values
host-provided builtins
```

Top-level functions must be available for:

```text
forward calls
self recursion
mutual recursion
```

before ordinary module statements requiring them execute.

---

# 10. Function Runtime Value

A Kaj function declaration evaluates/installs a callable Kaj function value.

A function value contains enough information to call the function later.

Conceptually:

```text
KajFunction
├── declaration
├── semantic signature
└── module/lexical environment reference
```

Since named functions are top-level only in v0, capturing the module environment is sufficient.

Do not implement general closure semantics in Checkpoint 8.

---

# 11. Function Installation

Before executing ordinary top-level statements, install all top-level Kaj function values into the module environment.

This mirrors the frontend's forward function visibility.

Therefore:

```kaj
first()

fn first() -> None {
}
```

may resolve/type-check according to the current grammar and module statement rules if permitted by earlier stages.

More importantly, functions can recursively call themselves or one another.

---

# 12. Module Binding Execution Order

Module `let`/`var` bindings execute in source order.

Do not pre-evaluate or hoist module variable initializers.

This preserves Checkpoint 5 source-order semantics.

---

# 13. `let` Runtime Binding

Example:

```kaj
let x = 10
```

Execution:

```text
evaluate initializer
→ 10

store:
Symbol(x) -> 10
```

`let` bindings are immutable.

Static checking should already reject assignment to them.

The runtime may defensively reject illegal mutation if encountered through malformed/internal AST execution.

---

# 14. `var` Runtime Binding

Example:

```kaj
var x = 10
```

Execution:

```text
evaluate initializer
→ 10

store mutable binding:
Symbol(x) -> 10
```

Later compatible assignment updates that symbol's runtime value.

---

# 15. Assignment

For:

```kaj
x = expression
```

execution:

```text
evaluate RHS
resolve target symbol from semantic resolution
update the runtime slot for that symbol
```

Member/index assignment is not fully executable until records/collections exist.

Checkpoint 8 must support identifier assignment.

Do not invent record/list assignment semantics.

---

# 16. Compound Assignment

The AST already supports:

```text
+=
-=
*=
/=
```

Checkpoint 8 should execute compound assignment for identifier targets using the same runtime operator semantics as the corresponding binary operation.

Conceptually:

```kaj
x += y
```

means:

```text
current = runtime value of x
rhs = evaluate y
result = add(current, rhs)
store result back into x
```

Static typing has already verified compatibility.

---

# 17. Literal Evaluation

Evaluate:

```text
IntegerLiteral -> Kaj Int runtime value
DecimalLiteral -> Kaj Decimal runtime value
StringLiteral -> Kaj String runtime value
BooleanLiteral -> Kaj Bool runtime value
NoneLiteral -> Kaj None runtime value
```

Do not parse numeric values through binary floating point.

Use `decimal.Decimal` for Kaj Decimal.

---

# 18. Identifier Evaluation

For an identifier expression:

```kaj
x
```

use its resolved symbol identity to retrieve the corresponding runtime value.

Do not perform a fresh lexical lookup by raw text if the resolver already provides symbol associations.

An unresolved identifier should never reach normal execution.

---

# 19. Numeric Promotion at Runtime

Checkpoint 6 defined:

```text
Int -> Decimal
```

as the only primitive implicit promotion.

At runtime, whenever a typed operation requires numeric promotion:

```text
Kaj Int runtime int
    ↓
convert exactly
    ↓
Python Decimal
```

For example:

```kaj
10 + 2.5
```

executes conceptually as:

```python
Decimal(10) + Decimal("2.5")
```

not:

```python
10 + 2.5
```

with Python float.

---

# 20. Arithmetic Operators

Execute the type-checked semantics already frozen in Checkpoint 6.

Supported:

```text
+
-
*
/
%
**
```

Do not infer operator legality dynamically from Python.

The runtime implementation should dispatch intentionally based on Kaj semantic operand types / known typing information.

---

# 21. Addition

Runtime behavior:

```text
Int + Int -> Int
numeric mixed -> Decimal
Decimal + Decimal -> Decimal
String + String -> String
```

String concatenation performs exact concatenation of the two Kaj String values.

No implicit stringification.

---

# 22. Subtraction and Multiplication

Use arbitrary-precision integer behavior for Int.

Use exact Decimal arithmetic for Decimal and mixed numeric operations.

---

# 23. Division

Kaj semantics:

```text
Int / Int -> Decimal
Int / Decimal -> Decimal
Decimal / Int -> Decimal
Decimal / Decimal -> Decimal
```

Therefore:

```kaj
5 / 2
```

evaluates to the Kaj Decimal value:

```text
2.5
```

Never use Python integer floor division.

---

# 24. Decimal Arithmetic Context

Checkpoint 8 must not silently use low-precision binary float arithmetic.

Use Python's `decimal.Decimal`.

If a Decimal operation produces a result requiring rounding according to Python Decimal context, use a clearly defined interpreter Decimal context and document it.

For the v0 interpreter, set a deterministic sufficiently high precision rather than inheriting arbitrary process-global settings.

Recommended initial precision:

```text
34 decimal digits
```

which aligns with decimal128-scale precision.

This is an interpreter/runtime implementation decision for non-terminating or precision-sensitive Decimal operations and may receive a deeper language-level numerical specification later.

Do not convert through `float`.

---

# 25. Modulo

Execute numeric modulo according to the type-approved operand combination.

For mixed numeric operands, promote Int to Decimal before operation.

---

# 26. Power

Execute:

```text
Int ** Int -> Int
```

when statically typed that way.

Numeric operations producing Decimal use Decimal-compatible execution.

If Python Decimal cannot directly represent a permitted exponent case without approximation or unsupported behavior, produce a structured runtime error rather than falling back silently to float.

Do not weaken exactness by hidden float conversion.

---

# 27. Unary Operators

Execute:

```text
+Int
-Int
+Decimal
-Decimal
not Bool
```

according to Kaj semantics.

---

# 28. Equality

Execute:

```text
==
!=
```

only for combinations already accepted by the type checker.

Numeric mixed comparison promotes Int to Decimal.

Result is Kaj Bool.

Do not rely on Python's cross-type equality behavior for illegal Kaj combinations.

---

# 29. Ordering

Execute:

```text
<
<=
>
>=
```

for numeric operands only, as established in Checkpoint 6.

Mixed numeric operands promote to Decimal.

---

# 30. Boolean Operators

Execute:

```text
and
or
not
```

on Bool values only.

`and` and `or` must use **short-circuit evaluation**.

Therefore:

```kaj
false and expression
```

does not evaluate `expression`.

And:

```kaj
true or expression
```

does not evaluate `expression`.

This is a Kaj semantic rule.

---

# 31. `if`

Execution:

```text
evaluate condition
condition must already be Bool
if true:
    execute then branch
else:
    execute else branch if present
```

Each branch executes in its own runtime block environment matching lexical scope.

---

# 32. `while`

Execution:

```text
evaluate condition
while condition == true:
    execute body
    reevaluate condition
```

The condition is required to be Bool by static typing.

Each loop iteration creates a fresh block environment for the body.

This ensures block-local bindings do not become module/function locals across iterations.

---

# 33. Break and Continue

The interpreter supports:

```text
break
continue
```

with dedicated internal control-flow signals. A loop consumes its own break/continue signals; return signals continue through the loop to function-call execution. Static checking rejects loop control outside a loop.

---

# 34. Expression Statements

An expression statement:

```kaj
factorial(5)
```

evaluates the expression and discards the resulting value unless the expression itself produces an observable effect such as `print`.

Do not automatically print expression results.

This is not a REPL specification.

---

# 35. Function Call Execution

For a call to a Kaj function:

```text
1. evaluate argument expressions in source order
2. use Checkpoint 7's argument-to-parameter mapping
3. create a fresh function-call environment
4. bind each parameter symbol to its argument runtime value
5. execute the function body
6. capture `return`
7. produce the returned runtime value
```

Named arguments do not change source evaluation order.

---

# 36. Argument Evaluation Order

Arguments evaluate **left to right in source order**.

Example:

```kaj
f(a(), b())
```

evaluates:

```text
a()
then
b()
```

Named arguments are still evaluated in source order even though they may map to parameters in a different declaration order.

This is now a frozen Kaj v0 runtime rule.

---

# 37. Parameter Passing

Kaj v0 parameters use value/local-binding semantics.

For primitive immutable runtime values this naturally means the called function receives the value.

A `var` parameter means the local parameter slot can be reassigned.

It does not mutate the caller binding.

Example:

```kaj
fn change(var x: Int) -> Int {
    x = 20
    return x
}

let original = 10
let result = change(original)
```

after execution:

```text
original == 10
result == 20
```

---

# 38. Function Call Environment

A function call gets a fresh environment per invocation.

This is required for recursion.

Example:

```kaj
factorial(5)
```

creates one call environment for `n = 5`, then another for `n = 4`, and so on.

Calls must not share parameter/local storage.

---

# 39. Recursive Execution

Self recursion works because the module environment already contains the function value.

Conceptually:

```text
module env
└── factorial -> KajFunction

call factorial(5)
└── call env n=5
      └── call factorial(4)
            └── call env n=4
                 ...
```

Each call is independent.

---

# 40. Mutual Recursion

Mutually recursive top-level functions execute through the same module function environment.

No special runtime mechanism beyond function preinstallation and fresh call frames is required.

---

# 41. Return Control Flow

`return` is not an ordinary expression value.

It exits the currently executing function immediately.

Recommended implementation:

```text
internal ReturnSignal(value)
```

or another private control-flow mechanism.

The interpreter may use a private Python exception class internally for non-local unwinding:

```python
class _ReturnSignal(Exception):
    ...
```

if it is never exposed as a user-visible failure.

This is acceptable because it models interpreter control flow, not Kaj errors.

---

# 42. Bare Return Runtime Value

For:

```kaj
return
```

the function returns the Kaj `None` runtime value.

A `None` function falling off the end also returns Kaj `None`.

---

# 43. Return With Value

For:

```kaj
return expression
```

evaluate `expression` and immediately return that runtime value from the current function call.

Any required `Int -> Decimal` conversion at the return boundary must be applied consistently with the statically approved return type.

Example:

```kaj
fn f() -> Decimal {
    return 10
}
```

runtime return value must be a Kaj Decimal value, not merely a Python int tagged conceptually as acceptable.

Boundary promotions should therefore be materialized by the interpreter.

---

# 44. Argument Boundary Promotion

Likewise:

```kaj
fn f(x: Decimal) -> Decimal {
    return x
}

f(10)
```

must bind `x` to a Kaj Decimal runtime value.

Because type checking approved:

```text
Int -> Decimal
```

the call boundary materializes the promotion.

Do not leave parameter runtime representation as Int while claiming its semantic type is Decimal.

---

# 45. Assignment Boundary Promotion

For:

```kaj
var x: Decimal = 10
```

store a Decimal runtime value.

For:

```kaj
var x: Decimal = 1.5
x = 2
```

assignment stores Decimal `2`, not Int `2`.

Any statically approved `Int -> Decimal` assignment conversion must be materialized.

---

# 46. Builtin `print`

Checkpoint 8 introduces one minimal host-provided builtin:

```text
print
```

This exists solely to provide observable output and support the acceptance program.

It is not yet a general standard-library design.

---

# 47. `print` Static Signature

For Checkpoint 8, `print` is injected by the host/compiler environment as a builtin symbol.

Because Kaj v0 has no generics or `Any`, define `print` as a special builtin handled explicitly by the type checker rather than pretending it has an ordinary generic function signature.

Checkpoint 8 extends semantic checking just enough that:

```kaj
print(expression)
```

is recognized as valid for currently executable primitive values:

```text
Bool
Int
Decimal
String
Bytes
None
```

`print`:

- requires exactly one positional argument
- does not accept named arguments in v0
- returns `None`

Do not generalize this into arbitrary builtin overloading infrastructure.

---

# 48. Builtin Resolution

Checkpoint 5 deliberately defined no implicit builtins.

Checkpoint 8 now introduces an explicit **host builtin scope/environment** containing `print`.

The resolver should support an injected outer/builtin scope or equivalent explicit builtin symbol registration.

The order is conceptually:

```text
builtin scope
    ↓ parent of
module scope
```

or an equivalent lookup mechanism.

`print` must resolve as a known builtin symbol without being declared in Kaj source.

Do not hard-code many speculative builtins.

Only `print` is required here.

---

# 49. Builtin Shadowing

Ordinary Kaj declarations may shadow the builtin `print` in a nested/module scope if the existing lexical shadowing rules permit declaration against an outer scope.

Example:

```kaj
let print = 10
```

is allowed because the builtin lives in an outer scope, not the same module scope.

After shadowing, a later:

```kaj
print(1)
```

attempts to call the local binding and should receive `TYPE_NOT_CALLABLE`.

This follows normal lexical shadowing.

---

# 50. `print` Runtime Behavior

`print(value)` writes one human-readable representation followed by a newline to the interpreter's output sink.

Canonical primitive formatting for v0:

```text
Bool:
true
false

Int:
base-10 integer

Decimal:
plain decimal representation without Python `Decimal(...)` wrapper

String:
raw string contents without quotes

Bytes:
deterministic developer-readable representation; exact user-facing bytes formatting may be refined later

None:
none
```

Examples:

```kaj
print(120)
```

prints:

```text
120
```

```kaj
print(true)
```

prints:

```text
true
```

```kaj
print("hello")
```

prints:

```text
hello
```

```kaj
print(none)
```

prints:

```text
none
```

---

# 51. Output Sink Abstraction

Do not hard-wire all interpreter output directly to global Python stdout.

The interpreter should accept or own an output sink abstraction.

At minimum tests must be able to capture output deterministically without monkey-patching global state.

Conceptually:

```text
Interpreter(output=...)
```

or:

```text
RuntimeIO.write_line(...)
```

CLI execution can use stdout.

Tests can use an in-memory buffer.

---

# 52. Runtime Errors

Even statically valid programs can encounter runtime errors.

Checkpoint 8 should define structured runtime failures at least for cases such as:

```text
division by zero
invalid internal execution state
unsupported runtime operation that passed frontend unexpectedly
```

Recommended stable codes:

```text
RUNTIME_DIVISION_BY_ZERO
RUNTIME_INVALID_OPERATION
RUNTIME_INTERNAL_ERROR
```

Do not expose raw Python exceptions as ordinary Kaj runtime diagnostics.

---

# 53. Division by Zero

Examples:

```kaj
1 / 0
1 % 0
```

may pass type checking but fail at runtime.

Report:

```text
RUNTIME_DIVISION_BY_ZERO
```

with the relevant expression span.

Do not expose Python:

```text
ZeroDivisionError
decimal.DivisionByZero
```

directly to Kaj users.

---

# 54. Runtime Diagnostic Spans

Runtime errors should reference existing AST source spans.

Do not invent a new coordinate model.

Use Checkpoint 1's span conventions.

---

# 55. Runtime Error Recovery

A runtime error terminates the current program execution for Checkpoint 8.

Unlike compiler diagnostics, interpreter execution does not attempt to continue after an unrecoverable runtime failure.

Return a structured execution result/failure rather than crashing the host process.

---

# 56. Execution Result

Provide a clear interpreter result.

Conceptually:

```text
ExecutionResult
├── value / None
├── output
└── runtime_error?
```

Exact API may vary.

Normal module execution itself has no meaningful program result in v0, so Kaj `None` is acceptable as the module result.

Observable output is captured separately.

---

# 57. Interpreter API

Provide an API conceptually similar to:

```python
interpret(
    program: Program,
    resolution: ResolutionResult,
    types: TypeCheckResult,
    *,
    output: RuntimeOutput | None = None,
) -> ExecutionResult
```

Exact names may differ.

Do not require reparsing source inside the interpreter.

---

# 58. Semantic Information Input

The interpreter should consume the resolver/type-checker results rather than reimplementing semantic analysis.

Use:

```text
identifier -> symbol
symbol -> type
expression -> type
call argument -> parameter mapping
function symbol -> signature
```

where available.

This keeps execution aligned with the already-approved static meaning.

---

# 59. Do Not Re-Type-Check Dynamically

The reference interpreter may contain defensive assertions/guards, but it must not become a second independent type system.

The type checker remains authoritative for static legality.

The interpreter performs the runtime consequences of already-established semantics.

---

# 60. Block Environments

Nested `if`/`while` bodies execute using child environments.

Example:

```kaj
let x = 1

if true {
    let x = 2
    print(x)
}

print(x)
```

must print:

```text
2
1
```

The runtime must respect resolver symbol identity and lexical scope.

---

# 61. Function-Body Scope

Checkpoint 5 established that parameters and direct declarations in a function body share one function scope.

The runtime should mirror that:

```text
function call environment
    contains parameters
    contains direct function-body locals
```

Do not create an unnecessary separate environment for the function body's outermost block.

Nested control-flow bodies still get child environments.

---

# 62. While Iteration Scope

Each loop iteration uses a fresh child block environment.

Example conceptual behavior:

```kaj
var n = 0

while n < 3 {
    let temp = n
    n += 1
}
```

`temp` is recreated each iteration and inaccessible outside the loop body.

---

# 63. Function Local Lifetime

Function parameter and local environments are destroyed/unreachable after the call returns.

Recursive calls have independent frames.

Do not store locals globally.

---

# 64. No Python Variable Generation

Do not translate:

```kaj
let x = 10
```

into dynamically executed Python source:

```python
x = 10
```

The interpreter explicitly evaluates AST nodes and stores Kaj bindings in runtime environments.

This is a critical architecture rule.

---

# 65. No Python Truthiness Leakage

Even though Python values back Kaj values, runtime condition handling must expect Kaj Bool.

Do not implement:

```python
if value:
```

as the semantic validation mechanism for arbitrary values.

Static typing should guarantee Bool; defensive runtime logic should verify Bool where necessary.

---

# 66. No Python Bool-as-Int Leakage

Python's:

```text
bool <: int
```

relationship is not a Kaj rule.

When runtime dispatch distinguishes Int from Bool, check Bool explicitly so:

```text
true
```

is not accidentally treated as Kaj Int.

---

# 67. No Float Leakage

Do not create Python `float` values for Kaj Decimal.

Do not use float as an intermediate conversion.

This includes:

```text
literal creation
promotion
division
mixed arithmetic
printing
```

---

# 68. Unsupported AST Nodes

Checkpoint 8 does not execute:

```text
ListLiteral
MapLiteral
MemberAccessExpression
IndexExpression
ForStatement
```

unless a later/earlier design explicitly requires a narrow part.

If such a node reaches normal execution despite being outside the runtime subset, fail with a structured unsupported runtime/internal diagnostic.

Do not silently invent behavior.

---

# 69. `for` Deferred

Although `for` syntax exists, iterable/collection runtime semantics are deferred until the Lists checkpoint.

Do not implement generic Python iteration over arbitrary Kaj/Python values.

---

# 70. Bytes Construction

`Bytes` has no source literal in the current language.

The runtime type representation may exist, primarily for future builtins/APIs.

Do not add bytes literal syntax during Checkpoint 8.

---

# 71. Native Backend Independence

The reference interpreter defines observable Kaj behavior, but future compiled backends do not need to use Python representations.

Future:

```text
Kaj frontend
   ↓
IR
   ├── reference interpreter semantics
   └── native backend
```

Both should agree on Kaj-visible results.

---

# 72. Factorial Execution Walkthrough

For:

```kaj
factorial(5)
```

runtime conceptually performs:

```text
call factorial with n = 5
    n <= 1 → false
    evaluate 5 * factorial(4)

call factorial with n = 4
    n <= 1 → false
    evaluate 4 * factorial(3)

call factorial with n = 3
    ...

call factorial with n = 1
    n <= 1 → true
    return 1

unwind:
2 * 1 = 2
3 * 2 = 6
4 * 6 = 24
5 * 24 = 120
```

Then:

```kaj
print(...)
```

writes:

```text
120
```

---

# 73. Source of Truth

For Kaj v0 reference execution:

```text
docs/internals/interpreter.md
        +
interpreter tests
        +
interpreter implementation
```

must agree.

Primitive static semantics remain defined by:

```text
docs/language/primitive-types.md
docs/language/functions.md
```

The interpreter must implement those semantics rather than redefine them.

---

# 74. Checkpoint 8 Definition of Done

Checkpoint 8 is complete when:

```text
[ ] Python reference interpreter implemented
[ ] explicit runtime environment implemented
[ ] environment uses resolved symbol identity where practical
[ ] module environment implemented
[ ] function call environments implemented
[ ] nested block environments implemented

[ ] Int literal executes
[ ] Decimal literal executes exactly
[ ] String literal executes
[ ] Bool literal executes
[ ] None literal executes

[ ] let binding executes
[ ] var binding executes
[ ] identifier lookup executes
[ ] identifier assignment executes
[ ] compound identifier assignment executes
[ ] immutable mutation remains guarded

[ ] + executes
[ ] - executes
[ ] * executes
[ ] / executes
[ ] % executes
[ ] ** executes
[ ] unary + executes
[ ] unary - executes
[ ] not executes
[ ] equality executes
[ ] numeric comparisons execute
[ ] and/or short-circuit

[ ] Int -> Decimal promotion materialized
[ ] Decimal uses decimal.Decimal
[ ] no Python float leakage
[ ] Int / Int yields Decimal runtime value

[ ] if executes
[ ] while executes
[ ] block scopes execute correctly

[ ] top-level functions installed before execution
[ ] function calls execute
[ ] positional arguments execute
[ ] named arguments use semantic parameter mapping
[ ] argument expressions evaluate left-to-right
[ ] fresh call frame created per invocation
[ ] self recursion executes
[ ] mutual recursion can execute
[ ] var parameters are mutable local bindings
[ ] var parameters do not mutate callers

[ ] return exits function immediately
[ ] return value executes
[ ] bare return yields None
[ ] None function fallthrough yields None
[ ] return-boundary Int -> Decimal conversion materialized
[ ] argument-boundary Int -> Decimal conversion materialized
[ ] assignment-boundary Int -> Decimal conversion materialized

[ ] explicit host builtin scope introduced
[ ] print resolves as builtin
[ ] print type checking supported narrowly
[x] print accepts one Kaj-displayable value, including controlled structured values
[ ] print returns None
[ ] output sink is testable/capturable
[ ] print formatting deterministic

[ ] runtime error model implemented
[ ] division by zero is structured
[ ] raw Python runtime exceptions do not leak for expected Kaj failures

[ ] unsupported future AST nodes do not gain accidental Python semantics
[ ] no eval/exec used
[ ] no Python-source transpilation used

[ ] factorial acceptance program prints 120
[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] Checkpoints 0-7 remain passing
```
