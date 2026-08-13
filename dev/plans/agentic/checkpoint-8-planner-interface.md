# Agentic Kaj — Checkpoint 8: Planner Interface

**Track:** Agentic Kaj  
**Checkpoint:** 8  
**Recommended path:** `dev/plans/agentic/checkpoint-8-planner-interface.md`

---

# Goal

Implement a generic, validated planner boundary for Agentic Kaj.

Authoritative semantics:

```text
docs/agentic/planner-interface.md
```

This checkpoint builds on Agentic Checkpoints 1–7.

The planner is optional and external.

Do not embed an LLM vendor into the Kaj runtime.

---

# Scope

Implement:

```text
plan region syntax
protected task-region semantics
PlannerRequest
PlannerProposal
PlanningAttemptId
PlannerAdapter interface
waiting_for_planner lifecycle state
planner suspension/resume
structured proposal validation
planner-facing diagnostics
stale/duplicate response rejection
accepted-plan installation
accepted-plan persistence
plan fingerprinting
tests
docs integration
```

---

# Frozen Syntax

Initial task plan region:

```kaj
task Research(topic: String) -> Report {
    goal "Research {topic}"

    plan {
    }

    success(result: Report) {
        result.topic == topic
    }
}
```

Checkpoint 8 permits at most:

```text
one plan block per task
```

---

# Protected Regions

Planner may modify/provide only contents of:

```text
plan { ... }
```

Planner may not modify:

```text
task name
task parameters
task parameter types
return type
goal
require
invariant
success
use declarations
capability grants
fixed source outside plan
```

Enforce this structurally, not by prompt instruction.

---

# Plan Contents

The planner may propose ordinary valid task-body structures allowed inside the plan region.

At minimum support:

```text
named steps
ordinary task statements
function calls
capability calls
human interaction
start/await
control flow where valid
```

All existing semantic restrictions remain in force.

---

# Parser / AST

Add:

```text
plan
```

as a reserved keyword if not already present.

Introduce an explicit AST node conceptually:

```text
PlanRegion
    body
    span
```

Source plan body may initially be empty or contain fixed plan code if the implementation supports it, but planner-controlled replacement must be explicit and bounded.

Do not encode runtime planner attempts in source AST.

---

# Planner Proposal Representation

Prefer:

```text
structured Kaj AST / plan-region AST JSON
```

The runtime may also accept planner-generated Kaj source as an intermediate input, but it must go through the normal parser.

Do not execute free-form planner strings.

---

# Planner Request

Introduce a structured request conceptually:

```text
PlannerRequest
    task_id
    planning_attempt_id
    task_definition_identity
    task_inputs
    goal
    requirements
    invariants
    success
    available_symbols
    available_types
    capability_contracts
    granted_capability_operations
    completed_steps
    current_runtime_state
```

Only include fields actually needed by the planner and safe for host exposure.

---

# PlanningAttemptId

Every unresolved planner request gets a unique opaque:

```text
PlanningAttemptId
```

Use it to:

```text
correlate response
reject stale response
persist wait state
audit accepted/rejected proposals
```

---

# Planner Adapter

Add a generic host/runtime interface conceptually:

```text
PlannerAdapter
    request_plan(request)
```

Support:

```text
synchronous proposal
asynchronous/pending proposal
structured planner failure
```

Do not import vendor-specific AI SDKs into core Kaj.

---

# Lifecycle

Add:

```text
WAITING_FOR_PLANNER
```

Allowed transitions:

```text
RUNNING -> WAITING_FOR_PLANNER
WAITING_FOR_PLANNER -> RUNNING
WAITING_FOR_PLANNER -> FAILED
WAITING_FOR_PLANNER -> CANCELLED
```

If a synchronous planner returns immediately, the runtime may avoid an externally observable wait while preserving the same validation semantics.

---

# Validation Pipeline

Every planner proposal must pass:

```text
proposal schema validation
AST structural validation
plan-region boundary validation
name resolution
type checking
task-effect restrictions
function/task composition restrictions
capability type checks
capability grant checks
contract protection checks
protected source comparison
```

Then and only then may it be installed.

Reuse existing Kaj analysis pipeline rather than building a second planner-only type system.

---

# Capability Grant Validation

The planner may call only operations that:

```text
exist on declared capability type
and
are granted to the current task binding
```

Reject a proposal that attempts to use:

```text
undeclared capability
different alias
new use declaration
denied operation
other task binding
```

No host side effect occurs during validation.

---

# Contract Protection

Ensure planner proposal cannot add/remove/modify:

```text
goal
require
invariant
success
```

Also reject contract clauses inside the plan region if the authoritative semantics prohibit them there.

---

# Task Signature Protection

Planner proposal must not modify:

