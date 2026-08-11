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
