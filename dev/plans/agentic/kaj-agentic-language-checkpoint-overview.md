# Kaj Agentic Language — Checkpoint Overview

**Status:** Planning overview  
**Scope:** Agentic Kaj language and runtime layer built on top of the completed pure Kaj baseline  
**Checkpoint numbering:** Starts at 1 because Agentic Kaj is treated as a separate development track

---

# 1. Development Track Separation

Pure Kaj and Agentic Kaj should now be treated as separate implementation tracks.

Recommended `dev/` structure:

```text
dev/
├── plans/
│   ├── pure/
│   │   ├── checkpoint-0-bootstrap.md
│   │   ├── checkpoint-1-lexer.md
│   │   ├── ...
│   │   ├── checkpoint-24-pure-language-hardening.md
│   │   └── pure-language-documentation.md
│   │
│   └── agentic/
│       ├── README.md
│       ├── checkpoint-1-tasks.md
│       ├── checkpoint-2-steps-lifecycle.md
│       ├── checkpoint-3-task-contracts.md
│       ├── checkpoint-4-human-interaction.md
│       ├── checkpoint-5-persistence-resume.md
│       ├── checkpoint-6-capabilities.md
│       ├── checkpoint-7-task-composition.md
│       ├── checkpoint-8-planner-interface.md
│       ├── checkpoint-9-controlled-replanning.md
│       └── checkpoint-10-agentic-conformance.md
│
├── decisions/
│   ├── pure/
│   └── agentic/
│
└── notes/
    ├── pure/
    └── agentic/
```

This keeps the two histories distinct:

```text
Pure Kaj
    ↓
ordinary language semantics

Agentic Kaj
    ↓
durable tasks, capabilities, human collaboration,
persistence, planning, replanning
```

Agentic Kaj depends on Pure Kaj.

Pure Kaj must not depend on Agentic Kaj.

---

# 2. Architectural Principle

Agentic Kaj is a semantic/runtime layer on top of Pure Kaj.

```text
Kaj Source
   ↓
Lexer / Parser
   ↓
AST
   ↓
Pure Semantic Analysis
   ↓
Agentic Semantic Analysis
   ↓
IR / Runtime Model
   ↓
Agentic Runtime
   ├── task state
   ├── persistence
   ├── human interaction
   ├── capabilities
   ├── planner integration
   └── host adapters
```

Pure Kaj remains authoritative for:

```text
values
types
functions
records
enums
Optional
Result
lists
maps
newtypes
control flow
modules
formatting
AST JSON
```

Agentic Kaj adds concepts that ordinary functions do not have:

```text
durability
task identity
steps
task lifecycle
suspension
resume
human interaction
external capabilities
task contracts
planning
replanning
```

---

# 3. Agentic Kaj Core Model

The target conceptual model is:

```text
Agentic Task
├── inputs
├── output type
├── required capabilities
├── task contract
│   ├── goal
│   ├── require
│   ├── invariant
│   └── success
├── execution plan
│   └── steps
├── human interactions
├── runtime state
├── persistence state
└── final result
```

A future task may conceptually look like:

```kaj
task FindProduct(query: String, max_price: Decimal)
    -> Result<Product, FindProductError>
{
    goal "Find {query} for no more than {max_price}"

    require {
        max_price > 0
    }

    step open_store {
        // ...
    }

    step search {
        // ...
    }

    step evaluate {
        // ...
    }

    success(product: Product) {
        product.price <= max_price
    }
}
```

This syntax is illustrative until the relevant checkpoints freeze it.

---

# Checkpoint 1 — Tasks

## Goal

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

## Main Areas

```text
task declaration syntax
task parameters
task return type
task body
task identity
task instance
task completion
task failure
task vs function rules
```

## Key Design Questions

Freeze:

```text
Can task call fn?               likely yes
Can fn call task?               likely no
Can task call task?             deferred to composition checkpoint
Can task recurse?               likely restricted/deferred initially
Does task invocation block?      must be explicitly defined
Does task invocation return a handle?
How are task instances identified?
```

## Initial Principle

A task is not merely a renamed function.

```text
fn:
    ordinary computation
    no persistent identity
    no lifecycle

task:
    durable work
    runtime identity
    lifecycle
    may later suspend/resume
    may later use capabilities
```

## Out of Scope

```text
steps
human interaction
persistence
capabilities
LLM planning
replanning
```

---

# Checkpoint 2 — Steps and Task Lifecycle

## Goal

Define durable execution boundaries inside tasks and the task state machine.

## Main Areas

```text
step syntax
named steps
step scope
step completion
step failure
task lifecycle states
cancellation
runtime execution record
```

## Preferred Direction

Favor named steps:

```kaj
step open_store {
    ...
}

step search {
    ...
}
```

because stable names improve:

```text
persistence
logs
recovery
UI
replanning
debugging
```

## Lifecycle

Initial states should likely include:

```text
created
ready
running
paused
completed
failed
cancelled
```

Waiting states are introduced more fully in later checkpoints.

## Semantic Questions

Freeze:

```text
Does step create lexical scope?
Can return inside step exit task?
Can loops span steps? likely no
Can step contain arbitrary ordinary Kaj statements? likely yes
What does step completion commit?
Can completed steps execute again?
```

## Out of Scope

```text
human waits
external capabilities
database persistence
planner-generated steps
```

---

# Checkpoint 3 — Task Contracts

## Goal

Define the declarative contract around a task.

Introduce and distinguish:

```text
goal
require
invariant
success
```

## `goal`

Describes task intent.

Example:

```kaj
goal "Find a flight to Boston under {budget}"
```

Initial principles:

```text
planner-visible
human-readable
immutable during execution
not itself proof of success
```

## `require`

Precondition checked before execution.

```kaj
require {
    budget > 0
}
```

## `invariant`

Condition that must remain true during execution.

```kaj
invariant {
    total_spend <= budget
}
```

Need to freeze when invariants are evaluated.

Recommended initial points:

```text
before task execution
after each completed step
before completion
```

## `success`

Machine-checkable definition of task completion.

```kaj
success(result: Product) {
    result.price <= max_price
}
```

Prefer pure ordinary Kaj expressions.

## Major Principle

```text
goal     = intention
success  = verification
```

The runtime should never treat a natural-language goal alone as proof of completion.

---

# Checkpoint 4 — Human Interaction

## Goal

Make interaction with a human a first-class resumable part of task execution.

Initial primitives:

```text
ask
choose
confirm
inform
handoff
```

## `ask`

Typed information request:

```kaj
let city = ask<String>("Where are you going?")
```

Task transitions:

```text
running
↓
waiting_for_human
↓
running
```

after a valid response.

## `choose`

Structured selection from explicit alternatives.

## `confirm`

Typed approval, likely returning `Bool`.

## `inform`

One-way notification that does not suspend execution.

## `handoff`

Explicit transfer of control to a human.

## Define

```text
waiting_for_human state
request identity
response typing
invalid response handling
user cancellation
multiple pending interactions
timeout/expiry behavior
```

Initial implementation should likely allow one active blocking interaction per task.

---

# Checkpoint 5 — Persistence and Resume

## Goal

Make tasks genuinely durable rather than merely long-running interpreter calls.

## Persisted State

Define a serializable task-state representation containing at least:

```text
task instance ID
task definition identity/version
inputs
current lifecycle state
current step
completed steps
persistent Kaj values
pending human interaction
task result/failure if terminal
```

## Core Rule

Values that survive suspension must be serializable Kaj values.

Native host objects must never leak directly into persistent Kaj state.

## Resume

Define:

```text
resume after process restart
resume after human response
resume paused task
resume compatibility with task definition changes
```

## Crash Semantics

Freeze behavior around:

```text
step completed before crash
step running during crash
unknown side-effect completion
```

This checkpoint should establish the conceptual persistence model even if the first storage backend is simple/local.

---

# Checkpoint 6 — Capabilities

## Goal

Define how Agentic Kaj accesses the outside world without embedding host-specific APIs into the language.

## Main Concepts

```text
capability declaration
capability requirement
capability instance
host binding
typed operation calls
missing capability
denied operation
capability-scoped authority
```

## Conceptual Declaration

```kaj
capability Browser {
    fn observe() -> Result<PageObservation, BrowserError>
    fn navigate(url: String) -> Result<None, BrowserError>
}
```

## Requirement

Conceptually:

```kaj
use Browser as browser
```

This means:

```text
this task requires a Browser capability instance
```

It does not grant itself permission.

The host supplies the actual implementation.

## Host Boundary

```text
Kaj capability contract
        ↓
host-provided adapter
        ↓
browser / filesystem / robot / app / API
```

## Required Design Work

Freeze:

```text
capability namespaces
capability operation typing
capability lookup
host registration
capability instance identity
scoped grants
missing capability errors
denied operation errors
suspending capability calls
```

Do not make browser-specific semantics part of Kaj core.

---

# Checkpoint 7 — Task Composition

## Goal

Allow one task to start and/or wait for another task.

## Questions to Freeze

```text
How does task invocation syntax differ from fn invocation?
Does task invocation return TaskHandle<T>?
How does a parent await a child?
Can child tasks outlive parent?
How is cancellation propagated?
How are child failures represented?
How are capabilities inherited?
```

## Possible Future Syntax

Not frozen:

```kaj
let result = perform FindWebsite(name)
```

or:

```kaj
let handle = start FindWebsite(name)
let result = await handle
```

Task invocation should remain visibly distinct from ordinary function calls.

## Runtime State

Add:

```text
waiting_for_task
```

if synchronous parent/child waiting is supported.

---

# Checkpoint 8 — Planner Interface

## Goal

Introduce an optional planner without making the LLM the runtime.

## Core Principle

```text
Planner proposes.
Kaj validates.
Runtime executes.
```

The planner is a runtime service.

It does not bypass:

```text
parser
AST validation
name resolution
type checking
capability checking
task contracts
host policy
```

## Planner Inputs

Define structured context such as:

```text
goal
task contract
current state
available capability operations
current observations
completed steps
relevant task values
planner-visible history
```