```text
task declaration name
parameters
return type
```

Prefer accepting only plan-region AST rather than a whole modified TaskDeclaration. This structurally minimizes attack surface.

---

# Planner Diagnostics

Return validation errors in structured form.

Conceptually:

```text
PlannerValidationDiagnostic
    code
    message
    span/path
```

Reuse existing compiler diagnostics where possible.

A host may feed these diagnostics into another planning attempt.

---

# Invalid Proposal Behavior

Freeze:

```text
invalid planner proposal:
    does not execute
    does not fail task automatically
    task remains WAITING_FOR_PLANNER
    attempt is marked rejected
```

Host may submit a new planning attempt.

If host policy chooses to stop, it may fail/cancel separately.

---

# Accepted Proposal

When valid:

```text
canonicalize/validate plan
compute plan fingerprint
persist accepted plan
bind plan to task instance
task -> RUNNING
continue at plan region
```

Do not invoke planner again merely because the plan begins executing.

---

# Stale / Duplicate Responses

Require response correlation to:

```text
TaskId
PlanningAttemptId
```

Reject:

```text
unknown attempt
wrong task
stale older attempt
duplicate response
response after task cancellation
response after plan already accepted
```

---

# Persistence

Extend TaskSnapshot with planner runtime data:

```text
active_planning_attempt_id
planner_request metadata/state
accepted_plan
accepted_plan_fingerprint
planner_status
validation diagnostics if useful
```

Do not persist live planner adapter objects.

---

# Restore

If restored state is:

```text
WAITING_FOR_PLANNER
```

restore the same active PlanningAttemptId.

The host may:

```text
continue awaiting external response
resubmit same semantic request to planner infrastructure
explicitly invalidate and create a new planning attempt
```

Do not silently accept a response for an invalidated attempt.

---

# Accepted Plan Restore

If a plan was already accepted:

```text
restore exact accepted plan
validate snapshot/task compatibility
continue execution
```

Do not regenerate the plan.

---

# Plan Fingerprint

Compute a deterministic fingerprint from canonical validated plan AST.

Use for:

```text
persistence
auditing
future replanning checkpoint
```

Exact hash algorithm is implementation detail.

---

# Planner Visibility

Expose structured schemas/signatures rather than Python implementation objects.

Examples:

```text
functions:
    normalize(String) -> String

capability:
    Browser.observe() -> Result<PageObservation, BrowserError>

granted:
    Browser.observe
    Browser.navigate
```

Do not expose arbitrary host internals.

---

# No Vendor-Specific Integration

Checkpoint 8 should include:

```text
mock deterministic planner adapter
```

for tests.

Optional examples may demonstrate how a host would wrap an LLM, but do not add OpenAI/Anthropic/etc. as required runtime dependencies.

---

# No Chain-of-Thought Requirement

Do not require the planner to return internal reasoning.

Planner proposal requires:

```text
structured executable plan
```

Optional concise metadata/rationale is non-semantic.

---

# Runtime / Scheduler Integration

When a parent awaits a child that waits for planner:

```text
parent = WAITING_FOR_TASK
child = WAITING_FOR_PLANNER
```

Ensure scheduler wakeups remain task-scoped.

---

# Diagnostics

Add/reuse stable diagnostics for:

```text
duplicate plan region
plan outside task
invalid planner proposal
planner changed protected structure
planner added capability requirement
planner used denied capability operation
planner type/name error
unknown planning attempt
stale planning attempt
duplicate planner response
planner response wrong task
planner unavailable/failure
accepted plan incompatible on restore
```

Suggested codes if conventions permit:

```text
TASK_DUPLICATE_PLAN_REGION
TASK_PLAN_OUTSIDE_TASK
PLANNER_PROPOSAL_INVALID
PLANNER_PROTECTED_REGION_MODIFIED
PLANNER_CAPABILITY_ESCALATION
PLANNER_CAPABILITY_OPERATION_DENIED
PLANNER_ATTEMPT_NOT_FOUND
PLANNER_ATTEMPT_STALE
PLANNER_RESPONSE_DUPLICATE
PLANNER_RESPONSE_TASK_MISMATCH
PLANNER_RUNTIME_FAILED
PLANNER_PLAN_INCOMPATIBLE
```

Use repository diagnostic naming conventions where appropriate.

---

# Reference Planner

Add a deterministic mock planner for tests.

Example behavior:

```text
given plan request for TestTask
return predefined valid plan AST
```

Also support fixtures for:

```text
invalid syntax
unknown symbol
type mismatch
capability escalation
denied operation
protected region modification
async completion
stale response
```

---

# Required Tests

Syntax/AST:

