# Tasks

Tasks are Agentic Kaj's durable unit of work.

A task is distinct from an ordinary function. Functions perform ordinary computation. Tasks represent work that has its own runtime identity and lifecycle and may gain suspension, persistence, human interaction, capabilities, and planning semantics in later Agentic Kaj features.

This document defines the initial task semantics introduced by Agentic Kaj.

---

## 1. Task declarations

A task is declared with the `task` keyword.

```kaj
task Add(a: Int, b: Int) -> Int {
    return a + b
}
```

The general form is:

```kaj
task Name(parameter: Type, ...) -> ReturnType {
    body
}
```

Task parameters and return types are explicit.

Task bodies use ordinary Kaj statements and expressions.

---

## 2. Tasks and functions

Tasks and functions serve different purposes.

A function:

```kaj
fn double(value: Int) -> Int {
    return value * 2
}
```

represents ordinary computation.

A task:

```kaj
task Compute(value: Int) -> Int {
    return double(value)
}
```

represents a distinct unit of work managed by the Agentic Kaj runtime.

The initial distinction is:

```text
fn
- ordinary computation
- no task identity
- no task lifecycle
- executes as part of the current Kaj evaluation

task
- distinct runtime task instance
- stable task identity while running
- task lifecycle
- terminal task result or runtime failure
```

Later Agentic Kaj features may allow tasks to suspend, resume, interact with humans, use capabilities, and participate in planning. Those behaviors are not implied merely by declaring a task.

---

## 3. Placement

Task declarations are module-level declarations.

Valid:

```kaj
task Hello() -> None {
    print("hello")
    return none
}
```

Task declarations may not be nested inside functions or other tasks.

Invalid:

```kaj
fn outer() -> None {
    task Inner() -> None {
        return none
    }

    return none
}
```

Task declarations in imported modules are definitions only. Importing a module does not automatically start its tasks.

---

## 4. Task names

Task names use normal Kaj identifiers.

```kaj
task ProcessOrder(order_id: String) -> Bool {
    return true
}
```

Task names share the module-level callable/declaration namespace with ordinary functions.

A module may not declare a function and a task with the same name.

Invalid:

```kaj
fn Work() -> Int {
    return 1
}

task Work() -> Int {
    return 2
}
```

Kaj does not provide task/function overloading.

---

## 5. Parameters

Task parameters use the same explicit typing rules as function parameters.

```kaj
task Greet(name: String, repeat: Int) -> String {
    return "Hello, {name}"
}
```

Parameters are immutable by default.

If Kaj's existing `var` parameter form is used, it has the same meaning inside tasks as inside functions: the local parameter binding may be rebound, but it does not create pass-by-reference semantics.

Task parameters participate in ordinary lexical scope and type checking.

---

## 6. Return types

Every task declares an explicit return type.

```kaj
task Total(a: Decimal, b: Decimal) -> Decimal {
    return a + b
}
```

Tasks may return any ordinary Kaj value type, including:

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

There is no special task-only return type in the initial task model.

---

## 7. Tasks returning `None`

A task with no meaningful result uses the ordinary Kaj `None` type.

```kaj
task Announce(message: String) -> None {
    print(message)
    return none
}
```

Kaj does not introduce a separate `void` task type.

---

## 8. Task bodies

A task body is ordinary Kaj code.

For example:

```kaj
task SumPositive(values: List<Int>) -> Int {
    var total = 0

    for value in values {
        if value > 0 {
            total = total + value
        }
    }

    return total
}
```

Existing pure Kaj semantics remain authoritative inside tasks.

This includes:

```text
let and var
if and else
for and while
break and continue
functions
records
enums
match
Optional
Result
lists
maps
newtypes
imports
string interpolation
explicit conversion
```

Task bodies do not use a separate expression or statement language.

---

## 9. Tasks may call functions

A task may call ordinary Kaj functions.

```kaj
fn double(value: Int) -> Int {
    return value * 2
}

task Compute(value: Int) -> Int {
    return double(value)
}
```

This is valid.

Functions remain the normal mechanism for reusable computation inside tasks.

---

## 10. Functions may not invoke tasks

Ordinary functions may not start or invoke tasks.

A task has runtime identity and lifecycle semantics that ordinary function evaluation does not have.

A task declaration therefore cannot be used as though it were a normal function.

Invalid:

```kaj
task Fetch() -> Int {
    return 10
}

fn compute() -> Int {
    return Fetch()
}
```

The task call is invalid.

Task execution must occur through the Agentic Kaj task-start mechanism.

---

## 11. Tasks may not invoke other tasks yet

The initial task model does not define task-to-task composition.

This means one task cannot start another task.

Conceptually invalid:

```kaj
task Child() -> Int {
    return 1
}

task Parent() -> Int {
    return Child()
}
```

A later Agentic Kaj feature defines child-task creation, task handles, waiting, cancellation propagation, and related composition semantics.

---

## 12. Task recursion

Task recursion is not supported in the initial task model.

Ordinary function recursion remains supported according to Pure Kaj semantics.

Task recursion may be reconsidered only after task composition semantics are defined.

---

## 13. Task execution

Declaring a task does not execute it.

```kaj
task Hello() -> None {
    print("hello")
    return none
}
```

Loading or importing the module only defines `Hello`.

A host or Agentic Kaj runtime must explicitly start the task.

Conceptually:

```text
host
  ↓
start Hello
  ↓
TaskInstance created
  ↓
task body executes
```

Task start is distinct from ordinary function-call syntax.

---

## 14. Task instances

Each execution of a task creates a distinct runtime task instance.

For example, two starts of:

```kaj
task Compute(value: Int) -> Int {
    return value * 2
}
```

produce two different task instances even if their arguments are equal.

Conceptually:

```text
Task definition: Compute

start Compute(5)
    → TaskInstance A

start Compute(5)
    → TaskInstance B
```

Task instances are runtime entities. They are not source declarations.

---

## 15. Task identity

Each task instance has an opaque runtime identity.

Conceptually:

```text
TaskId
```

A `TaskId` is:

```text
unique within the runtime
stable for the lifetime of the task instance
opaque to Kaj source
available to the host/runtime for tracking and inspection
```

The exact textual representation of a task ID is not part of Kaj source semantics.

Task IDs do not appear in source AST JSON.

---

## 16. Task lifecycle

Agentic Checkpoint 2 expands the task lifecycle to seven states:

```text
created
ready
running
paused
completed
failed
cancelled
```

Normal execution follows:

```text
created
   ↓
ready
   ↓
running
   ├──→ completed
   └──→ failed
```

At safe boundaries between named steps, a host may pause and later resume a running task. A host
may also cancel a non-terminal task. Completed, failed, and cancelled tasks are terminal.

See [Steps and Task Lifecycle](kaj-agentic-steps-and-lifecycle-spec.md) for the complete transition
table and cooperative pause/cancellation semantics.

---

## 17. `created`

A newly instantiated task begins in `created`.

At this point the runtime has:

```text
resolved the task declaration
validated the supplied arguments
created a task identity
created a TaskInstance
```

The task body has not yet begun executing.

After validation, the task transitions to `ready`. Before evaluation begins, it transitions to
`running`.

---

## 18. `running`

A task is `running` while its body is executing.

The Agentic Kaj runtime executes task statements synchronously. Cooperative pause and cancellation
take effect at safe boundaries between named steps. Paused execution is retained only in memory;
there is no persistence across process restart.

---

## 19. `completed`

A task enters `completed` when its body returns a valid value matching its declared return type.

```kaj
task Add(a: Int, b: Int) -> Int {
    return a + b
}
```

A successful execution may conceptually have:

```text
state: completed
result: 5
```

The returned value is an ordinary Kaj value.

---

## 20. `failed`

A task enters `failed` when execution encounters an unrecoverable runtime failure.

A runtime failure is distinct from returning a normal Kaj value that represents a domain-level failure.

Conceptually:

```text
state: failed
failure: RuntimeFailure(...)
```

The runtime should report Kaj-defined diagnostics rather than exposing host-language exception behavior as task semantics.

---

## 21. Domain failure is not task failure

A `Result.err(...)` value is a normal Kaj value.

For example:

```kaj
task FindUser(name: String) -> Result<User, String> {
    return err("not found")
}
```

If this executes normally, the task is:

```text
completed
```

with:

```text
result = err("not found")
```

It is not:

```text
failed
```

This distinction is fundamental.

```text
Result.err(...)
    = expected/domain-level outcome

task failed
    = runtime execution failure
```

Programs should use `Result` when failure is part of the task's expected domain model.

