# Agentic Kaj — Checkpoint 10: Agentic Conformance

**Track:** Agentic Kaj  
**Checkpoint:** 10  
**Recommended path:** `dev/plans/agentic/checkpoint-10-agentic-conformance.md`

---

# Goal

Freeze and verify the initial Agentic Kaj model as one coherent runtime/language system.

Authoritative semantics:

```text
docs/agentic/agentic-conformance.md
```

Checkpoint 10 is primarily:

```text
integration
conformance
hardening
cross-feature regression
diagnostic cleanup
fixture creation
runtime isolation verification
documentation consistency
```

Avoid adding major new language features.

---

# Scope

Implement/complete:

```text
Agentic Conformance 1 fixture suite
deterministic test host
cross-feature integration tests
runtime event trace for tests
persistence restart matrix
security/authority negative tests
AST/formatter conformance tests
diagnostic stability checks
host-language leak audit
agentic docs consistency audit
regression hardening
conformance/version reporting if clean
```

---

# Conformance Matrix

Validate all frozen features:

```text
Checkpoint 1:
    tasks

Checkpoint 2:
    steps/lifecycle

Checkpoint 3:
    contracts

Checkpoint 4:
    human interaction

Checkpoint 5:
    persistence/resume

Checkpoint 6:
    capabilities

Checkpoint 7:
    task composition

Checkpoint 8:
    planner interface

Checkpoint 9:
    controlled replanning
```

---

# Conformance Fixtures

Create a dedicated fixture structure, recommended:

```text
tests/conformance/agentic/
├── task-basics/
├── steps/
├── contracts/
├── human-interaction/
├── persistence/
├── capabilities/
├── task-composition/
├── planner/
├── replanning/
├── cross-feature/
└── negative/
```

Adapt to repository conventions if needed.

Fixtures should be as implementation-independent as practical.

---

# Fixture Shape

Each fixture should define enough structured expectations for deterministic validation.

Conceptually:

```text
source
task entrypoint
typed inputs
host configuration
human responses
capability responses
planner responses
expected lifecycle/events
expected result/failure
expected persisted/restored outcome
```

Use a data format already suitable for the repository.

Do not invent unnecessary test DSL complexity.

---

# Deterministic Test Host

Build/centralize a reference test host with mock:

```text
TaskStore
human interaction responder
capability registry/adapters
scheduler
planner adapter
clock/ID source where determinism is needed
event recorder
```

No real external services.

---

# Event Trace

Expose deterministic structured runtime events for tests.

At minimum support observing events equivalent to:

```text
task_created
task_state_changed
step_started
step_completed
step_failed
interaction_requested
interaction_resolved
capability_requested
capability_completed
child_started
planner_requested
planner_proposal_rejected
plan_accepted
replan_accepted
task_completed
task_failed
task_cancelled
```

Do not make event trace part of source AST.

---

# Lifecycle Conformance

Test every valid/important path among:

```text
CREATED
READY
RUNNING
PAUSED
WAITING_FOR_HUMAN
WAITING_FOR_CAPABILITY
WAITING_FOR_TASK
WAITING_FOR_PLANNER
COMPLETED
FAILED
CANCELLED
```

Also test invalid transitions.

---

# Completion / Failure Conformance

Explicitly verify distinctions:

```text
normal return -> COMPLETED
Result.err -> COMPLETED
runtime failure -> FAILED
require violation -> FAILED
invariant violation -> FAILED
success false -> FAILED
task cancellation -> CANCELLED
await failed child -> parent FAILED
await cancelled child -> parent FAILED
```

---

# Step Durability Conformance

Verify:

```text
completed step committed only after post-step invariant + persistence success
completed step not replayed after restart
incomplete step may replay
step runtime state preserved
```

---

# Human Interaction Conformance

Verify:

```text
ask typed response
choose membership
confirm true/false
inform non-blocking
handoff completion
waiting_for_human
InteractionId persistence
invalid input stays waiting
stale/duplicate response rejected
resume exact continuation
```

---

# Persistence Matrix

Add restart tests for:

```text
READY
PAUSED
WAITING_FOR_HUMAN
WAITING_FOR_CAPABILITY
WAITING_FOR_TASK
WAITING_FOR_PLANNER
COMPLETED
FAILED
CANCELLED
```

Verify IDs, state, continuation, and result/failure preservation.

---

# Capability Conformance

Verify:

```text
use is requirement, not grant
missing capability prevents start/resume
operation typing
operation-level grant denial
task-scoped isolation
cross-task access impossible
native object result rejected
wrong host result type rejected
async wait/resume
persistent binding descriptor
restore rebinding
indeterminate effect not blindly replayed
```

