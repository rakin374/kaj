# Agentic Conformance

Agentic Conformance defines the minimum behavior an implementation must satisfy to claim compatibility with the initial Agentic Kaj runtime model.

This checkpoint does not add major new language features.

It freezes cross-feature semantics, compatibility expectations, conformance fixtures, lifecycle rules, persistence guarantees, planner/capability isolation, and regression requirements across Agentic Kaj Checkpoints 1–9.

---

## 1. Purpose

The Agentic Kaj feature set now includes:

```text
tasks
steps and lifecycle
task contracts
human interaction
persistence and resume
capabilities
task composition
planner interface
controlled replanning
```

Checkpoint 10 validates that these features behave as one coherent system.

The goal is not merely that each subsystem passes isolated tests.

The goal is that an implementation behaves consistently across subsystem boundaries.

---

## 2. Conforming implementation

An implementation may claim initial Agentic Kaj conformance only if it satisfies:

```text
Pure Kaj semantics
Agentic task semantics
required lifecycle transitions
task contract enforcement
human interaction suspension/resume
persistence guarantees
capability authority rules
task composition rules
planner validation boundaries
controlled replanning rules
required diagnostics and interoperability fixtures
```

---

## 3. Pure Kaj remains authoritative

Agentic Kaj extends Pure Kaj.

It does not replace or weaken it.

A conforming runtime must preserve:

```text
Pure Kaj typing
lexical scope
value semantics
control flow
module semantics
formatter behavior
AST JSON determinism
diagnostic discipline
```

inside agentic constructs.

---

## 4. No host-language semantic leaks

Kaj semantics must remain independent of implementation language.

A conforming implementation must not expose host-specific behavior such as:

```text
Python repr
Python exception classes
native object pointers
Swift object identity
JavaScript undefined
host stack traces as ordinary Kaj errors
```

as Kaj language semantics.

---

## 5. Task identity

Every task execution has a distinct:

```text
TaskId
```

Task identity must remain stable:

```text
during execution
during suspension
across persistence/restart
while referenced by TaskHandle
```

A restored task is the same task instance.

---

## 6. Task definition versus instance

A conforming implementation must preserve the distinction:

```text
TaskDeclaration
    source-level reusable definition

TaskInstance
    one runtime execution
```

Runtime instance fields must not leak into source AST JSON.

---

## 7. Required task lifecycle

A conforming implementation supports:

```text
created
ready
running
paused
waiting_for_human
waiting_for_capability
waiting_for_task
waiting_for_planner
completed
failed
cancelled
```

Implementations may have extra internal states, but observable behavior must map consistently to these semantics.

---

## 8. Terminal states

These are terminal:

```text
completed
failed
cancelled
```

A terminal task must not resume through ordinary task APIs.

---

## 9. Completion versus failure

A conforming runtime must preserve:

```text
normal Kaj return
    -> completed

Result.err(...)
    -> completed with err value

runtime execution failure
    -> failed

contract violation
    -> failed

child task failed while awaited
    -> parent failed

task cancellation
    -> cancelled
```

These outcomes are semantically distinct.

---

## 10. Steps

A conforming implementation supports named steps with:

```text
task-local placement
unique names per task
lexical block scope
source-order execution
runtime states
durable completion records
```

Step states:

```text
pending
running
completed
failed
```

---

## 11. Step completion durability

A step may be treated as durably completed only after:

```text
step body completed
required post-step contract checks passed
durable persistence commit succeeded
```

After that point, restart must not replay the step.

---

## 12. Interrupted step semantics

If a process crashes during an incomplete step:

```text
the incomplete step may replay from its beginning
```

The initial conformance model therefore provides:

```text
at-least-once execution of interrupted incomplete steps
```

not exactly-once external effects.

---

## 13. Task contracts

A conforming implementation supports:

```text
goal
require
invariant
success
```

with the previously frozen typing, purity, placement, and lifecycle semantics.

---

## 14. Contract authority

The runtime, not the planner, is authoritative for task contracts.

A planner may not:

```text
modify
remove
weaken
bypass
```

the task's:

```text
goal
require
invariant
success
```

---

## 15. Human interaction

A conforming runtime supports:

```text
ask<T>
choose<T>
confirm
inform
handoff
```

with:

```text
typed responses
waiting_for_human
stable InteractionId
invalid-response retention
exact continuation resume
persistence across restart
```

---

## 16. Invalid human response

Malformed human input must not:

```text
resume task with invalid value
silently coerce arbitrarily
fail the task by default
```

The interaction remains pending.

---

## 17. Capability authority

