# Planner Interface

The planner interface allows an external planner, such as an LLM-backed agent, to propose executable Kaj task plans without becoming the Kaj runtime itself.

The planner proposes.

Kaj validates.

The runtime executes only validated Kaj structures.

This document defines the initial planner boundary for Agentic Kaj.

---

## 1. Core principle

The planner is not the runtime.

Conceptually:

```text
task definition
task state
capability grants
task contract
        ↓
planner input
        ↓
planner proposes plan
        ↓
Kaj validates proposal
        ↓
validated plan
        ↓
Kaj runtime executes
```

The planner cannot bypass:

```text
parsing
AST validation
name resolution
type checking
task contracts
capability requirements
capability grants
runtime lifecycle rules
```

---

## 2. Planner responsibility

A planner may decide how to organize work inside explicitly plannable task regions.

It may propose:

```text
ordered steps
step labels
ordinary Kaj statements inside plan steps
function calls
capability calls already authorized by the task
human interaction already permitted by the language/runtime
child task composition already permitted by the task
```

It does not gain new authority by planning.

---

## 3. Planner independence

Kaj does not require a specific planning model.

A planner may be:

```text
LLM
deterministic algorithm
rule engine
human-authored planner
remote service
local model
```

The planner protocol must be host/model independent.

---

## 4. Planner declaration

A task opts into planning using an explicit plan region.

Initial syntax:

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

The empty source `plan` block marks a region whose executable content may be supplied by a planner.

---

## 5. One plan region

The initial model allows at most one planner-controlled `plan` region per task.

A task may still contain fixed code outside the plan region if allowed by control-flow rules.

Example:

```kaj
task Research(topic: String) -> Report {
    goal "Research {topic}"

    let normalized = normalize(topic)

    plan {
    }

    return build_report(normalized)
}
```

---

## 6. Planner-controlled region

Only the contents of the explicit `plan` region are planner-controlled.

The planner may not modify source outside that region.

Protected task structure includes:

```text
task name
task parameters
task return type
goal
require clauses
invariant clauses
success clause
capability requirements
fixed code outside plan
```

---

## 7. Capability grants are protected

The planner may use capability aliases already declared by the task.

It may not:

```text
add a new `use`
change a capability type
change a capability alias binding
expand granted operations
access another task's capability
```

Planning does not confer authority.

---

## 8. Contracts are protected

The planner cannot modify:

```text
goal
require
invariant
success
```

These are part of the task's protected contract.

---

## 9. Task signature is protected

The planner cannot modify:

```text
task name
parameter list
parameter types
return type
```

---

## 10. Planner input

The runtime sends a structured planner request.

Conceptually:

```text
PlannerRequest
    task_id
    task_definition
    goal
    requirements
    invariants
    success
    task_inputs
    current_task_state
    available capability descriptions
    granted capability operations
    available functions/types/modules
    completed steps
    current plan state
```

Only information explicitly made planner-visible by the host/runtime should be included.

---

## 11. Planner output

The planner returns a structured proposal.

The preferred interchange format is Kaj AST JSON or a dedicated planner-plan structure that maps deterministically to Kaj AST.

Conceptually:

```text
PlannerProposal
    plan steps / plan AST
    metadata
```

Free-form natural language is not executable planner output.

A host may use natural language internally, but execution requires structured Kaj.

---

## 12. AST-first planning

The planner boundary should preserve Kaj's AST-first architecture.

Preferred flow:

```text
planner
   ↓
structured Kaj AST / plan AST JSON
   ↓
schema validation
   ↓
semantic validation
   ↓
execution
```

Do not execute raw planner strings directly.

---

## 13. Planner-generated source

A host may accept planner-generated `.kaj` source as an intermediate representation only if it is parsed normally.

Flow:

```text
planner text
   ↓
Kaj parser
   ↓
AST
   ↓
same validation pipeline
```

Planner text does not bypass parsing.

---

## 14. Plan contents

The initial plan region may contain named steps.

Example proposed plan:

```kaj
plan {
    step search {
        let page = browser.observe()
    }

    step summarize {
        // ...
    }
}
```

Planner-generated steps use the same step semantics as ordinary Agentic Kaj steps.