---

# Task Composition Conformance

Verify:

```text
TaskHandle<T>
child identity
parent relationship
waiting_for_task
child normal result
child Result.err
child failure
child cancellation
downward parent failure/cancel propagation
normal parent completion leaves child alive
child capability requirements independent
persistence of handles/relationships
```

---

# Planner Conformance

Verify:

```text
planner proposes structured Kaj
normal Kaj validation reused
raw natural language not directly executable
task signature protected
contracts protected
use declarations protected
capability grants enforced
fixed source protected
PlanningAttemptId correlation
stale/duplicate proposal rejection
accepted plan persistence
no vendor dependency in core
```

---

# Replanning Conformance

Verify:

```text
initial revision = 1
accepted replan increments revision
completed prefix immutable
running step protected
pending suffix replaceable
base revision/fingerprint required
stale patch rejected
contract/capability/fixed source protection
atomic patch application
accepted replan persists
existing effects/history preserved
```

---

# Cross-Feature Tests

Add substantial integration fixtures.

At minimum:

```text
contract + human interaction
human interaction + persistence
capability wait + persistence
capability result + invariant
child task + human interaction
child task + capability
child task + persistence
planner + capability grant validation
planner + human interaction
planner + child task
replan + capability value already produced
replan + existing TaskHandle
replan + invariant enforcement
restart while waiting for planner
restart after accepted replan
```

---

# Negative Security Tests

At minimum:

```text
planner adds use -> rejected
planner calls denied capability op -> rejected
planner changes success -> rejected
replan edits completed step -> rejected
replan uses stale revision -> rejected
task accesses another task binding -> rejected
stale human response -> rejected
stale capability response -> rejected
stale planner response -> rejected
native host object persistence -> rejected
corrupt snapshot -> rejected
definition mismatch -> rejected
```

Ensure rejected operations create no external side effect.

---

# AST Conformance

Verify all Agentic Kaj source nodes serialize deterministically.

At minimum include:

```text
task
step
goal
require
invariant
success
capability
use
start
await
plan
```

Check that runtime data never appears in source AST JSON:

```text
TaskId
InteractionId
CapabilityRequestId
PlanningAttemptId
task state
step state
runtime result
snapshot data
capability binding IDs
plan revision runtime metadata
```

---

# Formatter Conformance

For all agentic syntax:

```text
parse
format
parse
format
```

must stabilize.

Verify:

```text
canonical indentation
canonical block layout
idempotence
semantic preservation
```

---

# Diagnostics Audit

Audit agentic diagnostics for:

```text
stable code/category
useful source span where applicable
consistent stderr/structured API behavior
no raw Python traceback for ordinary user/compiler/runtime errors
```

Remove duplicate/inconsistent diagnostic pathways.

---

# Host-Language Leak Audit

Search for externally observable accidental dependence on Python implementation.

Examples to remove:

```text
repr(...)
Python exception names in user diagnostics
dict ordering assumptions not guaranteed by Kaj
host numeric formatting
raw object serialization
host stack traces
```

Pure Kaj display/serialization semantics remain authoritative.

---

# Persistence Format Audit

Verify:

```text
schema version
definition fingerprint
plan fingerprint/revision
nominal Kaj value identity
Decimal exactness
atomic writes
corrupt snapshot rejection
```

Do not require snapshot backward migration yet.

---

# Isolation Tests

Multiple task instances should not corrupt one another.

Test:

```text
separate environments
separate interactions
separate capability bindings
separate planner attempts
separate child trees
separate persistence snapshots
```

---

# Conformance Version

If it fits current CLI/runtime architecture, expose:

```text
Agentic Kaj Conformance 1
```

through runtime metadata or CLI version information.

Do not create a large compatibility-negotiation subsystem.

---

# Documentation Audit

Ensure public docs exist and agree with implementation:

```text
docs/agentic/tasks.md
docs/agentic/steps-and-lifecycle.md
docs/agentic/task-contracts.md
docs/agentic/human-interaction.md
docs/agentic/persistence-resume.md
docs/agentic/capabilities.md
docs/agentic/task-composition.md
docs/agentic/planner-interface.md
docs/agentic/controlled-replanning.md
docs/agentic/agentic-conformance.md
```

Update:

```text
docs/agentic/index.md
mkdocs.yml
```

as needed.

Public docs must not contain checkpoint-specific DoD/test instructions.

---

# Dogfood Programs

Add several readable Agentic Kaj examples.

