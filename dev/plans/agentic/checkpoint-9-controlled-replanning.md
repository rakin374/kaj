# Agentic Kaj — Checkpoint 9: Controlled Replanning

**Track:** Agentic Kaj  
**Checkpoint:** 9  
**Recommended path:** `dev/plans/agentic/checkpoint-9-controlled-replanning.md`

---

# Goal

Implement safe revision of future planner-controlled work after task execution has begun.

Authoritative semantics:

```text
docs/agentic/controlled-replanning.md
```

This checkpoint builds on Agentic Checkpoints 1–8.

---

# Scope

Implement:

```text
plan revisions
replan requests
replan purpose on PlannerRequest
replacement-pending-plan patches
protected completed history
safe replan boundaries
base revision/fingerprint validation
atomic replan application
replan persistence
replan audit metadata
stale/duplicate protection
tests
docs integration
```

Do not introduce unconstrained whole-task AST mutation.

---

# Core Replan Model

Freeze the initial model as:

```text
completed planner-owned prefix
    = immutable runtime history

pending planner-owned suffix
    = replaceable by validated replan
```

Example:

```text
completed:
    A
    B

pending:
    C
    D

proposal:
    E
    F

accepted:
    history A,B
    future E,F
```

Do not allow planner patches to rewrite A or B.

---

# Safe Boundary

A replan may be applied only at a safe runtime boundary.

Initial required boundary:

```text
after current step completes
after required post-step invariant checks pass
before next pending planner step begins
```

Do not replace a currently executing step.

---

# Runtime Replan API

Add host/runtime operation conceptually:

```text
request_replan(task_id, reason)
```

It should:

```text
validate task is non-terminal
validate safe/replannable state
create new PlanningAttemptId
capture current plan revision/fingerprint
create structured replan PlannerRequest
transition task to WAITING_FOR_PLANNER
```

No source-level `replan` syntax is required.

---

# PlannerRequest Extension

Extend planner request with:

```text
purpose:
    initial_plan | replan

current_plan_revision
current_plan_fingerprint
completed_steps
pending_plan
replan_reason
durable task state visible at boundary
```

Do not expose arbitrary Python/native runtime state.

---

# Plan Revision

Every accepted plan must have:

```text
revision: Int
fingerprint
```

Initial accepted plan:

```text
revision = 1
```

Each accepted replan increments monotonically.

Rejected attempts do not increment revision.

---

# Replan Proposal

Introduce a structured form conceptually:

```text
PlanPatch
    base_plan_revision
    base_plan_fingerprint
    replacement_pending_plan
    optional_metadata
```

Prefer replacement of future planner region rather than arbitrary AST edit operations.

---

# Base Validation

Reject if:

```text
base revision != current revision
base fingerprint != current fingerprint
task ID mismatch
PlanningAttemptId mismatch
attempt stale
```

No patch application occurs.

---

# Protected History

The runtime, not planner proposal, owns:

```text
completed step records
completed step names
committed results/state
TaskIds
human responses already accepted
capability results already accepted
existing child tasks
```

Planner proposal must not include edits to committed history.

Structurally omit completed history from the patch payload where possible.

---

# Protected Source

Replanning still may not modify:

```text
task signature
goal
require
invariant
success
use declarations
capability grants
fixed code outside plan
```

Reuse Checkpoint 8 protected-region machinery.

---

# Scope Validation

Validate replacement future plan against the current durable environment.

A proposal may reference:

```text
task parameters
still-live task-local bindings
completed-step-produced state still in scope
capability aliases
TaskHandles still in scope
ordinary module symbols
```

It may not reference bindings that would only have been created by removed pending steps.

---

# Existing Runtime Effects

Replanning must preserve reality.

Do not undo:

```text
human response already received
completed capability action/result
child task already started
inform event already emitted
completed step
```

No rollback semantics are introduced.

---

# Waiting States

Initial constraints:

```text
WAITING_FOR_HUMAN:
    do not ordinary-replan past unresolved interaction

WAITING_FOR_CAPABILITY:
    resolve/reconcile request first

WAITING_FOR_TASK:
    resolve awaited child outcome first
```

Replanning begins from a safe executable boundary.

