# Agentic Kaj — Checkpoint 1: Tasks

**Track:** Agentic Kaj  
**Checkpoint:** 1  
**Recommended path:** `dev/plans/agentic/checkpoint-1-tasks.md`  
**Status:** Implementation plan

---

# 1. Goal

Define the fundamental durable execution unit of Agentic Kaj.

This checkpoint answers:

```text
What is a task?
How is task different from fn?
How is a task declared?
How is a task instantiated?
How does a task finish?
What identity does a running task have?
```

This checkpoint introduces the minimum task model required for later Agentic Kaj work.

It does **not** introduce steps, persistence, capabilities, human interaction, planning, or replanning.

The goal is to establish a clean semantic foundation first.

---

# 2. Core Principle

A task is not merely a renamed function.

```text
fn:
    ordinary computation
    no persistent runtime identity
    no lifecycle
    executes as part of the current evaluation
    cannot later suspend/resume

task:
    durable unit of work
    creates a runtime task instance
    has a stable runtime identity
    has lifecycle state
    produces a terminal result
    may later gain steps
    may later suspend/resume
    may later use capabilities
```

For Checkpoint 1, tasks are still executed synchronously to completion by the reference runtime.

Durability in this checkpoint means:

```text
the runtime represents execution as a distinct TaskInstance
with identity and lifecycle
```

It does **not** yet mean the task can survive process restart.

Persistence arrives later.

---

# 3. Task Declaration Syntax

Introduce:

```kaj
task
```

as a reserved keyword.

Basic declaration:

```kaj
task Add(a: Int, b: Int) -> Int {
    return a + b
}
```

A task declaration resembles a function declaration syntactically:

```kaj
task Name(parameter: Type, ...) -> ReturnType {
    body
}
```

Example:

```kaj
task Greet(name: String) -> String {
    return "Hello, {name}"
}
```

Tasks use the same parameter syntax and type syntax as functions.

---

# 4. Task Names

Task names are identifiers.

Example:

```kaj
task ProcessOrder(order_id: String) -> Bool {
    return true
}
```

Task declarations occupy the same **value namespace** as functions and other callable declarations unless the existing compiler architecture strongly favors a separate declaration namespace.

Recommended rule:

```text
fn Foo(...)
task Foo(...)
```

at the same module scope is a duplicate declaration and must be rejected.

Do not permit ambiguous task/function overloading.

---

# 5. Task Placement

For Checkpoint 1:

```text
task declarations are module-level only
```

Do not permit:

```kaj
fn outer() {
    task Inner() {
    }
}
```

Do not permit tasks nested inside tasks.

This matches the current restriction on nested named functions and keeps task identity stable.

---

# 6. Task Parameters

Task parameters follow existing function parameter rules.

Example:

```kaj
task FindUser(
    name: String,
    minimum_age: Int
) -> Bool {
    return minimum_age >= 18
}
```

Parameters:

```text
must have explicit types
are immutable by default
may use existing `var` parameter semantics if functions already support them
follow ordinary Kaj name-resolution and shadowing rules
```

Do not invent task-specific parameter semantics.

---

# 7. Task Return Types

Tasks must declare an explicit return type.

Example:

```kaj
task ComputeTotal(a: Decimal, b: Decimal) -> Decimal {
    return a + b
}
```

No implicit task return-type inference in this checkpoint.

Tasks may return any normal Kaj value type supported by the pure language.

Examples:

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

---

# 8. `None` Tasks

Tasks that do not produce a meaningful value explicitly return `None`.

Example:

```kaj
task Announce(message: String) -> None {
    print(message)
    return none
}
```

Follow existing Kaj `None` semantics.

Do not add a special `void` task form.

---

# 9. Task Body

A task body contains ordinary Kaj statements.

Example:

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

Inside a task, all existing pure Kaj behavior remains authoritative:

```text
let / var
if / else
for / while
break / continue
functions
records
enums
match
Optional / Result
maps
newtypes
imports
```

Checkpoint 1 does not create a separate expression language inside tasks.

---

# 10. Task May Call Functions

A task may call ordinary Kaj functions.

Example:

```kaj
fn double(value: Int) -> Int {
    return value * 2
}

task Compute(value: Int) -> Int {
    return double(value)
}
```

