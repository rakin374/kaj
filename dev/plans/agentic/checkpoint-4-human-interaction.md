# Agentic Kaj — Checkpoint 4: Human Interaction

**Track:** Agentic Kaj  
**Checkpoint:** 4  
**Recommended path:** `dev/plans/agentic/checkpoint-4-human-interaction.md`

---

# Goal

Implement first-class human interaction and task suspension.

Authoritative semantics:

```text
docs/agentic/human-interaction.md
```

This checkpoint builds on:

```text
Checkpoint 1 — Tasks
Checkpoint 2 — Steps and Task Lifecycle
Checkpoint 3 — Task Contracts
```

---

# Scope

Implement:

```text
ask<T>
choose<T>
confirm
inform
handoff

waiting_for_human lifecycle state
blocking interaction suspension
interaction runtime records
InteractionId
host response API
typed response validation
resume at suspension point
interaction cancellation
step interaction semantics
diagnostics
tests
docs integration
```

Do not implement process-restart persistence yet.

---

# Frozen Primitive Semantics

## `ask<T>`

```kaj
let city = ask<String>("Where are you going?")
```

Rules:

```text
blocking
prompt must be String
response validated as T
invalid response keeps task waiting
valid response resumes and returns T
```

## `choose<T>`

```kaj
let option = choose<String>(
    "Choose",
    ["a", "b"]
)
```

Rules:

```text
blocking
options must be List<T>
options must be non-empty
selected response must equal one supplied option
returns T
```

## `confirm`

```kaj
let approved = confirm("Proceed?")
```

Rules:

```text
blocking
String prompt
returns Bool
approval -> true
rejection -> false
```

## `inform`

```kaj
inform("Started")
```

Rules:

```text
non-blocking
String prompt/message
returns None
runtime emits/records notification
```

## `handoff`

```kaj
handoff("Please complete the CAPTCHA")
```

Rules:

```text
blocking
String prompt
returns None after host marks handoff complete
```

---

# Lifecycle

Add:

```text
WAITING_FOR_HUMAN
```

Valid transitions:

```text
RUNNING -> WAITING_FOR_HUMAN
WAITING_FOR_HUMAN -> RUNNING
WAITING_FOR_HUMAN -> CANCELLED
WAITING_FOR_HUMAN -> FAILED
```

Do not use `PAUSED` for unresolved human interaction.

---

# Step Semantics

If a blocking interaction occurs inside a step:

```text
step state remains RUNNING
task state becomes WAITING_FOR_HUMAN
```

After valid response:

```text
task -> RUNNING
step remains RUNNING
execution resumes after interaction call
```

The interaction call must not run again.

---

# Runtime Representation

Add concepts such as:

```text
InteractionId
InteractionKind
InteractionStatus
HumanInteraction
```

Conceptually:

```text
HumanInteraction
    id
    task_id
    kind
    prompt
    expected_type
    options
    status
    response
```

Only one active blocking interaction per task.

---

# Host API

Provide a runtime API to inspect pending interaction and supply response.

Conceptually:

```text
get_pending_interaction(task_id)
respond_to_interaction(task_id, interaction_id, value)
complete_handoff(task_id, interaction_id)
cancel_interaction(task_id, interaction_id)
```

Exact API shape may follow current runtime conventions.

Responses must reference the correct active task and interaction.

---

# Typed Response Validation

Use Kaj's own type/value model.

Do not validate by Python `isinstance` alone.

Convert/validate host-supplied values into canonical Kaj runtime values.

Invalid response:

```text
interaction remains pending
task remains WAITING_FOR_HUMAN
structured validation error returned to host
```

Do not fail the task merely because a human supplied malformed input.

---

# `choose` Validation

Validate:

```text
options type == List<T>
options not empty
response type == T
response equals one supplied option using Kaj equality
```

Reject arbitrary host values not present in the option list.

---

# Static Restrictions

Human interaction is an Agentic effect.

