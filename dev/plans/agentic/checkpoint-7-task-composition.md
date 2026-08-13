# Agentic Kaj — Checkpoint 7: Task Composition

**Track:** Agentic Kaj  
**Checkpoint:** 7  
**Recommended path:** `dev/plans/agentic/checkpoint-7-task-composition.md`

---

# Goal

Implement child-task composition.

Authoritative semantics:

```text
docs/agentic/task-composition.md
```

This checkpoint builds on Agentic Checkpoints 1–6.

---

# Scope

Implement:

```text
TaskHandle<T>
start
await
child TaskInstance creation
parent/child relationships
waiting_for_task lifecycle state
child-result propagation
child failure/cancellation propagation through await
downward cancellation propagation
persistence of task handles/relationships
restore of waiting parent
capability binding independence for child tasks
diagnostics
tests
docs integration
```

---

# Frozen Syntax

Start:

```kaj
let child = start Child(21)
```

Await:

```kaj
let result = await child
```

Conceptual types:

```text
start Child(...) -> TaskHandle<ChildReturnType>
await TaskHandle<T> -> T
```

---

# `TaskHandle<T>`

Add an Agentic runtime type:

```text
TaskHandle<T>
```

It represents:

```text
specific child TaskId
expected result type T
relationship metadata
```

It is not the child result.

TaskHandle must be persistable.

---

# Start Semantics

`start` target must be a task declaration.

Validate:

```text
target exists
target is task
argument count
argument names
argument types
```

Then:

```text
create new child TaskInstance
assign new TaskId
set parent_task_id
satisfy child's capability requirements
schedule child
return TaskHandle<T>
```

If child creation/binding fails before creation becomes valid, return/raise structured composition runtime failure according to existing runtime error conventions.

---

# Await Semantics

For:

```text
handle: TaskHandle<T>
```

`await handle`:

```text
child COMPLETED
    -> return persisted/runtime result T

child FAILED
    -> fail parent with structured child failure

child CANCELLED
    -> fail parent with structured child-cancelled failure

child non-terminal
    -> parent WAITING_FOR_TASK
```

---

# Lifecycle

Add:

```text
WAITING_FOR_TASK
```

Transitions:

```text
RUNNING -> WAITING_FOR_TASK
WAITING_FOR_TASK -> RUNNING
WAITING_FOR_TASK -> FAILED
WAITING_FOR_TASK -> CANCELLED
```

A parent waiting on child remains non-running until child terminal outcome is known.

---

# Step Semantics

If `await` occurs inside a step:

```text
step remains RUNNING
parent -> WAITING_FOR_TASK
```

After child completes:

```text
parent -> RUNNING
step remains RUNNING
execution resumes after await
```

Do not replay `start` or `await` after normal suspension/resume.

---

# Parent/Child Runtime Metadata

Extend TaskInstance conceptually:

```text
parent_task_id: Optional<TaskId>
child_task_ids: List<TaskId>
waiting_on_task_id: Optional<TaskId>
```

Use appropriate indexed structures in implementation.

---

# Root Tasks

Host-started tasks:

```text
parent_task_id = none
```

Child-started tasks:

```text
parent_task_id = current task id
```

A child has one direct parent.

---

# Scheduling

Introduce a runtime scheduling abstraction sufficient for:

```text
start child
allow child to execute independently
wake waiting parent on child terminal state
```

Do not require OS-level parallelism.

A deterministic cooperative scheduler is acceptable.

---

# Parent Completion

Freeze:

```text
parent may complete with live children
```

Do not automatically cancel children on normal parent completion.

---

# Parent Failure/Cancellation

On parent:

```text
FAILED
or
CANCELLED
```

cancel all non-terminal descendants recursively.

This should be idempotent and deterministic.

---

# Child Cancellation

Child cancellation alone does not cancel parent.

If parent is awaiting that child:

```text
await -> structured parent failure
```

---

# Structured Child Failures

Add runtime failure categories conceptually:

```text
ChildTaskFailed
ChildTaskCancelled
ChildTaskMissing
ChildTaskResultTypeMismatch
TaskCompositionFailure
```

