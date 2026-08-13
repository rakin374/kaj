# Controlled Replanning

Controlled replanning allows an Agentic Kaj task to revise future planner-controlled work after execution has begun, without permitting the planner to rewrite protected task semantics or invalidate already-committed history.

The planner may propose a change.

Kaj validates the change.

The runtime applies only a valid patch to explicitly replannable regions.

---

## 1. Core principle

Replanning is constrained modification of future work.

Conceptually:

```text
current validated task
        ↓
runtime reaches replanning point
        ↓
planner receives current durable state
        ↓
planner proposes patch
        ↓
Kaj validates patch
        ↓
valid patch applied to future plan
        ↓
execution continues
```

The planner does not receive general self-modification authority.

---

## 2. Replanning versus initial planning

Checkpoint 8 defines initial planning:

```text
empty/unresolved plan region
        ↓
planner proposes initial plan
```

Checkpoint 9 adds:

```text
accepted plan already exists
        ↓
execution progresses
        ↓
runtime may request a revised future plan
```

Initial planning creates the first validated plan.

Replanning modifies only the allowed future portion of that plan.

---

## 3. Replanning boundary

Only planner-controlled content inside the task's existing:

```kaj
plan {
    ...
}
```

region may be replanned.

Fixed source outside the plan remains protected.

---

## 4. Protected task structure

Replanning may never modify:

```text
task name
task parameters
task parameter types
task return type
goal
require
invariant
success
use declarations
capability aliases
capability grants
fixed source outside plan
completed step history
committed task inputs
TaskId
parent/child identity
```

---

## 5. Completed steps are immutable

Once a step has been durably committed as:

```text
completed
```

replanning may not:

```text
delete it
rename it
edit its body
mark it uncompleted
reorder it relative to committed history
re-execute it automatically
```

Completed work is runtime history, not planner-owned draft state.

---

## 6. Current running step

The initial model does not allow replanning to replace the currently executing step.

A replan is applied only at a safe boundary.

Preferred safe boundary:

```text
after current step completes
and
after post-step invariant checks pass
```

---

## 7. Future steps

Replanning may modify future, not-yet-started planner-owned steps.

It may:

```text
add future steps
remove pending future steps
replace pending future steps
rename pending future steps
reorder pending future steps
change future step bodies
```

subject to ordinary Kaj validation.

---

## 8. Replanning trigger

A replan may be requested by the host/runtime.

Checkpoint 9 does not require automatic model-driven triggering.

Conceptually:

```text
request_replan(task_id, reason)
```

The host may use this after:

```text
new external information
capability result
human feedback
child-task result
recoverable execution condition
explicit user request
```

---

## 9. Source-level replan syntax

Checkpoint 9 does not require a general source-level:

```text
replan
```

statement.

Replanning is initially a runtime/host control operation applied to an existing planner-controlled task.

This keeps policy outside task source.

---

## 10. Replanning lifecycle

A task awaiting a replan uses:

```text
waiting_for_planner
```

from Checkpoint 8.

No separate `waiting_for_replanner` lifecycle state is introduced.

The active planning request records that its purpose is:

```text
initial_plan
or
replan
```

---

## 11. Replanning attempt identity

Each replan request receives a new:

```text
PlanningAttemptId
```

The attempt must identify:

```text
task ID
base accepted plan fingerprint
base plan revision
replan reason
current durable execution boundary
```

---

## 12. Plan revision

Every accepted plan has a monotonic runtime revision.

Conceptually:

```text
revision 1 = initial accepted plan
revision 2 = first accepted replan
revision 3 = second accepted replan
```

A replan proposal must target the current revision.

---

## 13. Stale base revision

If a proposal targets an old plan revision:

```text
reject as stale
```

It must not overwrite a newer accepted plan.

---

## 14. Replan request

A replan request includes structured current state.

Conceptually:

```text
PlannerRequest
    purpose = replan
    task_id
    planning_attempt_id
    current_plan_revision
    current_plan_fingerprint
    protected_task_definition
    task_inputs
    goal
    requirements
    invariants
    success
    capability schemas/grants
    completed_steps
    current/pending steps
    relevant Kaj task state
    replan_reason
```

---

## 15. Planner-visible execution history

The planner may receive structured summaries of:

```text
completed planner steps
step results visible as Kaj state
human responses
capability results
child task results
relevant diagnostics
```

The host controls what information is exposed.

The planner does not receive arbitrary runtime internals.

---

## 16. Replan proposal

A replan proposal should be represented as a structured patch or replacement of the future plan portion.

Preferred model:

```text
PlanPatch
    base_plan_revision
    base_plan_fingerprint
    replacement_pending_plan
```

The runtime does not accept arbitrary whole-task replacement.

---

## 17. Replacement-future model

The initial model may treat replanning as:

```text
keep immutable completed prefix
replace planner-owned pending suffix
```

This is simpler and safer than arbitrary AST edit operations.

Conceptually:

```text
completed:
    step A
    step B

pending old:
    step C
    step D

replan proposal:
    step E
    step F

new effective plan:
    step A [history]
    step B [history]
    step E
    step F
```

---

## 18. No completed-prefix rewrite

The planner proposal should not even need to resend the completed prefix.

The runtime owns it.

This structurally prevents accidental rewrite of committed history.

---

## 19. Validation

Every replan proposal must pass:

```text
schema validation
base revision validation
base fingerprint validation
plan-boundary validation
protected-region validation
completed-history protection
AST validation
name resolution
type checking
control-flow validation
capability requirement/grant validation
task composition validation
human interaction validation
contract protection
persistence compatibility
```

---

## 20. Capability authority

Replanning cannot add:

```kaj
use NewCapability as x
```

or change an existing use declaration.

It may call only capability operations available under the existing task bindings and grants.

---

## 21. Capability operation grants

A future step using a declared but runtime-denied operation is invalid.

Replanning does not expand runtime grants.

---

## 22. Human interactions

A replanned future step may contain:

```text
ask
choose
confirm
inform
handoff
```

subject to existing semantics.

Replanning cannot alter a human response that has already occurred.

---

## 23. Child tasks

Replanned future code may use:

```text
start
await
```

normally.

It cannot erase or rewrite child tasks already created by committed execution.

Existing live children remain real runtime tasks.

---

## 24. Existing child handles

Task-local `TaskHandle<T>` values created before the replan remain valid Kaj state.

Future replanned code may use them if they remain in scope and type-valid.

---

## 25. Existing capability results

Ordinary Kaj values produced before replanning remain part of task state.

Future steps may inspect them according to normal scope rules.

---

## 26. Scope preservation

A replan must respect the current durable task environment.

Planner-generated future code may reference only symbols that will validly exist at the replanning boundary.

It may not assume bindings from removed pending steps have already been created.

---

## 27. Pending-step local bindings

Bindings that would have been created only by removed pending steps do not exist.

New plan code referencing them is invalid.

---

## 28. Replanning while waiting for human

The initial model does not replace the continuation around an active unresolved human interaction.

A task in:

```text
waiting_for_human
```

must resolve or cancel that interaction before ordinary replanning of subsequent plan work.

The host may cancel the entire task separately.

---

## 29. Replanning while waiting for capability

The initial model does not patch around an unresolved capability request with an uncertain or pending outcome.

Resolve/reconcile the capability request first.

Then replan from a safe boundary.

---

## 30. Replanning while waiting for task

If the parent is awaiting a child, the initial model waits for that child terminal outcome before replanning past the await point.

The planner may later use the child outcome as new context.

---

## 31. Failed step

Checkpoint 9 does not automatically retry or replan a failed step after the task has entered terminal:

```text
failed
```

Automatic recovery from terminal failure is not introduced implicitly.

