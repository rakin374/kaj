# Kaj Integration Track — Checkpoint 1: Standard Capability Architecture

**Track:** Kaj Integrations  
**Checkpoint:** 1  
**Recommended path:** `dev/plans/integrations/checkpoint-1-standard-capability-architecture.md`

---

# Goal

Create the reusable architecture for standard Kaj capability packages and host adapters.

Authoritative semantics:

```text
docs/integrations/standard-capabilities.md
```

This checkpoint builds on completed Agentic Kaj capability semantics.

Do not redesign the core capability language.

---

# Scope

Implement/refine:

```text
standard capability logical namespace
standard capability source/package layout
CapabilityIdentity
capability major version
host adapter conformance metadata
CapabilityRegistry responsibilities
task-specific binding table separation
HostBindingId
CapabilityBindingDescriptor
registry/resolver API
restore-time rebinding
version compatibility validation
mock adapter support
capability package test conventions
docs integration
```

Do not implement the full Browser contract yet.

---

# Logical Namespace

Freeze standard capability modules under:

```text
std.capabilities
```

Examples for future checkpoints:

```text
std.capabilities.browser
std.capabilities.filesystem
std.capabilities.http
```

Physical repository path may be:

```text
std/capabilities/
```

if compatible with the current module loader.

Preserve the logical module identity even if physical layout differs.

---

# Capability Identity

Introduce/reuse a structured identity conceptually:

```text
CapabilityIdentity
    module_name
    capability_name
    major_version
```

Example canonical identity:

```text
std.capabilities.browser.Browser@1
```

The exact string format may be internal, but identity comparison must be deterministic.

---

# Versioning

Initial compatibility rule:

```text
major capability version must match exactly
```

Do not build a complex semver negotiation subsystem.

Provide enough structure for future version migration.

---

# Standard Capability Package Model

Establish conventions for a package containing:

```text
capability declaration
supporting Kaj types
public exports
docs
conformance fixtures
```

No host adapter implementation should live inside the standard Kaj package.

---

# Import Integration

Ensure the existing Kaj module/import system can load standard capability modules.

Do not create magical compiler lookup for Browser/etc.

A standard capability should be importable through ordinary Kaj module semantics.

If the current module loader cannot resolve the proposed std namespace, implement the smallest clean standard-library resolution mechanism.

Do not break local imports.

---

# CapabilityRegistry

Review/refine the generic registry introduced in Agentic Kaj Checkpoint 6.

Freeze its responsibility as:

```text
host-known capability implementations/resources
adapter registration
binding/factory resolution
restore-time host_binding_id lookup
adapter compatibility validation
```

Do not use the registry itself as the per-task authorization table.

---

# Task Binding Table

Ensure task-specific authority is represented separately.

Conceptually:

```text
TaskCapabilityBindings
    task_id
    alias -> capability binding
```

A task binding includes:

```text
CapabilityIdentity
HostBindingId
granted operations
adapter/resolved runtime handle
```

The resolved runtime handle is not persisted.

---

# Registration != Grant

Add tests that prove:

```text
registered adapter/resource
```

does not become available to a task unless explicitly bound/granted.

No source or planner path may enumerate the registry and self-bind.

---

# HostBindingId

Introduce/reuse an opaque stable host resource/binding identifier.

Requirements:

```text
host-defined
stable enough for persistence/rebinding
not interpreted by Kaj source
not globally enumerable by task code
```

---

# CapabilityBindingDescriptor

Freeze a persisted descriptor conceptually:

```text
CapabilityBindingDescriptor
    capability_identity
    local_alias
    host_binding_id
    granted_operations
```

Ensure TaskSnapshot persists this shape or an equivalent canonical representation.

Do not persist native adapter objects.

---

# Adapter Interface

Refine the host adapter interface around standard identity/version.

Conceptually:

```text
CapabilityAdapter
    capability_identity
    host_binding_id
    supported_operations
    invoke(...)
```

Exact Python API should follow repository conventions.

Avoid duplicate adapter abstractions if Checkpoint 6 already has one; migrate/refine instead.

---

# Adapter Resolver / Factory

Support restore-time resolution conceptually:

```text
resolve(
    capability_identity,
    host_binding_id
) -> CapabilityAdapter
```

This may be implemented by registry factories, resolvers, or direct lookup.

The important behavior is stable.

---

# Adapter Conformance Validation

At registration/bind time, validate where practical:

```text
identity match
major version match
required operations available
grant subset valid
host binding ID present
adapter output conversion contract available
```

Do not wait until arbitrary operation invocation to detect obvious registration incompatibility.

---

# Value Boundary

Reuse Agentic Kaj's canonical Kaj value conversion.

Verify adapter boundary supports:

```text
Bool
Int
Decimal
String
Bytes
None
List
Map
Optional
Result
records
enums
newtypes
```

No raw host-native object may enter Kaj state.

---

# Persistence / Rebinding

On task restore:

```text
load CapabilityBindingDescriptor
↓
resolve adapter by CapabilityIdentity + HostBindingId
↓
validate version
↓
reconstruct task-local binding
```

If binding cannot be restored:

```text
task must not resume
```

Do not bind an arbitrary replacement.

---

# Mock Capability Package / Adapter

Use or create a small generic standard-test capability for architecture tests.

Example:

```kaj
capability Counter {
    fn read() -> Int
    fn add(amount: Int) -> Int
}
```

Place it in test fixtures or a test namespace, not necessarily public `std`.

Use it to validate:

```text
identity
version
registration
binding
granting
persistence
rebind
cross-task isolation
```

---

# Conformance Fixture Convention

Define where integration capability fixtures live.

Recommended:

```text
tests/integrations/capabilities/
```

or repository-equivalent.

Do not create excessive new testing infrastructure if Agentic Conformance already provides a suitable fixture system.

Reuse it.

---

# Standard Library Resolution Tests

Test:

```text
std capability module resolves
supporting types resolve
capability declaration imports
local imports still work
unknown std module rejected cleanly
```

---

# Security Tests

At minimum:

```text
registered but unbound capability inaccessible
task A cannot access task B binding
host_binding_id knowledge alone insufficient
planner cannot add binding
capability version mismatch rejected
grant subset enforced
```

---

# Persistence Tests

At minimum:

```text
binding descriptor round-trip
adapter object not serialized
HostBindingId preserved
CapabilityIdentity preserved
major version preserved
restore resolver returns compatible adapter
missing binding blocks resume
version mismatch blocks resume
```

---

# Documentation

Add/update:

```text
docs/integrations/index.md
docs/integrations/standard-capabilities.md
```

Update MkDocs navigation if needed.

Public docs should explain architecture and semantics, not checkpoint DoD.

---

# Required Tests

Identity/version:

```text
CapabilityIdentity equality
different module differs
different name differs
different major differs
canonical deterministic representation
```

Registry:

```text
register adapter
resolve adapter
duplicate/conflicting registration behavior
wrong capability identity rejected
wrong version rejected
```

Bindings:

```text
task binding creation
alias lookup
multiple tasks isolated
multiple aliases same capability supported
registration != grant
```

Restore:

```text
descriptor persisted
resolver called
compatible adapter rebound
missing adapter blocks resume
version mismatch blocks resume
```

Imports:

```text
std.capabilities namespace loads
ordinary imports unaffected
```

Regression:

```text
Pure Kaj
Agentic Kaj Conformance
all existing Agentic tests
mkdocs build --strict
```

---

# Out of Scope

Do not implement:

```text
Browser capability operations
PageObservation
BrowserElement
ElementId
Chalok adapter
Playwright adapter
real browser execution
filesystem capability
HTTP capability
audio capability
robotics capability
real LLM planner
browser safety UI
```

---

# Definition of Done

```text
[ ] std.capabilities logical namespace established
[ ] standard module resolution works
[ ] local imports remain intact

[ ] CapabilityIdentity includes module/name/major
[ ] identity representation deterministic
[ ] exact major version compatibility enforced

[ ] standard capability package conventions documented
[ ] host adapter remains separate from standard package

[ ] CapabilityRegistry responsibility refined
[ ] task binding table separate from registry
[ ] registration != grant enforced

[ ] HostBindingId implemented/reused
[ ] CapabilityBindingDescriptor implemented/reused
[ ] descriptor persists without adapter object

[ ] adapter resolver/factory supports restore
[ ] registration/bind compatibility validation exists
[ ] cross-task binding isolation enforced

[ ] mock capability architecture tests pass
[ ] persistence/rebind tests pass
[ ] security tests pass

[ ] docs/integrations/index.md updated/created
[ ] docs/integrations/standard-capabilities.md matches implementation
[ ] mkdocs build --strict passes

[ ] Pure Kaj suite passes
[ ] Agentic Kaj suite/conformance passes
[ ] Integration Checkpoint 1 tests pass
```

---

# Completion Report

```text
Kaj Integration Checkpoint 1 — Standard Capability Architecture

Status:
COMPLETE / INCOMPLETE

Files changed:
- ...

Standard package:
- std.capabilities namespace: PASS/FAIL
- standard module resolution: PASS/FAIL
- local import regression: PASS/FAIL

Identity/version:
- CapabilityIdentity: PASS/FAIL
- module/name/major identity: PASS/FAIL
- deterministic representation: PASS/FAIL
- major-version compatibility: PASS/FAIL

Registry/bindings:
- CapabilityRegistry: PASS/FAIL
- task bindings separated: PASS/FAIL
- registration != grant: PASS/FAIL
- cross-task isolation: PASS/FAIL

Adapters:
- adapter identity metadata: PASS/FAIL
- HostBindingId: PASS/FAIL
- resolver/factory: PASS/FAIL
- compatibility validation: PASS/FAIL

Persistence:
- binding descriptor: PASS/FAIL
- adapter excluded from snapshot: PASS/FAIL
- restore/rebind: PASS/FAIL
- missing binding handling: PASS/FAIL
- version mismatch handling: PASS/FAIL

Testing:
- mock capability tests: PASS/FAIL
- security tests: PASS/FAIL
- persistence tests: PASS/FAIL

Regression:
- Pure Kaj: PASS/FAIL
- Agentic Kaj: PASS/FAIL
- Agentic Conformance: PASS/FAIL
- Integration Checkpoint 1: PASS/FAIL
- mkdocs build --strict: PASS/FAIL

Deferred intentionally:
- Browser capability
- Browser adapters
- Chalok integration
- real planner integration

Known issues:
- ...
```
