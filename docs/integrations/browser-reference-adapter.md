# Browser Reference Adapter

The Browser Reference Adapter is the deterministic reference implementation of the standard `Browser@1` capability.

It exists to validate browser-capability semantics without depending on:

```text
Chalok
WKWebView
Playwright
Chromium
network access
real websites
```

The adapter must behave like a real Browser capability host while remaining fully deterministic and testable.

---

## 1. Purpose

The reference adapter proves that the standard Browser capability is executable and internally coherent.

It should validate:

```text
Browser@1 operation semantics
PageObservation construction
ElementId identity
PageGeneration invalidation
typed BrowserError behavior
task capability grants
async capability suspension/resume
persistence and rebinding
stale request protection
deterministic browser state transitions
```

It is not a toy parser.

It should model enough browser behavior to exercise realistic Agentic Kaj workflows.

---

## 2. Capability identity

The reference adapter implements:

```text
std.capabilities.browser.Browser@1
```

Its adapter metadata must report the exact capability identity/version.

---

## 3. Host binding identity

Each reference browser instance has a stable opaque:

```text
HostBindingId
```

Example conceptually:

```text
mock-browser-session-A
```

Multiple reference browser instances may coexist.

---

## 4. Deterministic browser model

The reference adapter uses an in-memory browser model.

Conceptually:

```text
ReferenceBrowser
    current_url
    current_page
    generation
    viewport
    page_registry
```

Pages are predefined deterministic fixtures.

---

## 5. Page registry

The adapter should support a registry of mock pages.

Conceptually:

```text
URL -> ReferencePage
```

A page contains:

```text
url
title
viewport/content metadata
elements
action transitions
```

No network access is required.

---

## 6. Reference elements

Each page exposes deterministic browser elements.

Conceptually:

```text
ReferenceElement
    stable fixture key
    role
    text
    enabled
    visible
    selectable values if applicable
    text-entry capability if applicable
    click behavior
```

The adapter converts these into standard:

```text
BrowserElement
```

Kaj values.

---

## 7. ElementId generation

`ElementId` values must be deterministic for a given page generation.

They must remain opaque to Kaj.

A simple internal strategy is acceptable, such as combining:

```text
page fixture key
element fixture key
generation
```

as long as:

```text
IDs are unique within a generation
old-generation IDs are rejected as stale
```

---

## 8. PageGeneration

The adapter owns a numeric logical generation.

Initial generation may begin at:

```text
1
```

Generation changes whenever previous element references become invalid.

At minimum:

```text
successful navigation
successful page-changing click
explicit fixture-defined DOM refresh
```

must produce a new generation.

---

## 9. Observation

`observe()` returns:

```text
Result.ok(PageObservation)
```

for the current page when available.

The result must include:

```text
current URL
title
current generation
viewport
current visible/interactable fixture elements
```

---

## 10. Unavailable browser

A reference browser may be placed into an unavailable state for tests.

In that state:

```text
observe
navigate
click
type_text
select
scroll
```

return:

```text
err(BrowserError.unavailable)
```

unless a fixture explicitly models a more specific error.

---

## 11. Navigation

`navigate(url)` resolves only against the reference page registry.

Valid URL:

```text
switch current page
increment generation
reset or update viewport as fixture defines
return new PageObservation
```

Unknown or unsupported URL:

```text
err(BrowserError.navigation_failed(...))
```

Malformed URL:

```text
err(BrowserError.invalid_url)
```

---

## 12. Click

`click(element, generation)` validates:

```text
generation matches current generation
element exists
element visible
element enabled
element supports click
```

If generation mismatches:

```text
err(stale_element)
```

If element cannot be found:

```text
err(element_not_found)
```

If present but not interactable:

```text
err(element_not_interactable)
```

---

## 13. Click transitions

Fixture elements may define deterministic click effects.

Examples:

```text
navigate to another fixture page
toggle a checkbox-like state
change visible text
reveal another element
increment generation
```

If the click changes the page/interactive structure such that prior references are unsafe, generation must change.

---

## 14. Typing

`type_text(element, generation, text)` validates stale reference and interactability.

A valid text-entry element stores the typed value in reference browser state.

The returned `PageObservation` reflects the resulting state without violating sensitive-value rules.

---

## 15. Sensitive fields

A fixture may mark a text field as sensitive.

Typed sensitive content must not be exposed in later `PageObservation`.

The adapter may expose:

```text
empty/redacted/omitted visible value
```

according to the frozen BrowserElement schema.

---

## 16. Selecting

`select(element, generation, value)` validates:

```text
element exists
generation current
element supports selection
requested value is allowed
```

Unknown value:

```text
err(invalid_selection)
```

A valid selection updates deterministic browser state.

---

## 17. Scrolling

`scroll(delta_x, delta_y)` updates the current viewport deterministically.

The adapter should clamp positions to fixture-defined page bounds.

No generation increment is required for ordinary scrolling unless the fixture explicitly defines scroll-triggered page invalidation.

---

## 18. Dynamic fixture updates

