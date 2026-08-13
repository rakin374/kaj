# Task Composition

Task composition allows Agentic Kaj tasks to start, track, and wait for other tasks.

This document defines the initial semantics of child tasks, task handles, `start`, `await`, and `waiting_for_task`.

---

## 1. Overview

A task may delegate part of its work to another task.

Example:

```kaj
task Parent() -> Int {
    let child = start Child(21)
    let result = await child
    return result
}

task Child(value: Int) -> Int {
    return value * 2
}
```

Task composition introduces:

```text
child task instances
TaskHandle<T>
start
await
waiting_for_task
parent/child relationships
cancellation propagation rules
persistence of task dependencies
```

---

## 2. `start`

`start` creates a new child task instance.

Example:

```kaj
let child = start Child(21)
```

This does not execute the child as an ordinary function call.

It creates a distinct:

```text
TaskInstance
```

with its own:

```text
TaskId
lifecycle
steps
contracts
human interactions
capabilities
persistence state
```

---

## 3. `TaskHandle<T>`

`start` returns a task handle.

Conceptually:

```text
TaskHandle<T>
```

where `T` is the child task's declared return type.

Example:

```kaj
let child: TaskHandle<Int> = start Child(21)
```

The handle represents a specific child task instance.

It is not the child's result.

---

## 4. Task handles are typed

If:

```kaj
task Child() -> String {
    return "done"
}
```

then:

```kaj
start Child()
```

has type:

```text
TaskHandle<String>
```

This lets `await` recover the child result type statically.

---

## 5. `TaskHandle<T>` identity

A task handle refers to one runtime task instance.

Conceptually it contains/encapsulates:

```text
child TaskId
expected result type T
parent relationship metadata
```

Its exact runtime representation is implementation-defined.

---

## 6. `start` target

The target of `start` must be a task declaration.

Valid:

```kaj
let h = start Child()
```

Invalid:

```kaj
let h = start helper()
```

if `helper` is a normal `fn`.

---

## 7. Start argument typing

Arguments supplied to `start` use the child task's normal parameter typing rules.

Invalid:

```kaj
task Child(value: Int) -> Int {
    return value
}

let h = start Child("wrong")
```

The child must not be created if argument validation fails.

---

## 8. Parent/child relationship

A task created by `start` records the current task as its parent.

Conceptually:

```text
Parent TaskInstance
    ↓
Child TaskInstance
```

A child has at most one direct parent in the initial model.

A task may have multiple children.

---

## 9. Root tasks

Tasks started directly by the host have no parent.

They are root task instances.

---

## 10. Child task independence

A child task has its own lifecycle.

Starting a child does not merge its state into the parent.

Example:

```text
parent = running
child = running
```

or:

```text
parent = waiting_for_task
child = waiting_for_human
```

The two task instances remain distinct.

---

## 11. `await`

`await` waits for a task handle to reach a terminal state.

Example:

```kaj
let result = await child
```

If the child completes normally, `await` produces the child's result value.

---

## 12. `await` type

If:

```text
child: TaskHandle<T>
```

then:

```text
await child
```

has type:

```text
T
```

---

## 13. `waiting_for_task`

If the child is not yet terminal, the parent transitions:

```text
running
   ↓
waiting_for_task
```

When the awaited child reaches a terminal state, the parent becomes runnable again.

---

## 14. Lifecycle transitions

Checkpoint 7 adds:

```text
waiting_for_task
```

Relevant transitions:

```text
running -> waiting_for_task
waiting_for_task -> running
waiting_for_task -> failed
waiting_for_task -> cancelled
```

The exact outcome depends on the child terminal state and await semantics.

---

## 15. Awaiting completed child

If the child is already completed when `await` executes, the parent does not need to suspend.

The result is returned immediately.

---

## 16. Awaiting failed child

If the child is:

```text
failed
```

then the initial rule is:

```text
await causes the parent task to fail with a structured child-task failure
```

