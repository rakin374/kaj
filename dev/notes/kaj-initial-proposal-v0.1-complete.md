# Kaj Initial Proposal v0.1 — Complete Documentation Set

> Concatenated copy of the full initial proposal documentation.

---

# 0. Kaj Initial Language Proposal

## Proposal statement

Kaj is an independent, open-source programming language for ordinary computation and intelligent-agent work.

Its distinctive focus is the reliable expression of:

- goals,
- plans,
- computation,
- loops and recursion,
- mathematics,
- external-world actions,
- observations,
- evidence-backed knowledge,
- human collaboration,
- verification,
- recovery,
- and optional world-model prediction.

Kaj should remain general enough for web agents, robotics, vision/navigation, audio systems, simulation, API automation, filesystem work, and future environments.

## Initial technical direction

```text
Paradigm:
  imperative core + declarative contracts

Typing:
  strongly typed, static-by-default, aggressively inferred

State:
  immutable `let` by default, explicit `var`

Computation:
  functions, math, collections, loops, recursion, pattern matching

Agent semantics:
  task, step, goal, success, require, expect, verify

Human semantics:
  ask, choose, confirm, inform, handoff

Knowledge semantics:
  observe, learn, provenance, conflict preservation

Effects:
  explicit and capability-based

Capabilities:
  `use web`, later vision/robot/audio/etc.

Model integration:
  LLM initially emits schema-constrained Kaj AST JSON

Compilation:
  AST/source → typed semantic AST → Task IR

Execution:
  Task IR → host policy/runtime → capability provider

World models:
  optional predict-before-act and verify-after-act layer

CLI:
  `kaj file.kaj`

Source extension:
  `.kaj`
```

## First implementation philosophy

Build semantics from the inside out:

```text
AST
→ type system
→ effect model
→ task semantics
→ Task IR
→ formatter
→ Web capability
→ host integration
→ source parser
→ CLI/editor tooling
```

This lets Kaj immediately serve model-generated plans without freezing source syntax prematurely.

## Project boundary

Kaj should be its own repository and project.

```text
Kaj
 ↑
Berkbrain
 ↑
Chalok
```

Kaj must not depend on Berkbrain, Chalok, FastAPI, PostgreSQL, or WebKit.

Berkbrain is the first host. Chalok Web is the first production capability/runtime.

## Initial open-source posture

Proposed:

```text
Apache-2.0
maintainer-led governance
public Kaj Improvement Proposal (KIP) process
public specification
public reference compiler
public conformance tests
```

A foundation is not required at project inception.

## Definition of success for Kaj 0.1

Kaj 0.1 should make it possible to:

1. represent typed ordinary programs and tasks as AST,
2. reject invalid type/effect combinations,
3. lower valid programs into deterministic Task IR,
4. emit canonical human-readable `.kaj` source,
5. run ordinary pure Kaj computations,
6. express task contracts and structured human interactions,
7. define one real capability family: Web,
8. integrate with a host runtime without Kaj depending on that host.

---

# 1. Vision and Design Principles

## 1.1 The problem Kaj is designed around

Ordinary programming languages generally assume that execution happens over values and APIs whose behavior is mostly specified by software contracts.

Agent programs often operate differently:

```text
observe uncertain world
        ↓
reason
        ↓
choose action
        ↓
possibly ask human
        ↓
perform effect
        ↓
world changes
        ↓
observe again
        ↓
verify
        ↓
continue / replan
```

A web page may change unexpectedly. A robot can encounter a new obstacle. A payment request may time out after being accepted. An LLM can infer something incorrectly. A user can interrupt and alter the task halfway through.

Kaj should make those realities part of the language/runtime model rather than treating them as miscellaneous library conventions.

## 1.2 Why not only JSON

JSON is excellent for LLM structured output and machine interchange. It is poor as a long-form language for humans.

A large plan represented only as JSON becomes verbose, visually noisy, and difficult to review or author.

Kaj therefore has two primary forms:

```text
Kaj source        ← human-facing
Kaj AST / JSON    ← machine/model-facing
```

Both express the same semantics.

## 1.3 Why not only Python

Python is a great language. Kaj has a narrower opportunity: make agent execution concepts first-class.

Kaj can let the compiler/runtime understand:

- pure computation vs external effects,
- task goals,
- success criteria,
- preconditions,
- postconditions,
- expected outcomes,
- verification,
- observations,
- durable facts,
- provenance,
- human questions,
- human confirmations,
- handoffs,
- execution budgets,
- uncertainty,
- recovery,
- world-model predictions.

Python can model all of these through libraries, but Python itself does not generally assign them privileged semantics.

## 1.4 Imperative core, declarative contracts

Kaj should primarily be imperative because external-world execution is ordered.

```kaj
web.open(invoice.url)
observe web.page as portal
verify portal.amount == invoice.amount
confirm user "Pay {invoice.amount}?"
web.submit(payment)
```

The order matters.

But some concepts are naturally declarative:

```kaj
task pay_invoice {
    goal {
        "Pay the outstanding invoice."
    }

    success {
        payment is verified
    }

    step pay {
        require invoice.amount is confirmed

        ...

        expect {
            confirmation.amount == invoice.amount
        }
    }
}
```

Kaj should combine imperative execution with design-by-contract-like agent semantics.

## 1.5 Readability is a correctness feature

Kaj programs may be model-generated but human-reviewed.

Prefer:

```kaj
require invoice.amount is confirmed
```

over opaque framework boilerplate.

The syntax should be readable without sacrificing precise AST semantics.

## 1.6 Static guarantees without annotation noise

Kaj should aim for:

```text
strongly typed
statically checked by default
aggressively inferred
explicit at important boundaries
Dynamic/Any escape hatch where necessary
```

Typical code should be concise:

```kaj
let amount = $825.00
let tax = amount * 6.35%
```

The compiler still knows precise types before execution.

## 1.7 Immutable by default

```kaj
let value = 10
```

Use explicit mutability only when required:

```kaj
var attempts = 0
```

This helps both humans and models reason about programs and simplifies recovery.

## 1.8 Effects are explicit

Pure computation:

```kaj
fn total(items: List<Money<USD>>) {
    return sum(items)
}
```

Effectful task work:

```kaj
step submit_order(order: Order) {
    web.submit(order)
}
```

A pure function should not quietly open a browser or move a robot.

## 1.9 Capability verbs are not core keywords

Kaj should not permanently reserve every domain action.

These should be capability calls:

```kaj
web.open(...)
robot.move_to(...)
vision.locate(...)
audio.render(...)
```

This keeps the core language general.

## 1.10 External-world truth is evidence-backed

Kaj should distinguish:

```text
binding      temporary program value
observation  evidence from external world
fact         durable task knowledge
```

The language/model should not be able to turn an unsupported guess into canonical truth by assignment alone.

## 1.11 Verification is first-class

A dispatched action is not necessarily a successful action.

Kaj should make post-action checking natural:

```kaj
expect {
    confirmation.amount == invoice.amount
}

verify confirmation
```

## 1.12 Humans are part of execution

Kaj should treat human collaboration as structured execution rather than free-form chat only.

Initial human primitives:

```text
inform
ask
choose
confirm
handoff
```

## 1.13 Do not ban expressive programming features for safety

Kaj should support loops, recursion, functions, mathematics, and reusable abstractions.

Safety comes from:

- runtime budgets,
- type/effect checking,
- host permissions,
- human interruption,
- verification,
- idempotency,
- recovery semantics,
- lower-level physical safety systems.

## 1.14 Language personality

Kaj should feel:

- concise like Python,
- explicit about effects,
- readable like a good workflow language,
- strongly typed without ceremony,
- structured enough for LLMs,
- general enough for both digital and physical agents.

## 1.15 Things Kaj should avoid

Avoid:

- significant indentation as syntax,
- required semicolons everywhere,
- implicit truthiness,
- silent numeric/string coercion,
- unrestricted `null`,
- secret values treated as ordinary strings,
- hidden privilege encoded in source,
- arbitrary model prose executed directly,
- capability-specific global keywords,
- invisible infinite retries,
- canonical task state stored only as LLM prose,
- assuming a prediction equals an observation.

## 1.16 Long-term role

Kaj can become a common structured planning/execution representation between intelligent models and environments:

```text
Planner
  ↓
Kaj
  ↓
Task IR
  ↓
Policy / prediction / runtime
  ↓
Web | Robot | Vision | Audio | Simulation | APIs
```

---

# 2. Language and Execution Model

## 2.1 Kaj is a real runnable language

The normal user experience should be:

```bash
kaj hello.kaj
```

The internal implementation can be richer:

```text
source
  ↓
parse
  ↓
AST
  ↓
name resolution
  ↓
type/effect checking
  ↓
semantic validation
  ↓
Task IR / executable IR
  ↓
runtime
```

Kaj should not merely be a plan file consumed by Berkbrain.

## 2.2 Program categories

Kaj should support three overlapping categories.

