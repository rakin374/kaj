# Kaj Integration Track — Checkpoint 3: Browser Reference Adapter

**Track:** Kaj Integrations  
**Checkpoint:** 3  
**Recommended path:** `dev/plans/integrations/checkpoint-3-browser-reference-adapter.md`

---

# Goal

Implement a deterministic reference/mock adapter for:

```text
std.capabilities.browser.Browser@1
```

Authoritative semantics:

```text
docs/integrations/browser-reference-adapter.md
```

This checkpoint builds on Integration Checkpoints 1–2.

Do not integrate Chalok yet.

---

# Scope

Implement:

```text
ReferenceBrowser state model
ReferencePage fixtures
ReferenceElement fixtures
ReferenceBrowserAdapter
Browser@1 conformance
deterministic ElementId generation
PageGeneration invalidation
observe
navigate
click
type_text
select
scroll
typed BrowserError behavior
sync operation mode
deterministic async operation mode
CapabilityRequestId suspension/resume tests
grant enforcement tests
persistence/rebinding
multi-session isolation
test fixtures
docs integration
```

---

# Recommended Location

Use repository conventions, but a clean structure may be:

```text
src/kaj/testing/browser/
    __init__.py
    adapter.py
    model.py
    fixtures.py
```

or:

```text
tests/support/browser/
```

Choose based on whether the reference adapter is intended as a reusable host-testing utility.

Do not place it in:

```text
std/capabilities/browser.kaj
```

The standard Kaj package contains the contract, not the host implementation.

---

# Reference Browser Model

Create an explicit deterministic host model.

Conceptually:

```text
ReferenceBrowser
    host_binding_id
    current_page_key
    generation
    viewport
    page_state
    available
```

---

# Reference Page

Conceptually:

```text
ReferencePage
    key
    url
    title
    content_width
    content_height
    elements
```

Fixture-specific action handlers/transitions may be represented declaratively where practical.

---

# Reference Element

Conceptually:

```text
ReferenceElement
    fixture_key
    role
    text
    enabled
    visible
    kind/capabilities
    value
    sensitive
    select_options
    click_transition
```

Keep internal fixture model independent from Kaj runtime value classes where practical.

Convert at adapter boundary.

---

# Deterministic ElementId

Implement a deterministic mapping to standard:

```text
ElementId
```

Requirements:

```text
unique within generation
stable for repeated observe calls in same unchanged generation
different/stale after invalidating generation change
opaque to Kaj semantics
```

---

# PageGeneration

Initial generation:

```text
1
```

or repository-equivalent deterministic start.

Increment on:

```text
successful navigation
page-changing click
fixture-defined interactive-structure refresh
```

Do not increment for simple observe.

Ordinary scroll need not increment.

Typing/select may increment only if fixture semantics invalidate element references.

Document actual reference-adapter rule consistently.

---

# `observe`

Implement exact Browser@1 return type.

Test:

```text
URL
title
generation
viewport
elements
deterministic ordering
```

Repeated observe with no state change should return semantically identical observation.

---

# `navigate`

Validate URL.

Use fixture registry only.

Test:

```text
valid fixture URL
unknown URL
invalid URL
navigation generation change
returned observation
```

---

# `click`

Validate:

```text
current generation
element ID
visible
enabled
clickable
```

Test errors:

```text
stale_element
element_not_found
element_not_interactable
action_failed where fixture requests it
```

Support deterministic transitions.

---

# `type_text`

Support text-entry fixtures.

Test:

```text
valid typing
stale target
wrong element kind
disabled element
sensitive field redaction
state retained on observe
```

Do not leak secret values.

---

# `select`

Support deterministic options.

Test:

```text
valid option
invalid_selection
wrong target kind
stale target
```

---

# `scroll`

Implement:

```text
relative delta
clamping
updated viewport
deterministic observation
```

Test positive/negative movement and boundaries.

---

# BrowserError Coverage

Create fixtures/tests that exercise all Browser@1 error variants:

```text
unavailable
invalid_url
navigation_failed
element_not_found
stale_element
element_not_interactable
invalid_selection
action_failed
```

Ensure each is returned as ordinary:

```text
Result.err(BrowserError)
```

---

# Grants

Use existing capability grant machinery.

Tests must prove:

```text
ungranted operation is rejected before adapter invocation
```

Instrument reference adapter invocation count/log if useful.

---

# Sync Adapter Path

Default adapter invocation completes immediately.

Test through actual:

```text
CapabilityRegistry
TaskCapabilityBindings
TaskInstance execution
```

not only direct adapter unit calls.

---

# Deterministic Async Path

Allow selected fixture operations to return/present a pending host request compatible with Agentic Kaj's capability suspension machinery.

Test:

```text
task -> WAITING_FOR_CAPABILITY
CapabilityRequestId created
valid completion resumes
operation applied once
continuation resumes after call
```

---

# Stale / Duplicate Capability Response

Test generic runtime behavior with browser adapter:

```text
wrong request ID rejected
duplicate completion rejected
response after cancellation rejected
wrong task ID rejected
```

---

# Persistence

Persist/reconstruct reference-browser host state through a test-host store or resolver.

At minimum preserve:

```text
HostBindingId
current page
generation
viewport
non-sensitive fixture state
selection state
```

Do not persist adapter object in TaskSnapshot.

---

# Rebinding

Test:

```text
TaskSnapshot restored
Browser binding descriptor loaded
CapabilityRegistry resolver finds same HostBindingId
ReferenceBrowserAdapter recreated/resolved
task resumes
```

Missing host resource:

```text
resume blocked
```

---

# Multi-Session Isolation

Create at least two browser resources:

```text
browser-A
browser-B
```

Verify:

```text
navigation A does not change B
typing A does not change B
generation A independent from B
```

