# Standard Capability Architecture

Standard capabilities define reusable, host-independent interfaces for external systems used by Agentic Kaj tasks.

This document defines how standard capability contracts are identified, packaged, imported, versioned, registered, bound to task instances, and implemented by hosts.

It does not define the Browser capability itself. That is a later checkpoint.

---

## 1. Purpose

Agentic Kaj already defines generic capability semantics.

The Integration Track now needs a stable architecture for reusable standard capabilities such as:

```text
Browser
Filesystem
HTTP
Audio
Robotics
Application APIs
```

The goal is to make capability packages portable across:

```text
Chalok
Playwright
Berkbrain
test hosts
future runtimes
```

without changing Kaj language semantics.

---

## 2. Core separation

The architecture has four layers:

```text
Kaj Core
    ↓
Standard Capability Contract
    ↓
Host Adapter Interface
    ↓
Host-Specific Implementation
```

Example:

```text
Kaj Core
    ↓
Browser capability contract
    ↓
CapabilityAdapter
    ↓
ChalokBrowserAdapter
```

Kaj core must not depend on Chalok, Playwright, WKWebView, or any other host-specific technology.

---

## 3. Standard capability package

A standard capability package contains:

```text
capability declarations
supporting Kaj types
supporting enums/newtypes/records
public documentation
conformance fixtures
```

It does not contain:

```text
host-native implementation objects
vendor SDK clients
Chalok code
Playwright code
WKWebView code
```

---

## 4. Standard capability namespace

Standard capabilities live under a stable logical namespace.

Initial convention:

```text
std.capabilities
```

Examples:

```text
std.capabilities.browser
std.capabilities.filesystem
std.capabilities.http
```

The exact physical source layout may differ, but the logical module identity is stable.

---

## 5. Capability identity

A capability contract has a stable identity.

Conceptually:

```text
CapabilityIdentity
    module
    name
    version
```

Example:

```text
module = std.capabilities.browser
name = Browser
version = 1
```

Canonical logical identity:

```text
std.capabilities.browser.Browser@1
```

The exact internal encoding is implementation-defined.

---

## 6. Capability version

Standard capability contracts are versioned independently of host adapters.

Initial versioning model:

```text
positive integer major version
```

Examples:

```text
Browser@1
Filesystem@1
HTTP@1
```

Minor source-compatible improvements may remain within the same major contract version if they do not alter required semantics.

Incompatible contract changes require a new major version.

---

## 7. Import model

A Kaj program imports a standard capability package using ordinary Kaj module imports.

Conceptually:

```kaj
import std.capabilities.browser
```

The module exposes its public capability declarations and supporting types.

Task source then uses the imported capability normally:

```kaj
use Browser as browser
```

The exact import qualification rules follow normal Kaj module semantics.

---

## 8. No magical built-in capability names

`Browser`, `Filesystem`, and other standard capabilities are not special compiler keywords.

They are ordinary nominal capability declarations supplied by standard modules.

This keeps the language extensible.

---

## 9. Standard package stability

A standard capability package is considered part of Kaj's public integration surface.

Changing its public declarations may affect:

```text
source compatibility
host adapters
persisted capability bindings
planner-visible schemas
conformance tests
```

Therefore contract changes must be deliberate and versioned.

---

## 10. Host adapter

A host adapter implements one capability contract for one host environment.

Conceptually:

```text
CapabilityAdapter
    capability_identity
    host_binding_id
    supported_operations
    invoke(...)
```

The exact SDK/class shape is host-language-specific.

---

## 11. Adapter conformance

An adapter claiming to implement a standard capability must satisfy:

```text
correct capability identity
compatible capability version
required operation set
argument conversion
return conversion
typed error conversion
operation-grant enforcement
stable binding identity
persistence/rebinding support
no host-native object leakage
```

---

## 12. Adapter is not the capability

A capability declaration is the contract.

An adapter is one implementation.

Example:

```text
std.capabilities.browser.Browser@1
    ├── ChalokBrowserAdapter
    ├── PlaywrightBrowserAdapter
    └── MockBrowserAdapter
```

All adapters implement the same Kaj-visible contract.

---

## 13. Capability registry

The host/runtime maintains a registry of available capability implementations.

Conceptually:

```text
CapabilityRegistry
    host capability implementations
    binding descriptors
    adapter factories/resolvers
```

The registry is host/runtime infrastructure.

It is not a Kaj package registry.

---

## 14. Registry responsibility