### Ordinary computation

```kaj
let values = [10, 20, 30]
print(mean(values))
```

### Effectful scripts

```kaj
use filesystem

let content = filesystem.read("report.txt")
print(content)
```

### Goal-directed tasks

```kaj
use web

task research {
    goal {
        "Find three matching products."
    }

    success {
        products.count >= 3
    }

    ...
}
```

A file may combine all three.

## 2.3 Top-level execution

Proposed V0.x behavior: top-level executable statements run in source order.

```kaj
let name = "world"
print("Hello, {name}")
```

Running:

```bash
kaj hello.kaj
```

executes the program naturally.

Functions/tasks may be declared without automatically running.

Potential CLI later:

```bash
kaj file.kaj
kaj run file.kaj
kaj run file.kaj::research
```

## 2.4 Pure vs capability-dependent execution

Pure Kaj:

```kaj
fn square(x: Decimal) {
    return x * x
}

print(square(8))
```

can run on the ordinary runtime.

Capability-dependent Kaj:

```kaj
use web
web.open("https://example.com")
```

requires a provider implementing `web`.

Conceptually:

```text
Kaj language
+ runtime
+ capability provider
= executable effectful program
```

## 2.5 Runtime providers

A capability can have multiple providers.

```text
web
 ├── WKWebView provider
 ├── Playwright provider
 └── remote cloud-browser provider
```

The source program should target the capability contract, not one vendor/runtime.

## 2.6 Compilation strategy

Kaj initially does not need native machine-code compilation.

Early implementation can lower into typed IR interpreted/orchestrated by the runtime.

Long-term options may include:

- interpreter,
- bytecode VM,
- native compilation for pure code,
- JIT,
- robot/simulator-specific lowering,
- distributed runtime execution.

The language should not depend on one backend.

## 2.7 Deterministic semantics vs nondeterministic environments

Pure expression:

```kaj
let x = 2 + 2
```

must be deterministic.

External observation:

```kaj
observe vision.scene as room
```

depends on reality and time.

Kaj's effect system should preserve this distinction.

## 2.8 Host/runtime responsibilities

The compiler answers:

> Is this program valid and what does it mean?

The host runtime answers:

> Which capabilities exist, what authority exists, and how should valid effects be carried out?

Host responsibilities can include:

- task persistence,
- user permissions,
- authentication,
- browser/robot instances,
- secrets,
- task memory,
- world models,
- recovery,
- observability,
- usage accounting.

## 2.9 Hosted server authority

For Berkbrain/Chalok, authoritative compilation and policy should be server-side:

```text
user
 ↓
planner LLM
 ↓
structured Kaj AST
 ↓
server Kaj compiler
 ↓
Task IR
 ↓
server policy / permissions / safety
 ↓
authorized action envelope
 ↓
client browser runtime
```

Clients may locally parse/check for UX but should not become the sole authorization boundary for consequential actions.

## 2.10 Local execution

Kaj must remain usable outside Berkbrain.

Future possibilities:

```bash
kaj run research.kaj --runtime playwright
kaj run robot_task.kaj --runtime ros
kaj run simulation.kaj
```

## 2.11 Execution budgets

Every effectful host should impose budgets such as:

```text
max elapsed time
max actions
max loop iterations
max recursion depth
max model calls
max browser navigations
max external requests
max monetary exposure
```

Source can request limits, but source never overrides hard host limits.

## 2.12 Interruptibility

Long-running Kaj tasks must be:

- pausable,
- cancellable,
- supersedable,
- checkpointable,
- resumable,
- interruptible by human input.

## 2.13 Planning need not be whole-program upfront

In uncertain environments, Kaj hosts should support incremental task patches:

```text
initial task
 ↓
execute / observe
 ↓
planner adds or modifies task nodes
 ↓
validate patch
 ↓
continue
```

This is preferable to generating a rigid giant plan at the start.

---

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

---

# 4. Computation, Tasks, Effects, and Human Interaction

## 4.1 Ordinary scripting is first-class

Kaj is not merely a workflow notation.

```kaj
fn greet(name: String) {
    return "Hello, {name}"
}

let users = ["A", "B", "C"]

for user in users {
    print(greet(user))
}
```

## 4.2 Bindings

Immutable by default:

```kaj
let x = 10
```

Explicit mutation:

```kaj
var attempts = 0
attempts += 1
```

## 4.3 Functions

```kaj
fn add(a: Int, b: Int) {
    return a + b
}
```

The initial effect model should treat ordinary `fn` as pure/default computation.

## 4.4 If / else

```kaj
if amount > $500 {
    print("large")
} else {
    print("small")
}
```

## 4.5 Loops

Kaj should support real loops.

```kaj
for obligation in obligations {
    process(obligation)
}
```

```kaj
while search.has_next_page {
    collect(search.results)
    search.next()
}
```

Filtering syntax may be supported:

```kaj
for obligation in obligations
    where obligation.status == due
{
    process(obligation)
}
```

## 4.6 Break and continue

```kaj
for item in items {
    if should_skip(item) {
        continue
    }

    if finished(item) {
        break
    }
}
```

## 4.7 Recursion

Pure recursion is ordinary:

```kaj
fn factorial(n: Int) -> Int {
    if n <= 1 {
        return 1
    }

    return n * factorial(n - 1)
}
```

Effectful task recursion may use explicit syntax so recursive world interaction is visible:

```kaj
recurse inspect_category(child)
```

## 4.8 Execution budgets, not banned expressiveness

Loops and recursion are valuable. The runtime should enforce budgets rather than forbidding them.

Possible budget dimensions:

```text
iterations
recursion depth
elapsed time
actions
model calls
navigation hops
resource usage
```

Source may express narrower limits:

```kaj
while page.loading
    limit 5
{
    wait 1 second
}
```

Exact syntax is still proposed.

## 4.9 Pattern matching

Kaj should support pattern matching early because agent operations naturally return typed outcomes.

```kaj
match payment_result {
    case Confirmed(receipt) {
        print(receipt.id)
    }

    case Declined(reason) {
        inform user "Payment declined: {reason}"
    }

    case Uncertain {
        block task
    }
}
```

## 4.10 Error handling

General code may use:

```kaj
try {
    ...
} catch error {
    ...
}
```

Capability/environment outcomes should generally prefer typed `Result`/enum states where recovery behavior matters.

## 4.11 Math

Kaj should make mathematics easy.

```kaj
let prices = [$120.00, $85.50, $40.00]
let subtotal = sum(prices)
let tax = subtotal * 6.35%
let total = subtotal + tax
```

Useful initial math/collection functions:

```text
abs
min
max
sum
mean
round
floor
ceil
clamp
sqrt
pow
count
sort
filter
map
```

Long-term Kaj can add statistics, vectors, matrices, geometry, probability, and physical units.

# 4.12 Task semantics

`task` is a defining Kaj construct.

```kaj
task pay_housing_dues {
    goal {
        "Pay every currently due housing obligation."
    }

    success {
        every obligations.payment is verified
        no unresolved conflicts
        no uncertain actions
    }

    ...
}
```

A task may carry:

- goal,
- success criteria,
- steps,
- durable state,
- human interactions,
- checkpoints,
- recovery metadata,
- task memory,
- verification state.

## 4.13 Goal

`goal` expresses intent.

```kaj
goal {
    "Find the best monitor under $300."
}
```

## 4.14 Success

`success` defines objective completion conditions.

```kaj
success {
    candidates.count >= 3
    recommendation exists
    no unresolved conflicts
}
```

A planner should not simply declare completion while these are unmet.

## 4.15 Invariants

Potential:

```kaj
invariant {
    total_spend <= $1,000
}
```

Host hard policies always outrank source invariants.

## 4.16 Steps

```kaj
step discover {
    ...
}
```

Typed input:

```kaj
step pay(invoice: Invoice) {
    ...
}
```

Dependency:

```kaj
step pay after discover {
    ...
}
```

The host can compile sequential-looking source into a task DAG where dependencies permit.

## 4.17 Preconditions: `require`

```kaj
require invoice.amount is confirmed
require payment_account is confirmed
require balance >= invoice.amount
```

A failed requirement blocks progression.

## 4.18 Postconditions: `expect`

```kaj
expect {
    confirmation.visible
    confirmation.amount == invoice.amount
}
```

`expect` declares what should become true after an effect.

## 4.19 Verification: `verify`

```kaj
verify confirmation.amount == invoice.amount
```

or domain-aware:

```kaj
verify payment
```

Verification establishes truth from evidence; it is not a mere assertion of belief.

# 4.20 Effects

Kaj must distinguish pure computation from external effects.

Pure:

```kaj
fn total(items: List<Money<USD>>) {
    return sum(items)
}
```

Effectful:

```kaj
step submit_order(order: Order) {
    web.submit(order)
}
```

This should be rejected:

```kaj
fn total(items: List<Money<USD>>) {
    web.open("https://example.com")
    return sum(items)
}
```

