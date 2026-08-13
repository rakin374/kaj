# Agentic Kaj — Checkpoint 6: Capabilities

**Track:** Agentic Kaj  
**Checkpoint:** 6  
**Recommended path:** `dev/plans/agentic/checkpoint-6-capabilities.md`

---

# Goal

Implement Agentic Kaj's typed host capability system.

Authoritative semantics:

```text
docs/agentic/capabilities.md
```

This checkpoint builds on Agentic Checkpoints 1–5.

---

# Scope

Implement:

```text
capability keyword
capability declarations
typed capability operation signatures
use Capability as alias
task-local capability bindings
host capability registry
host adapter interface
capability instance identity/binding
operation-level grants
typed invocation
typed host result conversion
waiting_for_capability lifecycle state
CapabilityRequestId
asynchronous capability suspension/resume
persistent capability binding descriptors
restore-time rebinding
uncertain capability call state
diagnostics
tests
docs integration
```

Do not implement browser-specific language semantics.

---

# Frozen Syntax

Capability declaration:

```kaj
capability Browser {
    fn observe() -> Result<PageObservation, BrowserError>
    fn navigate(url: String) -> Result<None, BrowserError>
}
```

Task requirement:

```kaj
use Browser as browser
```

Operation call:

```kaj
browser.navigate("https://example.com")
```

---

# Declaration Rules

Capability declarations:

```text
module-level only
nominal
signatures only
no operation bodies
operation names unique within capability
parameter types explicit
return type explicit
```

Reject nested capability declarations.

---

# `use` Rules

`use` declarations:

```text
direct task body only
bind capability type to local alias
do not grant authority
require host binding before execution/resume
```

Example:

```kaj
task Example() -> None {
    use Browser as browser
    ...
}
```

Allow multiple aliases and multiple instances of the same capability type.

---

# Function Restrictions

Freeze:

```text
fn cannot declare use
fn cannot directly receive/use capability instance
task contracts cannot call capabilities
task steps may use task capability aliases
```

Keep Pure Kaj functions below the Agentic effect boundary.

---

# AST

Add explicit source representation conceptually:

```text
CapabilityDeclaration
CapabilityOperationSignature
UseCapabilityDeclaration
CapabilityMemberCall
```

or reuse member/call AST where appropriate while preserving semantic distinction.

Runtime binding/grant/request state must not appear in source AST JSON.

---

# AST JSON

Serialize deterministically:

```text
capability declaration name
operation signatures
use capability type
use alias
source spans
```

Do not serialize:

```text
host adapter
host binding ID
granted operation set
CapabilityRequestId
waiting_for_capability
runtime response
```

---

# Parser

Add reserved words:

```text
capability
use
as
```

if `as` is not already reserved.

Parse:

```kaj
capability Name {
    fn op(...) -> Type
}
```

No body after operation signature.

Parse:

```kaj
use CapabilityName as alias
```

only as direct task structure.

---

# Name Resolution

Resolve:

```text
capability type names
types used by capability operation signatures
task-local aliases from use
member operations on capability aliases
```

Capability alias is not an ordinary mutable value.

Reject duplicate aliases in one task.

Reject unknown capability type.

---

# Type Checking

For a capability call:

```kaj
browser.navigate(url)
```

validate:

```text
browser alias exists
alias type is Browser
Browser defines navigate
argument count
argument names
argument types
return type
```

Capability operation calls produce the declared Kaj return type.

---

# Runtime Capability Registry

Introduce a host-facing registry conceptually:

```text
CapabilityRegistry
    register_type(...)
    bind(task_id, alias, instance)
    resolve(task_id, alias)
    invoke(...)
```

Exact organization may differ.

The runtime must distinguish:

```text
capability type
host capability implementation
task-specific capability binding
```

---

# Host Adapter Interface

Provide a generic host adapter interface.

Conceptually:

```text
CapabilityAdapter
    capability_type
    host_binding_id
    granted_operations
    invoke(operation, arguments)
```

Do not hardcode browser/filesystem/robot concepts into the generic runtime.

---

# Host Registration

At task start:

```text
resolve task requirements
↓
host supplies matching bindings
↓
validate capability types/grants
↓
task may enter ready/running
```

If a required binding is absent:

```text
task must not start normal execution
```

Use structured capability-binding failure.

---

# Operation-Level Grants

A task binding may authorize only a subset of declared operations.

Before invocation:

```text
operation exists in capability declaration
↓
operation included in runtime grant
↓
invoke adapter
```

Denied operation must produce no host side effect.

---

# Host Value Conversion

Arguments:

```text
Kaj values
↓
adapter-safe host representation
```

Results:

```text
host result
↓
validated canonical Kaj value
```

Preserve:

```text
Decimal exactness
nominal type identity
typed map keys
structured Result/Optional/enums/records/newtypes
```

