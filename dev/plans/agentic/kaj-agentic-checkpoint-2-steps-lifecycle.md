# Agentic Kaj — Checkpoint 2: Steps and Task Lifecycle

**Track:** Agentic Kaj  
**Checkpoint:** 2  
**Recommended path:** `dev/plans/agentic/checkpoint-2-steps-lifecycle.md`

---

# Goal

Implement named task steps and expand the task runtime lifecycle.

Authoritative semantics:

```text
docs/agentic/steps-and-lifecycle.md
```

This checkpoint builds on Agentic Checkpoint 1.

---

# Scope

Implement:

```text
step keyword
named step syntax
top-level-in-task placement rules
step lexical scope
step execution order
step runtime records
step states
expanded task lifecycle
pause
resume from pause
cancellation
runtime inspection
AST / AST JSON
formatter
diagnostics
tests
docs integration
```

Do not implement persistence across process restart.

---

# Frozen Syntax

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

Step names are required.

Steps may appear only directly inside task bodies.

---

# Frozen Step Semantics

```text
step creates lexical block scope
outer task bindings visible inside step
outer task `var` may be mutated inside step
step-local bindings do not escape
return inside step exits task
break/continue retain nearest-loop meaning
steps execute in source order
no automatic retry
no step jumping
steps are not callable values
```

Step declarations inside functions, loops, conditionals, matches, or nested blocks are invalid.

---

# Step Runtime States

Implement:

```text
PENDING
RUNNING
COMPLETED
FAILED
```

Normal:

```text
PENDING -> RUNNING -> COMPLETED
PENDING -> RUNNING -> FAILED
```

A runtime failure in a step marks both:

```text
step = FAILED
task = FAILED
```

---

# Expanded Task Lifecycle

Replace/extend the initial lifecycle with:

```text
CREATED
READY
RUNNING
PAUSED
COMPLETED
FAILED
CANCELLED
```

Allowed transitions:

```text
CREATED -> READY
READY -> RUNNING

RUNNING -> COMPLETED
RUNNING -> FAILED
RUNNING -> PAUSED
PAUSED -> RUNNING

CREATED -> CANCELLED
READY -> CANCELLED
RUNNING -> CANCELLED
PAUSED -> CANCELLED
```

Terminal:

```text
COMPLETED
FAILED
CANCELLED
```

Reject invalid state transitions.

---

# Pause Semantics

Pause is host-requested and cooperative.

For Checkpoint 2:

```text
pause takes effect at a safe boundary between steps
```

Do not interrupt arbitrary expression evaluation.

A paused task resumes at the next not-yet-executed statement/step according to the runtime's existing execution representation.

If the current implementation cannot safely preserve arbitrary non-step statement position, constrain task execution so pause requests are honored immediately after a step completes and before the next top-level task statement begins.

Do not invent persistence to disk.

---

# Cancellation

Add a host/runtime cancellation operation.

Cancellation:

```text
is distinct from failure
is terminal
prevents future task execution
```

If cancellation is requested during a step, apply it at the next safe boundary unless the runtime already has a safe cancellation mechanism.

---

# Runtime Representation

Add or extend concepts such as:

```text
StepDefinition
StepExecution
StepState
TaskInstance.step_executions
```

Suggested conceptual representation:

```text
TaskInstance
    id
    definition
    state
    arguments
    result
    failure
    step_executions
    pause_requested
    cancel_requested
```

Implementation details are flexible.

Do not expose Python-specific structures as language semantics.

---

# AST

Add a step node conceptually:

```text
StepStatement
    name
    body
    span
```

or equivalent appropriate to the current AST hierarchy.

Steps are source constructs.

Task/step runtime state is not part of AST.

---

# AST JSON

Serialize step source structure deterministically.

Conceptually:

```json
{
  "kind": "step_statement",
  "name": "prepare",
  "body": { ... },
  "span": { ... }
}
```

Do not serialize:

```text
pending
running
completed
failed
pause state
cancellation state
```

---

# Lexer / Parser

Add:

```text
step
```

as a reserved keyword.

Parser must enforce placement:

```text
directly inside task body only
```

If cleaner architecturally, parser may construct the node and semantic analysis may reject invalid placement, but diagnostics must be deterministic.

---

# Name Resolution

Each step body introduces a block scope.

Resolve:

```text
task parameters
task-local outer variables
module-level values/functions
step-local bindings
```

Step names are unique within the task.

Step names are not ordinary local value bindings.

They cannot be referenced as values or called.

---

# Type Checking

Step bodies use ordinary Kaj typing.

Return analysis must understand:

```text
return inside step exits task
```

A task whose step definitely returns may satisfy task control-flow analysis where appropriate.

Do not let step boundaries weaken missing-return checking.

---

# Formatter

Canonical:

```kaj
step prepare {
    ...
}
```

Use ordinary four-space indentation and existing block formatting.

Formatter must remain idempotent.

---

# Diagnostics