---

## 15. Plan step names

Planner-generated step names must satisfy ordinary step naming rules.

They must be unique within the task's effective step namespace.

---

## 16. No hidden planner operations

Every planner-proposed action must correspond to valid Kaj syntax/AST.

The runtime must not support hidden model-only commands such as:

```text
CLICK_BUTTON
SEARCH_WEB
USE_TOOL
THINK
```

unless those are represented through normal Kaj capability/task constructs.

---

## 17. Validation pipeline

Every planner proposal must pass:

```text
schema validation
AST structural validation
name resolution
type checking
task-control restrictions
capability declaration checks
capability grant checks
contract protection checks
plan-region boundary checks
```

Only after validation may it become executable.

---

## 18. Validation failure

If a planner proposal is invalid, the runtime rejects it.

The task does not execute the invalid proposal.

The runtime may return structured diagnostics to the planner/host for another planning attempt.

---

## 19. Planner diagnostics

Planner-facing diagnostics should be machine-readable where practical.

Conceptually:

```text
PlannerValidationError
    diagnostic_code
    message
    span/path
    relevant symbol
```

The host may render them for humans or feed them back into a planner.

---

## 20. Planner attempt identity

Each planner request/response cycle has an opaque identity.

Conceptually:

```text
PlanningAttemptId
```

This allows:

```text
logging
persistence
stale response rejection
future replanning
```

---

## 21. Planning lifecycle state

Checkpoint 8 adds:

```text
waiting_for_planner
```

to the task lifecycle.

Relevant transitions:

```text
running -> waiting_for_planner
waiting_for_planner -> running
waiting_for_planner -> failed
waiting_for_planner -> cancelled
```

A task enters this state when it reaches an unresolved plan region and requires an external planner response.

---

## 22. Planner suspension

When execution reaches an unresolved:

```kaj
plan {
}
```

the runtime:

```text
creates PlannerRequest
assigns PlanningAttemptId
persists request state if task is persistent
transitions task to waiting_for_planner
```

The containing task/step execution continuation is preserved.

---

## 23. Planner completion

When a planner returns a proposal:

```text
waiting_for_planner
   ↓
validate proposal
```

If valid:

```text
install validated plan
task -> running
```

Execution begins at the plan region.

---

## 24. Invalid planner proposal

If the proposal fails validation:

```text
task remains waiting_for_planner
```

The planning attempt is recorded as rejected.

The host may submit another proposal.

An invalid proposal does not itself fail the task unless host policy explicitly chooses to stop planning.

---

## 25. Planner runtime failure

If the planner service itself is unavailable or irrecoverably fails, the host may:

```text
retry planning
cancel task
fail task with structured planner failure
```

The language does not silently treat planner failure as task-domain `Result.err`.

---

## 26. Stale planner responses

A planner response must reference the active:

```text
task ID
PlanningAttemptId
```

A stale response for an older attempt must be rejected.

It must never replace a newer accepted plan.

---

## 27. Duplicate planner responses

Once a planning attempt is accepted or rejected as terminal for that attempt, duplicate responses must not be applied.

---

## 28. Planner and persistence

Persist enough planning state to survive restart.

At minimum:

```text
PlanningAttemptId
planner request
planner status
accepted plan if any
continuation
validation diagnostics if useful
```

A task restored in:

```text
waiting_for_planner
```

remains waiting for the same active planning attempt unless host policy intentionally creates a new one.

---

## 29. Accepted plan persistence

Once a plan is accepted, persist the exact validated plan representation.

Do not ask the planner to regenerate the plan merely because the runtime restarted.

---

## 30. Plan fingerprint

The runtime should compute a deterministic fingerprint of the accepted plan.

This helps:

```text
persistence validation
logging
future controlled replanning
```

---

## 31. Planner visibility

The host/runtime controls what task/runtime information is exposed to the planner.

The planner should receive enough structured context to make a valid plan, but not arbitrary host secrets.

---

## 32. Capability descriptions

Planner input may include capability schemas.

Example:

```text
Browser
    observe() -> Result<PageObservation, BrowserError>
    navigate(String) -> Result<None, BrowserError>
```

It may also include which operations are actually granted.