Preserve nested child failure details where useful.

---

# Result.err Distinction

If child task's return type is:

```text
Result<T,E>
```

and it completes with:

```text
err(...)
```

then:

```text
await -> Result.err(...)
```

normally.

Do not treat it as task/runtime failure.

---

# Capability Integration

Child tasks resolve their own `use` requirements.

Do NOT automatically copy parent capability bindings.

At child start:

```text
resolve child requirements
ask host/registry for bindings
bind child independently
```

The host may intentionally reuse same underlying host binding, but this is explicit host policy.

---

# Human Interaction Integration

Child task may independently enter:

```text
WAITING_FOR_HUMAN
```

Parent awaiting it remains:

```text
WAITING_FOR_TASK
```

Runtime/host inspection must preserve correct TaskId ownership for interactions.

---

# Capability Waiting Integration

Child task may independently enter:

```text
WAITING_FOR_CAPABILITY
```

Parent awaiting it remains:

```text
WAITING_FOR_TASK
```

---

# Persistence

Extend TaskSnapshot/runtime persistence with:

```text
parent_task_id
child_task_ids
waiting_on_task_id
TaskHandle values
```

TaskHandle persistence stores:

```text
child TaskId
result type identity
```

Do not persist live TaskInstance references.

---

# Restore

When restoring parent waiting on child:

```text
load parent
load/resolve child TaskId

child non-terminal:
    parent remains WAITING_FOR_TASK

child completed:
    resume parent with persisted result

child failed/cancelled:
    resume failure path
```

If child is missing/corrupt:

```text
resume rejected/fails with structured composition persistence failure
```

Do not create replacement child automatically.

---

# AST / Parser

Introduce semantic forms for:

```text
start Task(...)
await expression
```

Prefer explicit AST nodes if useful:

```text
StartTaskExpression
AwaitTaskExpression
```

Do not treat `start` as ordinary function call.

Do not add runtime TaskId into AST.

---

# Type Checking

`start`:

```text
target must resolve to TaskDeclaration
arguments checked against task parameters
expression type = TaskHandle<return_type>
```

`await`:

```text
operand must be TaskHandle<T>
expression type = T
```

Reject:

```text
start fn
await non-handle
start/await inside fn
start/await in task contracts
```

---

# Formatter

Canonical:

```kaj
let child = start Child(21)
let result = await child
```

Follow existing expression formatting conventions.

---

# Diagnostics

Add/reuse stable diagnostics for:

```text
start target not task
unknown task
task argument mismatch
await non-handle
start in fn
await in fn
start/await in contract
child task missing
child task failed
child task cancelled
child result type mismatch
invalid parent/child relation
```

Suggested codes if conventions permit:

```text
TASK_START_TARGET_NOT_TASK
TASK_START_UNKNOWN_TASK
TASK_START_ARGUMENT_MISMATCH
TASK_AWAIT_EXPECTED_HANDLE
TASK_COMPOSITION_NOT_ALLOWED_IN_FUNCTION
TASK_COMPOSITION_NOT_ALLOWED_IN_CONTRACT
TASK_CHILD_FAILED
TASK_CHILD_CANCELLED
TASK_CHILD_NOT_FOUND
TASK_CHILD_RESULT_TYPE_MISMATCH
TASK_INVALID_PARENT_RELATION
```

---

# Required Tests

Syntax/type:

```text
start task valid
start fn rejected
unknown task rejected
argument count mismatch
argument type mismatch
TaskHandle<T> inferred
await handle returns T
await non-handle rejected
start/await in fn rejected
start/await in contracts rejected
```

Runtime:

```text
child TaskId distinct
parent_task_id set
child listed under parent
child completes
await completed child immediate
await running child -> WAITING_FOR_TASK
child completion wakes parent
child failed -> parent failure
child cancelled -> parent failure
Result.err child returns normally
```

Multiple children:

```text
start two children
await each independently
one child waiting_for_human
one child running
parent relationship correct
```

