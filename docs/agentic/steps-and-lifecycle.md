# Steps and Task Lifecycle

Steps are durable execution boundaries inside Agentic Kaj tasks.

This document defines the initial semantics for steps and the expanded task lifecycle.

---

## 1. Step declarations

A step is declared inside a task.

```kaj
task Example() -> None {
    step prepare {
        print("prepare")
    }

    step finish {
        print("finish")
    }

    return none
}
```

The initial form is:

```kaj
step Name {
    body
}
```

Step names are required in the initial model.

---

## 2. Why steps exist

A step is not a function.

A function is a reusable unit of computation.

A step is a runtime execution boundary used for:

```text
task progress
observability
lifecycle tracking
future persistence
future resume
future replanning
```

A step may contain ordinary Kaj statements and function calls.

---

## 3. Placement

Steps may appear only directly inside task bodies.

Valid:

```kaj
task Work() -> None {
    step first {
        print("one")
    }

    return none
}
```

Invalid:

```kaj
fn helper() -> None {
    step first {
        print("one")
    }

    return none
}
```

Invalid:

```kaj
task Work() -> None {
    if true {
        step first {
            print("one")
        }
    }

    return none
}
```

Steps are part of the task's top-level execution structure, not arbitrary nested statements.

---

## 4. Step names

Step names are identifiers.

Within one task, step names must be unique.

Invalid:

```kaj
task Work() -> None {
    step prepare {
    }

    step prepare {
    }

    return none
}
```

Step names are local to the containing task.

Two different tasks may use the same step name.

---

## 5. Step body

A step body uses ordinary Kaj statements.

```kaj
task Compute(values: List<Int>) -> Int {
    var total = 0

    step calculate {
        for value in values {
            total = total + value
        }
    }

    return total
}
```

Inside a step, ordinary Kaj semantics apply.

This includes:

```text
let / var
if / else
for / while
break / continue
function calls
match
records
enums
Optional
Result
lists
maps
newtypes
```

---

## 6. Step scope

A step creates a lexical block scope.

Bindings declared inside the step do not escape the step.

```kaj
task Example() -> None {
    step prepare {
        let message = "hello"
        print(message)
    }

    return none
}
```

`message` is not visible after `prepare`.

Bindings declared before the step remain visible inside it.

```kaj
task Example(name: String) -> None {
    step greet {
        print(name)
    }

    return none
}
```

---

## 7. Mutation across steps

A task-local `var` declared outside steps may be mutated by steps.

```kaj
task Counter() -> Int {
    var count = 0

    step first {
        count = count + 1
    }

    step second {
        count = count + 1
    }

    return count
}
```

This returns `2`.

This rule is important for later persistence semantics.

---

## 8. `return` inside a step

`return` inside a step exits the entire task.

```kaj
task Find(values: List<Int>) -> Optional<Int> {
    step search {
        for value in values {
            if value > 10 {
                return some(value)
            }
        }
    }

    return none
}
```

There is no separate "return from step" operation.

---

## 9. `break` and `continue`

`break` and `continue` retain normal Pure Kaj loop semantics inside steps.

They affect the nearest enclosing loop.

They do not affect step execution outside that loop.

---

## 10. Step execution order

Steps execute in source order.

```kaj
step first { ... }
step second { ... }
step third { ... }
```

executes as:

```text
first
second
third
```

unless the task returns or fails before reaching a later step.

There is no implicit parallelism.

---

## 11. Step runtime state

Each step execution has runtime state.

Initial states:

```text
pending
running
completed
failed
```

Normal transition:

```text
pending
   ↓
running
   ├──→ completed
   └──→ failed
```

A step that is never reached remains `pending`.

---

## 12. Step completion

A step becomes `completed` when its body finishes normally.

Example:

```kaj
step prepare {
    print("ready")
}
```

After the body completes:

```text
prepare = completed
```

Execution then continues to the next statement in the task.

---

## 13. Step failure

A step becomes `failed` if an unrecoverable runtime failure occurs while evaluating its body.

When a step fails, the containing task also fails.

Conceptually:

```text
step running
   ↓
step failed
   ↓
task failed
```

A returned `Result.err(...)` value is not a step failure unless ordinary Kaj code explicitly causes the task to return that value.

---

## 14. Task lifecycle

Agentic tasks use this lifecycle:

```text
created
ready
running
paused
completed
failed
cancelled
```

The initial runtime need not support persistence yet, but these states are now part of the Agentic Kaj task model.