Add/reuse stable diagnostics for:

```text
duplicate step name
step outside task
step not directly inside task body
attempt to use step as value/callable
invalid task lifecycle transition
invalid step lifecycle transition
```

Suggested names if existing conventions permit:

```text
TASK_DUPLICATE_STEP
TASK_STEP_OUTSIDE_TASK
TASK_INVALID_STEP_PLACEMENT
TASK_STEP_NOT_CALLABLE
TASK_INVALID_STATE_TRANSITION
TASK_INVALID_STEP_STATE_TRANSITION
```

Reuse existing diagnostics when they precisely fit.

---

# CLI / Runtime Inspection

Do not require a large new CLI surface.

If current task CLI has a useful inspection path, expose final lifecycle/step states there only if it fits cleanly.

The runtime API must make task and step states inspectable for tests and host integration.

---

# Required Tests

Lexer/parser:

```text
step keyword
valid named step
multiple steps
missing step name
duplicate names
step in fn rejected
step nested in if rejected
step nested in loop rejected
step nested in match rejected
```

Scope:

```text
task parameter visible inside step
outer let visible inside step
outer var mutable inside step
step-local let does not escape
```

Control flow:

```text
return inside step exits task
break inside loop inside step
continue inside loop inside step
later step not executed after task return
```

Execution:

```text
steps execute source order
pending -> running -> completed
step failure -> task failure
unreached step remains pending
```

Task lifecycle:

```text
created -> ready -> running
running -> completed
running -> failed
running -> paused
paused -> running
created/ready/running/paused -> cancelled
terminal states reject further transitions
```

Pause/cancel:

```text
pause request honored at safe boundary
resume continues without replaying completed steps
cancel prevents later steps
cancelled distinct from failed
```

AST/formatter:

```text
step AST
deterministic AST JSON
no runtime state in AST JSON
formatter idempotence
parse-format-parse preservation
```

Regression:

```text
all Pure Kaj tests
all Agentic Checkpoint 1 tests
mkdocs build --strict
```

---

# Out of Scope

Do not implement:

```text
goal
require
invariant
success
ask
choose
confirm
inform
handoff
waiting_for_human
waiting_for_capability
waiting_for_task
persistent storage
process-restart resume
capabilities
use
task composition
TaskHandle
planner
LLM integration
replanning
retry syntax
distributed scheduling
```

---

# Definition of Done

```text
[ ] `step` is reserved
[ ] named steps parse
[ ] step placement is restricted to direct task body
[ ] duplicate step names rejected

[ ] step creates lexical block scope
[ ] task outer bindings visible
[ ] outer task var can mutate across steps
[ ] step-local bindings do not escape
[ ] return inside step exits task

[ ] StepDefinition/AST representation exists
[ ] AST JSON deterministic
[ ] runtime states excluded from AST JSON
[ ] formatter canonical and idempotent

[ ] step runtime states implemented:
    pending/running/completed/failed

[ ] task lifecycle implemented:
    created/ready/running/paused/completed/failed/cancelled

[ ] state transition validation exists
[ ] pause works at safe step boundary
[ ] resume from pause works
[ ] cancellation is terminal
[ ] cancel prevents future steps
[ ] step failure fails task

[ ] runtime exposes step execution records
[ ] completed steps are not replayed during in-memory pause/resume

[ ] full Pure Kaj suite passes
[ ] Checkpoint 1 suite passes
[ ] Checkpoint 2 tests pass
[ ] mkdocs build --strict passes
```

---

# Completion Report

```text
Agentic Kaj Checkpoint 2 — Steps and Task Lifecycle

Status:
COMPLETE / INCOMPLETE

Files changed:
- ...

Syntax:
- step keyword: PASS/FAIL
- named steps: PASS/FAIL
- placement validation: PASS/FAIL
- formatter: PASS/FAIL
- AST JSON: PASS/FAIL

Step semantics:
- lexical scope: PASS/FAIL
- outer var mutation: PASS/FAIL
- return exits task: PASS/FAIL
- execution order: PASS/FAIL

Step runtime:
- pending: PASS/FAIL
- running: PASS/FAIL
- completed: PASS/FAIL
- failed: PASS/FAIL

Task lifecycle:
- created: PASS/FAIL
- ready: PASS/FAIL
- running: PASS/FAIL
- paused: PASS/FAIL
- completed: PASS/FAIL
- failed: PASS/FAIL
- cancelled: PASS/FAIL

Control:
- pause: PASS/FAIL
- resume: PASS/FAIL
- cancellation: PASS/FAIL
- invalid transitions rejected: PASS/FAIL

Regression:
- Pure Kaj: PASS/FAIL
- Agentic Checkpoint 1: PASS/FAIL
- Agentic Checkpoint 2: PASS/FAIL
- mkdocs build --strict: PASS/FAIL

Deferred intentionally:
- contracts
- human interaction
- persistence
- capabilities
- task composition
- planner
- replanning

Known issues:
- ...
```