Cancellation/failure:

```text
parent cancel recursively cancels descendants
parent fail recursively cancels descendants
child cancel does not auto-cancel parent
parent normal completion does not cancel live child
```

Steps:

```text
await inside step keeps step RUNNING
resume continues after await
start not replayed
await not replayed
```

Capabilities:

```text
child requirements bound independently
parent binding not implicitly inherited
same underlying host instance may be explicitly rebound by host
```

Persistence:

```text
TaskHandle round-trip
parent/child IDs persist
waiting_on_task_id persists
restart parent waiting child
completed child resumes parent
failed child fails parent
missing child rejected
```

Regression:

```text
Pure Kaj
Agentic Checkpoints 1–6
Checkpoint 7
mkdocs build --strict
```

---

# Out of Scope

Do not implement:

```text
structured concurrency enforcement
automatic join of all children
task groups
race/select over task handles
source-level cancel(handle)
source-level task status polling
detached task syntax
shared-parent DAG task graphs
planner
LLM integration
plan blocks
AST patches
replanning
distributed scheduler
remote task migration
```

---

# Definition of Done

```text
[ ] TaskHandle<T> exists
[ ] start parses/type-checks
[ ] await parses/type-checks
[ ] start fn rejected
[ ] await non-handle rejected
[ ] fn/contracts cannot compose tasks

[ ] child TaskInstance created
[ ] child TaskId unique
[ ] parent_task_id recorded
[ ] child list recorded

[ ] WAITING_FOR_TASK implemented
[ ] await suspends parent when needed
[ ] completed child resumes with T
[ ] failed child fails parent
[ ] cancelled child fails parent
[ ] Result.err remains normal result

[ ] parent cancellation cancels descendants
[ ] parent failure cancels descendants
[ ] parent completion leaves children running

[ ] child capability requirements resolved independently
[ ] no implicit capability inheritance

[ ] TaskHandle persists
[ ] task relationships persist
[ ] waiting parent restores correctly
[ ] missing child restore rejected

[ ] formatter canonical/idempotent
[ ] AST JSON excludes runtime TaskIds

[ ] Pure Kaj suite passes
[ ] Agentic Checkpoints 1–6 pass
[ ] Checkpoint 7 tests pass
[ ] mkdocs build --strict passes
```

---

# Completion Report

```text
Agentic Kaj Checkpoint 7 — Task Composition

Status:
COMPLETE / INCOMPLETE

Files changed:
- ...

Syntax:
- start: PASS/FAIL
- await: PASS/FAIL
- TaskHandle<T>: PASS/FAIL
- formatter: PASS/FAIL
- AST JSON: PASS/FAIL

Typing:
- start target validation: PASS/FAIL
- argument typing: PASS/FAIL
- TaskHandle inference: PASS/FAIL
- await typing: PASS/FAIL
- fn/contract restrictions: PASS/FAIL

Runtime:
- child TaskInstance: PASS/FAIL
- parent/child relation: PASS/FAIL
- waiting_for_task: PASS/FAIL
- child completion wakeup: PASS/FAIL
- child failure propagation: PASS/FAIL
- child cancellation propagation through await: PASS/FAIL
- Result.err distinction: PASS/FAIL

Cancellation:
- parent cancel -> descendants: PASS/FAIL
- parent fail -> descendants: PASS/FAIL
- parent completion leaves child alive: PASS/FAIL

Capabilities:
- child requirements independent: PASS/FAIL
- no implicit inheritance: PASS/FAIL

Persistence:
- TaskHandle persisted: PASS/FAIL
- relationships persisted: PASS/FAIL
- waiting parent restored: PASS/FAIL
- missing child rejected: PASS/FAIL

Regression:
- Pure Kaj: PASS/FAIL
- Agentic Checkpoints 1–6: PASS/FAIL
- Agentic Checkpoint 7: PASS/FAIL
- mkdocs build --strict: PASS/FAIL

Deferred intentionally:
- structured concurrency/task groups
- planner
- replanning
- distributed scheduling

Known issues:
- ...
```