A conforming runtime preserves:

```text
use Capability as alias
```

as a requirement, not a grant.

Source code may request capability access.

Only the host may bind authority.

---

## 18. Capability isolation

A task may access only capability bindings granted to that task.

It may not:

```text
enumerate unrelated host capabilities
access another task's binding
expand operation grants
self-authorize a new capability
```

---

## 19. Capability result typing

Host capability results must be converted to valid Kaj values and checked against declared return types before they enter Kaj execution state.

Native host objects must not leak into Kaj values.

---

## 20. Capability crash uncertainty

When a crash leaves an external capability action outcome unknown:

```text
the runtime must represent the request as indeterminate
```

Potentially effectful operations must not be blindly replayed.

---

## 21. Task composition

A conforming implementation supports:

```text
start
TaskHandle<T>
await
waiting_for_task
```

with independent child TaskInstances.

---

## 22. Child task result semantics

Freeze:

```text
child completed
    -> await returns T

child completed with Result.err(...)
    -> await returns Result.err normally

child failed
    -> awaiting parent fails

child cancelled
    -> awaiting parent fails
```

---

## 23. Parent cancellation/failure

A conforming implementation must propagate:

```text
parent cancelled
or
parent failed
```

downward to non-terminal descendants.

Normal parent completion does not automatically cancel children.

---

## 24. Capability inheritance

Child tasks do not implicitly inherit parent capability bindings.

Each child resolves its own declared capability requirements.

---

## 25. Persistence

A conforming persistent runtime stores enough state to reconstruct:

```text
TaskId
task definition identity/fingerprint
task lifecycle state
inputs
Kaj environment
execution position
step states
human interaction state
capability binding descriptors
pending capability requests
task handles and relationships
planner state
accepted plan revision
terminal result/failure
```

---

## 26. Definition compatibility

Resume must reject incompatible task definitions.

The initial conservative rule remains:

```text
definition fingerprint must match
```

unless the implementation provides a stricter compatible mechanism.

---

## 27. Snapshot versioning

Persistent state must be versioned.

Unsupported/corrupt snapshots must be rejected explicitly.

Implementations must not guess through incompatible durable state.

---

## 28. Planner boundary

A conforming planner integration preserves:

```text
planner proposes
Kaj validates
runtime executes
```

Planner output is untrusted until validated.

---

## 29. Planner portability

Kaj conformance does not depend on a specific model vendor.

A conforming runtime must not require:

```text
OpenAI
Anthropic
Google
local LLM
```

as part of the core language/runtime contract.

---

## 30. Planner output

Executable planner output must become structured Kaj.

Accepted forms:

```text
Kaj AST JSON
structured plan AST
Kaj source parsed by normal parser
```

Free-form natural language is not executable by itself.

---

## 31. Protected planner regions

A planner cannot modify:

```text
task signature
goal
require
invariant
success
use declarations
capability grants
fixed source outside plan region
```

---

## 32. Planner stale-response safety

Planner responses must be correlated using:

```text
TaskId
PlanningAttemptId
```

Stale or duplicate responses must not mutate runtime state.

---

## 33. Replanning

A conforming runtime supports controlled replanning of:

```text
future planner-owned work only
```

Completed durable history is immutable.

---

## 34. Plan revisions

Accepted plans carry:

```text
revision
fingerprint
```

Accepted replans increment revision.

Rejected replans do not.

---

## 35. Replan safety

A replan must not:

```text
rewrite completed steps
replace the currently running step
change contracts
change capability grants
undo human responses
undo completed capability outcomes
erase already-created child tasks
```

---

## 36. Replan atomicity

A valid replan is applied atomically.

If validation or persistence fails:

```text
the previous accepted plan remains authoritative
```

---

## 37. Conformance fixtures

The project should maintain canonical conformance programs.

Recommended categories:

```text
task-basics
task-contracts
human-interaction
persistence
capabilities
task-composition
planner
replanning
cross-feature
negative-diagnostics
```

Fixtures should be implementation-independent Kaj programs plus expected structured outcomes.

---

## 38. Positive fixtures

Positive fixtures define:

```text
source
inputs
host bindings/responses
expected lifecycle sequence
expected result
expected step states
expected persisted state where relevant
```

---

## 39. Negative fixtures

Negative fixtures define:

```text
invalid source or invalid runtime action
expected diagnostic code/category
expected absence of side effect
```

Diagnostics need not have byte-identical prose across every host SDK if the language project has not frozen exact text, but stable codes/categories should match.

---

## 40. Cross-feature fixtures

Conformance must include scenarios combining multiple agentic features.