This is valid.

Dependency direction:

```text
task
  ↓
fn
```

is allowed.

This is important because tasks should reuse the pure language rather than duplicate computation logic.

---

# 11. Function May Not Call Task

For Checkpoint 1, ordinary functions may not invoke tasks.

Invalid conceptually:

```kaj
task Fetch() -> Int {
    return 10
}

fn compute() -> Int {
    return Fetch()
}
```

Tasks have runtime identity and lifecycle, while functions are ordinary computation.

Allowing `fn -> task` would cause effectful/durable semantics to leak into the pure function layer.

Freeze:

```text
task may call fn
fn may not call task
```

Task invocation syntax is defined separately below and is not ordinary function-call syntax.

---

# 12. Task May Not Call Task Yet

Task composition is deferred.

For Checkpoint 1:

```text
task -> task invocation is not supported
```

Example conceptually invalid:

```kaj
task Child() -> Int {
    return 1
}

task Parent() -> Int {
    return Child()
}
```

A later Agentic Kaj checkpoint will define:

```text
child task creation
task handles
waiting_for_task
capability inheritance
cancellation propagation
```

Do not guess those semantics now.

---

# 13. Task Recursion

Task recursion is prohibited in Checkpoint 1.

Both direct and indirect recursion between tasks must be rejected if reachable through task invocation once task composition exists.

Since task-to-task invocation is not supported in Checkpoint 1, direct recursion should already be impossible through valid syntax.

Still document the rule:

```text
task recursion is not part of the initial Agentic Kaj model
```

Ordinary function recursion remains unchanged.

---

# 14. How Tasks Are Started

Checkpoint 1 needs an explicit execution boundary.

A task must **not** be invoked using ordinary call syntax inside Kaj.

Instead, the initial reference runtime starts a task from the host/CLI.

Recommended CLI extension:

```bash
kaj task run <file> <TaskName>
```

Example:

```bash
kaj task run playground/tasks.kaj Hello
```

If arguments are not yet supported through the CLI in a clean typed form, Checkpoint 1 may initially restrict CLI-run tasks to zero parameters for end-to-end execution tests.

However, the runtime API itself should support typed task arguments from the start.

Preferred host/runtime API conceptually:

```python
runtime.start_task(
    module=program,
    task_name="Add",
    arguments=[1, 2],
)
```

Do not add awkward ad hoc CLI argument parsing solely for this checkpoint.

---

# 15. Why Task Invocation Is Host-Started Initially

The initial model is:

```text
Host / CLI
    ↓
start task
    ↓
TaskInstance created
    ↓
task body executes
    ↓
terminal result
```

This gives tasks a clear top-level execution boundary without prematurely defining task composition.

Later:

```text
task
  ↓
start child task
```

can be designed separately.

---

# 16. Task Instance

Every execution of a task creates a distinct runtime `TaskInstance`.

Example:

```text
Task definition:
    ComputeTotal

Execution 1:
    task instance A

Execution 2:
    task instance B
```

Even when inputs are identical, the instances are distinct.

Conceptual runtime representation:

```text
TaskInstance
    id
    task_definition
    state
    arguments
    result
    failure
```

Checkpoint 1 does not require persistent storage.

The instance may exist only in memory.

---

# 17. Task Identity

Every running task instance must have a stable identifier for its lifetime.

Recommended representation:

```text
TaskId
```

backed by an opaque runtime-generated identifier.

Example:

```text
task_01K2...
```

or UUID.

The exact textual encoding is not part of Kaj source semantics.

Requirements:

```text
unique within the running runtime
opaque to Kaj source
stable for the lifetime of the TaskInstance
host-readable
available for logs/tests/runtime inspection
```

Kaj programs do not need direct access to their own TaskId in Checkpoint 1.

---

# 18. Task Lifecycle

Introduce the smallest useful lifecycle:

```text
created
running
completed
failed
```

State transitions:

```text
created
   ↓
running
   ├──→ completed
   └──→ failed
```

No:

```text
paused
waiting_for_human
waiting_for_capability
waiting_for_task
cancelled
```

yet.

Those arrive in later checkpoints.

---

# 19. `created`