```text
plan region valid
plan outside task rejected
duplicate plan region rejected
PlanRegion AST
deterministic AST JSON
formatter idempotence
```

Planner request:

```text
TaskId included
PlanningAttemptId unique
goal visible
contracts visible
capability schemas visible
grants visible
task inputs visible
protected source represented correctly
```

Valid proposal:

```text
valid step plan accepted
function call plan accepted
granted capability call accepted
human interaction allowed
start/await allowed
accepted plan executes
```

Invalid proposal:

```text
unknown name rejected
type mismatch rejected
new use rejected
denied capability operation rejected
goal modification rejected
require modification rejected
invariant modification rejected
success modification rejected
task signature modification rejected
fixed source modification rejected
```

Lifecycle:

```text
unresolved plan -> WAITING_FOR_PLANNER
valid response -> RUNNING
invalid response -> remains WAITING_FOR_PLANNER
task cancellation invalidates planning attempt
planner failure may fail task through host policy/runtime API
```

Stale/duplicate:

```text
wrong TaskId rejected
stale attempt rejected
duplicate response rejected
response after cancellation rejected
```

Persistence:

```text
PlanningAttemptId persists
waiting planner restores
accepted plan persists
plan fingerprint persists
accepted plan restored without replanning
```

Task composition:

```text
child waiting_for_planner
parent waiting_for_task
child accepted plan eventually wakes parent on completion
```

Regression:

```text
Pure Kaj
Agentic Checkpoints 1–7
Checkpoint 8
mkdocs build --strict
```

---

# Out of Scope

Do not implement:

```text
controlled replanning
plan patching during execution
automatic planner invocation after step failure
planner changes to completed steps
planner changes to contracts
planner changes to capabilities/grants
self-modifying planner policy
vendor-specific LLM SDK dependency
distributed planner service requirement
planner memory system
chain-of-thought storage
```

---

# Definition of Done

```text
[ ] plan region syntax implemented
[ ] one plan region per task enforced
[ ] planner-controlled boundary explicit
[ ] protected task structure enforced

[ ] PlannerRequest exists
[ ] PlannerProposal/plan AST input exists
[ ] PlanningAttemptId exists
[ ] generic PlannerAdapter exists
[ ] deterministic mock planner exists

[ ] WAITING_FOR_PLANNER implemented
[ ] planner suspension works
[ ] valid proposal resumes execution
[ ] invalid proposal stays waiting
[ ] stale/duplicate responses rejected

[ ] normal Kaj parser/analyzer reused
[ ] name/type checking enforced
[ ] capability grants enforced
[ ] planner cannot add `use`
[ ] contracts/signature/fixed source protected

[ ] accepted plan fingerprinted
[ ] accepted plan persisted
[ ] waiting planner state persisted
[ ] accepted plan restored without replanning

[ ] runtime does not require LLM vendor SDK
[ ] raw natural language is not directly executable

[ ] Pure Kaj suite passes
[ ] Agentic Checkpoints 1–7 pass
[ ] Checkpoint 8 tests pass
[ ] mkdocs build --strict passes
```

---

# Completion Report

```text
Agentic Kaj Checkpoint 8 — Planner Interface

Status:
COMPLETE / INCOMPLETE

Files changed:
- ...

Syntax:
- plan region: PASS/FAIL
- one-per-task rule: PASS/FAIL
- AST JSON: PASS/FAIL
- formatter: PASS/FAIL

Planner model:
- PlannerRequest: PASS/FAIL
- PlannerProposal: PASS/FAIL
- PlanningAttemptId: PASS/FAIL
- PlannerAdapter: PASS/FAIL
- mock planner: PASS/FAIL

Validation:
- parser/AST validation: PASS/FAIL
- name resolution: PASS/FAIL
- type checking: PASS/FAIL
- protected contracts: PASS/FAIL
- protected signature/source: PASS/FAIL
- capability escalation blocked: PASS/FAIL
- denied operation blocked: PASS/FAIL

Lifecycle:
- waiting_for_planner: PASS/FAIL
- valid proposal resume: PASS/FAIL
- invalid proposal remains waiting: PASS/FAIL
- stale response rejection: PASS/FAIL
- duplicate response rejection: PASS/FAIL

Persistence:
- attempt state persisted: PASS/FAIL
- accepted plan persisted: PASS/FAIL
- plan fingerprint: PASS/FAIL
- restore without replanning: PASS/FAIL

Regression:
- Pure Kaj: PASS/FAIL
- Agentic Checkpoints 1–7: PASS/FAIL
- Agentic Checkpoint 8: PASS/FAIL
- mkdocs build --strict: PASS/FAIL

Deferred intentionally:
- controlled replanning
- plan patching
- vendor-specific LLM integration

Known issues:
- ...
```