The adapter should support fixture-defined deterministic DOM-like refreshes.

Example:

```text
click "Load more"
    -> reveal new elements
    -> increment generation
```

This is important for stale-element testing.

---

## 19. Error mapping

The reference adapter should exercise all major `BrowserError` variants.

At minimum provide fixtures/tests for:

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

---

## 20. Result values

Expected browser problems are returned as ordinary:

```text
Result.err(BrowserError)
```

They are not Agentic Kaj runtime failures.

The adapter should reserve capability runtime failure for broken adapter/infrastructure conditions.

---

## 21. Adapter grants

The reference adapter must integrate with task capability grants.

If the task binding grants only:

```text
observe
navigate
```

then:

```text
click
type_text
select
scroll
```

must be rejected by generic capability authorization before adapter invocation.

Tests should verify the adapter method is not called.

---

## 22. Synchronous mode

The reference adapter should support immediate/synchronous operation completion.

This is the default deterministic testing mode.

---

## 23. Asynchronous mode

The reference adapter should also support deterministic pending operations for selected fixtures.

Example:

```text
navigate -> pending
```

The runtime then enters:

```text
waiting_for_capability
```

and produces a `CapabilityRequestId`.

The test host can later resolve the request.

---

## 24. Async completion

A pending reference-browser request may be completed explicitly by the deterministic test host.

The completion must:

```text
validate request identity
apply the fixture transition exactly once
produce typed Browser result
resume exact task continuation
```

---

## 25. Stale async completion

A stale or duplicate completion for a Browser request must be rejected by the generic capability runtime.

The reference adapter should provide tests that prove this.

---

## 26. Persistence

Reference browser capability bindings use:

```text
CapabilityBindingDescriptor
```

and persist:

```text
Browser@1 identity
HostBindingId
granted operations
```

The native adapter instance is not serialized.

---

## 27. Reference browser state persistence

For deterministic restart tests, the host/reference-browser layer should be able to persist or reconstruct the logical browser resource behind a `HostBindingId`.

At minimum restore:

```text
current URL
generation
viewport
fixture element state
typed text/selection state where non-sensitive
```

This state belongs to the host adapter/test host, not Kaj task AST.

---

## 28. Rebinding

On task restore:

```text
CapabilityBindingDescriptor
    ↓
CapabilityRegistry / resolver
    ↓
same HostBindingId
    ↓
ReferenceBrowserAdapter
```

The task must bind back to the same logical reference browser instance.

---

## 29. Missing reference browser

If the persisted HostBindingId cannot be resolved:

```text
task resume is blocked
```

Do not create a new default browser resource silently.

---

## 30. Multi-session isolation

Two task bindings to two reference browser instances must remain isolated.

Operations against:

```text
session A
```

must not mutate:

```text
session B
```

---

## 31. Shared resource policy

The host may intentionally bind multiple tasks to the same reference browser instance.

If it does, they share host resource state.

This should be explicit in test setup.

No implicit cross-task sharing occurs.

---

## 32. Planner use

The reference adapter should be suitable for PlannerAdapter tests.

A planner can receive deterministic `PageObservation` values and propose:

```text
navigate
click
type_text
select
scroll
```

without network nondeterminism.

---

## 33. Human interaction combinations

Reference-browser tasks may combine browser operations with:

```text
ask
choose
confirm
inform
handoff
```

The adapter itself does not implement human interaction.

---

## 34. Child-task combinations

Reference-browser tasks may start child tasks.

Each child resolves its own Browser requirement normally.

The deterministic host may bind children to:

```text
same reference browser
or
different reference browser
```

explicitly.

---

## 35. No browser-engine emulation requirement

The adapter does not need to implement:

```text
HTML parsing
CSS layout
JavaScript
browser event loop
network stack
real accessibility tree
```

It models the Browser capability contract, not a complete browser engine.

---

## 36. Fixture readability

Reference pages should be easy to author and inspect.

Prefer explicit fixture data over opaque generated state.

Example conceptually:

```text
home page
    Search textbox
    Search button

results page
    Product A link
    Product B link
```

---

## 37. Deterministic identifiers

Tests must be able to compare:

```text
PageGeneration
ElementId
PageObservation
BrowserError
```

without random ordering or unstable IDs.

---

## 38. Event trace

Reference browser execution should work cleanly with Agentic Kaj's structured event trace.

Browser-related task tests should be able to observe:

```text
capability_requested
capability_completed
task_state_changed
step_started
step_completed
```

---

## 39. No host leakage

Reference adapter internals must not appear in Kaj-visible values or diagnostics.

Do not expose:

```text
Python dataclass repr
fixture object path
memory address
host exception class
```

---

## 40. Summary

The Browser Reference Adapter freezes:

```text
deterministic in-memory Browser@1 implementation
predefined page fixtures
deterministic elements and IDs
generation-based stale reference handling
typed BrowserError behavior
sync and deterministic async operation support
grant enforcement through generic capability runtime
persistence/rebinding through HostBindingId
multi-session isolation
no network dependency
no real browser engine requirement
```
