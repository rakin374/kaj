# Persistence and Resume

Persistence allows Agentic Kaj tasks to survive process interruption and resume from durable runtime state.

This document defines the initial semantics of persistent task state, suspension checkpoints, restart recovery, and resume behavior.

---

## 1. Overview

Agentic Kaj tasks are durable units of work.

Checkpoint 5 makes that durability real across process restart.

A task may be suspended while:

```text
paused
waiting_for_human
```

and later resume without restarting from the beginning.

The runtime persists enough state to reconstruct the task instance safely.

---

## 2. Persisted task identity

Every persistent task instance retains its existing opaque:

```text
TaskId
```

across process restart.

A restored task is the same task instance, not a new execution.

---

## 3. Persisted task definition identity

Persistent state must record which task definition it belongs to.

At minimum:

```text
module identity
task name
task definition version/fingerprint
```

The runtime must not resume a persisted task against an incompatible task definition silently.

---

## 4. Persisted lifecycle state

Persistent state includes the task lifecycle state.

Persistable non-terminal states include:

```text
ready
paused
waiting_for_human
```

A task that is `running` at crash time requires recovery semantics described below.

Terminal states may also be persisted:

```text
completed
failed
cancelled
```

so that task history remains inspectable.

---

## 5. Persisted inputs

Task input arguments are persisted as canonical Kaj values.

Only values representable by the Kaj runtime's persistent value encoding may survive restart.

---

## 6. Persisted task-local values

Values needed after a suspension point must be persisted.

This may include:

```text
task parameters
task-local let bindings
task-local var bindings
loop/control state if suspension can occur within them
current step-local state if the task is suspended within a step
```

The runtime must not rely on a live Python stack frame for durable resume.

---

## 7. Serializable Kaj values

Persistent task state may contain only serializable Kaj values.

This includes ordinary pure Kaj values such as:

```text
Bool
Int
Decimal
String
Bytes
None
List<T>
Map<K,V>
Optional<T>
Result<T,E>
records
enums
newtypes
```

Runtime/native host objects are not persistable Kaj values.

---

## 8. Native objects may not leak into task state

The task runtime must never persist direct host objects such as:

```text
WKWebView
browser session object
Python file handle
socket
database connection
native callback
thread
future/promise object
```

Future capabilities must be represented by durable capability bindings/identifiers rather than native object references.

---

## 9. Persistent execution position

The runtime must persist where task execution should continue.

Checkpoint 5 requires an explicit continuation/execution representation.

A restored task must not restart from the beginning.

---

## 10. Safe persistence boundaries

The initial durable persistence boundaries are:

```text
after task creation/validation
after each completed step
when entering paused
when entering waiting_for_human
after terminal completion/failure/cancellation
```

The runtime may persist more often, but these are the required semantic boundaries.

---

## 11. Completed steps

Completed step records are persisted.

After restart, completed steps must not execute again merely because the process restarted.

Example:

```text
prepare = completed
search = completed
approve = running/waiting
finish = pending
```

After restore, `prepare` and `search` remain completed.

---

## 12. Waiting for human

If a task is:

```text
waiting_for_human
```

the pending interaction must be persisted.

Persist at least:

```text
InteractionId
interaction kind
prompt
expected type
options if choose
status
suspension continuation
```

After restart, the host may inspect and answer the same pending interaction.

---

## 13. Interaction identity survives restart

A pending `InteractionId` remains stable across restart.

The host must not need to create a new interaction merely because the runtime restarted.

---

## 14. Resume after human response

After a valid response to a restored interaction:

```text
waiting_for_human
    ↓
running
```

Execution resumes immediately after the interaction suspension point.

The interaction primitive is not re-executed.

---

## 15. Paused task persistence

A paused task may be persisted and restored.

After restart it remains:

```text
paused
```

until the host explicitly resumes it.

Restoring a paused task does not automatically start execution.

---

## 16. Resume from paused

When the host resumes a persisted paused task:

```text
paused
   ↓
invariant validation
   ↓
running
```

Existing contract semantics remain authoritative.

If an invariant fails, the task fails instead of resuming.

---

## 17. Crash during a running task

A process may crash while the task state is:

```text
running
```

The runtime must not blindly assume the currently executing operation completed.

Checkpoint 5 distinguishes:

```text
last committed durable state
current uncommitted execution
```

Recovery resumes from the last committed safe boundary.

---

## 18. Crash between steps

If the runtime has durably committed:

```text
step A = completed
```

and crashes before step B begins, restore continues at step B.

Step A is not replayed.

---

## 19. Crash during a step

If the process crashes while a step is still running, the step has not been durably completed.

Initial recovery rule:

```text
restore task at the beginning of the incomplete step
```

This means code inside the incomplete step may execute again.

Therefore, side effects inside steps are not yet guaranteed exactly-once.

Capabilities later need idempotency/reconciliation semantics.

---

## 20. Step replay warning

Checkpoint 5 provides:

```text
at-least-once execution for an interrupted incomplete step
```

not exactly-once external side effects.

Pure computation replay is safe.

External side-effect safety is addressed when capabilities are introduced.

---

## 21. Durable commit of step completion

A step is considered durably completed only after:

```text
step body finishes normally
contract checks required after the step pass
persistent runtime state is committed
```

Only then may recovery skip that step.

---

## 22. Terminal states

Persist terminal task state:

```text
completed
failed
cancelled
```

A restored terminal task remains terminal.

It must never execute again through ordinary resume.

---

## 23. Persisted result