---

# Shared Binding Test

Optionally bind two tasks to same HostBindingId deliberately and verify shared host state behaves as expected.

This is a host-policy test, not default behavior.

---

# Planner Compatibility

Using existing planner schema/request machinery, run at least one deterministic planner/task fixture against the reference Browser.

Do not add real LLM integration.

The fixture may use a predefined PlannerProposal.

---

# Cross-Feature Tests

Add representative workflows such as:

```text
navigate -> observe -> click
type -> click -> navigation
browser + confirm
browser + persistence
browser child task
browser plan execution
```

Keep them deterministic.

---

# Event Trace

Verify browser workflows emit stable runtime events through existing conformance tracing.

Do not create a second browser-specific event system.

---

# Diagnostics

Adapter misuse/internal host failures should map into existing capability/runtime diagnostics.

Expected Browser errors should remain Kaj `BrowserError` values.

Do not leak Python traceback for normal Browser fixture errors.

---

# Required Tests

Reference model:

```text
page fixture construction
element fixture construction
deterministic IDs
deterministic observations
```

Observe:

```text
initial page
repeat observe
unavailable browser
```

Navigate:

```text
valid URL
invalid URL
unknown URL
generation increments
```

Click:

```text
valid click
navigation click
state-change click
stale generation
unknown element
disabled/invisible/not-interactable
action_failed
```

Type:

```text
valid text
sensitive redaction
stale element
invalid target
```

Select:

```text
valid selection
invalid selection
stale element
```

Scroll:

```text
relative movement
clamping
no unnecessary generation change
```

Capability runtime:

```text
grant allowed
grant denied pre-adapter
sync completion
async wait
async resume
stale response
duplicate response
```

Persistence:

```text
binding descriptor
host state restore
same HostBindingId
same logical page/generation
missing host blocks resume
```

Isolation:

```text
two sessions independent
```

Regression:

```text
Pure Kaj
Agentic Kaj Conformance
Integration Checkpoints 1–2
Integration Checkpoint 3
mkdocs build --strict
```

---

# Out of Scope

Do not implement:

```text
ChalokBrowserAdapter
PlaywrightBrowserAdapter
WKWebView
network access
HTML parser
JavaScript engine
real websites
real planner API
browser safety approvals
production browser persistence
screenshots
downloads
tabs
PDFs
```

---

# Definition of Done

```text
[ ] ReferenceBrowser model exists
[ ] deterministic page fixtures exist
[ ] deterministic element fixtures exist
[ ] ReferenceBrowserAdapter implements Browser@1

[ ] ElementId deterministic
[ ] PageGeneration invalidation works
[ ] observe works
[ ] navigate works
[ ] click works
[ ] type_text works
[ ] select works
[ ] scroll works

[ ] all BrowserError variants covered
[ ] expected errors returned as Result.err

[ ] capability grants enforced
[ ] denied operation does not invoke adapter

[ ] sync mode works
[ ] deterministic async mode works
[ ] WAITING_FOR_CAPABILITY exercised
[ ] stale/duplicate completions rejected

[ ] HostBindingId rebinding works
[ ] reference browser state restores
[ ] adapter object not persisted
[ ] missing host resource blocks resume

[ ] multi-session isolation passes

[ ] planner-compatible deterministic workflow passes
[ ] event trace works

[ ] docs/integrations/browser-reference-adapter.md matches implementation
[ ] mkdocs navigation updated
[ ] mkdocs build --strict passes

[ ] Pure Kaj suite passes
[ ] Agentic Kaj suite/conformance passes
[ ] Integration Checkpoints 1–2 pass
[ ] Integration Checkpoint 3 tests pass
```

---

# Completion Report

```text
Kaj Integration Checkpoint 3 — Browser Reference Adapter

Status:
COMPLETE / INCOMPLETE

Files changed:
- ...

Reference browser:
- model: PASS/FAIL
- page fixtures: PASS/FAIL
- element fixtures: PASS/FAIL
- deterministic IDs: PASS/FAIL
- PageGeneration: PASS/FAIL

Browser operations:
- observe: PASS/FAIL
- navigate: PASS/FAIL
- click: PASS/FAIL
- type_text: PASS/FAIL
- select: PASS/FAIL
- scroll: PASS/FAIL

Errors:
- unavailable: PASS/FAIL
- invalid_url: PASS/FAIL
- navigation_failed: PASS/FAIL
- element_not_found: PASS/FAIL
- stale_element: PASS/FAIL
- element_not_interactable: PASS/FAIL
- invalid_selection: PASS/FAIL
- action_failed: PASS/FAIL

Capability runtime:
- grants: PASS/FAIL
- denied pre-adapter: PASS/FAIL
- sync completion: PASS/FAIL
- async wait/resume: PASS/FAIL
- stale completion rejection: PASS/FAIL
- duplicate completion rejection: PASS/FAIL

Persistence:
- binding descriptor: PASS/FAIL
- host state persistence: PASS/FAIL
- rebind same HostBindingId: PASS/FAIL
- missing host blocks resume: PASS/FAIL

Isolation/integration:
- multi-session isolation: PASS/FAIL
- planner compatibility: PASS/FAIL
- event trace: PASS/FAIL

Documentation:
- browser-reference-adapter.md: PASS/FAIL
- mkdocs navigation: PASS/FAIL
- mkdocs build --strict: PASS/FAIL

Regression:
- Pure Kaj: PASS/FAIL
- Agentic Kaj: PASS/FAIL
- Agentic Conformance: PASS/FAIL
- Integration Checkpoints 1–2: PASS/FAIL
- Integration Checkpoint 3: PASS/FAIL

Deferred intentionally:
- Chalok adapter
- real browser engine
- real planner integration
- browser safety/approval integration

Known issues:
- ...
```