A TaskInstance begins in:

```text
created
```

after the runtime:

```text
resolves the task definition
validates arguments
creates TaskId
creates TaskInstance
```

Before body execution begins:

```text
created -> running
```

---

# 20. `running`

While the task body is evaluating, state is:

```text
running
```

The body uses the ordinary Kaj interpreter/runtime.

No special scheduler is required yet.

---

# 21. `completed`

If the task body returns a value matching its declared return type, the task becomes:

```text
completed
```

and stores the result.

Example:

```kaj
task Add(a: Int, b: Int) -> Int {
    return a + b
}
```

Runtime:

```text
TaskInstance
state: completed
result: 5
failure: none
```

---

# 22. `failed`

`failed` is reserved for **runtime/task execution failure**, not an ordinary domain-level `Result.err`.

Example:

```kaj
task FindUser(name: String) -> Result<User, FindUserError> {
    return err(not_found)
}
```

This task completed successfully from the runtime's perspective:

```text
state: completed
result: err(not_found)
```

It did **not** enter `failed`.

By contrast, if execution encounters an unrecoverable runtime error:

```text
state: failed
failure: RuntimeError(...)
```

This distinction is critical.

---

# 23. Domain Failure vs Runtime Failure

Freeze:

```text
Result.err(...)
    = normal Kaj value
    = task completed

runtime failure
    = task failed
```

Example:

```kaj
task Divide(a: Decimal, b: Decimal)
    -> Result<Decimal, String>
{
    if b == 0 {
        return err("division by zero")
    }

    return ok(a / b)
}
```

For `b == 0`:

```text
TaskInstance.state = completed
TaskInstance.result = err("division by zero")
```

not:

```text
TaskInstance.state = failed
```

---

# 24. Missing Return

Task missing-return analysis should mirror function analysis.

Example:

```kaj
task Bad(value: Bool) -> Int {
    if value {
        return 1
    }
}
```

must be rejected statically using the existing missing-return machinery or a task-specific equivalent consistent with existing diagnostics.

Do not defer obvious task return errors to runtime.

---

# 25. Return Semantics

Inside a task:

```kaj
return value
```

terminates the entire task body.

Example:

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

`return` does not create a child function-like frame with different semantics.

It terminates the current task execution.

---

# 26. Top-Level Task Declarations Do Not Execute Automatically

Merely declaring:

```kaj
task Hello() -> None {
    print("hello")
    return none
}
```

must not execute it during module initialization.

Task declarations behave like function declarations:

```text
definition exists
execution requires explicit task start
```

This is important for import/module initialization.

---

# 27. Module Semantics

Tasks may be declared in imported modules.

Example:

```kaj
import jobs

// jobs.Process exists as a task declaration
```

However, Checkpoint 1 does not need to support starting imported tasks from Kaj source.

The host/runtime task-start API should be able to resolve a qualified task definition if module resolution already makes that practical.

Example conceptual host lookup:

```text
jobs.Process
```

No automatic execution occurs on import.

---

# 28. Name Resolution

Add task declarations to module-level declaration collection.

Requirements:

```text
task names resolve deterministically
duplicate task names rejected
task/function name collisions rejected
task references cannot be used as arbitrary ordinary values unless explicitly designed
```

Do not implicitly make tasks first-class function values.

---

# 29. Task Type Model

Do not introduce general first-class task function types yet.

For Checkpoint 1, a task declaration is a special callable declaration known to the compiler/runtime.

Avoid inventing:

```text
TaskFn<(A,B),R>
```

unless strictly required internally.

The language can gain first-class task handles/types later.

---

# 30. Static Restrictions on Invocation

Ordinary call syntax:

```kaj
Foo(...)
```

must continue to resolve only ordinary callable constructs valid in pure Kaj.

A task declaration used as an ordinary function call should produce a stable diagnostic.

Suggested:

```text
TASK_CANNOT_CALL_AS_FUNCTION
```

or existing naming convention equivalent.

Example:

```kaj
task Work() -> Int {
    return 1
}

let x = Work()
```

must be rejected.

---

# 31. Runtime Representation

Introduce runtime types conceptually similar to:

```text
TaskDefinition
TaskInstance
TaskState
TaskId
TaskFailure
```