The failure should preserve:

```text
child TaskId
child task name
child failure
```

The parent does not receive a normal `T` value.

---

## 17. Awaiting cancelled child

If the child is:

```text
cancelled
```

then:

```text
await causes the parent task to fail with a structured child-cancelled failure
```

Initial Kaj does not silently convert child cancellation into a default value.

---

## 18. Domain `Result.err` remains normal

If a child task returns:

```kaj
Result<T, E>
```

and completes with:

```kaj
err(...)
```

then:

```text
child state = completed
```

and:

```text
await child
```

returns that `Result.err(...)` value normally.

This is not child-task failure.

---

## 19. Multiple child tasks

A parent may start multiple child tasks.

Example:

```kaj
let a = start FetchA()
let b = start FetchB()

let a_result = await a
let b_result = await b
```

The child tasks are independent.

The initial model does not require parallel execution, but the runtime may schedule them independently.

---

## 20. Scheduling

Kaj semantics do not require a specific scheduler.

A host/runtime may run child tasks:

```text
immediately
cooperatively
on a worker pool
remotely
```

The observable task semantics must remain consistent.

---

## 21. `start` does not imply `await`

A parent may start a child and continue execution.

Example:

```kaj
let h = start BackgroundWork()
inform("child started")
```

The parent is not required to await the child immediately.

---

## 22. Unawaited children

A child continues as an independent child task even if the parent does not immediately await it.

However, the parent-child relationship remains recorded.

The parent completing does not automatically imply the child completed.

---

## 23. Parent completion with live children

Initial rule:

```text
a parent may complete while child tasks are still non-terminal
```

Child tasks continue according to host/runtime scheduling.

A later structured-concurrency mode may impose stricter rules, but it is not part of the initial model.

---

## 24. Parent cancellation

When a parent task is cancelled, the initial default rule is:

```text
cancel all non-terminal direct child tasks
```

Cancellation propagates recursively through descendants.

---

## 25. Child cancellation does not cancel parent automatically

Cancelling a child does not automatically cancel its parent.

The parent is affected only if it later awaits the cancelled child, or host policy explicitly cancels the parent.

---

## 26. Parent failure

Initial rule:

```text
parent failure cancels all non-terminal descendants
```

This prevents abandoned task trees by default.

---

## 27. Parent completion

Parent completion does not cancel children.

This asymmetry is intentional:

```text
failure/cancellation -> propagate cancellation downward
normal completion -> children may continue
```

---

## 28. Task handles and persistence

A `TaskHandle<T>` must be persistable.

Persist enough information to restore:

```text
child TaskId
expected result type
relationship metadata
```

Do not persist a direct in-memory child object reference.

---

## 29. Restoring parent waiting on child

If a persisted parent is:

```text
waiting_for_task
```

the snapshot must retain the awaited child identity.

After restart:

```text
restore parent
restore/locate child
inspect child state
```

If child is still non-terminal, parent remains waiting.

If child is terminal, the parent may resume according to await rules.

---

## 30. Restoring completed child

If child completed before restart and parent was waiting, the parent can resume with the persisted child result.

No child task re-execution is required.

---

## 31. Missing child on restore

If a parent snapshot refers to a child task that cannot be found, resume must fail with a structured task-composition persistence error.

Do not silently create a replacement child.

---

## 32. Child TaskId stability

Child task IDs remain stable across persistence/restart just like root task IDs.

---

## 33. `start` and capabilities

A child task has its own capability requirements.

The parent does not automatically transfer all of its capability bindings.

At child creation, the host/runtime must satisfy the child's declared capability requirements.

---

## 34. No implicit capability inheritance

Given:

```kaj
task Parent() -> None {
    use Browser as browser
    let h = start Child()
    return none
}
```

`Child` does not automatically receive `browser`.

If `Child` requires Browser, it declares its own:

```kaj
use Browser as browser
```

and the host provides/binds a suitable instance.