Hosts may request replanning only while the task is in a non-terminal state at a safe boundary.

---

## 32. Recoverable trigger

A host may request a replan after a normal completed step whose result changes the desired future strategy.

Example:

```text
step inspect -> completed
result says target unavailable
host requests replan
```

No task failure is required.

---

## 33. Replan acceptance

If valid:

```text
canonicalize replacement future
compute new plan fingerprint
increment plan revision
persist new accepted plan
invalidate older active attempts
task -> running
```

---

## 34. Invalid replan

If invalid:

```text
proposal is rejected
task remains waiting_for_planner
current accepted plan remains unchanged
```

The invalid patch is never partially applied.

---

## 35. Atomic plan replacement

Applying a replan is atomic.

The runtime must not expose a half-updated plan.

Either:

```text
entire validated replan accepted
```

or:

```text
current plan remains unchanged
```

---

## 36. Replan persistence

Persist:

```text
current plan revision
current plan fingerprint
accepted future plan
completed step history
active replan attempt
replan reason
```

A restart must preserve exactly which revision was accepted.

---

## 37. Restart while waiting for replan

If the task is:

```text
waiting_for_planner
```

for a replan at crash time, restore the same active planning attempt unless host policy invalidates it.

Stale-response rules remain in force.

---

## 38. Restart after replan accepted

Restore the exact accepted plan revision.

Do not ask the planner to regenerate it.

---

## 39. Audit history

The runtime should preserve enough metadata to inspect:

```text
initial plan revision
accepted replans
rejected attempts
plan fingerprints
replan reasons
timestamps if host supplies them
```

The exact event-log backend is implementation-specific.

---

## 40. Planner rationale

A replan may include optional concise metadata explaining why the future plan changed.

This rationale is not executable and does not affect validation.

---

## 41. No chain-of-thought dependency

Controlled replanning does not require hidden model reasoning.

Kaj needs:

```text
structured state
structured patch
validation result
```

---

## 42. No source self-authorization

Planner-generated code cannot change runtime policy governing whether replanning is allowed.

The host/runtime controls replanning permission.

---

## 43. Host policy

The host may restrict:

```text
whether task may be replanned
maximum replan attempts
which planner adapter may respond
cost/time limits
manual approval before accepting proposal
```

These are host policies unless later promoted into language semantics.

---

## 44. Optional human approval

A host may require human approval before applying a validated replan.

This does not change Kaj validation semantics.

The runtime must not apply the plan until the host accepts it.

---

## 45. Replanning and success

A planner cannot weaken or alter `success`.

The final task still completes only through normal:

```text
return
final invariants
success validation
```

---

## 46. Replanning and goal

The original goal remains immutable.

If the user wants a different goal, that is a new task or future explicit contract-mutation feature, not a replan.

---

## 47. Replanning and requirements

Requirements are immutable.

A planner cannot revise preconditions after task start to make execution appear valid.

---

## 48. Replanning and invariants

Invariants remain active across every plan revision.

A replan proposal itself must not require violating an invariant.

Runtime invariant enforcement remains authoritative during execution.

---

## 49. Security principle

A replan proposal is untrusted code.

It receives no trust from the fact that an earlier plan from the same planner was valid.

Every revision is independently validated.

---

## 50. Summary

Checkpoint 9 freezes:

```text
replanning modifies only future planner-owned work
completed durable history is immutable

replanning occurs at safe boundaries
current running step is not replaced

planner proposes replacement pending suffix
runtime owns completed prefix

task signature/contracts/capabilities/fixed source remain protected
existing human responses/capability outcomes/child tasks remain real history

every plan has:
    revision
    fingerprint

every replan targets:
    current revision
    current fingerprint

stale proposals are rejected
invalid proposal leaves current plan unchanged
accepted replacement is atomic

waiting_for_planner is reused for replan requests
PlanningAttemptId identifies each attempt

accepted replans persist across restart
planner cannot weaken success or expand authority
```
