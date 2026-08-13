# Kaj Integration Track

**Track:** Kaj Integrations  
**Purpose:** Move Agentic Kaj from a complete language/runtime foundation into real host applications, beginning with browser automation and Chalok.

**Recommended path:** `dev/plans/integrations/integration-track.md`

## Goal

The Integration Track connects Agentic Kaj to real external systems without weakening the language/runtime boundaries established by Agentic Kaj Conformance 1.

The first production target is Chalok.

The final architecture should look like:

```text
Chalok request
    ↓
Agentic Kaj task
    ↓
Kaj planner boundary
    ↓
validated plan
    ↓
Kaj runtime
    ↓
Browser capability
    ↓
Chalok adapter
    ↓
BrowserSession
    ↓
WKWebView
```

## Design Principle

Kaj core must not depend on Chalok.

```text
Kaj Core
    ↓
generic capability semantics

Standard Capability Package
    ↓
typed capability contract

Host Adapter Interface
    ↓
host-specific implementation

Chalok
    ↓
BrowserSession / WKWebView
```

The same Kaj Browser capability should be usable with Chalok, Playwright, a deterministic mock browser, or another future browser host without changing Kaj source semantics.

## Track Boundaries

This track covers:

```text
standard capability architecture
standard Browser capability
browser host adapters
Chalok integration
real planner integration
safety/approval integration
persistence
replanning
integration conformance
```

It does not redesign the already-frozen Agentic Kaj task, lifecycle, contract, capability, composition, planner, or replanning semantics.

---

# Checkpoint 1 — Standard Capability Architecture

## Goal

Define how standard Kaj capabilities are packaged, identified, imported, implemented, registered, bound, versioned, persisted, and tested.

## Main Areas

```text
standard capability package layout
capability identity
capability versioning
imports
host adapter contract
capability registry
task-specific bindings
adapter conformance
persistence/rebinding
mock adapter support
```

## Key Decisions

Freeze:

```text
where standard capability contracts live
how standard capabilities are named
how capability identity is represented
how capability versions are represented
how hosts register implementations
how task bindings differ from global registrations
how adapters are rebound after restart
how Kaj values cross the adapter boundary
how adapter conformance is tested
```

Keep these distinct:

```text
CapabilityRegistry
    available host implementations/resources

Task capability bindings
    what one specific TaskInstance is allowed to use
```

## Out of Scope

```text
full Browser contract
Chalok adapter
real browser execution
real planner API
```

---

# Checkpoint 2 — Standard Browser Capability

## Goal

Define the host-independent standard Browser capability contract.

## Main Areas

```text
Browser capability
PageObservation
BrowserElement
ElementId
page generation / stale identity
navigation
observation
click
type
select
scroll
browser errors
structured results
```

## Key Questions

Freeze:

```text
what browser state Kaj may observe
how elements are identified
how stale elements are detected
how page generation/versioning works
what browser operations return
how browser errors are typed
how much DOM/page data is exposed
how sensitive fields are represented
```

The spec describes browser behavior, not WKWebView, Chromium, Playwright, or Chalok internals.

---

# Checkpoint 3 — Browser Reference / Mock Adapter

## Goal

Implement a deterministic host adapter for the standard Browser capability.

## Main Areas

```text
mock browser state
mock pages
mock elements
navigation
click/type/select/scroll
page generation
stale elements
typed errors
capability grants
async requests
persistence/rebinding
```

Kaj Browser behavior must be testable without Chalok, WKWebView, Playwright, network access, or a real browser.

---

# Checkpoint 4 — Chalok Browser Adapter

## Goal

Bind the standard Kaj Browser capability to a real Chalok `BrowserSession`.

## Architecture

```text
Kaj Browser binding
    ↓
ChalokBrowserAdapter
    ↓
Chalok BrowserSession
    ↓
AgentAction / observation bridge
    ↓
WKWebView
```

## Main Areas

```text
session binding
observation conversion
element identity mapping
navigation
click
typing
selection
scrolling
page generation
stale element handling
error conversion
async host requests
capability persistence/rebinding
```

Each Browser capability instance must be scoped to one specific browser resource/session.

---

# Checkpoint 5 — End-to-End Chalok Task Execution

## Goal

Run complete Agentic Kaj tasks through Chalok.

## Main Areas

```text
task creation from Chalok
Browser capability binding
task execution
steps
human interaction
capability waits
task status
results
failure propagation
cancellation
activity/event mapping
```

## Required Outcome

A real Kaj task can:

```text
start
observe page
navigate
interact
request human input if necessary
continue
complete
```

against a live Chalok session.

---

# Checkpoint 6 — Real Planner Adapter

## Goal

Connect a real model-backed planner to Agentic Kaj's generic PlannerAdapter boundary.

## Main Areas

```text
PlannerRequest serialization
model prompt/protocol
structured planner output
Kaj AST / plan generation
validation feedback
retry after invalid proposal
planner timeout/failure
cost/token metadata
provider-independent boundary
```

Core rule:

```text
model proposes
Kaj validates
runtime executes
```

The model never directly performs browser actions outside Kaj runtime authority.