The registry is responsible for:

```text
registering host capability implementations
resolving a capability identity/version
resolving persistent host binding IDs
constructing/retrieving adapters
validating adapter compatibility
```

It must not automatically grant every registered capability to every task.

---

## 15. Task binding table

Task capability bindings are separate from the global capability registry.

Conceptually:

```text
Task 123 bindings
    browser -> host-binding-A
    files   -> host-binding-B
```

Another task may have:

```text
Task 456 bindings
    browser -> host-binding-C
```

The task binding table determines what authority a particular task possesses.

---

## 16. Registry versus task binding

Freeze the distinction:

```text
CapabilityRegistry
    = what implementations/resources the host knows about

Task capability bindings
    = what a specific task is allowed to use
```

A task must never be allowed to enumerate the registry as a way to obtain authority.

---

## 17. Host binding ID

A host capability instance has a stable opaque:

```text
HostBindingId
```

Examples conceptually:

```text
chalok-browser-session-123
filesystem-sandbox-A
robot-arm-7
```

The exact format is host-defined.

Kaj source does not inspect it directly.

---

## 18. Binding descriptor

Persistent tasks store a durable capability binding descriptor.

Conceptually:

```text
CapabilityBindingDescriptor
    capability_identity
    local_alias
    host_binding_id
    granted_operations
```

Do not persist the adapter object itself.

---

## 19. Task start resolution

At task start:

```text
task declares use Capability as alias
↓
runtime identifies required capability contract
↓
host resolves/provides a compatible binding
↓
runtime validates identity/version/grants
↓
task binding created
```

If the host cannot satisfy the requirement, the task does not start normal execution.

---

## 20. Binding policy

The host decides which resource satisfies a requirement.

Example:

```text
Task A:
    use Browser as browser
        -> BrowserSession A

Task B:
    use Browser as browser
        -> BrowserSession B
```

Kaj source requests the contract.

The host chooses the concrete binding.

---

## 21. Multiple instances

A task may bind multiple instances of the same standard capability type.

Example:

```kaj
use Browser as primary
use Browser as secondary
```

The host may bind:

```text
primary   -> browser-session-A
secondary -> browser-session-B
```

---

## 22. Operation grants

A task binding may restrict the operations available on the capability.

Example:

```text
Browser@1 contract:
    observe
    navigate
    click
    type
    purchase

task grant:
    observe
    navigate
    click
    type
```

`purchase` remains part of the type contract but is not authorized for that task binding.

---

## 23. Planner visibility

Planner input may expose:

```text
capability identity
capability version
operation signatures
granted operation subset
supporting Kaj types
```

The planner does not receive adapter internals.

---

## 24. Adapter registration

Hosts should register adapters explicitly.

Conceptually:

```text
registry.register(
    capability_identity,
    binding_id,
    adapter
)
```

or through a resolver/factory.

The exact API is implementation-specific.

---

## 25. Adapter factories

Hosts may register a factory/resolver instead of a permanent in-memory adapter.

This is important for:

```text
persistent task restore
remote capabilities
lazy session creation
device reconnect
```

Conceptually:

```text
resolve(capability_identity, host_binding_id)
    -> CapabilityAdapter
```

---

## 26. Persistence and rebinding

On task restore:

```text
load binding descriptor
↓
resolve capability identity/version
↓
resolve host_binding_id through registry/resolver
↓
validate adapter
↓
recreate task binding
```

If resolution fails, the task must not silently bind a different resource.

---

## 27. Binding compatibility

A restored adapter must be compatible with the persisted capability identity/version.

Example:

```text
persisted Browser@1
```

must not silently rebind to:

```text
Browser@2
```

unless an explicit compatibility policy says it is safe.

Initial rule:

```text
exact major version match
```

---

## 28. Supporting Kaj types

A standard capability package may define supporting types.

Example:

```text
newtype ElementId = String
type PageObservation { ... }
enum BrowserError { ... }
```

These types belong to the standard package and are part of its versioned public contract.

---

## 29. Host value conversion

Adapters convert between:

```text
Kaj values
and
host-native values
```

The boundary must preserve:

```text
type correctness
Decimal exactness
nominal type identity
enum identity/payloads
record fields
newtypes
Optional/Result
List/Map
```

---

## 30. No native-object leakage

Standard capability packages may never expose host-native objects as Kaj-visible values.

Examples not allowed:

```text
WKWebView
Playwright Page
Python file handle
Swift class instance
socket
database cursor
```