## Planner Output

Prefer structured Kaj AST / plan structures.

Avoid free-form action strings.

## Out of Scope

Unrestricted self-modifying code.

---

# Checkpoint 9 — Controlled Replanning

## Goal

Allow an agent to modify its execution plan while protecting the task contract.

## Protected Region

Planner must not modify:

```text
task inputs
goal
require
invariants
success conditions
capability grants
human approval requirements
host policy
```

## Replannable Region

Planner may modify only explicitly designated plan/step regions.

## Mechanism

Prefer AST patches rather than entire source replacement.

Conceptually:

```text
planner
  ↓
AST patch
  ↓
schema validation
  ↓
name resolution
  ↓
type checking
  ↓
capability validation
  ↓
contract/policy validation
  ↓
accept or reject
```

## Define

```text
patch operations
stable step identity
insert/remove/replace rules
completed-step protection
replanning history
rejected plan handling
```

---

# Checkpoint 10 — Agentic Conformance and Hardening

## Goal

Freeze the first Agentic Kaj baseline through comprehensive conformance testing and dogfooding.

No major new syntax should be introduced here.

## Required Coverage

```text
task declaration
task instances
step execution
lifecycle transitions
contracts
human interactions
suspension
resume
persistence
capability binding
capability failures
task composition
planner validation
replanning
cancellation
crash recovery
```

## Security / Authority Tests

Ensure:

```text
source cannot self-grant capabilities
planner cannot expand capability grants
planner cannot rewrite protected contracts
native host objects do not leak into Kaj values
task cannot access another task's capabilities accidentally
capability instance scoping is preserved
```

## Persistence Tests

Cover:

```text
restart while running
restart while waiting_for_human
restart between steps
completed steps not accidentally repeated
terminal task restoration
version mismatch handling
```

## Planner Tests

Cover:

```text
valid plan accepted
invalid AST rejected
type-invalid plan rejected
unknown capability rejected
protected contract modification rejected
invalid AST patch rejected
```

## Dogfood Scenarios

Build generic end-to-end tasks using mock capabilities first.

Examples:

```text
approval workflow
multi-step research workflow
file processing workflow
human-assisted workflow
nested child-task workflow
```

Then test at least one real host integration.

Browser is a strong candidate, but it remains outside Kaj core.

---

# 4. Recommended Implementation Sequence

The sequence is intentionally:

```text
1. Tasks
2. Steps + Lifecycle
3. Contracts
4. Human Interaction
5. Persistence + Resume
6. Capabilities
7. Task Composition
8. Planner
9. Controlled Replanning
10. Conformance
```

The reasoning is:

```text
deterministic durable execution
        ↓
suspension and persistence
        ↓
outside-world access
        ↓
multi-task orchestration
        ↓
LLM planning
        ↓
safe replanning
```

Do not begin with an LLM planner.

The runtime model must work deterministically first.

---

# 5. What Is Intentionally Deferred

Do not add these to the first Agentic Kaj baseline unless a checkpoint explicitly requires them:

```text
distributed task scheduling
multi-agent swarms
task marketplaces
remote package registry
agent identity system
memory/vector database semantics
autonomous capability discovery
unrestricted dynamic code generation
reflection
macros
concurrent task syntax
async/await for ordinary Kaj
cron/scheduling language
workflow visual DSL
browser-specific syntax
robot-specific syntax
filesystem-specific syntax
```

These can be layered later.

---

# 6. Public Documentation Structure

As Agentic Kaj becomes real, add stable user-facing docs separately from checkpoint plans.

Recommended:

```text
docs/
├── agentic/
│   ├── index.md
│   ├── tasks.md
│   ├── steps.md
│   ├── lifecycle.md
│   ├── contracts.md
│   ├── human-interaction.md
│   ├── persistence.md
│   ├── capabilities.md
│   ├── task-composition.md
│   ├── planning.md
│   └── replanning.md
```

These files should contain only implemented/frozen semantics.

Implementation checklists and checkpoint-specific verification remain under:

```text
dev/plans/agentic/
```

---

# 7. Agentic Track README

Create:

```text
dev/plans/agentic/README.md
```

It should explain:

```text
Agentic Kaj starts at Checkpoint 1.
Pure Kaj is a completed dependency.
Agentic checkpoints are numbered independently.
Agentic Kaj must not weaken Pure Kaj semantics.
Host-specific integrations are adapters, not language-core features.
Planner/LLM behavior is subordinate to Kaj validation and runtime policy.
```

It should also link to every Agentic Kaj checkpoint as they are created.

---

# 8. Immediate Next Step

Do not implement all ten checkpoints from this overview.

The next task should be to write the full specification/implementation plan for:

```text
Agentic Checkpoint 1 — Tasks
```

That checkpoint should freeze:

```text
task declaration syntax
task parameters
task return type
task body
task instance identity
task completion
task runtime failure
task vs fn rules
initial invocation semantics
AST representation
name resolution
type checking
formatter behavior
AST JSON behavior
interpreter/runtime representation
diagnostics
tests
```

Only once Checkpoint 1 is frozen should implementation begin.