---

# Checkpoint 7 — Browser Safety and Approval Integration

## Goal

Connect Kaj capability authority and human interaction semantics to Chalok's safety system.

## Main Areas

```text
SafetyPolicy
ApprovalRequest
sensitive actions
operation grants
human confirmation
credential fields
payments
destructive actions
downloads/uploads
external submissions
```

## Architecture

```text
Kaj capability call
    ↓
Kaj grant validation
    ↓
Chalok safety policy
    ↓
approval if required
    ↓
host executes
```

Neither layer may silently bypass the other.

---

# Checkpoint 8 — Persistent Browser Tasks

## Goal

Allow Chalok-backed Kaj tasks to survive app/backend/runtime interruption.

## Main Areas

```text
TaskSnapshot
Browser binding descriptor
BrowserSession rebinding
waiting_for_human restore
waiting_for_capability restore
waiting_for_planner restore
child task restore
accepted plan restore
browser request reconciliation
session disappearance
```

Persist identifiers/descriptors, not native Swift/WKWebView/session objects.

---

# Checkpoint 9 — Browser Replanning

## Goal

Use Agentic Kaj controlled replanning during real browser workflows.

## Main Areas

```text
replan trigger
new page state
failed search strategy
human feedback
capability result changes
plan revision
pending-step replacement
completed-step protection
browser history preservation
```

Example:

```text
completed:
    search site A

new fact:
    no suitable result

replan future:
    search site B
    compare results
```

Completed browser actions remain immutable runtime history.

---

# Checkpoint 10 — Chalok / Kaj Integration Conformance

## Goal

Freeze the first production-quality Kaj host integration.

## Main Areas

```text
end-to-end conformance
multi-session isolation
capability authority
safety
planner validation
human interaction
persistence
replanning
cancellation
failure recovery
event trace
diagnostics
performance sanity
documentation
```

## Required Test Categories

```text
simple navigation
multi-step browser task
human confirmation
stale element
capability denial
invalid planner proposal
planner capability escalation attempt
persistent wait/resume
crash during browser request
child browser task
replanning
multi-task/multi-session isolation
cancellation
```

---

# Repository Organization

Recommended:

```text
docs/
├── agentic/
│   └── ...
├── capabilities/
│   └── browser.md
└── integrations/
    ├── index.md
    ├── standard-capabilities.md
    └── chalok.md

dev/
└── plans/
    └── integrations/
        ├── integration-track.md
        ├── checkpoint-1-standard-capability-architecture.md
        ├── checkpoint-2-browser-capability.md
        ├── checkpoint-3-browser-reference-adapter.md
        ├── checkpoint-4-chalok-browser-adapter.md
        ├── checkpoint-5-chalok-task-execution.md
        ├── checkpoint-6-real-planner-adapter.md
        ├── checkpoint-7-browser-safety-approvals.md
        ├── checkpoint-8-persistent-browser-tasks.md
        ├── checkpoint-9-browser-replanning.md
        └── checkpoint-10-chalok-kaj-conformance.md
```

The physical standard-library/package location for capability definitions should be frozen during Checkpoint 1 rather than guessed in this overview.

---

# End-to-End Integration Architecture

```text
User
 ↓
Chalok UI
 ↓
Task request
 ↓
PlannerAdapter
 ↓
PlannerRequest
 ↓
Model
 ↓
structured Kaj plan
 ↓
Kaj validation
 ↓
TaskInstance
 ↓
steps
 ↓
Browser capability
 ↓
CapabilityRegistry + task binding
 ↓
ChalokBrowserAdapter
 ↓
BrowserSession
 ↓
WKWebView
```

Human intervention:

```text
Kaj ask/choose/confirm/handoff
 ↓
Chalok HITL UI
 ↓
typed response
 ↓
Kaj runtime resume
```

Persistence:

```text
TaskSnapshot
 ↓
TaskStore
 ↓
restore
 ↓
capability/session rebinding
 ↓
resume
```

Replanning:

```text
new browser state
 ↓
request replan
 ↓
PlannerRequest(purpose=replan)
 ↓
validated future-plan replacement
 ↓
continue
```

---

# Non-Goals

Do not turn the Integration Track into another general language-design phase.

Defer unless required:

```text
new primitive types
new general collection features
task syntax redesign
structured concurrency redesign
generic retry language
distributed task scheduler
robot capability
audio capability
filesystem capability implementation
HTTP capability implementation
multi-planner consensus
```

---

# Exit Criteria

The Integration Track is complete when:

```text
[ ] standard capability packaging architecture is stable
[ ] standard Browser capability is frozen
[ ] deterministic Browser adapter passes
[ ] Chalok adapter passes
[ ] real Chalok task execution works
[ ] real planner adapter works
[ ] browser safety/approvals integrate correctly
[ ] browser tasks survive persistence/restart
[ ] controlled browser replanning works
[ ] multi-task/browser-session isolation is verified
[ ] integration conformance suite passes
[ ] docs build cleanly
```

At that point Kaj has proven its Agentic Kaj model in a real host application rather than only in its reference runtime.
