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
