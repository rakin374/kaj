# 3. Syntax, Keywords, and Type System

## 3.1 Syntax goals

Kaj syntax should be compact, readable, unambiguous, easy for humans to review, and easy for both parsers and LLMs to generate.

## 3.2 Blocks use braces

Kaj should not use indentation as syntax.

```kaj
if ready {
    run()
}
```

Whitespace is formatting, not semantics.

## 3.3 Semicolons

Semicolons should not be required for ordinary statements. The canonical formatter should not emit them unless a later grammar requirement justifies it.

## 3.4 Comments

Proposed:

```kaj
// single-line

/*
multiline
*/

/// documentation comment
fn example() { ... }
```

## 3.5 Strings

Basic:

```kaj
"hello"
```

Interpolation:

```kaj
"Pay {invoice.amount} for {invoice.unit}?"
```

Non-renderable values such as secrets must be rejected by the compiler/runtime.

## 3.6 Numeric literals

Proposed:

```kaj
10          // Int
10.5        // Decimal
6.35%       // Percent
$825.00     // Money<USD>
EUR 120.00  // Money<EUR>
```

Decimal should be the default fractional numeric type rather than binary floating point.

## 3.7 Physical/unit literals

Long-term:

```kaj
2 meters
5 seconds
0.4 meters / second
30 degrees
```

The first implementation can begin with `Duration`, `Money`, and `Percent`.

## 3.8 Proposed hard-reserved keywords

```text
let
var

fn
return

if
else
when

for
in
while

break
continue

match
case

true
false
none

and
or
not
is

import
from
as
use

type
enum

task
step

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

try
catch
```

This is a working set, not a permanent freeze.

## 3.9 Contextual keywords

Prefer contextual treatment for words such as:

```text
goal
success
invariant

after
before
until

recurse
complete
block
wait

exists
confirmed

user
parallel
timeout
limit
where
```

For example, outside a task contract this should remain legal:

```kaj
let success = 0.95
```

## 3.10 Capability verbs are not reserved

Do not reserve:

```text
open
close
click
navigate
scroll
grasp
move
rotate
send
pay
buy
speak
listen
```

Use capability namespaces:

```kaj
web.open(...)
robot.move_to(...)
mail.send(...)
```

## 3.11 Boolean operators

Prefer readable forms:

```kaj
if authenticated and account.active {
    ...
}

if not page.loading {
    ...
}
```

## 3.12 No implicit truthiness

Kaj should require real Boolean conditions.

Avoid Python-style ambiguity:

```kaj
// invalid or discouraged
if items {
    ...
}
```

Prefer:

```kaj
if items.count > 0 {
    ...
}
```

## 3.13 Optional existence

Readable forms:

```kaj
if payment_url exists {
    ...
}

if result is none {
    ...
}
```

The type checker should narrow values after successful checks.

# 3.14 Type philosophy

Kaj should be:

```text
strongly typed
statically checked by default
aggressively inferred
explicit at important boundaries
able to opt into Dynamic/Any where genuinely needed
```

Kaj should feel lightweight without deferring basic correctness until runtime.

## 3.15 Local inference

```kaj
let name = "Kaj"
let count = 10
let amount = $825.00
let active = true
```

Compiler view:

```text
name   : String
count  : Int
amount : Money<USD>
active : Bool
```

## 3.16 Function boundaries

Prefer explicit parameter types at reusable interfaces:

```kaj
fn calculate_tax(amount: Money<USD>, rate: Percent) {
    return amount * rate
}
```

Return types may be inferred when unambiguous.

Explicit return type remains allowed:

```kaj
fn calculate_tax(amount: Money<USD>, rate: Percent) -> Money<USD> {
    return amount * rate
}
```

## 3.17 Primitive types

Baseline candidates:

```text
Bool
Int
Decimal
String
Bytes
```

Possible later:

```text
Float32
Float64
BigInt
```

## 3.18 Domain types

Early useful types:

```text
Money<C>
Percent
Duration
Date
DateTime
Url
Domain
```

Long-term physical types:

```text
Length
Area
Volume
Velocity
Acceleration
Mass
Force
Angle
Temperature
Pose
Trajectory
```

## 3.19 Collections

Baseline:

```text
List<T>
Map<K,V>
Set<T>
Optional<T>
Result<T,E>
```

## 3.20 Optionals instead of unrestricted null

```kaj
let result: Optional<Product> = none

if result exists {
    print(result.name)
}
```

## 3.21 Strong typing and coercions

Kaj should reject surprising coercions.

Invalid:

```kaj
"10" + 5
```

Invalid:

```kaj
2 meters + 5 seconds
```

Invalid:

```kaj
$100 + EUR 50.00
```

unless an explicit conversion operation exists.

## 3.22 Money

Money should not be a floating scalar.

Conceptually:

```kaj
let price = $825.00
```

becomes a typed value such as:

```text
Money<USD>(minor_units = 82500)
```

Currency mismatch must be explicit.

## 3.23 Percent

```kaj
let tax = subtotal * 6.35%
let discount = price * 15%
```

`Percent` should be a real type.

## 3.24 Dimensional typing

Long-term:

```kaj
let distance = 2.5 meters
let speed = 0.5 meters / second
let duration = distance / speed
```

Compiler derives `Duration`.

## 3.25 Secrets

Secrets must not be ordinary strings.

Potential types:

```text
Secret<T>
Credential
AuthTokenRef
PrivateKeyRef
```

The LLM/source should normally carry secure references rather than raw bytes.

This should fail:

```kaj
inform user "{credential.password}"
```

with a diagnostic such as:

```text
SECRET_VALUE_NOT_RENDERABLE
```

## 3.26 Dynamic data

Kaj should provide an explicit escape hatch:

```kaj
let payload: Dynamic = json.parse(raw)
let user = payload.decode<User>()
```

Effectful agent boundaries should strongly prefer typed values.

## 3.27 User-defined types

Proposed:

```kaj
type Product {
    name: String
    price: Money<USD>
    url: Url
}
```

Enums:

```kaj
enum PaymentStatus {
    pending
    confirmed
    declined
}
```

Rich enum payloads later:

```kaj
enum PaymentResult {
    Confirmed(Receipt)
    Declined(Reason)
    Uncertain
}
```

## 3.28 Generics

Expected:

```kaj
fn first<T>(items: List<T>) -> Optional<T> {
    ...
}
```

Generic constraints/traits should be designed only after the core type model is proven.

## 3.29 Type states

Agent systems may eventually benefit from state-refined types:

```text
Payment<Prepared>
Payment<Submitted>
Payment<Verified>
Fact<Money, Confirmed>
```

V0.x can model most of this as runtime/task-memory state before adopting advanced static typestate.