---

## 22. Return semantics

`return` inside a task terminates the task body.

```kaj
task FirstPositive(values: List<Int>) -> Optional<Int> {
    for value in values {
        if value > 0 {
            return some(value)
        }
    }

    return none
}
```

The returned value must be assignable to the declared task return type under ordinary Kaj typing rules.

---

## 23. Missing returns

Tasks are subject to the same definite-return requirements as functions.

Invalid:

```kaj
task Choose(value: Bool) -> Int {
    if value {
        return 1
    }
}
```

Because the task promises to return `Int`, all reachable completion paths must satisfy Kaj's return rules.

An exhaustive `match` whose branches all return may satisfy the same return analysis used for functions.

---

## 24. Ordinary call syntax does not start tasks

Task declarations are not ordinary function values.

Given:

```kaj
task Work() -> Int {
    return 1
}
```

this is invalid:

```kaj
let x = Work()
```

Ordinary call syntax remains reserved for callable constructs defined by Pure Kaj.

Starting a task occurs through the Agentic Kaj runtime boundary.

---

## 25. Host-started execution

The initial task model is host-started.

Conceptually:

```text
Host or CLI
    ↓
resolve task declaration
    ↓
validate typed arguments
    ↓
create TaskInstance
    ↓
created
    ↓
running
    ↓
completed / failed
```

The host may inspect:

```text
task ID
task name
lifecycle state
result
runtime failure
```

Host implementation details are not exposed as Kaj values unless a later language feature explicitly does so.

---

## 26. Synchronous initial execution

In the initial task model, task execution is synchronous from the runtime's perspective.

Once started, a task runs until it:

```text
returns normally
or
encounters a runtime failure
```

There is no:

```text
suspension
resume
waiting
persistence
child task
planner intervention
```

yet.

The existence of task identity and lifecycle is intentionally established before those features are added.

---

## 27. Modules and imports

Tasks may be declared in modules.

Example:

```kaj
// jobs.kaj

task Cleanup() -> None {
    print("cleaning")
    return none
}
```

Another module may import `jobs` according to normal module rules.

Importing `jobs` does not start `jobs.Cleanup`.

Task declarations follow normal module qualification rules.

Task execution must still be explicitly requested by the host/runtime.

---

## 28. Type checking

Task bodies use normal Kaj static typing.

The compiler checks:

```text
parameter types
declared return type
return expressions
name resolution
control flow
function calls
record construction
enum construction
Optional and Result usage
collection operations
module references
```

A task body does not bypass or weaken Pure Kaj type checking.

---

## 29. Task declaration identity versus task instance identity

A task declaration and a task instance are different concepts.

```text
Task declaration
    source-level definition
    e.g. `task Compute(...)`

Task instance
    one runtime execution of that declaration
    has TaskId and lifecycle state
```

Many task instances may originate from one task declaration.

---

## 30. Runtime state is not source syntax

Task lifecycle information is runtime data.

For example:

```text
task ID
created/running/completed/failed
runtime result
runtime failure
```

must not be serialized as though it were part of the source task declaration.

AST JSON represents the declaration:

```text
task name
parameters
return type
body
source spans
```

It does not represent a running task instance.

---

## 31. Relationship to future Agentic Kaj features

The initial task model is deliberately minimal.

Future Agentic Kaj features build on it.

Conceptually:

```text
task
  ↓
steps and lifecycle expansion
  ↓
task contracts
  ↓
human interaction
  ↓
persistence and resume
  ↓
capabilities
  ↓
task composition
  ↓
planner
  ↓
controlled replanning
```

Those features extend the task runtime without changing the basic meaning of a task as a distinct durable unit of work.

---

## 32. Summary

The initial Agentic Kaj task model freezes these rules:

```text
task is a module-level declaration

task parameters are explicitly typed
task return type is explicit
task body uses ordinary Kaj

task may call fn
fn may not invoke task
task may not invoke task yet
task recursion is not supported yet

task declaration does not execute automatically
task execution is explicitly started by a host/runtime

every execution creates a distinct TaskInstance
every TaskInstance has an opaque TaskId

initial lifecycle:
    created
    running
    completed
    failed

normal return:
    completed + result

Result.err(...):
    completed + err value

runtime execution failure:
    failed

initial tasks run synchronously
persistence/suspension are added later
```