Possible Python representations:

```python
@dataclass(frozen=True)
class TaskDefinition:
    ...

@dataclass
class TaskInstance:
    id: TaskId
    definition: TaskDefinition
    state: TaskState
    arguments: tuple[KajValue, ...]
    result: KajValue | None
    failure: TaskFailure | None
```

The exact class organization is implementation-specific.

Do not expose Python implementation details as Kaj semantics.

---

# 32. Task State Representation

Recommended internal enum:

```text
CREATED
RUNNING
COMPLETED
FAILED
```

State transitions must be validated.

Invalid transitions should not occur silently.

Example:

```text
COMPLETED -> RUNNING
```

is invalid.

A simple runtime invariant is enough in Checkpoint 1.

---

# 33. Task Failure Representation

Task runtime failure should preserve:

```text
stable Kaj runtime diagnostic/error code
message
source span where available
task ID
task name
```

Do not rely on Python exception text as user-facing semantics.

Normal user runtime failures should remain traceback-free through CLI behavior.

---

# 34. AST

Add a task declaration AST node.

Conceptually:

```text
TaskDeclaration
    name
    parameters
    return_type
    body
    span
```

Reuse existing function parameter/type/body nodes where appropriate.

Do not duplicate AST structures unnecessarily.

The distinction between:

```text
FunctionDeclaration
TaskDeclaration
```

must remain explicit.

---

# 35. AST JSON

Extend canonical AST JSON deterministically.

Conceptual form:

```json
{
  "kind": "task_declaration",
  "name": "Add",
  "parameters": [
    ...
  ],
  "return_type": {
    ...
  },
  "body": {
    ...
  },
  "span": {
    ...
  }
}
```

Follow all existing AST JSON rules:

```text
strict fields
deterministic serialization
spans included according to current policy
no runtime task IDs
no lifecycle state
no semantic/type-checker annotations
```

Important:

```text
TaskInstance state is runtime data.
It must NOT appear in source AST JSON.
```

---

# 36. Parser

Add `task` to the lexer keyword set.

Parser should recognize:

```kaj
task Name(...) -> Type {
    ...
}
```

Only at valid module declaration positions.

Diagnostics for malformed declarations should follow normal parser conventions.

Do not add `step`, `goal`, `use`, etc. in this checkpoint.

---

# 37. Formatter

Canonical formatting should mirror functions:

```kaj
task Add(a: Int, b: Int) -> Int {
    return a + b
}
```

Long signatures follow existing multiline formatting rules.

Formatter requirements:

```text
idempotent
parse -> format -> parse preserves semantic AST ignoring spans
no task-specific formatting options
```

---

# 38. Type Checking

Task body type checking should largely reuse function checking.

Validate:

```text
parameter types
return type exists
return expressions assignable to declared type
missing return
ordinary expression typing
ordinary control flow
function calls
```

Do not permit task calls from ordinary call expressions.

---

# 39. Entry / Host Runtime API

Introduce a runtime API capable of:

```text
resolve task definition
validate supplied arguments
create TaskInstance
execute task
return TaskInstance / terminal result
```

Conceptually:

```python
instance = runtime.start_task(
    "Add",
    [1, 2],
)

assert instance.state == COMPLETED
assert instance.result == 3
```

The API should expose the TaskId.

This runtime API is more important than sophisticated CLI syntax in Checkpoint 1.

---

# 40. CLI

Add a minimal task execution command if it fits cleanly with the current CLI architecture.

Recommended:

```bash
kaj task run <file> <TaskName>
```

For Checkpoint 1, it is acceptable to support only zero-argument tasks through the CLI while the runtime API tests parameterized tasks directly.

Example:

```kaj
task Hello() -> None {
    print("Hello from a Kaj task")
    return none
}
```

Run:

```bash
kaj task run hello.kaj Hello
```

Expected stdout:

```text
Hello from a Kaj task
```

Exit behavior should follow current CLI conventions:

```text
0   completed successfully
1   compile error
2   runtime/task execution failure
64  CLI misuse
```

A task that returns `Result.err(...)` still exits `0` if execution itself completed normally unless a later CLI policy explicitly changes this.