This enables the planner to construct valid calls without expanding authority.

---

## 33. Pure Kaj functions

Planner input may expose available function signatures and relevant type definitions.

The planner may call only functions that ordinary Kaj code could call from the plan region.

---

## 34. Child tasks

Planner-generated code may use:

```text
start
await
```

only if task composition is already valid in that context.

The planner does not receive special task-composition privileges.

---

## 35. Human interaction

Planner-generated code may use:

```text
ask
choose
confirm
inform
handoff
```

subject to existing Agentic Kaj rules.

---

## 36. Planner may not bypass contracts

Even a valid accepted plan executes under the task's existing:

```text
requirements
invariants
success
```

The runtime remains responsible for contract enforcement.

---

## 37. Planner may not claim success

A planner cannot mark the task completed merely by saying it succeeded.

Completion still requires:

```text
normal Kaj return
final invariants
success condition if present
```

---

## 38. Planner metadata

Planner proposals may carry non-semantic metadata such as:

```text
model name
planner version
reason code
cost/latency metrics
trace IDs
```

This metadata is runtime/host information.

It does not alter Kaj semantics.

---

## 39. Chain of thought is not required

The planner protocol does not require hidden reasoning or chain-of-thought.

The executable artifact is the structured plan.

A planner may optionally provide a concise rationale for host/UI use, but runtime correctness does not depend on it.

---

## 40. Controlled replanning

The planner interface supports initial planning directly.

After execution begins, only future planner-owned work may be revised at a safe
boundary. The rules are defined by [Controlled Replanning](controlled-replanning.md).

---

## 41. No planner self-modification

The planner may not modify:

```text
planner interface rules
validation rules
runtime policy
capability grants
task contracts
protected source
```

---

## 42. Determinism of accepted plan

Given the same accepted plan AST, Kaj runtime execution follows ordinary deterministic semantics subject to external capability/human/task outcomes.

The planner's probabilistic nature does not change Kaj's validation semantics.

---

## 43. Planner host interface

The runtime should expose a generic planner adapter.

Conceptually:

```text
PlannerAdapter
    request_plan(PlannerRequest)
```

It may return immediately or asynchronously.

The generic Kaj runtime must not depend on OpenAI, Anthropic, or any particular vendor SDK.

---

## 44. Asynchronous planner requests

A planner adapter may return a pending request.

The runtime then uses:

```text
waiting_for_planner
PlanningAttemptId
```

until completion.

---

## 45. Synchronous planner adapters

A deterministic/local planner may return a proposal immediately.

In that case the runtime may validate it without visibly remaining in `waiting_for_planner`.

The same semantic validation applies.

---

## 46. Planner request cancellation

Cancelling a task while:

```text
waiting_for_planner
```

cancels/invalidates the active planning attempt.

Later planner responses for that attempt are stale.

---

## 47. Parent/child interaction

A child task may independently wait for its planner while its parent waits for the child.

Example:

```text
parent = waiting_for_task
child = waiting_for_planner
```

Task identities remain distinct.

---

## 48. Persistence compatibility

Restoring an accepted plan requires compatibility with:

```text
task definition fingerprint
plan fingerprint
snapshot version
```

If protected task structure changed incompatibly, ordinary persistence rules reject resume.

---

## 49. Security principle

Planner output is untrusted input until validated.

Even if the planner runs inside the same process, Kaj must treat proposals as externally supplied structured code.

---

## 50. Summary

Checkpoint 8 freezes:

```text
planner is optional and external to runtime
planner proposes; Kaj validates; runtime executes

task explicitly marks one plan region
only plan-region contents are planner-controlled

protected:
    task signature
    goal
    require
    invariant
    success
    capability requirements/grants
    fixed source outside plan

planner output must become structured Kaj AST
raw natural language is not directly executable

every proposal passes normal Kaj validation
invalid proposal is rejected without execution

waiting_for_planner is a lifecycle state
PlanningAttemptId identifies each planning cycle
stale/duplicate planner responses are rejected

accepted plans are persisted
accepted plans are not regenerated on restart

planner may use only existing Kaj authority
planner cannot self-authorize
planner cannot claim task success

no controlled replanning yet
```
