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