Possible diagnostic:

```text
EFFECT_NOT_ALLOWED
Pure function `total` cannot invoke capability `web`.
```

Long-term the compiler may track typed effect sets.

# 4.21 Three kinds of agent state

Kaj should distinguish:

### Binding

```kaj
let total = sum(items.amount)
```

Temporary program value.

### Observation

```kaj
observe web.page as checkout
```

External-world evidence at a point in time.

### Fact

```kaj
learn invoice.amount from checkout.balance
```

Durable task knowledge backed by provenance.

## 4.22 Observations are ephemeral

Observations may become stale and should carry metadata such as source/time/world version.

Examples:

- web snapshot,
- camera scene,
- robot joint state,
- API response,
- audio scene.

## 4.23 Facts are durable and versioned

A host fact should carry some combination of:

```text
key/value
type
source/evidence
authority
status
timestamp
scope
version
```

Possible fact states:

```text
OBSERVED
CONFIRMED
SUPERSEDED
CONFLICTED
STALE
INVALID
```

## 4.24 Facts require provenance

The planner should not invent canonical truth with an unsupported assignment.

Prefer:

```kaj
learn invoice.amount
    from portal.balance
```

or explicit user input.

## 4.25 Conflicts are preserved

If an email says `$825` and a portal says `$850`, do not overwrite one with the other.

Expose a conflict:

```kaj
if invoice.amount is conflicted {
    ask user
        "The notice says $825 but the portal says $850. Which amount should I use?"
    as amount_resolution
}
```

# 4.26 Human interaction

Kaj should treat humans as first-class collaborators.

Initial primitives:

```text
inform
ask
choose
confirm
handoff
```

### `inform`

Non-blocking progress:

```kaj
inform user
    "I found two outstanding obligations."
```

### `ask`

Request missing information:

```kaj
ask user
    "Which account should I use?"
as payment_account
```

### `choose`

Structured options:

```kaj
choose user payment_account
    from available_accounts
```

### `confirm`

Consequential checkpoint:

```kaj
confirm user
    "Pay {invoice.amount} to {invoice.payee}?"
```

A host permission system may inject confirmations even when source omits them.

### `handoff`

Human performs a user-only action:

```kaj
handoff user for sign_in
    on payment_portal
```

Typical uses:

- login,
- MFA,
- CAPTCHA,
- credential entry,
- physical manual intervention.

## 4.27 Human interactions as typed task nodes

A host should give interactions stable identity and fields such as:

```text
interaction_id
type
scope
expected answer type
blocking nodes
status
response
```

This prevents ambiguity like "use the second one".

## 4.28 Live corrections

Human feedback may alter execution at any time.

Example:

```text
"Do not pay Unit B yet."
```

The host should persist a user-authoritative constraint, invalidate stale execution where necessary, and replan rather than blindly continuing.

## 4.29 Completion and blocking

Potential:

```kaj
complete
```

The runtime verifies success criteria before completion.

Potential:

```kaj
block task
    "The payment amount is unresolved."
```

Blocked tasks remain resumable.

---

# 5. Capabilities, World Models, and Runtime

# 5.1 Capabilities make Kaj general

Kaj core should not know how to browse, move a robot, or transform audio.

Instead:

```kaj
use web
use vision
use robot
```

loads typed environmental capability contracts.

## 5.2 `import` vs `use`

Proposed distinction:

```kaj
import math
```

means ordinary code/module dependency.

```kaj
use web
```

means an effectful environmental capability requirement.

## 5.3 Capability contract

A capability should define:

```text
name
version
types
operations
observations
effects
errors
serialization
provider interface
policy metadata
```

## 5.4 Web capability

The first production capability.

Potential types:

```text
Web.Tab
Web.Page
Web.Element
Web.Form
Web.NavigationResult
Web.Download
```

Potential operations:

```text
web.open
web.close
web.switch
web.navigate
web.back
web.forward
web.reload

web.click
web.enter
web.select
web.scroll

web.observe
web.extract
```

The exact API must align with the real Chalok browser workspace/runtime rather than an imagined generic browser.

## 5.5 Vision capability

Future types:

```text
Vision.Scene
Vision.Object
Vision.Mask
Vision.BoundingBox
Vision.DepthMap
Vision.Track
```

Potential operations:

```text
vision.observe
vision.locate
vision.track
vision.segment
vision.measure
```

## 5.6 Robotics capability

Future types:

```text
Robot.Pose
Robot.Grasp
Robot.Trajectory
Robot.JointState
Robot.Force
```

Potential operations:

```text
robot.move_to
robot.grasp
robot.release
robot.rotate
robot.stop
robot.observe_state
```

## 5.7 Navigation capability

Potential types:

```text
Location
Route
Map
Obstacle
Path
```

Potential operations:

```text
navigation.plan
navigation.follow
navigation.stop
navigation.localize
```

## 5.8 Audio capability

Potential types:

```text
Audio.Scene
Audio.Source
Audio.Clip
Audio.Transform
```

Potential operations:

```text
audio.observe
audio.locate
audio.transform
audio.render
audio.verify
```

## 5.9 Providers

The language targets capability contracts; hosts provide implementations.

```text
web
 ├── WKWebView
 ├── Playwright
 └── cloud browser
```

```text
robot
 ├── ROS provider
 ├── simulator provider
 └── proprietary hardware provider
```

## 5.10 Capability versioning

Programs/AST should record requirements:

```text
web@1
vision@1
```

## 5.11 Capability operations and permissions

A low-level action name may not be sufficient for authorization.

Example:

```text
web.click(button)
```

may semantically classify as:

```text
commerce.place_paid_order
```

The host policy engine uses semantic context, not just raw verbs.

## 5.12 Capability SDK

Long-term open-source ecosystem should support third-party providers without compiler modification.

Potential ecosystems:

- ROS,
- Playwright,
- Home Assistant,
- filesystem,
- shell,
- email,
- calendar,
- databases,
- cloud APIs,
- simulation,
- CAD,
- industrial controllers.

# 5.13 Kaj and world models

Kaj is not a world model.

Kaj answers:

> What does the program propose, what must already be true, and what outcome is expected?

A world model answers:

> Given the current state and proposed action, what is likely to happen next?

The runtime answers:

> What actually happened?

## 5.14 Transition model

Conceptually:

```text
(state_t, action_t) → predicted_state_t+1
```

Kaj gives the system a structured action and explicit expected outcomes.

## 5.15 Predict-before-act loop

Long-term:

```text
Kaj action
   ↓
WorldModel.predict
   ↓
predicted next state
   ↓
compare with:
  goal
  invariant
  policy
  safety
  expect clauses
   ↓
execute or replan
```

## 5.16 Post-action loop

```text
actual observation
   ↓
compare with prediction
   ↓
compare with Kaj expectations
   ↓
verification
   ↓
task memory update
   ↓
continue / replan
```

## 5.17 Web example

```kaj
web.click(place_order_button)

expect {
    order.status == confirmed
}
```

A web world model may predict likely navigation/effect semantics. Permission policy still decides whether the action is allowed.

## 5.18 Robotics example

```kaj
robot.grasp(cup)

expect {
    robot.holds(cup)
    cup.position follows robot.gripper
}
```

A world model may predict grasp success/collision risk before execution.

## 5.19 Navigation example

```kaj
navigation.follow(route)

expect {
    distance_to(destination) decreases
    collision == false
}
```

## 5.20 Model-agnostic language

Kaj source should not care whether the host uses:

- deterministic simulation,
- specialist world models,
- multimodal foundation models,
- physics engines,
- learned latent dynamics,
- or no predictor at all.

## 5.21 Training data connection

Kaj execution can generate structured trajectories:

```text
task state
observation
Kaj action
permission decision
prediction
actual result
verification
human feedback
```

This can become high-quality training/evaluation data for future planners and world models.

## 5.22 Predictions are not facts

Preserve:

```text
PREDICT → EXECUTE → OBSERVE → VERIFY
```

Never:

```text
PREDICT → ASSUME SUCCESS
```

---

# 6. AST, Task IR, and LLM Integration

# 6.1 AST-first design

Kaj should be defined semantically from the AST inward rather than inventing pretty syntax first and discovering semantics later.

The initial production planner contract should be:

```text
LLM
 ↓
schema-constrained JSON
 ↓
Kaj AST
```

This avoids requiring frontier models to already be fluent in a brand-new textual language.

## 6.2 Two serializations, one meaning

```text
                 Kaj AST
               /         \
              /           \
        JSON form       source form
        machine         human
```

Human `.kaj` source parses into the same AST.

The canonical formatter emits source from AST.

## 6.3 AST node families

Initial semantic model should include nodes such as:

```text
Program
Import
UseCapability
TypeDeclaration
EnumDeclaration
FunctionDeclaration
TaskDeclaration
StepDeclaration

LetBinding
VarBinding

If
For
While
Match
Return
Break
Continue

Call
MemberAccess
BinaryExpression
UnaryExpression
Literal
Reference

Goal
Success
Invariant
Require
Expect
Verify

Observe
Learn

Ask
Choose
Confirm
Inform
Handoff
```

