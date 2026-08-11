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