---

## 35. Host binding policy for child capabilities

The host may choose to bind the child's requirement to:

```text
the same underlying resource
a different resource
or deny the requirement
```

Kaj source does not implicitly decide this.

---

## 36. Child task contracts

A child task evaluates its own:

```text
goal
require
invariant
success
```

independently.

Parent contracts do not automatically become child contracts.

---

## 37. Human interaction in child tasks

A child may enter:

```text
waiting_for_human
```

while the parent waits in:

```text
waiting_for_task
```

The host may surface the child's pending interaction using the child TaskId.

---

## 38. Capabilities in child tasks

A child may enter:

```text
waiting_for_capability
```

independently.

The parent's lifecycle need not change beyond remaining:

```text
waiting_for_task
```

if it awaits the child.

---

## 39. `start` inside steps

Tasks may be started inside steps.

Example:

```kaj
step fetch {
    let h = start Fetch()
    let result = await h
}
```

If the parent waits, the step remains:

```text
running
```

while the parent is:

```text
waiting_for_task
```

---

## 40. `start` inside functions

Ordinary `fn` may not start tasks.

Invalid:

```kaj
fn helper() -> TaskHandle<Int> {
    return start Child()
}
```

Task composition requires Agentic task runtime state.

---

## 41. `await` inside functions

Ordinary `fn` may not await tasks.

Task handles are Agentic runtime values and are not part of Pure Kaj function behavior in the initial model.

---

## 42. Contracts cannot compose tasks

The following are forbidden inside:

```text
goal
require
invariant
success
```

```text
start
await
```

Contracts remain pure.

---

## 43. Task handle equality

Task handles compare by task identity.

Conceptually:

```text
handle_a == handle_b
```

is true iff they refer to the same TaskId.

If general equality support for TaskHandle is not exposed initially, this behavior may remain runtime-internal.

---

## 44. Task handles are not task definitions

A task declaration identifies reusable task code.

A TaskHandle identifies one execution instance.

These are distinct.

---

## 45. No direct child-result polling syntax

The initial model uses:

```text
await
```

for result synchronization.

Source-level APIs such as:

```text
is_done(handle)
result(handle)
cancel(handle)
```

are deferred unless explicitly needed by the runtime/host API.

---

## 46. Host task inspection

The host may inspect task relationships.

Conceptually:

```text
task_id
parent_task_id
child_task_ids
awaited_task_id
```

These are runtime metadata, not source syntax.

---

## 47. Task tree

Composition creates a task tree.

Example:

```text
Root
├── Child A
│   └── Grandchild A1
└── Child B
```

Initial parent relation is single-parent, so arbitrary DAG composition is not introduced.

---

## 48. No task-handle sharing between unrelated task trees

The initial language model does not provide a general mechanism for one unrelated task to obtain another task's handle.

Handles arise from `start` or restored parent state.

This keeps task authority scoped.

---

## 49. Failure propagation

Freeze:

```text
child completed:
    await returns result

child failed:
    await fails parent

child cancelled:
    await fails parent

parent failed:
    cancel non-terminal descendants

parent cancelled:
    cancel non-terminal descendants

parent completed:
    descendants may continue
```

---

## 50. Summary

Checkpoint 7 freezes:

```text
start Task(args...) -> TaskHandle<T>
TaskHandle<T> refers to one child TaskInstance
await TaskHandle<T> -> T

child tasks have independent:
    TaskId
    lifecycle
    steps
    contracts
    human interactions
    capabilities
    persistence

waiting_for_task is a task lifecycle state

await completed child -> result
await failed child -> parent fails
await cancelled child -> parent fails
Result.err from completed child remains normal value

parent cancellation/failure cancels descendants
parent completion does not cancel descendants

capabilities are not implicitly inherited
child requirements are satisfied independently

TaskHandle is persistable
parent waiting state persists child identity
missing child on restore is an error

fn and contracts cannot use start/await
```