## 6.4 Stable IDs for durable task nodes

Agent task nodes should support stable IDs:

```json
{
  "node_id": "step_pay_unit_a",
  "kind": "step",
  "name": "pay_unit"
}
```

This supports:

- task patches,
- persistence,
- recovery,
- diagnostics,
- observability,
- model updates.

Ordinary expression nodes do not necessarily need durable IDs.

## 6.5 Example AST

Source:

```kaj
step choose_account {
    choose user payment_account
        from available_accounts

    require payment_account is confirmed
}
```

Possible JSON AST:

```json
{
  "kind": "step",
  "name": "choose_account",
  "body": [
    {
      "kind": "user_choice",
      "binding": "payment_account",
      "options": {
        "kind": "reference",
        "name": "available_accounts"
      }
    },
    {
      "kind": "require",
      "condition": {
        "kind": "state_predicate",
        "subject": {
          "kind": "reference",
          "name": "payment_account"
        },
        "state": "confirmed"
      }
    }
  ]
}
```

Exact schema should evolve through KIPs.

## 6.6 AST versioning

Every serialized AST should include:

```json
{
  "language": "kaj",
  "language_version": "0.1",
  "ast_schema_version": 1
}
```

## 6.7 Compiler validation stages

1. schema validity,
2. node-shape validity,
3. name resolution,
4. type checking,
5. effect checking,
6. control-flow validation,
7. capability validation,
8. semantic validation,
9. IR lowering.

## 6.8 Diagnostics

Machine-readable diagnostic:

```json
{
  "code": "TYPE_MISMATCH",
  "severity": "error",
  "message": "web.navigate expects Url, received Money<USD>",
  "node_id": "action_42",
  "expected": "Url",
  "actual": "Money<USD>"
}
```

Source diagnostics additionally include spans/line-column information.

# 6.9 Task IR

IR means **Intermediate Representation**.

Kaj source and AST are designed for expression and readability.

Task IR is designed for deterministic execution machinery:

- validation,
- permissions,
- persistence,
- recovery,
- testing,
- world-model prediction,
- provider lowering.

## 6.10 Pipeline

```text
Kaj source / AST
      ↓
typed semantic AST
      ↓
compiler
      ↓
Task IR
      ↓
host policy/runtime
```

## 6.11 Why not execute the AST directly

The compiler should resolve source-level abstractions:

- names,
- types,
- aliases,
- capability references,
- control flow,
- task dependencies,
- effect categories,
- normalized expressions.

IR becomes a smaller and more stable runtime contract.

## 6.12 Generic IR operation families

Potential generic Task IR:

```text
Compute
Branch
Loop
CallPure

Action
Observe
Verify
Require
Expect

RequestHumanInput
RequestHumanChoice
RequestHumanConfirmation
RequestHumanHandoff
InformHuman

TaskNodeCreate
TaskNodeUpdate
MemoryMutationProposal

Wait
CompleteTask
BlockTask
```

## 6.13 Capability action IR

Conceptual:

```json
{
  "kind": "ACTION",
  "action_id": "a_123",
  "capability": "web",
  "operation": "navigate",
  "arguments": {
    "url": "https://example.com"
  }
}
```

## 6.14 Human interaction IR

```json
{
  "kind": "REQUEST_CONFIRMATION",
  "interaction_id": "i_77",
  "message": "Pay $825.00 for Unit A?",
  "blocks_action_id": "a_91"
}
```

## 6.15 Generic and capability-specific IR

Recommended layering:

```text
Task IR
  ↓
capability lowering
  ├── Web IR
  ├── Robot IR
  ├── Vision IR
  └── Audio IR
```

Not every capability needs a separate IR. Simple providers may consume generic Task IR directly.

## 6.16 IR is not authorization

IR says:

> This is the normalized effect the program proposes.

The host still decides:

> Is it allowed now?

## 6.17 Consequential action lifecycle

Hosts should track:

```text
PROPOSED
AUTHORIZED
DISPATCHED
EXECUTED
VERIFIED
```

plus:

```text
FAILED
REJECTED
INTERRUPTED
UNCERTAIN
```

## 6.18 UNCERTAIN

`UNCERTAIN` means an effect may have happened but cannot currently be verified.

Examples:

- network disconnect after payment submit,
- process crash after order placement,
- robot action executed while verification sensor failed.

Recovery reconciles before replay.

## 6.19 Idempotency

Effectful IR actions should carry stable action IDs. Providers may use those IDs for idempotent retry/deduplication.

## 6.20 Execution epochs

Effectful agent runs should carry a control epoch/lease. Human takeover or newer execution invalidates stale actions.

# 6.21 LLM planning

Kaj should not initially require an LLM to emit raw `.kaj` correctly.

Preferred:

```text
LLM
 ↓
structured AST JSON
 ↓
compiler
```

## 6.22 Models can still read Kaj

Model context can contain canonical Kaj source while response is constrained AST.

```text
LLM reads:
  beautiful Kaj

LLM writes:
  strict AST JSON
```

## 6.23 Correction loop

```text
LLM proposes AST
 ↓
compiler
 ↓
valid?
 ├─ yes → continue
 └─ no
      ↓
 structured diagnostics
      ↓
 model emits corrected patch
```

This reduces the need for immediate fine-tuning.

## 6.24 Incremental task patches

Prefer model responses such as:

```text
TaskPatch {
  base_task_version
  operations[]
}
```

Possible operations:

```text
ADD_STEP
ADD_DEPENDENCY
REPLACE_STEP
ADD_REQUIREMENT
ADD_USER_INTERACTION
ADD_MEMORY_MUTATION_PROPOSAL
MARK_STEP_SUPERSEDED
```

This prevents a model from repeatedly rewriting an entire long task state.

## 6.25 Model cannot rewrite canonical truth

Planner output can propose memory changes but does not directly mark unsupported facts confirmed or actions verified.

## 6.26 Fine-tuning later

Kaj execution can generate high-quality training records:

```text
user request
compiled task context
accepted AST patch
compiler diagnostics
permission decisions
actions
observations
verification
human feedback
final outcome
```

This can later train:

- Kaj-native planner models,
- cheaper distilled models,
- domain-specific models,
- world models.

## 6.27 Grammar-constrained raw Kaj later

Once useful, Kaj can publish formal grammar for constrained decoding.

Grammar validity still does not replace type/effect/semantic checking.

---

# 7. Compiler Architecture and Project Layout

## 7.1 Kaj is a standalone project

Kaj should not live inside the Berkbrain monorepo as an internal feature.

Recommended projects:

```text
Projects/
├── kaj/
├── berkbrain/
├── berkbrain-integration/
├── berkbrain-chalok/
├── berkbrain-prism/
└── berkbrain-sonic/
```

## 7.2 Dependency direction

```text
Kaj
 ↑
Berkbrain
 ↑
Chalok integration
```

Never the reverse.

Kaj must not import:

- Berkbrain models,
- FastAPI,
- SQLAlchemy,
- Chalok sessions,
- WebKit,
- user accounts.

## 7.3 Suggested repository layout

```text
kaj/
├── README.md
├── LICENSE
├── NOTICE
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
│
├── docs/
├── proposals/
├── grammar/
├── schemas/
├── examples/
│
├── kaj/
│   ├── ast/
│   ├── parser/
│   ├── types/
│   ├── compiler/
│   ├── ir/
│   ├── formatter/
│   ├── diagnostics/
│   └── capabilities/
│
├── tests/
└── pyproject.toml
```

## 7.4 Initial implementation language

Recommendation: Python reference compiler initially.

Reasons:

- fast iteration,
- existing backend ecosystem,
- easy AST/schema work,
- Pydantic-style validation available,
- compiler performance is not the bottleneck yet.

Do not start with LLVM or a Rust rewrite simply because Kaj is called a compiler.

## 7.5 Compiler pipeline

```text
source / AST JSON
    ↓
parse or deserialize
    ↓
schema validation
    ↓
name resolution
    ↓
type checking
    ↓
effect checking
    ↓
control-flow validation
    ↓
capability resolution
    ↓
semantic validation
    ↓
Task IR lowering
```

## 7.6 Compiler determinism

The compiler itself should not call an LLM.

Given the same:

```text
AST
compiler version
capability definitions
compilation environment
```

it should produce the same diagnostics/IR.

## 7.7 Compilation environment

The compiler should not query application databases.

Instead hosts supply an explicit compilation environment.

Conceptually:

```python
CompilationEnvironment(
    language_version=...,
    capabilities=...,
    symbols=...,
    types=...,
    host_features=...,
)
```

This keeps the compiler reusable and testable.

## 7.8 Compiler vs permission engine

Compiler:

> Is this program valid?

Permission engine:

> May this valid effect execute for this user and state?

Example:

```kaj
web.submit(payment)
```

can compile successfully while runtime returns:

```text
ASK
```

or:

```text
DENY
```

## 7.9 Compiler vs world model

Compiler:

> What does the proposed action mean?

World model:

> What is likely to happen?

Do not mix these responsibilities.

## 7.10 Compiler vs task memory

Compiler validates structure/types/references.

Task memory owns canonical durable state and evidence.

## 7.11 Host runtime responsibilities

Host runtimes may own:

- user identity,
- task persistence,
- run lifecycle,
- permission decisions,
- capability providers,
- task memory,
- human interaction delivery,
- secrets,
- world models,
- recovery,
- logs/metrics,
- billing/usage.

## 7.12 Berkbrain integration

Suggested host package:

```text
berkbrain/backend/app/kaj_runtime/
├── planner_adapter.py
├── compiler_adapter.py
├── execution_service.py
├── task_memory_adapter.py
├── permission_adapter.py
└── world_model_adapter.py
```

Berkbrain imports Kaj as a dependency.

## 7.13 Hosted Chalok path

```text
User request
 ↓
Chalok planner
 ↓
Kaj AST patch
 ↓
Kaj compiler
 ↓
Task IR
 ↓
Task memory
 ↓
PermissionEngine
 ↓
Browser workspace runtime
 ↓
Observation / verification
```

## 7.14 Text parser order

Do **not** make raw-text parsing the first implementation milestone.

Recommended order:

```text
AST JSON
→ compiler
→ Task IR
→ formatter
→ host integration
→ textual parser
```

This provides immediate production value while the source grammar remains fluid.

## 7.15 CLI architecture

Target UX:

```bash
kaj hello.kaj
kaj run hello.kaj
kaj check hello.kaj
kaj fmt .
kaj ast file.kaj
kaj ir file.kaj
```

`kaj hello.kaj` should be the simplest and canonical execution form.

## 7.16 Namespace collision fallback

Canonical executable is `kaj`.

Official fallback/compiler alias can be `kajc`.

Installers should never silently overwrite an unrelated existing `kaj` executable.

## 7.17 Formatter

Kaj should have one canonical formatter.

```bash
kaj fmt .
```

This reduces style fragmentation and creates cleaner datasets for model training.

## 7.18 Language server

Future `kajls` should provide LSP editor intelligence:

- errors,
- autocomplete,
- hover types,
- go to definition,
- find references,
- rename,
- code actions,
- capability completion.

It must reuse the compiler frontend rather than implementing its own parser/type checker.

## 7.19 Possible future Rust core

If Kaj becomes broadly embedded and portability/performance matter:

```text
Kaj compiler core (Rust)
 ├── Python bindings
 ├── Swift bindings
 ├── CLI
 ├── server runtime
 └── robotics runtime
```

This is explicitly deferred.

---

# 8. Security, Permissions, Verification, and Recovery

## 8.1 Core security boundary

Kaj source is a proposal for computation and effects.

It is not authority.

```text
potentially untrusted:
  LLM output
  user source
  packages
        ↓
compiler / semantic validation
        ↓
host permission / policy / safety
        ↓
authorized effect
```

## 8.2 Permission model

Hosts may classify semantic effects.

A low-level action such as:

```text
web.click(button)
```

may resolve to:

```text
commerce.place_paid_order
```

Policy can then return:

```text
ALLOW
ASK
DENY
```

## 8.3 Source cannot self-authorize

Kaj must have no construct equivalent to:

```kaj
web.submit(payment, bypass_permissions: true)
```

Source can request or describe effects; it cannot grant itself authority.

## 8.4 Human confirmation can be runtime-injected

Kaj source may explicitly say:

```kaj
confirm user
    "Pay {amount}?"
```

but the host may insert confirmation/approval even if source omitted it.

## 8.5 Secrets

Secrets belong in secure host mechanisms.

Kaj/model/task logs should see symbolic references, not raw:

- passwords,
- access tokens,
- private keys,
- MFA secrets.

## 8.6 Verification principle

Dispatch success is not real-world success.

```text
HTTP response received
≠
payment definitely succeeded
```

Kaj should model expected results and verification explicitly.

## 8.7 Expected outcome

```kaj
expect {
    confirmation.visible
    confirmation.amount == invoice.amount
}
```

## 8.8 Verification result

Internal states should include:

```text
VERIFIED
FAILED
UNCERTAIN
```

`UNCERTAIN` is not success.

## 8.9 Consequential preconditions

Before payment/order/message/delete/physical actions, hosts may require:

```text
entity confirmed
amount confirmed
destination confirmed
selected account confirmed
permission decision current
human approval resolved if required
```

Host rules may be stricter than source.

## 8.10 Consequential postconditions

After action:

```text
fresh observation
confirmation/receipt evidence
amount/destination match
unique result identity where available
memory update
```

## 8.11 Action lifecycle

Recommended:

```text
PROPOSED
AUTHORIZED
DISPATCHED
EXECUTED
VERIFIED
```

plus failure states.

## 8.12 Crash uncertainty

If a crash occurs after dispatch but before confirmation:

```text
submit payment
 ↓
connection lost
```

mark the action `UNCERTAIN`.

Never blindly replay consequential effects.

## 8.13 Idempotency

Every effectful action should have a stable action ID.

Providers should use idempotency/deduplication where supported.

## 8.14 Recovery resumes goals, not stale action sequences

After restart:

```text
stored task goal
+ verified progress
+ unresolved/uncertain effects
+ fresh observation
      ↓
reconcile
      ↓
replan safe next action
```

Do not blindly replay old browser clicks or robot commands.

## 8.15 Checkpoints

Checkpoint meaningful boundaries:

- step completion,
- verified action,
- human interaction creation/resolution,
- task-memory mutation,
- run pause,
- navigation commit,
- uncertain action.

## 8.16 Control leases/epochs

Human takeover or a newer planner run should invalidate stale autonomous commands.

## 8.17 Execution budgets

Hard limits protect against:

- infinite loops,
- runaway recursion,
- navigation storms,
- model-call storms,
- resource exhaustion,
- accidental financial exposure.

## 8.18 Package security

Kaj packages/capability providers are code and should be treated accordingly.

Hosts may require:

- dependency locking,
- provenance/signatures,
- review,
- sandboxing,
- declared capability scopes.

## 8.19 Robotics safety

Kaj must never replace lower-level physical safety mechanisms such as:

- emergency stops,
- certified safety controllers,
- collision avoidance,
- hardware interlocks,
- joint/mechanical limits.

Kaj is a higher-level planning/execution language.

## 8.20 Auditability

Hosts should preserve safe records of:

```text
task version
IR action
permission decision
human interaction
provider result
verification result
memory mutation
```

without logging secrets or unnecessary raw world state.

## 8.21 Core safety principle

> The more consequential an effect, the stronger the evidence, authorization, and post-action verification required before Kaj considers it successful.

---

# 9. Tooling, Open Source, Governance, and Versioning

# 9.1 Developer experience

Kaj should feel like a normal programming language from the shell.

Canonical:

```bash
kaj hello.kaj
```

Recommended early commands:

```bash
kaj run hello.kaj
kaj check hello.kaj
kaj fmt .
kaj ast file.kaj
kaj ir file.kaj
kaj version
```

Later:

```bash
kaj test
kaj repl
kaj capabilities
kaj doctor
```

## 9.2 Source extension

```text
.kaj
```

## 9.3 REPL

Eventually:

```bash
kaj repl
```

or perhaps bare `kaj` with no file.

Pure computation works locally; effectful capabilities require attached providers.

## 9.4 Language server

Future:

```text
kajls
```

using LSP.

Potential features:

- diagnostics,
- autocomplete,
- hover types,
- go to definition,
- find references,
- rename,
- capability-operation completion,
- task/step navigation.

## 9.5 Package system

Kaj may eventually need a native package ecosystem.

Possible manifest:

```text
kaj.toml
```

Conceptual:

```toml
[package]
name = "example"
version = "0.1.0"

[dependencies]
kaj-web = "1"
```

Exact format is deferred.

## 9.6 Standard library

Initial stdlib should remain small and high quality.

Likely modules:

```text
collections
math
json
text
time
result
```

Do not attempt Python-scale coverage immediately.

## 9.7 Testing

Language/compiler repo should heavily use golden fixtures:

```text
source.kaj
expected.ast.json
expected.ir.json
expected.diagnostics.json
```

Kaj may later gain native test syntax.

## 9.8 Conformance suite

Third-party compilers/runtimes should eventually prove compatibility through public conformance tests.

Possible levels:

```text
Kaj Core
Kaj Task
Kaj Web Capability v1
```

# 9.9 Open-source position

Kaj should be independent and open source from the beginning.

Proposed code license:

```text
Apache License 2.0
```

Reasons include permissive adoption and explicit patent-grant language.

This is a project proposal, not legal advice.