Examples:

```text
task contract + human interaction
human interaction + persistence
capability + persistence
child task + human interaction
child task + capability
planner + capability grant restriction
planner + task composition
replanning + persisted child handle
replanning + invariant enforcement
```

---

## 41. Deterministic test host

The Kaj repository should include a deterministic reference test host.

It should provide mock:

```text
human interaction responses
capability adapters
task scheduler
planner adapter
persistence store
```

This allows conformance tests without external services.

---

## 42. No network dependency for core conformance

Core conformance tests must run without:

```text
internet access
real browser
real database service
real LLM API
real human operator
```

External integration suites may exist separately.

---

## 43. Event trace

For conformance testing, the runtime should expose a deterministic structured event trace.

Conceptually events may include:

```text
task_created
task_state_changed
step_started
step_completed
interaction_requested
interaction_resolved
capability_requested
capability_completed
child_started
planner_requested
plan_accepted
replan_accepted
task_completed
task_failed
task_cancelled
```

Exact public API may vary, but test observability must be sufficient.

---

## 44. Event trace is not source semantics

The test trace is runtime observability.

It does not become source AST or new Kaj language syntax.

---

## 45. AST conformance

Agentic source AST JSON must remain:

```text
deterministic
runtime-state-free
host-independent
```

Runtime IDs and snapshots are separate from source representation.

---

## 46. Formatter conformance

All Agentic Kaj syntax must participate in canonical formatting.

Required:

```text
formatter idempotence
parse-format-parse semantic preservation
```

---

## 47. Diagnostics conformance

Agentic diagnostics should be:

```text
structured
stable by code/category
source-aware where applicable
free of raw host tracebacks for ordinary user errors
```

---

## 48. Security conformance

A conforming runtime must test negative authority boundaries.

At minimum:

```text
planner capability escalation rejected
cross-task capability access rejected
contract mutation rejected
stale planner response rejected
stale interaction response rejected
stale capability response rejected
completed-history rewrite rejected
```

---

## 49. Persistence conformance

Required restart fixtures include:

```text
paused task
waiting_for_human
waiting_for_capability
waiting_for_task
waiting_for_planner
accepted plan
accepted replan
completed task
failed task
cancelled task
```

---

## 50. Compatibility declaration

The project may expose a conformance/version identifier.

Conceptually:

```text
Agentic Kaj Conformance 1
```

The exact CLI/API spelling is implementation-defined.

---

## 51. Conformance versioning

Future incompatible agentic semantic changes should advance the conformance version.

Minor implementation changes that preserve these semantics need not.

---

## 52. Reference runtime

The initial Python runtime remains a reference implementation, not the definition of Kaj itself.

Other runtimes may conform if they reproduce the same observable semantics.

---

## 53. Host SDKs

A host SDK may expose convenience APIs for:

```text
task start
task inspection
human responses
capability registration
planner registration
persistence
```

SDK ergonomics may differ by language.

They must preserve Kaj semantics.

---

## 54. No hidden privileged execution path

A conforming runtime must not give planner adapters or capability adapters an undocumented path that bypasses ordinary validation/authority checks.

---

## 55. Failure containment

A malformed:

```text
planner response
human response
capability response
persistent snapshot
```

must not corrupt unrelated task instances.

Task isolation should be maintained.

---

## 56. Stable public semantics versus implementation detail

The following are public semantics:

```text
task lifecycle
contract behavior
waiting behavior
capability authority
composition behavior
planner/replan boundaries
persistence guarantees
```

The following may remain implementation details:

```text
Python class layout
database schema
scheduler internals
hash algorithm
transport protocol
threading model
storage engine
```

---

## 57. Conformance summary

An implementation conforming to the initial Agentic Kaj model must preserve:

```text
Pure Kaj correctness

durable typed tasks
named durable steps
contracts
human suspension/resume
persistent restart recovery
typed host capabilities with explicit authority
child task composition
validated planner boundary
controlled future-only replanning

stable task identity
stable wait identities
no planner self-authorization
no raw host-object leakage
no silent replay of indeterminate effects
no rewrite of committed task history
no runtime state in source AST
```

---

## 58. Initial Agentic Kaj boundary

After Checkpoint 10, the initial Agentic Kaj foundation is considered complete.

Future work may add:

```text
standard capability libraries
real host adapters
browser integration
filesystem integration
robotics integration
distributed execution
richer structured concurrency
retry policies
effect/idempotency annotations
planner policies
debugger/inspector tooling
performance optimization
additional host SDKs
```

These additions should build on, rather than weaken, the conformance rules frozen here.
