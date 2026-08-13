# Agentic Kaj — Checkpoint 3: Task Contracts

**Track:** Agentic Kaj  
**Checkpoint:** 3  
**Recommended path:** `dev/plans/agentic/checkpoint-3-task-contracts.md`

---

# Goal

Implement the initial Agentic Kaj task contract system:

```text
goal
require
invariant
success
```

Authoritative public semantics:

```text
docs/agentic/task-contracts.md
```

This checkpoint builds on:

```text
Agentic Checkpoint 1 — Tasks
Agentic Checkpoint 2 — Steps and Task Lifecycle
```

---

# Scope

Implement:

```text
goal keyword/clause
require keyword/clause
invariant keyword/clause
success keyword/clause

task-level placement rules
AST nodes
AST JSON
formatter
name resolution
type checking
purity restrictions
runtime contract representation
require evaluation
invariant evaluation
success evaluation
contract-related lifecycle transitions
contract diagnostics
tests
docs integration
```

Do not implement planner behavior merely because `goal` exists.

---

# Frozen Semantics

## Goal

```kaj
goal "Find {query} for no more than {max_price}"
```

Rules:

```text
optional
at most one
must type-check as String
task-level only
immutable
human-readable/runtime-inspectable
future planner-visible
not proof of completion
```

## Require

```kaj
require {
    max_price > 0
}
```

Rules:

```text
zero or more
must evaluate to Bool
pure
source-order evaluation
evaluated before ready/running
false -> task failed
```

## Invariant

```kaj
invariant {
    total_spend <= max_price
}
```

Rules:

```text
zero or more
must evaluate to Bool
pure
source-order evaluation
checked:
    before execution
    after each completed step
    before task completion
    before resume from paused
false -> task failed
```

## Success

```kaj
success(result: Product) {
    result.price <= max_price
}
```

Rules:

```text
zero or one
must evaluate to Bool
pure
for non-None task:
    success parameter type must equal task return type
for None task:
    parameterless success allowed
evaluated after return value and final invariants
false -> task failed
```

No success clause means normal valid return is sufficient for completion.

---

# Parser / Placement

Add reserved syntax for:

```text
goal
require
invariant
success
```

Contract clauses may appear only directly inside task bodies.

Reject them inside:

```text
fn
step
if
loop
match
nested block
```

Contract clauses are task structure, not ordinary statements.

The implementation may normalize/collect clauses independently of textual position, but duplicate/ordering behavior must remain deterministic.

---

# AST

Add explicit nodes or equivalent structures:

```text
GoalClause
RequireClause
InvariantClause
SuccessClause
```

Recommended TaskDeclaration structure conceptually:

```text
TaskDeclaration
    name
    parameters
    return_type
    goal
    requirements
    invariants
    success
    executable_body / steps
```

Do not encode runtime pass/fail outcomes into the source AST.

---

# AST JSON

Serialize contract declarations deterministically.

Do not serialize runtime data such as:

```text
requirement passed/failed
invariant passed/failed
success passed/failed
contract runtime failure
```

Preserve existing AST JSON strictness and span policy.

---

# Formatter

Canonical examples:

```kaj
goal "Research {topic}"
```

```kaj
require {
    budget > 0
}
```

```kaj
invariant {
    total <= budget
}
```

```kaj
success(result: Product) {
    result.price <= budget
}
```

Use existing indentation, wrapping, expression formatting, and idempotence rules.

Do not add formatter configuration.

---

# Name Resolution

Contract expressions resolve within the containing task's semantic environment.

Allow:

```text
task parameters
module-level values permitted by existing rules
pure fn calls
task-local state when semantically available
success result parameter
```

The success result parameter is scoped only to the success clause.

Contract clause names are not ordinary bindings.

---

# Type Checking

Enforce:

```text
goal -> String
require -> Bool
invariant -> Bool
success -> Bool
```

For success:

```text
non-None task:
    result parameter required
    parameter type == task declared return type

None task:
    parameterless success allowed
```

Reject duplicate goal/success clauses statically.

---

# Purity

Checkpoint 3 must introduce a minimal purity rule for contract expressions.

At minimum, contract clauses may contain only operations that cannot cause Agentic effects.

Since capabilities/human interaction/task composition do not exist yet, enforce purity against current constructs and future-proof the semantic representation.

Allow:

```text
ordinary expressions
local reads
pure fn calls
comparisons
Boolean logic
collection reads
record/enum/newtype construction where pure
```

Disallow any construct already considered runtime/agentic control rather than expression evaluation.

Do not over-design a full effect system yet.

If function purity is not explicitly represented today, use a conservative rule for calls from contract expressions and document any temporary limitation.

---

# Runtime Contract Model

Extend TaskDefinition conceptually with:

```text
goal
requirements
invariants
success
```

Add runtime helpers for:

```text
evaluate_requirements
evaluate_invariants
evaluate_success
```

Each should return structured Kaj/runtime outcomes rather than raw Python Boolean/exceptions.

---

# Lifecycle Integration

Implement:

```text
TaskInstance created
↓
evaluate requirements

require violation/error:
    -> failed

all requirements pass:
    -> ready

before running:
    evaluate invariants

invariant violation/error:
    -> failed

otherwise:
    -> running
```

After each completed step:

```text
evaluate invariants
```

Before normal completion:

```text
evaluate invariants
evaluate success if present
```

Only then:

```text
completed
```

Before:

```text
paused -> running
```

re-evaluate invariants.

Cancellation remains cancellation and does not evaluate success.

---

# Contract Failure Representation

Add structured failure categories, conceptually:

```text
RequirementViolation
InvariantViolation
SuccessConditionFailed
ContractEvaluationFailure
```

Integrate with existing TaskFailure representation.

Preserve:

```text
Result.err(...) != runtime/task failure
```

---

# Diagnostics

Add/reuse stable diagnostics for:

```text
goal outside task
require outside task
invariant outside task
success outside task
invalid contract placement
duplicate goal
duplicate success
goal not String
require not Bool
invariant not Bool
success not Bool
success parameter mismatch
invalid success parameter form
impure contract expression
requirement violation
invariant violation
success condition failed
contract evaluation failure
```

Suggested names if conventions permit:

```text
TASK_DUPLICATE_GOAL
TASK_DUPLICATE_SUCCESS
TASK_CONTRACT_INVALID_PLACEMENT
TASK_GOAL_TYPE_MISMATCH
TASK_REQUIRE_TYPE_MISMATCH
TASK_INVARIANT_TYPE_MISMATCH
TASK_SUCCESS_TYPE_MISMATCH
TASK_SUCCESS_PARAMETER_MISMATCH
TASK_CONTRACT_NOT_PURE

TASK_REQUIREMENT_VIOLATED
TASK_INVARIANT_VIOLATED
TASK_SUCCESS_NOT_SATISFIED
TASK_CONTRACT_EVALUATION_FAILED
```

Reuse exact existing diagnostics when sufficient.

---

# Required Tests

Lexer/parser:

```text
goal recognized
require recognized
invariant recognized
success recognized
valid placement
invalid placement
duplicate goal
duplicate success
multiple require
multiple invariant
```

Type checking:

```text
goal String valid
goal non-String rejected
require Bool valid
require non-Bool rejected
invariant Bool valid
invariant non-Bool rejected
success Bool valid
success non-Bool rejected
success result type match
success result type mismatch
None task parameterless success
```

Runtime:

```text
requirements pass
require false -> failed
require evaluation error -> failed
invariant passes initially
invariant fails initially
invariant checked after step
invariant checked before completion
invariant checked before resume
success true -> completed
success false -> failed
success evaluation error -> failed
no success -> normal completion
```

Distinctions:

```text
Result.err + success accepts -> completed
Result.err is not runtime failure
cancelled task does not evaluate success
contract failure categories distinct
```

AST/formatter:

```text
contract AST
deterministic AST JSON
runtime outcomes absent from AST JSON
formatter canonical
formatter idempotent
parse-format-parse preservation
```

Regression:

```text
Pure Kaj full suite
Agentic Checkpoint 1
Agentic Checkpoint 2
Checkpoint 3
mkdocs build --strict
```

---

# Out of Scope

Do not implement:

```text
ask
choose
confirm
inform
handoff
waiting_for_human
persistent storage
process restart resume
capability
use
task composition
TaskHandle
planner
LLM integration
planner-visible execution integration
plan blocks
AST patching
replanning
retry syntax
distributed scheduling
```

`goal` may be stored for future planner use, but no planner runs in this checkpoint.

---

# Definition of Done

```text
[ ] goal implemented
[ ] require implemented
[ ] invariant implemented
[ ] success implemented

[ ] contract placement restricted to direct task body
[ ] duplicate goal rejected
[ ] duplicate success rejected

[ ] goal requires String
[ ] require requires Bool
[ ] invariant requires Bool
[ ] success requires Bool
[ ] success result parameter typing enforced

[ ] contract expressions obey initial purity restrictions

[ ] contract AST exists
[ ] AST JSON deterministic
[ ] runtime outcomes excluded from AST JSON
[ ] formatter canonical/idempotent

[ ] requirements evaluated before ready/running
[ ] initial invariants evaluated
[ ] invariants evaluated after completed steps
[ ] invariants evaluated before completion
[ ] invariants evaluated before resume

[ ] success evaluated before completion
[ ] success false prevents completion
[ ] missing success permits ordinary completion

[ ] structured contract failures exist
[ ] contract failures remain distinct from Result.err

[ ] Pure Kaj suite passes
[ ] Agentic Checkpoint 1 passes
[ ] Agentic Checkpoint 2 passes
[ ] Agentic Checkpoint 3 passes
[ ] mkdocs build --strict passes
```

---

# Completion Report

```text
Agentic Kaj Checkpoint 3 — Task Contracts

Status:
COMPLETE / INCOMPLETE

Files changed:
- ...

Syntax:
- goal: PASS/FAIL
- require: PASS/FAIL
- invariant: PASS/FAIL
- success: PASS/FAIL
- placement: PASS/FAIL
- formatter: PASS/FAIL
- AST JSON: PASS/FAIL

Typing:
- goal String: PASS/FAIL
- require Bool: PASS/FAIL
- invariant Bool: PASS/FAIL
- success Bool: PASS/FAIL
- success result typing: PASS/FAIL
- purity checks: PASS/FAIL

Runtime:
- requirements: PASS/FAIL
- initial invariants: PASS/FAIL
- post-step invariants: PASS/FAIL
- pre-completion invariants: PASS/FAIL
- resume invariants: PASS/FAIL
- success validation: PASS/FAIL
- structured contract failures: PASS/FAIL
- Result.err distinction: PASS/FAIL

Regression:
- Pure Kaj: PASS/FAIL
- Agentic Checkpoint 1: PASS/FAIL
- Agentic Checkpoint 2: PASS/FAIL
- Agentic Checkpoint 3: PASS/FAIL
- mkdocs build --strict: PASS/FAIL

Deferred intentionally:
- human interaction
- persistence
- capabilities
- task composition
- planner
- replanning

Known issues:
- ...
```