## 9.10 Copyright

Choose the initial copyright holder deliberately before publication.

Possible form:

```text
Copyright © 2026 <owner>
```

## 9.11 Trademark/name

Code licensing and the Kaj project name are separate issues.

Open-sourcing the compiler does not require immediately filing a federal trademark.

The project should avoid implying that the source-code license automatically grants ownership of the Kaj brand/logo.

## 9.12 Contributions

Simple initial model:

- contributions are provided under the project's Apache-2.0 terms,
- contributors certify they have the right to submit them,
- a DCO-style sign-off process may be added.

A complicated CLA is not required at inception.

## 9.13 Governance

Initial governance can be maintainer-led.

Suggested statement:

> Kaj is currently maintained by the Kaj project maintainers. Significant changes to syntax, semantics, type system, Task IR, or capability contracts should be proposed through a Kaj Improvement Proposal. Maintainers make final acceptance decisions while Kaj is in early development.

## 9.14 Kaj Improvement Proposals

Use **KIP** as the proposal process.

Potential first proposals:

```text
KIP-0001 Core Language and Principles
KIP-0002 Lexical Grammar
KIP-0003 Type System
KIP-0004 Functions and Effect Model
KIP-0005 Task and Step Semantics
KIP-0006 Contracts and Verification
KIP-0007 Human Interaction
KIP-0008 Observation and Fact Model
KIP-0009 Capability System
KIP-0010 Kaj AST Schema
KIP-0011 Task IR
KIP-0012 Web Capability v1
KIP-0013 Compiler Architecture
KIP-0014 Host Runtime Interface
KIP-0015 World Model Interface
```

## 9.15 Version components independently

Track separate versions for:

```text
Kaj language
AST schema
Task IR
capabilities
reference compiler
```

Example:

```text
Kaj language 0.1
AST v1
Task IR v1
web capability v1
compiler 0.1.3
```

## 9.16 Persisted metadata

```json
{
  "language": "kaj",
  "language_version": "0.1",
  "ast_schema_version": 1,
  "task_ir_version": 1,
  "capabilities": {
    "web": 1
  }
}
```

## 9.17 Compatibility policy

During `0.x`:

- syntax may change,
- semantics may change,
- AST/IR may change,
- formatter output may change.

Changes should still be documented.

Before `1.0`, define:

- source compatibility,
- deprecation policy,
- AST compatibility,
- IR compatibility,
- capability compatibility.

## 9.18 Specification vs implementation

Distinguish:

```text
Kaj Language Specification
```

from:

```text
Kaj Reference Compiler
```

A third party should be able to implement a conforming compiler/runtime.

## 9.19 Foundation

No foundation is needed initially.

Potential evolution only if scale requires it:

```text
maintainer-led
  ↓
steering committee
  ↓
neutral foundation / consortium
```

## 9.20 Repository starter files

Recommended:

```text
README.md
LICENSE
NOTICE
CONTRIBUTING.md
SECURITY.md
CHANGELOG.md
GOVERNANCE.md
CODE_OF_CONDUCT.md
```

## 9.21 Minimal KIP template

```markdown
# KIP-NNNN: Title

Status: Draft
Author:
Created:
Target version:

## Summary
## Motivation
## Design
## Syntax
## Static semantics
## Runtime semantics
## AST representation
## IR lowering
## Capability/effect implications
## Security considerations
## Alternatives
## Compatibility
## Open questions
```

---

# 10. Implementation Roadmap

## Phase 0 — Repository and design baseline

Create standalone Kaj repository with:

```text
README
LICENSE
NOTICE
CONTRIBUTING
SECURITY
GOVERNANCE
CHANGELOG
docs/
proposals/
schemas/
examples/
```

Publish the initial proposal and mark Kaj experimental.

## Phase 1 — Semantic AST and JSON schema

Build first:

- AST node model,
- versioned schema-constrained JSON,
- stable durable task node IDs,
- diagnostic schema,
- source locations optional.

Do **not** build raw textual parser first.

Reason: the first production LLM path can immediately use structured AST.

## Phase 2 — Core type system

Implement:

```text
Bool
Int
Decimal
String
Optional
List
Map
Result
Money
Percent
Duration
Url
Dynamic
```

Implement:

- literal/local inference,
- function parameter checking,
- return inference,
- no implicit truthiness,
- no silent incompatible coercions.

## Phase 3 — Core computation AST/interpreter

Implement semantics for:

```text
let
var
fn
return
if
else
for
while
break
continue
match
```

Initially AST can be tested directly before `.kaj` parser exists.

## Phase 4 — Task semantics

Implement:

```text
task
step
goal
success
invariant
require
expect
verify
```

Build internal task graph representation.

## Phase 5 — Human interaction semantics

Implement:

```text
inform
ask
choose
confirm
handoff
```

Each should lower into typed interaction IR.

## Phase 6 — Effect model and knowledge semantics

Implement:

```text
fn vs step effect restrictions
capability invocation
observe
learn
```

Compiler should reject forbidden world effects inside pure functions.

## Phase 7 — Generic Task IR

Implement normalized IR with:

- actions,
- observations,
- verification,
- requirements,
- human interactions,
- task control,
- memory mutation proposals,
- stable action IDs,
- versioning.

## Phase 8 — Canonical formatter

Build:

```text
AST → canonical Kaj source
```

At this stage an LLM can generate AST and developers can inspect real Kaj source without a parser yet.

## Phase 9 — Web capability v1

Define the first real capability around the actual browser workspace/runtime.

Use stable browser concepts such as:

- tab IDs,
- navigation,
- page interaction,
- observation,
- lifecycle results.

Avoid fictional APIs that the runtime cannot faithfully implement.

## Phase 10 — Berkbrain/Chalok host integration

Pipeline:

```text
user request
 ↓
LLM structured Kaj task patch
 ↓
Kaj compiler
 ↓
Task IR
 ↓
Chalok task memory
 ↓
permissions
 ↓
browser workspace
 ↓
verification
```

The server is the authoritative compilation/policy host.

## Phase 11 — Text lexer/parser

Implement `.kaj` parsing into the exact same AST.

Target round trip:

```text
source
 ↓
AST
 ↓
formatter
 ↓
canonical source
```

## Phase 12 — CLI

Implement:

```bash
kaj file.kaj
kaj check file.kaj
kaj fmt file.kaj
kaj ast file.kaj
kaj ir file.kaj
```

## Phase 13 — Basic standard library

Implement high-value modules/functions for:

- collections,
- math,
- strings/text,
- JSON,
- time,
- typed results.

## Phase 14 — REPL

Implement ordinary interactive computation.

## Phase 15 — Language server

Build `kajls` using the same compiler frontend.

## Phase 16 — Package/capability SDK

Stabilize third-party capability/provider contracts.

## Phase 17 — Generality experiments

Do not claim Kaj is universal until tested.

Build small experimental capabilities for:

```text
vision
robotics/simulation
audio
```

Use those experiments to improve the core language abstractions.

## Phase 18 — World-model host interface

Add optional prediction hooks.

Do not require a world model for ordinary Kaj execution.

## Phase 19 — Model specialization

After meaningful data exists:

- fine-tune models on Kaj AST/source,
- distill smaller planners,
- build domain-specialized planners,
- train world models from structured transitions.

## Recommended first package tree

```text
kaj/
├── kaj/
│   ├── ast/
│   ├── schema/
│   ├── types/
│   ├── compiler/
│   │   ├── validate.py
│   │   ├── resolve.py
│   │   ├── typecheck.py
│   │   ├── effects.py
│   │   ├── controlflow.py
│   │   └── lower.py
│   ├── ir/
│   ├── formatter/
│   ├── diagnostics/
│   └── capabilities/
│       └── core/
├── schemas/
├── tests/
└── examples/
```

## First implementation milestone (M0)

M0 succeeds when:

1. schema-valid AST can represent ordinary computation and a simple task,
2. compiler catches representative type/effect errors,
3. compiler lowers valid AST into deterministic Task IR,
4. formatter emits readable canonical Kaj,
5. golden tests lock the semantic baseline.

No browser automation is required to call the language frontend real.

## Kaj 0.1 milestone

Kaj 0.1 should add:

- source parser,
- `kaj` CLI,
- runnable ordinary Kaj,
- task semantics,
- initial Web capability contract,
- at least one real host integration.

---

# 11. Examples

These examples define intended style. They are not yet a frozen grammar suite.

## 11.1 Hello world

```kaj
print("Hello from Kaj")
```

```bash
kaj hello.kaj
```

## 11.2 Function

```kaj
fn greet(name: String) {
    return "Hello, {name}"
}

print(greet("world"))
```

## 11.3 Type inference

```kaj
let name = "Kaj"
let year = 2026
let price = $825.00
let tax_rate = 6.35%
```

## 11.4 Explicit mutation

```kaj
var attempts = 0

while attempts < 3 {
    attempts += 1
    print(attempts)
}
```

