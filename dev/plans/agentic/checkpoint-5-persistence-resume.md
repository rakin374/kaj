# Agentic Kaj — Checkpoint 5: Persistence and Resume

**Track:** Agentic Kaj  
**Checkpoint:** 5  
**Recommended path:** `dev/plans/agentic/checkpoint-5-persistence-resume.md`

---

# Goal

Implement durable task persistence and process-restart resume.

Authoritative semantics:

```text
docs/agentic/persistence-resume.md
```

This checkpoint builds on Agentic Checkpoints 1–4.

---

# Scope

Implement:

```text
persistent TaskId
TaskSnapshot
snapshot schema/version
task definition fingerprint/compatibility
serializable Kaj runtime environment
persisted step states
persisted lifecycle state
persisted pending human interaction
persisted terminal result/failure
TaskStore abstraction
reference persistence backend
restore API
resume API
crash recovery from last durable boundary
incomplete-step replay
atomic snapshot writes
corrupt/incompatible snapshot handling
tests
docs integration
```

---

# Core Recovery Model

Freeze:

```text
completed step:
    never replay after successful durable commit

incomplete running step at crash:
    replay from beginning of that step

waiting_for_human:
    restore same pending interaction and InteractionId

paused:
    restore paused

completed/failed/cancelled:
    restore terminal and never resume
```

The initial model is:

```text
at-least-once execution for interrupted incomplete steps
```

not exactly-once side effects.

---

# Persistence Boundaries

Required durable writes:

```text
after validated task creation
after each completed step + post-step contract checks
when task enters paused
when task enters waiting_for_human
when task enters completed
when task enters failed
when task enters cancelled
```

The implementation may persist more often.

---

# Snapshot Model

Introduce conceptually:

```text
TaskSnapshot
    schema_version
    task_id
    task_definition_identity
    task_definition_fingerprint
    task_state
    inputs
    execution_position
    environment
    step_states
    pending_interaction
    result
    failure
```

Do not serialize live Python stacks or native objects.

---

# Serializable Values

Create/extend a canonical persistence codec for Kaj runtime values.

Must support all currently persistable pure Kaj values:

```text
Bool
Int
Decimal
String
Bytes
None
List
Map
Optional
Result
records
enums
newtypes
```

Preserve nominal type identity for:

```text
records
enums
newtypes
```

Preserve typed map key identity.

Preserve Decimal exactly.

Do not use lossy JSON number encoding for Decimal.

---

# Native Object Rejection

Persisted environments must reject native/host objects.

If such an object appears where persistence is required, fail with a structured persistence/runtime diagnostic.

Future capability bindings must use durable descriptors rather than native references.

---

# Execution Continuation

Checkpoint 4 already requires in-memory continuation.

Checkpoint 5 must convert this into a reconstructable durable execution representation.

Do not rely on:

```text
live Python generator
live coroutine frame
live exception stack
```

as the only source of resume state.

Implement explicit execution state sufficient to reconstruct:

```text
current task position
current step
nested control state needed after suspension
interaction continuation
```

If needed, normalize task execution to an explicit interpreter frame/continuation model.

This architecture should remain extensible for capabilities and task composition.

---

# Task Definition Fingerprint

Compute a deterministic fingerprint for the task definition and relevant dependency graph.

Initial conservative rule:

```text
exact fingerprint match required for resume
```

If mismatch:

```text
restore may inspect
resume rejected
```

No automatic migration.

---

# TaskStore

Introduce an interface conceptually:

```text
TaskStore.save(snapshot)
TaskStore.load(task_id)
TaskStore.list(...)
TaskStore.delete(...)
```

Add:

```text
InMemoryTaskStore
```

for deterministic tests.

Add one durable reference backend.

Preferred simple choices:

```text
SQLite
or
atomic JSON snapshot directory
```

Use whichever best fits the existing repository with minimal unnecessary dependency cost.

---

# Atomic Writes

Durable backend must avoid interpreting partial writes as valid snapshots.

For file backend use:

```text
write temporary file
fsync where practical
atomic replace
```

For SQLite use a transaction.

---

# Restore API

Add runtime operations conceptually:

```text
restore_task(task_id)
resume_task(task_id)
```

`restore_task` reconstructs without automatically executing.

`resume_task` validates state and continues if resumable.

---

# State Rules

Restored:

```text
READY:
    host may start/resume

PAUSED:
    remains paused until resume requested

WAITING_FOR_HUMAN:
    remains waiting

COMPLETED:
    terminal

FAILED:
    terminal

CANCELLED:
    terminal
```

If a snapshot records `RUNNING` due to crash:

```text
recover from last durable continuation boundary
mark current incomplete step pending/restartable as required
```

Do not resume from an arbitrary half-evaluated host stack.

---

# Incomplete Step Recovery

If crash occurs during:

```text
step process
```

and no durable completion commit exists:

```text
process executes again from its beginning
```

Any task-local state must be restored to the state at the last committed boundary before that step.

This requires checkpoint snapshots to represent pre-step durable state correctly.

---

# Step Completion Commit

Commit order should conceptually be:

```text
step body completes
↓
post-step invariant checks pass
↓
update step = completed
↓
save durable snapshot atomically
↓
step is considered durably committed
```

If persistence fails:

```text
do not report step as durably completed
task/runtime enters structured failure state as appropriate
```

---

# Human Interaction Persistence

Persist:

```text
InteractionId
kind
prompt
expected type
options
status
continuation
```

After restart:

```text
get_pending_interaction(task_id)
```

returns the same interaction.

Valid response resumes exact continuation.

Do not regenerate InteractionId.

---

# Terminal Persistence

Persist:

```text
completed result
failed TaskFailure
cancelled state/reason
```

