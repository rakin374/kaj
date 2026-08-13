# Capabilities

Capabilities are Agentic Kaj's typed interface to the outside world.

They let a task request access to host-provided functionality such as:

```text
browser
filesystem
robotics
audio
network services
application APIs
```

A capability declaration defines what operations exist.

A host-provided capability instance defines how those operations are actually performed.

A Kaj task may require a capability, but Kaj source does not grant itself authority.

---

## 1. Core model

Capabilities separate:

```text
what Kaj code may call
```

from:

```text
how the host implements it
```

Conceptually:

```text
Kaj task
   ↓
capability contract
   ↓
host capability instance
   ↓
host application / service / device
```

Example:

```text
Kaj Browser capability
   ↓
Chalok browser adapter
   ↓
BrowserSession
   ↓
WKWebView
```

or:

```text
Kaj Browser capability
   ↓
Playwright adapter
   ↓
Chromium
```

The Kaj task does not depend on the host implementation language.

---

## 2. Capability declarations

A capability is declared with:

```kaj
capability Browser {
    fn navigate(url: String) -> Result<None, BrowserError>
    fn observe() -> Result<PageObservation, BrowserError>
}
```

A capability declaration defines a named interface.

It does not contain implementation code.

---

## 3. Capability operations

Capability operations use typed function-like signatures.

Example:

```kaj
capability Browser {
    fn click(element: ElementId) -> Result<None, BrowserError>
}
```

The operation specifies:

```text
name
parameter names
parameter types
return type
```

The host implementation must satisfy that contract.

---

## 4. Capability declarations are module-level

Capability declarations may appear only at module scope.

They may not be declared:

```text
inside fn
inside task
inside step
inside conditional
inside loop
```

---

## 5. Capability namespace

Capability type names occupy the type/declaration namespace used for named language declarations.

A capability name must not collide with another incompatible top-level declaration of the same name.

Do not introduce overload-by-kind ambiguity.

---

## 6. Capability declarations contain signatures only

Capability operation bodies are not written in Kaj.

Invalid:

```kaj
capability Browser {
    fn navigate(url: String) -> Result<None, BrowserError> {
        // implementation
    }
}
```

Capability declarations describe host operations.

Their implementation exists outside Kaj source.

---

## 7. Requiring a capability

A task requires a capability using:

```kaj
use Browser as browser
```

This creates a task-local capability binding named:

```text
browser
```

with capability type:

```text
Browser
```

---

## 8. Meaning of `use`

`use Browser as browser` means:

```text
this task requires a host-provided Browser capability instance
```

It does not mean:

```text
grant this task Browser authority
```

The source declares a requirement.

The host decides whether to supply a matching capability instance.

---

## 9. Host authority

The host is authoritative over capability grants.

Conceptually:

```text
task requires Browser
        ↓
host has matching Browser instance?
        ├── yes -> bind and start
        └── no  -> task cannot begin
```

Source code cannot manufacture or escalate a capability grant.

---

## 10. Capability instance

A capability instance is a runtime host binding satisfying a capability declaration.

Conceptually:

```text
Capability type:
    Browser

Capability instance:
    Browser instance bound to BrowserSession ABC
```

Two tasks may receive different instances of the same capability type.

---

## 11. Instance scoping

A capability instance may be scoped to a specific resource.

Example:

```text
Browser instance A
    -> Chalok BrowserSession A

Browser instance B
    -> Chalok BrowserSession B
```

A task given instance A cannot automatically access instance B.

This scoping is part of the capability authority model.

---

## 12. Capability operation calls

Given:

```kaj
use Browser as browser
```

the task may call:

```kaj
browser.navigate("https://example.com")
```

Kaj type-checks the operation against the declared capability contract.

---

## 13. Unknown operations

Invalid:

```kaj
browser.fly_plane()
```

if `Browser` does not define:

```text
fly_plane
```

This is a static error.

---

## 14. Argument typing

Capability calls use ordinary Kaj argument typing.

If:

```kaj
fn navigate(url: String) -> Result<None, BrowserError>
```

then:

```kaj
browser.navigate(42)
```

is invalid.

No host call occurs when the call is statically invalid.

---

## 15. Return values

Capability operations return ordinary Kaj values.

Examples:

```text
Result<None, BrowserError>
PageObservation
List<BrowserElement>
Bool
String
```

The host adapter converts host-native results into canonical Kaj values.

---

## 16. Host-native values may not leak

Capability implementations must not expose raw host objects directly to Kaj.

Invalid conceptual result:

```text
WKWebView
Python Page object
socket
database connection
native pointer
```

Return values must be representable in Kaj's value system.

---

## 17. Capability errors

Expected capability failures should generally be represented as typed Kaj results.

Example:

```kaj
enum BrowserError {
    unavailable
    stale_element
    navigation_failed(message: String)
}
```

Then:

```kaj
fn navigate(url: String) -> Result<None, BrowserError>
```

allows ordinary Kaj error handling.

---

## 18. Host/runtime capability failure

A host/runtime failure is distinct from a returned typed error.

Example:

```text
browser.navigate(...)
returns err(navigation_failed(...))
```

is a normal completed capability call.

By contrast:

```text
adapter crashed
transport corrupted
host capability disappeared unexpectedly
```

may produce a runtime capability failure.

These must remain distinct.

---

## 19. Capability requirements belong to tasks

Initial `use` declarations may appear only directly inside task bodies.

Example:

```kaj
task Browse() -> None {
    use Browser as browser

    step open {
        browser.navigate("https://example.com")
    }

    return none
}
```

---

## 20. Functions cannot require capabilities

Invalid:

```kaj
fn browse() -> None {
    use Browser as browser
    return none
}
```

Ordinary functions remain below the Agentic effect layer.

---

## 21. Functions cannot directly call capability operations

A capability binding exists only in task scope.

A pure `fn` cannot capture or receive a capability instance in the initial model.

This keeps capability effects out of Pure Kaj functions.

Higher-level pure helper functions may operate on ordinary Kaj values returned by capabilities.

---

## 22. Step access

A capability binding declared at task scope is visible inside steps.

Example:

```kaj
task Browse() -> None {
    use Browser as browser

    step open {
        browser.navigate("https://example.com")
    }

    return none
}
```

---

## 23. Capability declarations and imports

Capability declarations may live in modules.

Example:

```text
capabilities/browser.kaj
```

containing:

```kaj
capability Browser {
    ...
}
```

Another module may import it according to ordinary Kaj import rules.

---

## 24. Multiple capability requirements

A task may require multiple capability instances.

Example:

```kaj
use Browser as browser
use Filesystem as files
```

Each binding has its own type and runtime instance.

---

## 25. Multiple instances of the same capability type

A task may require more than one instance of the same capability type if aliases differ.

Example:

```kaj
use Browser as primary
use Browser as secondary
```

The host may bind them to different browser sessions.

---

## 26. Binding identity

Each runtime capability binding has identity conceptually composed from:

```text
task ID
capability type
local alias
host instance identity
```

The exact host instance identifier is runtime-specific.

---

## 27. Binding persistence

Checkpoint 6 integrates with persistent tasks.

Persistent snapshots must not serialize the native adapter object itself.

Instead, persist a durable binding descriptor sufficient for the host to rebind the capability.

Conceptually:

```text
CapabilityBindingDescriptor
    capability_type
    alias
    host_binding_id
```

---

## 28. Rebinding after restart

When restoring a persistent task that requires capabilities, the runtime must ask the host to restore/rebind the required instances before execution resumes.

Conceptually:

```text
restore TaskSnapshot
↓
read required capability bindings
↓
host resolves host_binding_id
↓
rebind capability instance
↓
resume task
```

---

## 29. Missing binding on restore

If a required persistent capability cannot be rebound, the task cannot resume.

The task should remain non-running and report a structured capability-binding failure.

Do not silently bind an arbitrary replacement instance.

---

## 30. Capability grants and source requirements

The host may provide more functionality than a particular task requires.

Only the capability bindings granted to that task are visible.

A task cannot enumerate or access unrelated host capabilities unless a later feature explicitly permits discovery.

---

## 31. Operation-level authority

A host capability instance may expose a restricted subset of the full capability contract.

Conceptually, the declaration may define:

```text
observe
navigate
click
type
purchase
```

while a particular runtime grant authorizes only:

```text
observe
navigate
click
type
```

A denied operation must not execute.

---

## 32. Static contract versus runtime grant

There are two layers:

```text
capability declaration:
    what operations exist in the type

runtime grant:
    which operations this task instance is authorized to use
```

The type checker validates operation existence.

The runtime validates actual grant/authority.

---

## 33. Denied operation

If source contains a valid capability operation but the runtime grant denies it:

```kaj
browser.purchase(item)
```

the runtime rejects the operation before host side effects occur.

This is a capability authorization failure.

---

## 34. Capability calls and task lifecycle

A capability operation executes while the task is:

```text
running
```

Some capability operations may complete immediately.

Others may require asynchronous host work.

Checkpoint 6 introduces:

```text
waiting_for_capability
```

for operations that cannot complete immediately.

---

## 35. `waiting_for_capability`

Lifecycle transitions:

```text
running -> waiting_for_capability
waiting_for_capability -> running
waiting_for_capability -> failed
waiting_for_capability -> cancelled
```

The step containing the capability call remains:

```text
running
```

while the task waits.

---

## 36. Capability request identity

A pending asynchronous capability operation has an opaque runtime:

```text
CapabilityRequestId
```

This allows host responses to be correlated to the correct task and call.

---

## 37. Capability request record

Conceptually:

```text
CapabilityRequest
    request_id
    task_id
    capability_alias
    operation
    typed_arguments
    status
```

The exact transport representation is host-specific.

---

## 38. Synchronous versus asynchronous host implementation

Kaj source does not care whether a host capability implementation is:

```text
local synchronous
local asynchronous
remote RPC
WebSocket proxy
device bridge
```

The Agentic Kaj runtime normalizes the behavior.

---

## 39. Capability completion

When the host completes an asynchronous request:

```text
waiting_for_capability
    ↓
validate returned Kaj value
    ↓
running
```

Execution resumes immediately after the capability call.

The call is not re-issued.

---

## 40. Capability response validation

Host responses must be validated against the operation's declared Kaj return type.

Malformed host responses are runtime capability failures.

The runtime must not trust host adapter output blindly.

---

## 41. Capability persistence

Pending capability requests must be persistable if the task is durably suspended.

Persist at least:

```text
CapabilityRequestId
binding descriptor
operation name
arguments
expected return type
request status
continuation
```

However, exactly-once external execution is not guaranteed by this checkpoint.

---

## 42. Crash during capability call

If the runtime crashes after sending a host operation but before durably recording completion, the operation may be in an uncertain state.

Checkpoint 6 must represent this explicitly.

Do not silently replay potentially effectful operations without policy.

---

## 43. Uncertain capability outcome

Introduce a runtime concept such as:

```text
indeterminate capability request
```

when the runtime cannot prove whether the host operation completed.

The task must not automatically assume success or failure.

---

## 44. Idempotent capability operations

A capability operation may be declared/registered by the host as safely retryable.

The exact language syntax for idempotency is deferred.

Checkpoint 6 runtime APIs may attach host metadata such as:

```text
retry_safe
idempotency_key
```

without exposing new source syntax.

---

## 45. No automatic replay of uncertain effects

For a potentially effectful capability call with unknown completion status:

```text
do not automatically replay
```

The host must reconcile, fail, or explicitly retry according to adapter policy.

This prevents accidental duplicate:

```text
purchase
send email
delete file
robot movement
```

---

## 46. Capability calls in contracts

Capability operations are not permitted inside:

```text
goal
require
invariant
success
```

Task contracts remain pure.

---

## 47. Capability calls in human-interaction prompts

Capability calls may compute values before constructing a prompt, but no capability call executes as part of evaluating a pure contract.

Human interaction and capability waiting states remain distinct.

---

## 48. Capability declaration types

Capability signatures may refer to ordinary Kaj types imported or declared in scope.

Example:

```kaj
type PageObservation {
    url: String
    title: String
}

enum BrowserError {
    unavailable
}

capability Browser {
    fn observe() -> Result<PageObservation, BrowserError>
}
```

---

## 49. Capability declarations are nominal

A capability type is nominal.

Two separately declared capability types with identical operation shapes are still distinct.

---

## 50. Host adapter conformance

A host adapter must implement every operation required by the capability instance it claims to provide, with compatible input/output conversions.

The host SDK/runtime should validate adapter registration where practical.

---

## 51. Capability discovery

Automatic capability discovery is not part of the initial model.

A task declares exactly what it requires.

The host explicitly binds matching instances.

---

## 52. Security principle

Capability possession is authority.

A task cannot perform an external operation merely because the operation exists somewhere in the host.

It must possess the corresponding granted capability binding.

---

## 53. Source cannot self-authorize

Kaj source cannot:

```text
create a host capability instance
expand its own grant
change host binding scope
change host policy
access another task's binding
```

These are host/runtime responsibilities.

---

## 54. Planner restriction

Future planners may generate code that uses capabilities already granted to the task.

A planner may not expand the task's capability grant.

This rule is frozen now even though planning is introduced later.

---

## 55. Summary

Checkpoint 6 freezes:

```text
capability declarations define typed host interfaces
capability declarations have signatures only
capability types are nominal

tasks require capabilities with:
    use Capability as alias

use declares a requirement
use does not grant authority

host provides capability instances
instances may be scoped to specific resources
multiple instances may exist

task capability calls are statically typed
host results convert to Kaj values
native objects never leak into Kaj

runtime grants may restrict operation-level authority
denied operations never execute

functions cannot use capabilities
contracts cannot use capabilities
steps may use task capability bindings

waiting_for_capability is a task lifecycle state
pending capability requests have identity
responses resume exact continuation

persistent tasks store binding descriptors, not native adapters
restore requires explicit host rebinding

uncertain external effects are not automatically replayed
exactly-once external side effects are not guaranteed yet

source and future planners cannot self-authorize
```