Do not leak arbitrary host objects.

---

# Lifecycle

Add:

```text
WAITING_FOR_CAPABILITY
```

Allowed transitions:

```text
RUNNING -> WAITING_FOR_CAPABILITY
WAITING_FOR_CAPABILITY -> RUNNING
WAITING_FOR_CAPABILITY -> FAILED
WAITING_FOR_CAPABILITY -> CANCELLED
```

If capability result is immediately available, the runtime may remain `RUNNING`.

---

# Pending Capability Requests

Introduce:

```text
CapabilityRequestId
CapabilityRequest
```

Conceptually:

```text
CapabilityRequest
    id
    task_id
    alias
    capability_type
    operation
    arguments
    expected_return_type
    status
```

Only one blocking suspension point need be active per single-threaded task execution.

---

# Asynchronous Completion API

Provide host/runtime API conceptually:

```text
complete_capability_request(
    task_id,
    request_id,
    result
)

fail_capability_request(
    task_id,
    request_id,
    failure
)
```

Validate task/request identity and expected return type.

Reject stale/duplicate completions.

---

# Resume Semantics

After valid host result:

```text
WAITING_FOR_CAPABILITY -> RUNNING
```

resume exactly after the suspended capability call.

Do not re-invoke the operation.

The containing step remains `RUNNING` until its body completes.

---

# Persistence Integration

Extend TaskSnapshot with durable capability state.

Persist task binding descriptors:

```text
capability type
alias
host_binding_id
granted operation metadata if required
```

Do not persist adapter objects.

Pending request snapshot includes:

```text
CapabilityRequestId
binding descriptor
operation
arguments
expected return type
request status
continuation
```

---

# Restore-Time Rebinding

On restore:

```text
load task
↓
read capability binding descriptors
↓
ask host registry/resolver for matching instances
↓
validate grants
↓
rebind
```

If rebinding fails:

```text
task does not resume
```

Do not substitute unrelated capability instance.

---

# Crash / Indeterminate Requests

If crash occurs after dispatching a host request but before durable completion is known, mark request:

```text
indeterminate
```

or equivalent.

Do not blindly replay an effectful operation.

Host adapter/runtime must explicitly:

```text
reconcile
confirm completion
retry if safe
or fail
```

No automatic exactly-once guarantee.

---

# Idempotency Hooks

The generic runtime may allow adapters to supply metadata such as:

```text
retry_safe
idempotency_key
reconcile(request_id)
```

Do not add Kaj source syntax for this yet.

This is host/runtime metadata only.

---

# Diagnostics

Add/reuse stable diagnostics for:

```text
capability declaration outside module
capability operation body present
duplicate capability name
duplicate operation
unknown capability type
use outside task
duplicate capability alias
unknown capability alias
unknown capability operation
capability argument mismatch
capability return mismatch from host
missing required capability
denied capability operation
capability binding mismatch
stale capability request
duplicate capability completion
capability rebind failure
indeterminate capability request
capability in fn
capability in contract
```

Suggested names if conventions permit:

```text
CAPABILITY_DUPLICATE_NAME
CAPABILITY_DUPLICATE_OPERATION
CAPABILITY_UNKNOWN_TYPE
CAPABILITY_USE_OUTSIDE_TASK
CAPABILITY_DUPLICATE_ALIAS
CAPABILITY_UNKNOWN_ALIAS
CAPABILITY_UNKNOWN_OPERATION
CAPABILITY_NOT_PROVIDED
CAPABILITY_OPERATION_DENIED
CAPABILITY_ARGUMENT_MISMATCH
CAPABILITY_RETURN_MISMATCH
CAPABILITY_BINDING_MISMATCH
CAPABILITY_REQUEST_NOT_FOUND
CAPABILITY_REQUEST_STALE
CAPABILITY_REQUEST_ALREADY_COMPLETED
CAPABILITY_REBIND_FAILED
CAPABILITY_REQUEST_INDETERMINATE
CAPABILITY_NOT_ALLOWED_IN_FUNCTION
CAPABILITY_NOT_ALLOWED_IN_CONTRACT
```

Follow existing diagnostic naming conventions where they differ.

---

# Reference Mock Capability

Add at least one generic mock/test capability.

Example:

```kaj
capability Counter {
    fn read() -> Int
    fn add(amount: Int) -> Int
}
```

Use a host-side test adapter to validate:

```text
binding
typed invocation
grant denial
sync completion
async completion
persistence/rebind
```

Do not make Browser the first required implementation if that couples Kaj tests to Chalok.

---

# Required Tests

Syntax/parser:

```text
valid capability declaration
multiple operations
operation parameters
operation return type
operation body rejected
nested declaration rejected
use valid in task
use in fn rejected
use nested in step/if rejected if direct-task-only
duplicate alias rejected
```

Resolution/type:

```text
capability type resolves
signature types resolve
alias resolves
member operation resolves
unknown operation rejected
argument count/type mismatch
return type propagated
```

Host binding:

```text
required capability provided
missing capability blocks start
two tasks receive distinct instances
two aliases same type receive distinct instances
binding scoped to task
```

Grants:

```text
allowed operation executes
denied operation does not invoke adapter
planner/source cannot expand grant through runtime API
```

Sync/async:

```text
sync result
async request -> WAITING_FOR_CAPABILITY
valid completion -> RUNNING
step remains RUNNING while waiting
stale request rejected
duplicate completion rejected
wrong return type rejected
```

Persistence:

```text
binding descriptor persisted
native adapter not serialized
restore rebind success
restore rebind failure
pending request persisted
CapabilityRequestId survives restart
```

Crash safety:

```text
indeterminate request represented
effectful request not blindly replayed
retry-safe adapter path works if implemented
```

Security:

```text
fn cannot use capability
contracts cannot use capability
task cannot access another task binding
unknown host capability not discoverable
```

Regression:

```text
Pure Kaj
Agentic Checkpoints 1–5
Checkpoint 6
mkdocs build --strict
```

---

# Out of Scope

Do not implement:

```text
standard Browser capability package
Chalok adapter
filesystem capability package
robot capability package
network capability package
task composition
TaskHandle
waiting_for_task
planner
LLM integration
plan blocks
AST patches
replanning
capability discovery
dynamic capability acquisition
source-level idempotency syntax
exactly-once external side effects
distributed capability routing
```

---

# Definition of Done

```text
[ ] capability declarations parse
[ ] capability operations are signatures only
[ ] capability types are nominal
[ ] use Capability as alias parses
[ ] use restricted to task scope
[ ] fn capability use rejected
[ ] contract capability use rejected

[ ] AST support exists
[ ] AST JSON deterministic
[ ] formatter canonical/idempotent

[ ] capability type/member resolution works
[ ] operation arguments type-check
[ ] return type propagates

[ ] host CapabilityRegistry exists
[ ] generic adapter interface exists
[ ] task-specific bindings exist
[ ] instance scoping enforced
[ ] operation-level grants enforced

[ ] host arguments/results use Kaj value conversion
[ ] host return type validated
[ ] native objects do not leak

[ ] WAITING_FOR_CAPABILITY implemented
[ ] CapabilityRequestId implemented
[ ] async suspension/resume works
[ ] stale/duplicate completion rejected
[ ] step remains running while waiting

[ ] binding descriptors persist
[ ] adapter objects do not persist
[ ] restore-time rebinding works
[ ] missing rebind blocks resume

[ ] indeterminate crash-time request represented
[ ] effectful request not blindly replayed

[ ] generic mock capability tests pass

[ ] Pure Kaj suite passes
[ ] Agentic Checkpoints 1–5 pass
[ ] Checkpoint 6 tests pass
[ ] mkdocs build --strict passes
```

---

# Completion Report

```text
Agentic Kaj Checkpoint 6 — Capabilities

Status:
COMPLETE / INCOMPLETE

Files changed:
- ...

Syntax:
- capability declaration: PASS/FAIL
- operation signatures: PASS/FAIL
- use/as: PASS/FAIL
- formatter: PASS/FAIL
- AST JSON: PASS/FAIL

Typing:
- capability resolution: PASS/FAIL
- alias resolution: PASS/FAIL
- operation resolution: PASS/FAIL
- argument typing: PASS/FAIL
- return typing: PASS/FAIL

Runtime:
- CapabilityRegistry: PASS/FAIL
- adapter interface: PASS/FAIL
- task-scoped binding: PASS/FAIL
- operation grants: PASS/FAIL
- Kaj/host value conversion: PASS/FAIL

Async:
- waiting_for_capability: PASS/FAIL
- CapabilityRequestId: PASS/FAIL
- suspend/resume: PASS/FAIL
- stale completion rejection: PASS/FAIL
- duplicate completion rejection: PASS/FAIL

Persistence:
- binding descriptor: PASS/FAIL
- native adapter excluded: PASS/FAIL
- restore rebind: PASS/FAIL
- pending request persistence: PASS/FAIL
- indeterminate request handling: PASS/FAIL

Security:
- fn cannot use capability: PASS/FAIL
- contracts cannot use capability: PASS/FAIL
- cross-task isolation: PASS/FAIL
- denied operation has no side effect: PASS/FAIL

Regression:
- Pure Kaj: PASS/FAIL
- Agentic Checkpoints 1–5: PASS/FAIL
- Agentic Checkpoint 6: PASS/FAIL
- mkdocs build --strict: PASS/FAIL

Deferred intentionally:
- concrete browser/filesystem/robot packages
- task composition
- planner
- replanning
- exactly-once effects

Known issues:
- ...
```