Do not conflate domain values with process errors.

---

# 41. CLI Output

Do not automatically print the task's returned value unless explicitly designed.

Recommended initial behavior:

```text
program print() output -> stdout
diagnostics -> stderr
task result available through runtime API
```

If CLI result printing is desired, define it explicitly rather than leaking Python repr.

For the first checkpoint, keeping task return values silent is simplest and matches `kaj run` program semantics.

---

# 42. Diagnostics

Introduce stable task-specific diagnostics where existing diagnostics are insufficient.

Recommended inventory:

```text
TASK_DUPLICATE_NAME
TASK_CANNOT_CALL_AS_FUNCTION
TASK_NOT_FOUND
TASK_ARGUMENT_COUNT_MISMATCH
TASK_ARGUMENT_TYPE_MISMATCH
TASK_INVALID_STATE_TRANSITION
```

Some may reuse existing general diagnostics if those codes already precisely cover the case.

Prefer reuse over redundant codes.

Do not invent task-specific codes merely to rename an existing exact semantic error.

---

# 43. Pure Language Compatibility

All existing pure-language behavior must remain unchanged.

Specifically:

```text
kaj check
kaj run
kaj fmt
kaj ast
```

for ordinary pure Kaj programs must behave exactly as before.

Adding `task` must not destabilize:

```text
functions
module initialization
formatter
AST JSON
name resolution
type checking
interpreter behavior
CLI exit codes
```

except where `task` is now a reserved keyword.

---

# 44. Reserved Keyword Compatibility

Because `task` becomes a keyword, source such as:

```kaj
let task = 10
```

will no longer be valid if keywords cannot be used as identifiers.

Document this as the expected language change.

Do not silently permit context-sensitive keyword behavior unless the lexer/parser architecture already uses it.

---

# 45. Tests — Lexer

Add tests for:

```text
task recognized as keyword
task cannot be used where ordinary identifier is required
source spans correct
```

---

# 46. Tests — Parser

Valid:

```kaj
task Hello() -> None {
    return none
}
```

```kaj
task Add(a: Int, b: Int) -> Int {
    return a + b
}
```

Invalid:

```text
missing task name
missing parameter list
missing return type
missing body
nested task declaration
```

---

# 47. Tests — AST / AST JSON

Verify:

```text
TaskDeclaration node shape
parameter preservation
return type preservation
body preservation
spans
deterministic JSON
round-trip expectations where applicable
no runtime fields serialized
```

---

# 48. Tests — Resolution

Cover:

```text
task name registered
duplicate task rejected
task/function collision rejected
task body resolves parameters
task body resolves module-level functions
task body respects lexical scopes
```

---

# 49. Tests — Type Checking

Cover:

```text
valid return
wrong return type
missing return
task calling function
function attempting task call
ordinary call expression targeting task rejected
records/enums/Optional/Result/newtypes as task returns
```

---

# 50. Tests — Runtime

Cover:

```text
TaskInstance created
TaskId assigned
initial state created
created -> running
running -> completed
result stored
runtime failure -> failed
failure stored
two executions create different TaskIds
same task definition can create multiple instances
```

---

# 51. Tests — Domain Result vs Runtime Failure

Explicitly test:

```kaj
task ExpectedFailure() -> Result<Int, String> {
    return err("not found")
}
```

Required runtime outcome:

```text
state == completed
result == err("not found")
failure == none
```

This distinction must be locked down early.

---

# 52. Tests — Module Behavior

Verify:

```text
task declarations do not execute during module initialization
importing a module containing tasks is side-effect free except ordinary top-level code
task names remain qualified according to existing module rules
```

---

# 53. Tests — Formatter

Verify:

```text
canonical spacing
multiline task signatures
task body indentation
idempotence
semantic AST preservation
```

---

# 54. Tests — CLI

If `kaj task run` is implemented:

```text
valid zero-argument task
unknown task
compile failure
runtime failure
CLI misuse
stdout/stderr separation
exit codes
no traceback
```

---

# 55. Example Program

Add a simple dogfood example such as:

```text
examples/agentic/task-basics.kaj
```

Example:

```kaj
fn double(value: Int) -> Int {
    return value * 2
}

task Compute() -> Int {
    let value = double(21)
    print(value)
    return value
}
```