Reject use:

```text
inside fn
inside goal
inside require
inside invariant
inside success
```

Allow use:

```text
inside task body
inside step
inside ordinary task control flow
```

---

# Suspension Implementation

Checkpoint 4 requires resumable in-memory execution.

Do not restart the task from the beginning after a response.

The runtime must preserve enough continuation state to resume exactly after:

```text
ask
choose
confirm
handoff
```

If the current interpreter architecture cannot suspend/resume a Python call stack safely, introduce an explicit task execution/continuation representation rather than using fragile generator tricks that conflict with future persistence.

Favor architecture that can be serialized in Checkpoint 5.

---

# Interaction Cancellation

Initial rule:

```text
cancelling active blocking interaction -> task CANCELLED
```

This is terminal.

Do not invent recoverable interaction cancellation yet.

---

# Duplicate / Stale Responses

Reject:

```text
unknown interaction ID
response for wrong task
response after interaction already completed
response to no-longer-active interaction
```

These must not resume task incorrectly.

---

# AST / Parser

Most primitives may be represented as special Agentic expressions rather than ordinary host builtins.

Prefer explicit AST nodes if needed for:

```text
effect restrictions
type parameters
suspension semantics
future persistence
```

Possible nodes:

```text
AskExpression
ChooseExpression
ConfirmExpression
InformExpression
HandoffExpression
```

If the existing call-expression representation can encode these cleanly while semantic analysis distinguishes them, that is acceptable.

Do not encode runtime interaction IDs in AST.

---

# Type Checking

Freeze signatures conceptually:

```text
ask<T>(String) -> T
choose<T>(String, List<T>) -> T
confirm(String) -> Bool
inform(String) -> None
handoff(String) -> None
```

Enforce prompt type `String`.

Enforce explicit/inferable generic `T` behavior consistently with Kaj's current generic builtins.

If Kaj does not have user-facing generic-call syntax today, implement the smallest unambiguous syntax consistent with existing language conventions and update the public spec only if necessary.

Do not silently invent inconsistent generic syntax.

---

# Formatter

Canonical formatting should preserve ordinary call-style formatting.

Examples:

```kaj
let city = ask<String>("Where are you going?")
```

```kaj
let option = choose<String>(
    "Choose a color",
    ["red", "green", "blue"],
)
```

```kaj
confirm("Proceed?")
inform("Done")
handoff("Please complete setup")
```

Follow existing multiline/trailing-comma rules.

---

# Diagnostics

Add/reuse stable diagnostics for:

```text
human interaction inside fn
human interaction inside contract
invalid prompt type
unsupported ask type
choose options not list
choose option type mismatch
choose empty options
response type mismatch
choose response not in options
unknown interaction
stale interaction
duplicate response
interaction already completed
multiple blocking interactions
```

Suggested codes if conventions permit:

```text
TASK_HUMAN_INTERACTION_OUTSIDE_TASK
TASK_HUMAN_INTERACTION_IN_CONTRACT
TASK_INTERACTION_PROMPT_TYPE_MISMATCH
TASK_INTERACTION_UNSUPPORTED_TYPE
TASK_CHOOSE_EMPTY_OPTIONS
TASK_CHOOSE_RESPONSE_INVALID
TASK_INTERACTION_RESPONSE_TYPE_MISMATCH
TASK_INTERACTION_NOT_FOUND
TASK_INTERACTION_STALE
TASK_INTERACTION_ALREADY_COMPLETED
TASK_MULTIPLE_PENDING_INTERACTIONS
```

Runtime cancellation/failure should use structured TaskFailure/interaction outcomes.

---

# Required Tests

Syntax/type:

```text
ask<String>
ask<Int>
choose<String>
confirm
inform
handoff
prompt non-String rejected
choose wrong option type rejected
empty choose rejected where statically knowable
interaction inside fn rejected
interaction in contracts rejected
```

Lifecycle:

```text
ask -> WAITING_FOR_HUMAN
choose -> WAITING_FOR_HUMAN
confirm -> WAITING_FOR_HUMAN
handoff -> WAITING_FOR_HUMAN
inform remains RUNNING
valid response -> RUNNING
interaction cancel -> CANCELLED
```

Resume:

```text
ask resumes with typed value
choose resumes with selected option
confirm true
confirm false
handoff completion resumes
interaction is not re-executed
subsequent statements execute once
```

Invalid response:

```text
wrong type keeps waiting
choose value not in options keeps waiting
stale interaction rejected
duplicate response rejected
wrong task ID rejected
```

Steps:

```text
step remains RUNNING during wait
step completes after resumed body finishes
later steps do not start while waiting
```

Runtime/host:

```text
InteractionId unique
pending interaction inspectable
one active blocking interaction per task
inform event recorded
```

Regression:

```text
Pure Kaj
Agentic Checkpoints 1-3
Checkpoint 4
mkdocs build --strict
```

---

# Out of Scope

Do not implement:

```text
database persistence
process-restart resume
interaction persistence across restart
capability
use
browser integration
task composition
TaskHandle
waiting_for_task
planner
LLM integration
plan blocks
AST patches
replanning
retry syntax
interaction timeout syntax
multiple simultaneous human requests
recoverable interaction cancellation
```

---

# Definition of Done

```text
[ ] ask<T> implemented
[ ] choose<T> implemented
[ ] confirm implemented
[ ] inform implemented
[ ] handoff implemented

[ ] WAITING_FOR_HUMAN lifecycle state implemented
[ ] blocking interactions suspend task
[ ] valid responses resume exact continuation
[ ] interaction call is not re-executed

[ ] InteractionId exists
[ ] pending interaction runtime record exists
[ ] one blocking interaction per task enforced

[ ] typed response validation uses Kaj value/type semantics
[ ] invalid response keeps task waiting
[ ] choose validates membership
[ ] interaction cancellation cancels task

[ ] interactions rejected inside fn
[ ] interactions rejected inside task contracts

[ ] steps remain RUNNING during interaction wait
[ ] later steps wait for interaction resolution

[ ] AST/semantic representation supports suspension cleanly
[ ] formatter canonical/idempotent
[ ] runtime interaction state excluded from AST JSON

[ ] host response API exists
[ ] stale/duplicate responses rejected

[ ] Pure Kaj suite passes
[ ] Agentic Checkpoints 1-3 pass
[ ] Checkpoint 4 tests pass
[ ] mkdocs build --strict passes
```

---

# Completion Report

```text
Agentic Kaj Checkpoint 4 — Human Interaction

Status:
COMPLETE / INCOMPLETE

Files changed:
- ...

Primitives:
- ask: PASS/FAIL
- choose: PASS/FAIL
- confirm: PASS/FAIL
- inform: PASS/FAIL
- handoff: PASS/FAIL

Typing:
- typed ask: PASS/FAIL
- choose typing: PASS/FAIL
- prompt typing: PASS/FAIL
- fn restriction: PASS/FAIL
- contract restriction: PASS/FAIL

Lifecycle:
- waiting_for_human: PASS/FAIL
- valid resume: PASS/FAIL
- cancellation: PASS/FAIL
- step remains running: PASS/FAIL

Runtime:
- InteractionId: PASS/FAIL
- pending interaction record: PASS/FAIL
- one blocking interaction: PASS/FAIL
- stale/duplicate response rejection: PASS/FAIL
- exact continuation resume: PASS/FAIL
- inform event: PASS/FAIL

Regression:
- Pure Kaj: PASS/FAIL
- Agentic Checkpoints 1-3: PASS/FAIL
- Agentic Checkpoint 4: PASS/FAIL
- mkdocs build --strict: PASS/FAIL

Deferred intentionally:
- persistent resume
- capabilities
- task composition
- planner
- replanning

Known issues:
- ...
```