Runtime inspection after restart must show identical terminal outcome.

---

# Persistence Errors

Add/reuse structured failures/diagnostics for:

```text
snapshot not found
snapshot corrupt
unsupported snapshot version
task definition mismatch
dependency fingerprint mismatch
non-serializable value
persistence write failure
persistence read failure
invalid restored state
```

Suggested codes if conventions permit:

```text
TASK_PERSISTENCE_NOT_FOUND
TASK_PERSISTENCE_CORRUPT
TASK_PERSISTENCE_VERSION_UNSUPPORTED
TASK_DEFINITION_MISMATCH
TASK_PERSISTENCE_VALUE_NOT_SERIALIZABLE
TASK_PERSISTENCE_WRITE_FAILED
TASK_PERSISTENCE_READ_FAILED
TASK_PERSISTENCE_INVALID_STATE
```

---

# AST

No new source syntax is required by this checkpoint.

Do not add persistence metadata to source AST or AST JSON.

Persistence is runtime state.

---

# CLI

If cleanly useful, add minimal host/debug commands such as:

```bash
kaj task resume <file> <TaskId>
```

or a repository-appropriate equivalent.

Do not force CLI design if it complicates the checkpoint.

Runtime API correctness is mandatory; CLI persistence commands are optional.

---

# Required Tests

Value codec:

```text
Bool
Int arbitrary precision
Decimal exact
String Unicode
Bytes
None
List
Map typed keys
Optional
Result
record identity
enum identity/payload
newtype identity
nested values
```

Snapshots:

```text
save/load round trip
schema version
TaskId preserved
definition fingerprint preserved
step states preserved
environment preserved
pending interaction preserved
terminal result preserved
failure preserved
```

Restart scenarios:

```text
restart after task creation
restart after completed step
restart while paused
restart while waiting_for_human
restart after completed
restart after failed
restart after cancelled
```

Crash during step:

```text
incomplete step replayed
completed prior steps not replayed
environment restored to pre-step committed state
```

Human interaction:

```text
InteractionId survives restart
response resumes exact continuation
duplicate response still rejected
```

Compatibility:

```text
matching definition resumes
changed task definition rejected
changed dependency rejected if fingerprinted
unsupported snapshot version rejected
corrupt snapshot rejected
```

Atomicity/failure:

```text
persistence failure does not falsely commit step
partial/corrupt file not accepted
non-serializable value rejected
```

Regression:

```text
Pure Kaj
Agentic Checkpoints 1–4
Checkpoint 5
mkdocs build --strict
```

---

# Out of Scope

Do not implement:

```text
capability declarations
use
host capability adapters
browser integration
exactly-once external side effects
idempotency keys
task composition
TaskHandle
waiting_for_task
planner
LLM integration
plan blocks
AST patches
replanning
snapshot migration
distributed scheduler
multi-node task ownership
automatic startup resume
```

---

# Definition of Done

```text
[ ] TaskSnapshot exists
[ ] snapshot schema is versioned
[ ] TaskId persists across restart
[ ] task definition fingerprint stored/validated

[ ] canonical Kaj value persistence codec exists
[ ] Decimal preserved exactly
[ ] nominal identities preserved
[ ] native objects rejected

[ ] step states persist
[ ] task lifecycle state persists
[ ] task environment persists
[ ] pending human interaction persists
[ ] terminal result/failure persists

[ ] TaskStore abstraction exists
[ ] InMemoryTaskStore exists
[ ] durable reference store exists
[ ] writes are atomic

[ ] restore_task works
[ ] resume_task works

[ ] paused restores paused
[ ] waiting_for_human restores waiting
[ ] terminal tasks remain terminal
[ ] completed steps are not replayed
[ ] incomplete crash-time step replays from beginning

[ ] InteractionId survives restart
[ ] restored interaction accepts valid response
[ ] continuation resumes exactly after interaction

[ ] incompatible definition rejected
[ ] corrupt snapshot rejected
[ ] unsupported version rejected
[ ] persistence failures structured

[ ] no persistence metadata added to AST JSON

[ ] Pure Kaj suite passes
[ ] Agentic Checkpoints 1–4 pass
[ ] Checkpoint 5 tests pass
[ ] mkdocs build --strict passes
```

---

# Completion Report

```text
Agentic Kaj Checkpoint 5 — Persistence and Resume

Status:
COMPLETE / INCOMPLETE

Files changed:
- ...

Persistence model:
- TaskSnapshot: PASS/FAIL
- schema version: PASS/FAIL
- TaskId persistence: PASS/FAIL
- definition fingerprint: PASS/FAIL
- value codec: PASS/FAIL
- nominal identity: PASS/FAIL

Storage:
- TaskStore: PASS/FAIL
- in-memory backend: PASS/FAIL
- durable backend: PASS/FAIL
- atomic writes: PASS/FAIL

Resume:
- restore task: PASS/FAIL
- paused restore: PASS/FAIL
- human-wait restore: PASS/FAIL
- terminal restore: PASS/FAIL
- exact interaction continuation: PASS/FAIL

Crash recovery:
- completed steps not replayed: PASS/FAIL
- incomplete step replay: PASS/FAIL
- pre-step state restore: PASS/FAIL

Validation:
- definition mismatch: PASS/FAIL
- corrupt snapshot: PASS/FAIL
- version mismatch: PASS/FAIL
- non-serializable values: PASS/FAIL

Regression:
- Pure Kaj: PASS/FAIL
- Agentic Checkpoints 1–4: PASS/FAIL
- Agentic Checkpoint 5: PASS/FAIL
- mkdocs build --strict: PASS/FAIL

Deferred intentionally:
- capabilities
- exactly-once side effects
- task composition
- planner
- replanning

Known issues:
- ...
```