## 11.5 Math

```kaj
let prices = [$120.00, $85.50, $40.00]

let subtotal = sum(prices)
let tax = subtotal * 6.35%
let total = subtotal + tax

print(total)
```

## 11.6 Recursive computation

```kaj
fn fibonacci(n: Int) -> Int {
    if n <= 1 {
        return n
    }

    return fibonacci(n - 1) + fibonacci(n - 2)
}

for n in 1 through 10 {
    print(fibonacci(n))
}
```

## 11.7 Pattern matching

```kaj
match payment_result {
    case Confirmed(receipt) {
        print(receipt.id)
    }

    case Declined(reason) {
        print(reason)
    }

    case Uncertain {
        print("Result needs reconciliation")
    }
}
```

## 11.8 Basic task

```kaj
task research {
    goal {
        "Find three relevant products."
    }

    success {
        products.count >= 3
    }

    step gather {
        ...
    }
}
```

## 11.9 Web research

```kaj
use web

task find_monitor {
    goal {
        "Find strong 27-inch monitors under $300."
    }

    success {
        candidates.count >= 3
        every candidates.price is confirmed
    }

    step research {
        web.open("https://example.com")

        observe web.page as results

        extract candidates
            from results

        let affordable = candidates
            .filter(.price <= $300)

        inform user
            "I found {affordable.count} candidates."
    }
}
```

## 11.10 Housing dues workflow

```kaj
use web

task pay_housing_dues {
    goal {
        "Pay every currently due housing obligation."
    }

    success {
        every obligations.payment is verified
        no unresolved conflicts
        no uncertain payment actions
    }

    step find_notice {
        web.open(gmail)

        let results = web.search("monthly housing dues")

        observe web.page as messages

        find dues_email: Email
            in messages
            where .subject contains "dues"

        require dues_email exists

        inform user
            "I found the housing dues notice."
    }

    step discover_obligations after find_notice {
        extract obligations: List<HousingObligation>
            from dues_email

        require obligations.count > 0

        learn obligations
            from dues_email

        inform user
            "I found {obligations.count} current obligations."
    }

    step choose_account after discover_obligations {
        choose user payment_account
            from available_payment_accounts

        require payment_account is confirmed
    }

    for obligation in obligations {
        step prepare_payment(obligation: HousingObligation)
            after choose_account
        {
            web.open(obligation.payment_url)

            observe web.page as portal

            verify portal.unit == obligation.unit
            verify portal.amount == obligation.amount

            require obligation.unit is confirmed
            require obligation.amount is confirmed
            require payment_account is confirmed

            confirm user
                "Pay {obligation.amount} for {obligation.unit} using {payment_account}?"
        }

        step submit_payment(obligation: HousingObligation)
            after prepare_payment
        {
            web.submit(payment)

            expect {
                confirmation.visible
                confirmation.amount == obligation.amount
                confirmation.unit == obligation.unit
            }

            verify payment

            inform user
                "Payment for {obligation.unit} was confirmed."
        }
    }
}
```

## 11.11 Conflict handling

```kaj
if invoice.amount is conflicted {
    ask user
        "The notice says {invoice.amount.notice} but the portal says {invoice.amount.portal}. Which amount should I use?"
    as amount_resolution
}
```

## 11.12 Human handoff

```kaj
handoff user for sign_in
    on payment_portal
```

## 11.13 Effect error

Invalid:

```kaj
fn calculate_total(items: List<Money<USD>>) {
    web.open("https://example.com")
    return sum(items)
}
```

Expected:

```text
EFFECT_NOT_ALLOWED
```

## 11.14 Robot task

```kaj
use robot
use vision

task clear_table {
    goal {
        "Move every cup from the table to the tray."
    }

    success {
        no Cup is on table
        every moved Cup is in tray
    }

    observe vision.scene as scene

    let cups = vision.locate(Cup, in: scene)
        .filter(.surface == table)

    for cup in cups {
        step move(cup: Vision.Object) {
            let grasp = robot.plan_grasp(cup)

            require grasp.is_safe

            robot.move_to(cup)
            robot.grasp(cup, using: grasp)

            verify robot.holds(cup)

            robot.move_to(tray)
            robot.release(cup)

            observe vision.scene as result
            verify cup is in tray
        }
    }
}
```

## 11.15 Navigation task

```kaj
use navigation
use vision
use robot

task deliver_package(destination: Location) {
    goal {
        "Deliver the package to {destination}."
    }

    success {
        robot.position == destination
        package is at destination
    }

    while robot.position != destination {
        observe vision.scene as surroundings

        let route = navigation.plan(
            from: robot.position,
            to: destination,
            avoiding: surroundings.obstacles
        )

        require route.is_safe

        navigation.follow(route)

        when vision.detects(unexpected_obstacle) {
            navigation.stop()
        }
    }

    robot.release(package)
    verify package is at destination
}
```

## 11.16 Audio task

```kaj
use audio

task enhance_rain {
    observe audio.scene as scene

    let rain = audio.locate(Rain, in: scene)

    audio.increase(rain.intensity, by: 20%)

    expect {
        rain.prominence > scene.rain.prominence
        speech.intelligibility >= 0.9
    }

    verify audio.output
}
```

## 11.17 Recursive task traversal

```kaj
recursive step inspect_category(category: Category)
    depth at most 6
{
    observe category as page

    learn page.products
        from page

    for child in page.subcategories {
        recurse inspect_category(child)
    }
}
```

The exact `recursive step`/depth grammar remains open.

## 11.18 Dynamic JSON boundary

```kaj
let raw: Dynamic = json.parse(response.body)
let product = raw.decode<Product>()

print(product.name)
```

## 11.19 Unit-safe robotics math

```kaj
let distance = 2.5 meters
let speed = 0.5 meters / second
let duration = distance / speed

print(duration)
```

Expected inferred type:

```text
Duration
```

---

# 12. Open Questions and KIP Backlog

Kaj should not pretend every decision is settled. These questions should drive the first Kaj Improvement Proposals.

## 12.1 Static vs dynamic typing

Current preferred direction:

```text
static by default
strongly typed
heavy inference
explicit Dynamic/Any escape hatch
```

Still test whether function parameter types can be inferred more often without creating confusing whole-program inference.

## 12.2 `fn` purity

Should every `fn` be pure by definition?

Options:

1. `fn` pure, effects only in `step`,
2. explicit effect annotations on `fn`,
3. another construct such as `proc`,
4. inferred effect sets.

Initial proposal favors pure/default `fn` and effectful `step`.

## 12.3 What exactly is a `step`?

Need formal rules for:

- return values,
- local state,
- retries,
- dependencies,
- resumability,
- concurrency,
- recursion,
- whether steps can exist outside tasks.

## 12.4 Task return values

Should this be legal?

```kaj
task research(topic: String) -> Report {
    ...
}
```

Likely yes, but define result/completion semantics.

## 12.5 `when`

Do not make `when` a redundant `if`.

Possible future meanings:

- event/reactive handler,
- wait-until trigger,
- pattern guard.

## 12.6 Async/concurrency

Likely future needs:

```text
parallel for
spawn
await
race
```

Need safe semantics for side effects.

## 12.7 Cancellation

How do effectful tasks clean up on cancellation?

## 12.8 Exceptions vs Result

Need distinction between:

- programming failures,
- expected environmental outcomes,
- task blocking,
- host infrastructure failures.

Likely prefer typed Result/enums for normal capability outcomes.

## 12.9 Ranges

Choose canonical syntax:

```text
1 through 3
1..3
1..<3
```

or a carefully specified combination.

## 12.10 Object/type model

Do not prematurely reserve:

```text
class
struct
trait
protocol
interface
```

Need first decide Kaj's actual semantics.

## 12.11 Generic constraints

Need trait/type-class/protocol-like model only when real use cases demand it.

## 12.12 Module system

Need:

- file/module mapping,
- imports,
- package visibility,
- public/private APIs.

Likely eventually needs `pub` or equivalent.

## 12.13 Numeric overflow and precision

Specify:

- integer overflow behavior,
- Decimal precision,
- Decimal rounding,
- Money rounding,
- currency minor units.

## 12.14 Physical units

Need design for:

- syntax,
- dimensions,
- conversions,
- user-defined units,
- robotics coordinate frames.

## 12.15 Observation syntax

Current proposal:

```kaj
observe web.page as page
```

Need formal source and metadata semantics.

## 12.16 `learn`

Need define:

- where it is legal,
- how scope is selected,
- what evidence is required,
- whether model inference can ever be directly durable,
- how conflicts are represented.

Likely source proposes knowledge; host memory policy validates it.

## 12.17 Fact state predicates

Readable:

```kaj
invoice.amount is confirmed
```

Need determine whether `confirmed`, `conflicted`, `stale`, etc. are contextual grammar or ordinary enum/state APIs.

## 12.18 Contract block semantics

Likely lines in:

```kaj
success { ... }
expect { ... }
invariant { ... }
```