Use Kaj-defined records/newtypes/identifiers instead.

---

## 31. Typed host errors

Expected adapter failures should map to Kaj-declared error values whenever the capability contract defines them.

Unexpected adapter/runtime failures remain structured capability runtime failures.

---

## 32. Mock adapters

Every standard capability package should support a deterministic mock/reference adapter used by conformance tests.

The mock adapter should implement the same capability identity/version as the real adapters.

---

## 33. Conformance fixtures

Each standard capability package should eventually have capability-specific conformance fixtures.

Fixtures should test:

```text
operation typing
host value conversion
grant enforcement
binding identity
persistence/rebinding
typed errors
async completion if relevant
stale response protection if relevant
```

---

## 34. Standard capability source location

Checkpoint 1 freezes the logical namespace, not necessarily the final physical package manager.

Recommended repository layout:

```text
std/
└── capabilities/
```

For example:

```text
std/capabilities/browser.kaj
```

may map logically to:

```text
std.capabilities.browser
```

If the repository's current module loader requires another physical layout, preserve the logical namespace.

---

## 35. Kaj core responsibilities

Kaj core is responsible for generic capability semantics:

```text
capability declarations
use declarations
type checking
task bindings
grant validation
waiting_for_capability
persistence descriptors
adapter interface contracts
```

Kaj core is not responsible for:

```text
browser behavior
filesystem behavior
HTTP semantics
Chalok sessions
Playwright
robot hardware
```

---

## 36. Standard library responsibilities

The standard capability library is responsible for:

```text
capability declarations
supporting Kaj data types
typed error models
public semantic documentation
capability-specific conformance fixtures
```

---

## 37. Host responsibilities

The host is responsible for:

```text
registering adapters
choosing concrete bindings
granting operation subsets
resolving persistent bindings
enforcing host-side policy
converting host/native values
executing external operations
```

---

## 38. Security principle

A registered capability is not automatically granted authority.

Freeze:

```text
registration != grant
```

A host may know about many capability instances.

A task sees only its explicit bindings.

---

## 39. Cross-task isolation

Task capability bindings are isolated by TaskId.

A task must not access another task's binding merely by knowing:

```text
capability type
alias
host binding ID
```

The runtime's task binding table is authoritative.

---

## 40. Capability package discovery

Automatic runtime discovery of all standard capability packages is not required.

Normal Kaj imports determine which contracts source code references.

Host registry discovery is separate.

---

## 41. No dynamic source acquisition

Checkpoint 1 does not add source syntax for dynamically acquiring a capability at runtime.

Requirements remain declared by:

```kaj
use Capability as alias
```

---

## 42. Version mismatch

If source/runtime requires:

```text
Capability@1
```

and host provides only:

```text
Capability@2
```

the requirement is unsatisfied unless explicit compatibility support exists.

Initial rule:

```text
major versions must match exactly
```

---

## 43. Adapter metadata

Adapters may expose non-semantic metadata such as:

```text
host implementation name
adapter version
transport type
debug label
latency metrics
```

This metadata does not alter Kaj capability semantics.

---

## 44. Transport independence

A capability adapter may execute:

```text
in-process
through IPC
through WebSocket
through HTTP/RPC
on another device
```

The standard capability contract must remain transport-independent.

---

## 45. Chalok compatibility

This architecture must allow a future Chalok adapter to bind:

```text
Browser capability instance
```

to exactly one:

```text
BrowserSession
```

without introducing Chalok types into Kaj core or standard capability definitions.

---

## 46. Future capability compatibility

The same architecture must work for future capabilities such as:

```text
Filesystem
HTTP
Audio
Robot
SpatialEnvironment
Application
```

without redesigning core capability binding semantics.

---

## 47. Summary

Checkpoint 1 freezes:

```text
standard capability logical namespace:
    std.capabilities

capability identity includes:
    module
    name
    major version

standard capability package contains:
    capability declarations
    supporting Kaj types
    docs
    conformance fixtures

adapter implements contract
adapter is host-specific
adapter is not Kaj source semantics

CapabilityRegistry:
    knows host implementations/resources

Task capability bindings:
    define per-task authority

registration != grant

persistent binding stores descriptor, not adapter object

restore:
    descriptor -> registry/resolver -> compatible adapter

major capability version must match initially

Kaj core remains host-agnostic
standard packages remain host-agnostic
hosts choose resources and grants
native objects never cross into Kaj values
```