For a completed task, persist:

```text
result
```

as a canonical Kaj value.

For a failed task, persist structured task failure information.

For a cancelled task, persist cancellation state/reason if available.

---

## 24. Persistent failure representation

Persist task failure using Kaj/runtime-defined structured data.

Do not serialize arbitrary Python exception objects as the durable contract.

At minimum preserve:

```text
failure category/code
message
source span if available
task ID
task name
relevant step if any
```

---

## 25. Storage backend independence

Kaj semantics do not require a particular persistence backend.

Valid hosts may use:

```text
SQLite
Postgres
files
key-value store
embedded database
remote workflow store
```

Checkpoint 5 reference implementation may use a simple local backend.

The durable state format must remain conceptually host-independent.

---

## 26. Reference storage backend

For the reference runtime, prefer a simple explicit persistence interface.

Conceptually:

```text
TaskStore
    save(TaskSnapshot)
    load(TaskId)
    list(...)
    delete(...)
```

The first backend may be:

```text
JSON files
SQLite
in-memory test store
```

but tests must not depend on accidental storage behavior.

---

## 27. Task snapshot

A durable task snapshot conceptually contains:

```text
task_id
task_definition_identity
task_state
inputs
execution_position
persistent environment
step execution states
pending interaction
result
failure
schema/version
```

Exact serialization format is implementation detail.

---

## 28. Snapshot versioning

Persistent snapshots must carry a format/schema version.

The runtime must not silently interpret incompatible snapshot formats.

---

## 29. Task definition compatibility

A persisted task may only resume if its task definition is compatible with the snapshot.

Initial conservative rule:

```text
definition fingerprint must match exactly
```

If it does not:

```text
resume is rejected
```

Do not attempt automatic migration in the first model.

---

## 30. Definition fingerprint

The runtime may compute a deterministic fingerprint from the canonical task definition/AST.

It should represent semantics relevant to continuation compatibility.

The exact hash algorithm is implementation detail.

---

## 31. Module dependency compatibility

If imported definitions affect the task's execution, the runtime should conservatively include relevant module/dependency identity in compatibility validation.

The first implementation may use a module graph fingerprint.

---

## 32. Resume API

The runtime provides a host-facing resume operation.

Conceptually:

```text
load TaskSnapshot
validate snapshot/version
validate task definition compatibility
reconstruct TaskInstance
restore Kaj environment
restore execution position
restore interaction/step states
resume if requested
```

---

## 33. Restore versus resume

These are distinct operations conceptually.

```text
restore:
    reconstruct task instance from storage

resume:
    cause a resumable restored task to continue execution
```

A restored `waiting_for_human` task remains waiting.

A restored `paused` task remains paused.

---

## 34. Auto-resume

Checkpoint 5 does not require automatic resume after runtime startup.

The host chooses which resumable tasks to resume.

This avoids surprising side effects after process launch.

---

## 35. Persistent human interactions

A restored human interaction must be inspectable by the host using the same structured interaction model introduced earlier.

The host may render it again without creating a duplicate interaction.

---

## 36. Duplicate human responses after restart

Existing stale/duplicate response rules remain in force.

A response for an already completed interaction must be rejected even after restart.

---

## 37. Cancellation persistence

If a persistent task is cancelled, persist the `cancelled` terminal state before reporting cancellation complete to the host where practical.

A restarted runtime must not resurrect the task.

---

## 38. Persistence failures

Failure to save required durable state is a runtime failure.

The runtime must not report a checkpoint as durable if persistence failed.

---

## 39. Atomicity

Snapshot updates should be atomic enough that a crash does not produce a partially written snapshot interpreted as valid state.

Reference implementations should use:

```text
transaction
atomic file replace
or equivalent
```

depending on storage backend.

---

## 40. Corrupt snapshots

Corrupt/unreadable snapshots must be rejected with a structured persistence error.

Do not partially recover by guessing missing state.

---

## 41. Persistence and `inform`

`inform` is non-blocking.

Checkpoint 5 does not require replaying notifications after crash.

If an `inform` occurs inside an incomplete step that is replayed, it may be emitted again.

Exactly-once event delivery is deferred.

---

## 42. Persistence and contracts

Persist enough task state for contract checks to remain correct after restore.

On resume from `paused`, re-check invariants as previously defined.

A restored `waiting_for_human` task does not re-run prior requirements or completed-step invariant checks unnecessarily.

---

## 43. Runtime event history

A host may persist an append-only event log in addition to snapshots.

This is optional in the initial model.

Kaj semantics require correct restored state, not a specific event-sourcing architecture.

---

## 44. Security

Snapshots may contain user/task data.

Hosts are responsible for storage security.

The Kaj runtime must not serialize arbitrary host secrets that are not represented as task-visible Kaj values.

---

## 45. Summary

Checkpoint 5 freezes:

```text
TaskId survives restart
task definition identity/fingerprint persisted
task inputs persisted
persistent Kaj environment persisted
step states persisted
pending human interaction persisted
terminal results/failures persisted

safe durable boundaries:
    task initialization
    completed step
    paused
    waiting_for_human
    terminal state

completed steps are not replayed
incomplete step may replay from its beginning
initial semantics are at-least-once for interrupted steps
exactly-once external effects are deferred

paused restores as paused
waiting_for_human restores as waiting
terminal tasks remain terminal
host explicitly chooses resume

snapshot format is versioned
task definition compatibility is validated
corrupt/incompatible snapshots are rejected
storage backend is host-independent
```