Running:

```bash
kaj task run examples/agentic/task-basics.kaj Compute
```

should print:

```text
42
```

and the runtime TaskInstance should finish as:

```text
completed
```

with result:

```text
42
```

---

# 56. Out of Scope

Do not implement any of the following in Checkpoint 1:

```text
step
named steps
task persistence
resume
pause
waiting states
human interaction
ask
choose
confirm
inform
handoff
capability declarations
use
host capability adapters
task-to-task composition
TaskHandle
start/await syntax
LLM planner
planner context
plan blocks
AST patches
replanning
task retries
distributed execution
database-backed task storage
browser-specific integration
filesystem-specific integration
robot-specific integration
```

If implementation pressure suggests one of these is required, stop and document the dependency rather than silently adding semantics.

---

# 57. Definition of Done

Checkpoint 1 is complete when:

```text
[ ] `task` is a reserved Kaj keyword

[ ] module-level task declarations parse
[ ] task parameters use existing typed parameter semantics
[ ] task return type is explicit
[ ] task body uses ordinary Kaj statements

[ ] task declarations have explicit AST representation
[ ] AST JSON serializes task declarations deterministically
[ ] runtime task state does not leak into AST JSON
[ ] formatter formats tasks canonically

[ ] task body name resolution works
[ ] task body type checking works
[ ] missing-return checking works

[ ] task may call fn
[ ] fn may not call task
[ ] task may not call task yet
[ ] ordinary function-call syntax cannot invoke a task
[ ] task recursion is not introduced

[ ] TaskDefinition runtime representation exists
[ ] TaskInstance runtime representation exists
[ ] every TaskInstance has opaque TaskId
[ ] two executions receive distinct TaskIds

[ ] lifecycle supports created
[ ] lifecycle supports running
[ ] lifecycle supports completed
[ ] lifecycle supports failed
[ ] state transitions are deterministic

[ ] normal return stores result and completes task
[ ] Result.err is treated as a normal completed result
[ ] runtime failure marks task failed
[ ] runtime failure is distinct from domain-level Result.err

[ ] task declarations do not execute automatically

[ ] host/runtime API can start a task by definition/name
[ ] typed task arguments are validated by runtime/compiler boundary

[ ] minimal CLI task execution exists if cleanly implementable
[ ] existing pure Kaj CLI behavior remains unchanged

[ ] lexer tests pass
[ ] parser tests pass
[ ] AST tests pass
[ ] AST JSON tests pass
[ ] resolver tests pass
[ ] type-checker tests pass
[ ] formatter tests pass
[ ] runtime tests pass
[ ] module tests pass
[ ] CLI tests pass if CLI task command is included

[ ] full pure-language regression suite remains green
[ ] mkdocs build --strict remains green after any doc updates
```

---

# 58. Public Documentation After Implementation

Once semantics are implemented and frozen, create/update stable user-facing documentation.

Recommended:

```text
docs/agentic/tasks.md
```

That document should explain only public semantics:

```text
what a task is
task syntax
task parameters
return type
task vs fn
task completion
domain failure vs runtime failure
how a host starts a task
```

Do not put this checkpoint's:

```text
Definition of Done
test matrix
implementation sequence
suggested internal classes
Codex instructions
```

into public docs.

Those belong only here under `dev/plans/agentic/`.

---

# 59. Suggested Implementation Order

Implement in this order:

```text
1. lexer keyword
2. AST TaskDeclaration
3. parser
4. AST JSON
5. formatter
6. declaration collection / name resolution
7. type checking
8. task-call restrictions
9. runtime TaskDefinition
10. TaskId / TaskState / TaskInstance
11. runtime start_task API
12. task execution wrapper
13. runtime failure handling
14. CLI command if clean
15. examples
16. tests
17. docs
18. full regression + mkdocs strict
```

Keep the checkpoint focused.

---

# 60. Completion Report Format

When implementation is complete, report:

```text
Agentic Kaj Checkpoint 1 — Tasks

Status:
COMPLETE / INCOMPLETE

Files changed:
- ...

Syntax:
- task keyword: PASS/FAIL
- task declarations: PASS/FAIL
- formatter: PASS/FAIL
- AST JSON: PASS/FAIL

Semantics:
- task -> fn: PASS/FAIL
- fn -> task rejected: PASS/FAIL
- task -> task rejected/deferred: PASS/FAIL
- return checking: PASS/FAIL

Runtime:
- TaskDefinition: PASS/FAIL
- TaskInstance: PASS/FAIL
- TaskId: PASS/FAIL
- created: PASS/FAIL
- running: PASS/FAIL
- completed: PASS/FAIL
- failed: PASS/FAIL
- Result.err completes normally: PASS/FAIL

CLI:
- task execution command: PASS/FAIL/DEFERRED
- exit codes: PASS/FAIL
- stdout/stderr: PASS/FAIL

Regression:
- pure Kaj tests: PASS/FAIL
- new agentic tests: PASS/FAIL
- mkdocs build --strict: PASS/FAIL

Deferred intentionally:
- steps
- human interaction
- persistence
- capabilities
- task composition
- planner
- replanning

Known issues:
- ...
```

---

# 61. Codex / AI Implementation Instruction

Give the implementation agent the following prompt:

```text
Implement Agentic Kaj Checkpoint 1 from:

dev/plans/agentic/checkpoint-1-tasks.md

Treat the checkpoint plan as the implementation contract.

Important constraints:

1. Agentic Kaj builds on the completed Pure Kaj language. Do not weaken,
   redesign, or regress existing pure-language semantics.

2. Implement only Checkpoint 1: Tasks.

3. Add:
   - `task` keyword
   - module-level task declarations
   - typed parameters
   - explicit return types
   - TaskDeclaration AST support
   - deterministic AST JSON support
   - canonical formatter support
   - name resolution
   - task body type checking
   - task/function invocation restrictions
   - TaskDefinition runtime representation
   - TaskInstance runtime representation
   - opaque TaskId
   - lifecycle states: created, running, completed, failed
   - runtime task-start API
   - correct task completion/failure behavior
   - tests
   - minimal public task documentation after implementation

4. Freeze these rules:
   - a task may call ordinary `fn`
   - an ordinary `fn` may not call/start a task
   - a task may not start another task yet
   - task recursion is not supported
   - ordinary function call syntax must not invoke tasks
   - task declarations do not execute automatically
   - every execution creates a distinct TaskInstance and TaskId
   - `Result.err(...)` is a normal returned Kaj value and therefore
     completes the task; it is NOT a runtime task failure
   - unrecoverable runtime errors transition the TaskInstance to `failed`

5. For this checkpoint, tasks execute synchronously to completion.
   Do not implement persistence or suspension yet.

6. If clean within the existing CLI architecture, add:

       kaj task run <file> <TaskName>

   It is acceptable for the first CLI implementation to support only
   zero-argument tasks while the runtime API supports typed arguments.
   Do not create awkward ad hoc CLI argument parsing merely to support
   parameterized tasks.

7. Do NOT implement:
   - step
   - lifecycle waiting states
   - persistence/resume
   - ask/choose/confirm/inform/handoff
   - capabilities/use
   - browser integration
   - task-to-task composition
   - TaskHandle/start/await
   - planner/LLM integration
   - plan blocks
   - AST patches
   - replanning
   - retry syntax
   - distributed execution

8. Reuse existing Pure Kaj compiler machinery wherever possible:
   parser structures, parameter nodes, return analysis, resolver,
   type checker, formatter, diagnostics, module loading, interpreter,
   AST JSON conventions, and CLI error conventions.

9. Do not put checkpoint implementation checklists or Definition of Done
   material into public docs. Public docs should contain only stable
   implemented task semantics.

10. Preserve all existing CLI behavior:

       kaj check
       kaj run
       kaj fmt
       kaj ast
       kaj --version

11. Run the complete existing test suite plus the new Agentic Kaj task
    tests.

12. Run:

       mkdocs build --strict

    after documentation changes.

13. When finished, provide the completion report in the exact format
    specified at the end of the checkpoint plan, including files changed,
    PASS/FAIL results, deferred items, and known issues.

Do not continue into Agentic Checkpoint 2.
Stop after Checkpoint 1 is fully implemented and verified.
```