---

# Planner Lifecycle

Reuse:

```text
WAITING_FOR_PLANNER
```

No new task lifecycle state.

Planner attempt records:

```text
purpose = replan
base revision
base fingerprint
reason
```

---

# Invalid Replan

Freeze:

```text
invalid patch:
    rejected
    current accepted plan unchanged
    task remains WAITING_FOR_PLANNER
```

Never partially apply a plan.

---

# Accepted Replan

Commit conceptually:

```text
validate entire replacement future
↓
canonicalize
↓
compute new fingerprint
↓
persist revision + replacement atomically
↓
increment revision
↓
invalidate older attempts
↓
task -> RUNNING
```

---

# Atomicity

Replan application must be atomic with persistence.

If persistent commit fails:

```text
do not expose new revision as accepted
```

Use TaskStore transaction/atomic write semantics.

---

# Persistence

Extend snapshot with:

```text
plan_revision
plan_fingerprint
accepted_pending_plan
active_replan_attempt
replan_reason
```

Preserve completed-step history separately.

---

# Restore

Waiting replan:

```text
restore same WAITING_FOR_PLANNER state
restore active PlanningAttemptId
restore base revision/fingerprint
```

Accepted revision:

```text
restore exact plan revision
do not regenerate
```

---

# Audit Metadata

Track at least:

```text
PlanningAttemptId
purpose
base revision
proposal accepted/rejected
resulting revision if accepted
base/new fingerprints
replan reason
validation diagnostics
```

Storage shape may be event log or snapshot-associated records.

---

# Capability Validation

Replanned code:

```text
cannot add use
cannot change aliases
cannot change binding identity
cannot expand grants
cannot use denied operation
```

Reuse Checkpoint 8 capability validation.

---

# Human Interaction Validation

Future plan may contain human interaction.

Do not modify already completed interaction outcomes.

Ensure new planned interactions receive new InteractionIds only when executed.

---

# Task Composition Validation

Future plan may start/await tasks normally.

Existing child tasks/handles stay valid.

Do not delete runtime child relationships because their originating planner step is historical.

---

# Contract Enforcement

After replan:

```text
goal unchanged
requirements unchanged
invariants unchanged
success unchanged
```

Runtime continues ordinary invariant/success checks.

---

# Planner Adapter

Reuse generic PlannerAdapter.

No vendor-specific SDK.

Deterministic mock planner should support:

```text
valid replan
invalid replan
stale base revision
protected-region escalation
scope error
capability escalation
```

---

# Diagnostics

Add/reuse diagnostics for:

```text
task not replannable
unsafe replan boundary
stale plan revision
plan fingerprint mismatch
attempt purpose mismatch
completed history modification
invalid future scope
replan protected-region modification
replan capability escalation
replan apply persistence failure
```

Suggested codes if conventions permit:

```text
PLANNER_REPLAN_NOT_ALLOWED
PLANNER_REPLAN_UNSAFE_BOUNDARY
PLANNER_PLAN_REVISION_STALE
PLANNER_PLAN_FINGERPRINT_MISMATCH
PLANNER_ATTEMPT_PURPOSE_MISMATCH
PLANNER_COMPLETED_HISTORY_MODIFIED
PLANNER_REPLAN_SCOPE_INVALID
PLANNER_PROTECTED_REGION_MODIFIED
PLANNER_CAPABILITY_ESCALATION
PLANNER_REPLAN_COMMIT_FAILED
```

Use repository conventions if different.

---

# Required Tests

Revision model:

```text
initial accepted plan revision = 1
accepted replan increments revision
rejected replan does not increment
fingerprint changes with accepted future change
```

Safe boundaries:

```text
replan after completed step accepted
replan during running step rejected/deferred
replan while unresolved human wait rejected
replan while unresolved capability wait rejected
replan while awaited child unresolved rejected
```

Protected history:

```text
completed steps immutable
completed step cannot be renamed
completed step cannot be removed
completed step cannot be replaced
completed step not re-executed
```

Future replacement:

```text
remove pending step
replace pending step
add pending step
reorder pending steps
new future plan executes
old removed future does not execute
```

Scope:

```text
reference existing durable binding valid
reference removed pending-step binding rejected
existing TaskHandle remains valid
existing capability result remains valid
```

Authority/contracts:

```text
goal modification rejected
require modification rejected
invariant modification rejected
success modification rejected
new use rejected
grant escalation rejected
denied operation rejected
fixed source modification rejected
```

Staleness:

```text
old revision rejected
wrong fingerprint rejected
stale PlanningAttemptId rejected
duplicate accepted response rejected
```

Atomicity:

```text
invalid patch leaves old plan unchanged
persistence failure leaves old revision active
accepted patch installed fully
```

Persistence:

```text
revision persists
fingerprint persists
accepted future persists
active replan attempt persists
restart waiting for replan
restart accepted replan without regeneration
```

Task composition/effects:

```text
existing child task preserved
existing human answer preserved
completed capability result preserved
```

Regression:

```text
Pure Kaj
Agentic Checkpoints 1–8
Checkpoint 9
mkdocs build --strict
```

---

# Out of Scope

Do not implement:

```text
whole-task AST rewriting
contract mutation
goal mutation
capability grant mutation
rollback of completed external effects
automatic terminal-failure recovery
automatic retry syntax
planner-trigger language statements
task migration/distributed scheduler
multi-planner consensus
planner self-modification
```

---

# Definition of Done

```text
[ ] plan revision implemented
[ ] plan fingerprint tied to revision
[ ] request_replan runtime API exists
[ ] replan PlannerRequest purpose implemented
[ ] PlanPatch/replacement future representation exists

[ ] safe replan boundary enforced
[ ] running step cannot be replaced
[ ] completed history immutable
[ ] pending future replaceable

[ ] base revision validated
[ ] base fingerprint validated
[ ] stale attempts rejected

[ ] current durable scope used for type/name validation
[ ] removed pending bindings unavailable
[ ] existing TaskHandles/capability results remain usable

[ ] contracts protected
[ ] capability requirements/grants protected
[ ] fixed source protected

[ ] invalid patch leaves current plan unchanged
[ ] accepted patch applied atomically
[ ] accepted replan increments revision
[ ] accepted plan fingerprint updated

[ ] replan state persists
[ ] accepted revision restores exactly
[ ] waiting replan restores correctly

[ ] audit metadata recorded

[ ] Pure Kaj suite passes
[ ] Agentic Checkpoints 1–8 pass
[ ] Checkpoint 9 tests pass
[ ] mkdocs build --strict passes
```

---

# Completion Report

```text
Agentic Kaj Checkpoint 9 — Controlled Replanning

Status:
COMPLETE / INCOMPLETE

Files changed:
- ...

Revision:
- plan revision: PASS/FAIL
- fingerprint: PASS/FAIL
- increment on acceptance: PASS/FAIL
- stale revision rejection: PASS/FAIL

Boundary/history:
- safe boundary: PASS/FAIL
- running step protected: PASS/FAIL
- completed steps immutable: PASS/FAIL
- pending future replaceable: PASS/FAIL

Validation:
- current scope: PASS/FAIL
- protected contracts: PASS/FAIL
- fixed source protection: PASS/FAIL
- capability escalation blocked: PASS/FAIL
- base fingerprint validation: PASS/FAIL

Application:
- invalid patch atomic rejection: PASS/FAIL
- accepted patch atomic commit: PASS/FAIL
- old future removed: PASS/FAIL
- new future executes: PASS/FAIL

Persistence:
- revision persisted: PASS/FAIL
- fingerprint persisted: PASS/FAIL
- active replan persisted: PASS/FAIL
- accepted replan restore: PASS/FAIL

Effects/history:
- existing child tasks preserved: PASS/FAIL
- human outcomes preserved: PASS/FAIL
- capability outcomes preserved: PASS/FAIL

Regression:
- Pure Kaj: PASS/FAIL
- Agentic Checkpoints 1–8: PASS/FAIL
- Agentic Checkpoint 9: PASS/FAIL
- mkdocs build --strict: PASS/FAIL

Deferred intentionally:
- whole-task rewriting
- automatic failure recovery
- rollback
- multi-planner coordination

Known issues:
- ...
```