are implicitly ANDed, but this should be formally defined.

## 12.19 Human interaction syntax

Compare:

```kaj
ask user "Age?" as age: Int
```

vs:

```kaj
let age: Int = ask user "Age?"
```

The task-oriented form is currently preferred but both deserve evaluation.

## 12.20 Capability manifest/package format

Need stable provider declaration and trust model.

## 12.21 Capability trust

Distinguish:

- pure Kaj package,
- native plugin,
- remote provider,
- privileged hardware provider.

## 12.22 Python interoperability

Potentially extremely useful because of NumPy/PyTorch/scientific libraries.

But arbitrary Python calls can bypass Kaj's effect model.

Interop needs explicit trust/effect semantics.

## 12.23 Native FFI

Eventually needed for robotics/science/system integration.

Potential C ABI/Rust/Python paths should be evaluated later.

## 12.24 Web capability boundary

Must align with actual browser workspace semantics: stable tab IDs, navigation lifecycle, page actions, site-initiated popups, external schemes, action results, and recovery.

## 12.25 World-model hook granularity

Should world models predict:

- individual IR actions,
- action groups,
- entire steps,
- alternative candidate plans?

Start with individual consequential actions and expand experimentally.

## 12.26 Recovery in language vs host

Most recovery belongs to the host.

Potential future syntax such as:

```kaj
on uncertain { ... }
```

should not be added until real patterns justify it.

## 12.27 Source-level capability requirements

Source may declare needed effects/capabilities, but never grant authorization.

## 12.28 Compiler implementation language

Start in Python.

Consider Rust only when stability, embedding, performance, or cross-platform packaging justify migration.

## 12.29 KIP backlog

Suggested initial sequence:

```text
KIP-0001 Core Goals and Design Principles
KIP-0002 Lexical Grammar and Keywords
KIP-0003 Type System
KIP-0004 Functions, Control Flow, and Math
KIP-0005 Effect Model
KIP-0006 Task and Step Semantics
KIP-0007 Contracts and Verification
KIP-0008 Human Interaction
KIP-0009 Observation and Fact Model
KIP-0010 Capability System
KIP-0011 Kaj AST Schema
KIP-0012 Task IR
KIP-0013 Compiler Architecture
KIP-0014 Host Runtime Interface
KIP-0015 Web Capability v1
KIP-0016 World Model Interface
```

## 12.30 Guiding rule for unresolved choices

Prefer the option that:

1. makes invalid agent behavior harder to express,
2. remains pleasant for ordinary scripting,
3. stays readable to humans,
4. stays easy for models to generate,
5. compiles into precise typed semantics,
6. does not unnecessarily bind Kaj to one host or capability.

---

# 13. Repository Starter Files

This document contains suggested starter text. It is not legal advice.

## README opening

```markdown
# Kaj

Kaj is an open-source programming language for intelligent agents and ordinary scripting.

Kaj combines general computation with first-class constructs for goal-directed tasks, external capabilities, observation, verification, and human collaboration.

```bash
kaj hello.kaj
```

Kaj is currently experimental. Syntax and semantics may change during the 0.x series.
```

## CONTRIBUTING.md starter

```markdown
# Contributing to Kaj

Kaj is in early language-design and implementation development.

Contributions are welcome in compiler implementation, tests, documentation, examples, diagnostics, tooling, and language-design discussion.

Substantial changes to language syntax, semantics, type system, Task IR, or capability contracts should begin as a Kaj Improvement Proposal (KIP).

By submitting a contribution, you agree that your contribution may be distributed under the project's license and that you have the right to submit it.
```

## SECURITY.md starter

```markdown
# Security

Please do not open a public issue for vulnerabilities that could enable unsafe external effects, permission bypass, secret exposure, or arbitrary code execution.

Report security issues privately through the repository's configured security reporting channel.

Kaj source and Kaj capability packages should be treated as potentially untrusted input by host runtimes.
```

## GOVERNANCE.md starter

```markdown
# Governance

Kaj is currently maintained under a maintainer-led governance model.

Significant changes to syntax, semantics, the type system, Task IR, or capability model should be proposed through the Kaj Improvement Proposal (KIP) process.

The maintainers make final acceptance decisions while Kaj is in early development.

The governance model may evolve if the project develops a broader independent community.
```

## KIP template

```markdown
# KIP-NNNN: Title

Status: Draft
Author:
Created:
Target version:

## Summary

## Motivation

## Design

## Syntax

## Static semantics

## Runtime semantics

## AST representation

## IR lowering

## Capability / effect implications

## Security considerations

## Alternatives considered

## Compatibility

## Open questions
```

## NOTICE

If Apache-2.0 is selected, create the project `NOTICE` appropriate to the final copyright holder and legal setup.

---

# Kaj Initial Proposal v0.1

**Status:** Initial proposal / design baseline  
**Language:** Kaj  
**Source extension:** `.kaj`  
**Primary CLI:** `kaj`  
**Compiler-safe fallback alias:** `kajc`  
**Proposed license:** Apache License 2.0  
**Initial implementation:** standalone open-source reference compiler, initially in Python  
**First production host:** Berkbrain  
**First production capability/runtime:** Chalok Web

Kaj is a proposed strongly typed, human-readable programming language for intelligent agents and ordinary scripting. It is designed to express computation, long-running goal-directed work, external-world actions, observation, evidence-backed knowledge, human collaboration, verification, and eventually world-model-assisted planning across web, robotics, vision, audio, simulation, and other domains.

The name **Kaj** comes from the Bangla word **কাজ**, meaning **work**.

This documentation set is intentionally broad. It establishes the starting architecture from which Kaj should be built. It is not a claim that every syntax choice is permanently frozen.

## Core thesis

Kaj should be able to express ordinary programs:

```kaj
fn average(values: List<Decimal>) {
    return sum(values) / values.count
}

let result = average([10, 20, 30])
print(result)
```

and goal-directed agent programs:

```kaj
use web

task research_monitor {
    goal {
        "Find a strong 27-inch monitor under $300."
    }

    success {
        candidates.count >= 3
        every candidates.price is confirmed
    }

    step research {
        web.open("https://example.com")
        observe web.page as page
        extract candidates from page

        inform user
            "I found {candidates.count} candidates."
    }
}
```

and later physical-agent programs:

```kaj
use robot
use vision

task clear_table {
    observe vision.scene as room

    let cups = room.objects.filter(.kind == Cup)

    for cup in cups {
        let grasp = robot.plan_grasp(cup)
        require grasp.is_safe

        robot.grasp(cup, using: grasp)
        verify robot.holds(cup)

        robot.move_to(tray)
        robot.release(cup)
        verify cup.position is in tray
    }
}
```

Kaj is therefore **not a web DSL**. Web automation is simply its first major capability environment.

## Architectural position

```text
Natural-language intent
        ↓
Planner / LLM
        ↓
Structured Kaj AST
        ↓
Kaj compiler
        ↓
Validated Task IR
        ↓
Host runtime
        ↓
Capabilities / permissions / task memory / world models
        ↓
External environment
```

Human-authored Kaj follows the parallel route:

```text
.kaj source
    ↓
parser
    ↓
Kaj AST
    ↓
same compiler pipeline
```

The **AST is the canonical semantic representation**. Textual Kaj is the canonical human-readable source form. Structured JSON AST is the preferred initial LLM output format.

## Design-status vocabulary

- **Baseline** — part of the initial direction and should be implemented unless a concrete issue is discovered.
- **Proposed** — preferred design but still expected to evolve.
- **Deferred** — intentionally not required for the first compiler/runtime.

## Documentation map

1. `00-initial-proposal.md`
2. `01-vision-and-design-principles.md`
3. `02-language-and-execution-model.md`
4. `03-syntax-keywords-and-type-system.md`
5. `04-computation-tasks-effects-and-human-interaction.md`
6. `05-capabilities-world-models-and-runtime.md`
7. `06-ast-ir-and-llm-integration.md`
8. `07-compiler-architecture-and-project-layout.md`
9. `08-security-permissions-verification-and-recovery.md`
10. `09-tooling-open-source-governance-and-versioning.md`
11. `10-implementation-roadmap.md`
12. `11-examples.md`
13. `12-open-questions-and-kip-backlog.md`

## Non-goals for the first implementation

Kaj 0.x does not need to immediately become:

- a replacement for Python's library ecosystem,
- a native-code optimizing compiler,
- a robotics middleware stack,
- a browser engine,
- a world model,
- an AI model,
- a permission system,
- a database,
- or a universal planner.

The first milestone is a coherent language frontend, AST, type/effect system, generic Task IR, canonical formatter, runnable pure programs, and one useful environmental capability family: Web.

## Central architectural rule

> Kaj defines how programs express computation, goals, effects, evidence, interaction, and verification. Kaj source does not grant itself authority to perform external effects.

Compilation establishes meaning and validity. Host runtimes establish authorization and perform effects.