---

## 15. `created`

A task instance is `created` immediately after instantiation.

---

## 16. `ready`

A task becomes `ready` once its definition and inputs are validated and it can begin execution.

Normal startup:

```text
created
   ↓
ready
   ↓
running
```

---

## 17. `running`

A task is `running` while ordinary statements or a step body are executing.

---

## 18. `paused`

A host may pause a running task at a safe runtime boundary.

The initial safe boundary is between steps.

A paused task does not continue executing until resumed by the host.

Durable behavior across process restart is defined by
[Persistence and Resume](persistence-resume.md).

---

## 19. `completed`

A task becomes `completed` after returning a valid result.

---

## 20. `failed`

A task becomes `failed` after an unrecoverable runtime failure.

Domain-level `Result.err(...)` remains a normal completed result.

---

## 21. `cancelled`

A host may cancel a non-terminal task.

After cancellation:

```text
state = cancelled
```

The task must not continue executing.

Cancellation is distinct from failure.

---

## 22. Terminal states

These states are terminal:

```text
completed
failed
cancelled
```

A terminal task does not return to:

```text
ready
running
paused
```

---

## 23. Initial valid lifecycle transitions

The initial allowed transitions are:

```text
created -> ready
ready -> running
running -> completed
running -> failed
running -> paused
paused -> running
created -> cancelled
ready -> cancelled
running -> cancelled
paused -> cancelled
```

No other transition is valid.

---

## 24. Step execution records

A task instance tracks the runtime state of its named steps.

Conceptually:

```text
TaskInstance
    task_id
    state
    steps:
        prepare -> completed
        search  -> running
        finish  -> pending
```

This execution record is runtime state, not source AST.

---

## 25. Completed steps are recorded

Once a step completes, the runtime records it as completed for the lifetime of the TaskInstance.

Persistence and resume semantics use these completion records to avoid replaying
committed steps.

---

## 26. Pausing

Pausing is cooperative.

The host may request pause while a task is running.

The initial runtime applies the pause at the next safe boundary between steps.

It does not interrupt arbitrary Pure Kaj expression evaluation mid-operation.

---

## 27. Cancellation

Cancellation is also cooperative unless the host can safely terminate execution.

The runtime must prevent execution of future steps after cancellation is accepted.

The exact external cancellation API is host/runtime-specific.

---

## 28. No automatic retry

Failed steps do not automatically retry.

There is no retry syntax in Agentic Kaj Conformance 1.

Retry semantics may be introduced later.

---

## 29. No step jumping

Kaj source cannot arbitrarily jump to another step.

There is no:

```text
goto step
resume step
skip step
```

syntax.

Normal task control flow determines which steps are reached.

---

## 30. Steps are not callable values

A step cannot be called like a function.

Invalid conceptually:

```kaj
prepare()
```

Step names identify runtime boundaries inside their containing task.

They are not first-class values.

---

## 31. Steps and loops

A loop may exist inside a step.

A step may not be declared inside a loop.

Valid:

```kaj
step process {
    for item in items {
        print(item)
    }
}
```

Invalid:

```kaj
for item in items {
    step process {
        print(item)
    }
}
```

---

## 32. Steps and conditionals

Conditionals may exist inside steps.

A step may not be declared inside a conditional.

Steps belong to the task's top-level structure.

---

## 33. AST distinction

A step is a source-level construct and therefore appears in the task AST.

Step runtime state does not appear in source AST JSON.

AST represents:

```text
step name
step body
source span
```

Runtime represents:

```text
pending
running
completed
failed
```

---

## 34. Relationship to persistence

The lifecycle records enough runtime structure for durable persistence.

The reference runtime persists:

```text
current task state
current step
completed steps
task-local values
pending interaction
```

Serialization and crash recovery are defined by [Persistence and Resume](persistence-resume.md).

---

## 35. Summary

The initial step and lifecycle model freezes:

```text
steps are named
steps appear only directly inside tasks
step names are unique per task
steps create lexical block scope
steps execute in source order
steps may contain ordinary Kaj
return inside step exits the task
outer task vars may be mutated across steps

step states:
    pending
    running
    completed
    failed

task states:
    created
    ready
    running
    paused
    completed
    failed
    cancelled

pause occurs at safe boundaries between steps
cancelled is terminal
completed/failed/cancelled are terminal
no automatic retry
no persistence yet
no human waits yet
no capabilities yet
```