At minimum include concepts such as:

```text
human approval workflow
mock external capability workflow
parent/child task workflow
planner-controlled workflow
replanning workflow
persistent wait/resume workflow
```

Use deterministic mock hosts for automated execution.

---

# Performance

Checkpoint 10 is not primarily a performance checkpoint.

However, remove obvious accidental pathological behavior found during conformance testing.

Do not undertake large optimizer/compiler rewrites unless required for correctness.

---

# Required Verification

Run:

```text
full Pure Kaj test suite
all Agentic Checkpoints 1–9 tests
Agentic Conformance suite
formatter tests
AST JSON tests
persistence/restart suite
negative security suite
mkdocs build --strict
```

Use repository-native lint/type/static checks as well.

---

# Out of Scope

Do not add major new semantics such as:

```text
task groups
structured concurrency redesign
retry language syntax
exactly-once capability semantics
new standard capability libraries
real Chalok Browser adapter
distributed execution
remote task migration
planner memory
multi-planner consensus
contract mutation
goal mutation
snapshot migration framework
```

Fix correctness gaps required to satisfy already-frozen semantics.

---

# Definition of Done

```text
[ ] Agentic Conformance 1 fixture suite exists
[ ] deterministic test host exists
[ ] structured event trace exists for tests

[ ] full lifecycle paths covered
[ ] completion/failure distinctions covered
[ ] step durability/replay semantics covered
[ ] contracts covered
[ ] human interaction covered
[ ] persistence restart matrix covered
[ ] capabilities covered
[ ] composition covered
[ ] planner covered
[ ] replanning covered

[ ] required cross-feature fixtures pass
[ ] security/authority negative tests pass
[ ] multi-task isolation tests pass

[ ] AST JSON deterministic for all agentic syntax
[ ] runtime state excluded from source AST JSON
[ ] formatter idempotent for all agentic syntax

[ ] diagnostics audited
[ ] host-language leaks removed
[ ] persistence format audited

[ ] agentic public docs complete/consistent
[ ] docs/agentic/index.md updated
[ ] mkdocs navigation updated

[ ] dogfood programs added

[ ] Pure Kaj suite passes
[ ] Agentic Checkpoints 1–9 pass
[ ] Agentic Conformance suite passes
[ ] mkdocs build --strict passes
```

---

# Completion Report

```text
Agentic Kaj Checkpoint 10 — Agentic Conformance

Status:
COMPLETE / INCOMPLETE

Files changed:
- ...

Conformance infrastructure:
- fixture suite: PASS/FAIL
- deterministic test host: PASS/FAIL
- runtime event trace: PASS/FAIL

Semantics:
- tasks: PASS/FAIL
- steps/lifecycle: PASS/FAIL
- contracts: PASS/FAIL
- human interaction: PASS/FAIL
- persistence/resume: PASS/FAIL
- capabilities: PASS/FAIL
- task composition: PASS/FAIL
- planner interface: PASS/FAIL
- controlled replanning: PASS/FAIL

Cross-feature:
- interaction + persistence: PASS/FAIL
- capability + persistence: PASS/FAIL
- child + interaction/capability: PASS/FAIL
- planner + capability: PASS/FAIL
- planner + composition: PASS/FAIL
- replanning + persisted state: PASS/FAIL
- contracts across planner/replan: PASS/FAIL

Security/isolation:
- capability escalation blocked: PASS/FAIL
- cross-task binding isolation: PASS/FAIL
- stale response protection: PASS/FAIL
- completed-history protection: PASS/FAIL
- multi-task isolation: PASS/FAIL

Language tooling:
- AST JSON: PASS/FAIL
- formatter: PASS/FAIL
- diagnostics: PASS/FAIL
- host-language leak audit: PASS/FAIL

Persistence:
- restart matrix: PASS/FAIL
- snapshot integrity: PASS/FAIL
- definition compatibility: PASS/FAIL
- atomicity: PASS/FAIL

Documentation:
- public agentic docs: PASS/FAIL
- agentic index: PASS/FAIL
- mkdocs navigation: PASS/FAIL
- mkdocs build --strict: PASS/FAIL

Regression:
- Pure Kaj: PASS/FAIL
- Agentic Checkpoints 1–9: PASS/FAIL
- Agentic Conformance: PASS/FAIL

Conformance version:
- Agentic Kaj Conformance 1: PASS/FAIL/DEFERRED

Known issues:
- ...

Deferred future work:
- standard capability libraries/adapters
- richer concurrency
- retries/exactly-once effect policy
- distributed execution
- production planner integrations
```
