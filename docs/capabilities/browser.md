# Standard Browser Capability

The standard Browser capability defines a host-independent interface for browser automation in Agentic Kaj.

This document freezes the initial `Browser@1` contract, its supporting Kaj types, element identity rules, page-generation semantics, and typed browser errors.

The contract must work across hosts such as:

```text
Chalok
Playwright
deterministic test browsers
future native browser hosts
```

It must not depend on WKWebView, Chromium, Playwright internals, DOM node objects, or Chalok-specific runtime types.

---

## 1. Capability identity

The standard Browser capability has logical identity:

```text
std.capabilities.browser.Browser@1
```

It is imported through the standard capability namespace.

Conceptually:

```kaj
import std.capabilities.browser

task Browse() -> None {
    use std.capabilities.browser.Browser as browser
    return none
}
```

If normal import rules allow unqualified names, a host/program may use:

```kaj
use Browser as browser
```

after import.

---

## 2. Design goals

`Browser@1` should provide a small, composable set of primitives for ordinary web interaction.

It should support:

```text
observe page state
navigate
click
type text
select an option
scroll
```

Higher-level workflows such as:

```text
shopping
checkout
email
travel booking
form completion
```

must be built from these primitives.

The standard Browser capability must not contain site- or product-specific operations.

---

## 3. Initial operation set

`Browser@1` defines:

```text
observe
navigate
click
type_text
select
scroll
```

Names are part of the versioned contract.

---

## 4. Supporting newtypes

The Browser package defines nominal identifiers.

Recommended:

```kaj
newtype ElementId = String
```

`ElementId` identifies a browser element within a page generation.

It is not a CSS selector, XPath, or raw DOM pointer.

---

## 5. Page generation

Every page observation includes a monotonically changing logical generation.

Conceptually:

```kaj
newtype PageGeneration = Int
```

The host increments or replaces generation whenever previously issued element references may no longer be trusted.

Examples may include:

```text
navigation
full page reload
document replacement
major DOM refresh
host-detected invalidation
```

Generation semantics are host-independent even if hosts detect invalidation differently.

---

## 6. Element reference validity

An `ElementId` is valid only for the page generation from which it was observed.

The runtime/adapter must detect when an operation targets an element reference from an obsolete generation.

Such an operation returns:

```text
stale_element
```

rather than acting on an arbitrary current element.

---

## 7. Browser element model

The standard package defines a structured element record.

Conceptually:

```kaj
type BrowserElement {
    id: ElementId
    role: String
    text: String
    enabled: Bool
    visible: Bool
}
```

The exact initial fields should remain small.

Do not attempt to expose the entire DOM.

---

## 8. Optional element metadata

The initial contract may include additional host-independent fields where clearly useful, such as:

```text
name / accessible label
value
placeholder
selected
checked
```

Only fields that can be represented consistently across browser hosts should be standardized.

Avoid host-specific DOM attributes unless they have clear cross-host meaning.

---

## 9. Browser viewport

Define a host-independent viewport record if needed for scroll and observation.

Conceptually:

```kaj
type BrowserViewport {
    width: Int
    height: Int
    scroll_x: Int
    scroll_y: Int
}
```

All dimensions/offsets should use a single documented logical coordinate convention.

Do not expose host-native geometry objects.

---

## 10. Page observation

Define:

```kaj
type PageObservation {
    url: String
    title: String
    generation: PageGeneration
    viewport: BrowserViewport
    elements: List<BrowserElement>
}
```

A host may internally observe more information, but only standardized fields cross the capability boundary.

---

## 11. Observation scope

`observe()` returns the current browser-visible structured page state.

It should favor information useful for action planning:

```text
URL
title
generation
viewport
interactive/meaningful elements
```

The initial Browser contract should not require full raw HTML or complete DOM serialization.

---

## 12. Interactive element selection

Hosts should return elements suitable for interaction and planning.

Typical element roles may include:

```text
button
link
textbox
checkbox
radio
combobox
option
menuitem
tab
```

The standard contract should not require every DOM node.

---

## 13. Accessibility-first semantics

Where possible, standardized element fields should derive from browser accessibility semantics rather than brittle implementation-specific DOM details.

Preferred concepts:

```text
role
accessible name
visible text
current value
enabled/disabled state
```

This improves portability across hosts.

---

## 14. Sensitive values

Hosts must not expose secret/sensitive field contents unnecessarily.

For sensitive inputs such as password fields:

```text
the observation may identify the field
but should not reveal the secret value
```

A standardized value representation may use:

```text
none
redacted marker
or omitted value
```

depending on the final BrowserElement schema.

---

## 15. Browser errors

Define a standard typed error enum.

Conceptually:

```kaj
enum BrowserError {
    unavailable
    invalid_url
    navigation_failed(message: String)
    element_not_found
    stale_element
    element_not_interactable
    invalid_selection
    action_failed(message: String)
}
```

Keep expected browser failures inside ordinary Kaj `Result`.

---

## 16. Runtime failures versus BrowserError

A normal host/browser failure covered by the capability contract returns:

```text
Result.err(BrowserError)
```

Examples:

```text
stale element
navigation rejected
element not interactable
```

Infrastructure failures outside the normal browser contract remain Agentic Kaj capability runtime failures.

---

## 17. `observe`

Signature:

```kaj
fn observe() -> Result<PageObservation, BrowserError>
```

`observe` does not mutate the page intentionally.

It returns the current structured observation.

---

## 18. `navigate`

Signature:

```kaj
fn navigate(url: String) -> Result<PageObservation, BrowserError>
```

On success:

```text
navigation completes sufficiently for host-defined usable observation
generation reflects the resulting page
returned observation describes the resulting page
```

The host may internally wait for an appropriate load milestone.

The exact browser-engine load event is not part of Kaj semantics.

---

## 19. URL semantics

`navigate` accepts a `String`.

The adapter/host validates URL usability.

Malformed or unsupported URLs return:

```text
invalid_url
```

or another precisely documented BrowserError.

---

## 20. `click`

Signature conceptually:

```kaj
fn click(
    element: ElementId,
    generation: PageGeneration
) -> Result<PageObservation, BrowserError>
```

The generation parameter ensures the target reference is validated against the page state from which it came.

---

## 21. Why generation is explicit

Passing generation explicitly makes stale-reference safety visible in the typed API.

A planner/task that observed:

```text
generation = 12
element = submit-button
```

must act against that same generation.

If the current page is generation 13:

```text
click -> err(stale_element)
```

---

## 22. `type_text`

Signature conceptually:

```kaj
fn type_text(
    element: ElementId,
    generation: PageGeneration,
    text: String
) -> Result<PageObservation, BrowserError>
```

The operation enters text into an interactable text-entry element.

---

## 23. Typing semantics

`type_text` means setting/entering text through browser interaction semantics.

The exact key event sequence is host-specific.

The contract does not require exposing raw keyboard event primitives.

---

## 24. Secret text input

Typing a secret string is permitted if the host policy allows it.

The following subsequent observation must not expose the secret merely because it was typed into a password-like field.

Safety/approval policies remain host/runtime concerns.

---

## 25. `select`

Signature conceptually:

```kaj
fn select(
    element: ElementId,
    generation: PageGeneration,
    value: String
) -> Result<PageObservation, BrowserError>
```

This selects a value on a selectable control such as a combobox/select-like element.

---

## 26. Invalid selection

If the requested selection is not valid for the target control:

```text
err(invalid_selection)
```

The adapter must not silently select an unrelated fallback.

---

## 27. `scroll`

Define a small host-independent scroll API.

Recommended initial signature:

```kaj
fn scroll(
    delta_x: Int,
    delta_y: Int
) -> Result<PageObservation, BrowserError>
```

The offsets use the same logical coordinate convention as `BrowserViewport`.

---

## 28. Scroll semantics

`scroll` is relative.

It requests movement from the current viewport position by:

```text
delta_x
delta_y
```

Hosts may clamp at page boundaries.

A successful result returns an updated observation.

---

## 29. No raw coordinate clicking in Browser@1

The initial standard capability should not expose:

```text
click(x, y)
```

as the primary interaction primitive.

Prefer stable semantic element references.

Coordinate interaction may be introduced later as a separate operation if real hosts prove it necessary.

---

## 30. No raw JavaScript evaluation

`Browser@1` must not expose:

```text
eval_js
execute_script
```

to Kaj tasks.

Those operations are too host-specific and bypass structured authority/safety boundaries.

---

## 31. No raw DOM mutation

The standard capability does not include arbitrary DOM mutation APIs.

Kaj interacts through standardized browser actions.

---

## 32. No site-specific operations

Do not add operations such as:

```text
buy
checkout
search_amazon
send_email
book_flight
```

These are task/workflow semantics, not Browser semantics.

---

## 33. Action result observation

Successful mutating Browser operations should return an updated `PageObservation`.

This gives the caller an immediate new page generation and state.

It reduces the need for a separate `observe()` after every action.

---

## 34. Host async behavior

Browser operations may be asynchronous in real hosts.

Agentic Kaj capability runtime semantics already support:

```text
waiting_for_capability
CapabilityRequestId
```

The Browser contract itself remains expressed as ordinary typed operations.

---

## 35. Stale generation after action

A successful page-changing action may return a new generation.

Example:

```text
before click:
    generation 7

after click:
    generation 8
```

Old element references from generation 7 become stale.

---

## 36. Element ID uniqueness

Within one page generation, element IDs must uniquely identify the elements exposed in that observation.

The exact generation strategy for IDs is host-specific.

---

## 37. Element IDs are opaque

Kaj code/planners may store and pass `ElementId`.

They must not infer host meaning from its underlying string representation.

---

## 38. Deterministic mock behavior

The future Browser reference adapter must be able to produce deterministic:

```text
PageObservation
ElementId
PageGeneration
BrowserError
```

for conformance testing.

The standard contract should avoid fields that make deterministic mocking impractical.

---

## 39. Planner visibility

The planner may receive the Browser capability schema and observations.

The planner should see:

```text
operation signatures
BrowserError
PageObservation
BrowserElement
current grants
```

It must not receive adapter-native objects.

---

## 40. Capability grants

The host may grant a task only a subset of Browser operations.

Example:

```text
observe
navigate
scroll
```

while denying:

```text
click
type_text
select
```

The generic capability grant machinery remains authoritative.

---

## 41. Browser identity and persistence

A persistent Browser binding descriptor stores:

```text
std.capabilities.browser.Browser@1
local alias
HostBindingId
granted operations
```

It does not persist a browser object.

---

## 42. Browser session rebinding

On restore, the host resolves the persisted Browser binding to the original logical browser resource where possible.

If the original resource cannot be restored:

```text
task must not silently bind to a different browser session
```

Later integration checkpoints define Chalok-specific behavior.

---

## 43. Transport independence

`Browser@1` must work when the adapter is:

```text
in-process
remote
WebSocket-backed
RPC-backed
device-backed
```

No transport concept appears in the standard Kaj contract.

---

## 44. Chalok mapping

A future Chalok adapter should be able to map:

```text
PageObservation
BrowserElement
ElementId
PageGeneration
BrowserError
```

onto Chalok's existing browser observation/action system.

This mapping requirement must not cause Chalok-specific fields to enter `Browser@1`.

---

## 45. Versioning

The initial contract is:

```text
Browser@1
```

Incompatible changes to:

```text
operation names
required parameters
return types
core supporting type shapes
stale-element semantics
```

require a new major capability version.

---

## 46. Initial Browser@1 contract

Conceptually:

```kaj
capability Browser {
    fn observe()
        -> Result<PageObservation, BrowserError>

    fn navigate(url: String)
        -> Result<PageObservation, BrowserError>

    fn click(
        element: ElementId,
        generation: PageGeneration
    ) -> Result<PageObservation, BrowserError>

    fn type_text(
        element: ElementId,
        generation: PageGeneration,
        text: String
    ) -> Result<PageObservation, BrowserError>

    fn select(
        element: ElementId,
        generation: PageGeneration,
        value: String
    ) -> Result<PageObservation, BrowserError>

    fn scroll(
        delta_x: Int,
        delta_y: Int
    ) -> Result<PageObservation, BrowserError>
}
```

Exact formatter layout follows ordinary Kaj formatting rules.

---

## 47. Summary

`Browser@1` freezes:

```text
identity:
    std.capabilities.browser.Browser@1

operations:
    observe
    navigate
    click
    type_text
    select
    scroll

structured types:
    ElementId
    PageGeneration
    BrowserElement
    BrowserViewport
    PageObservation
    BrowserError

element references are opaque
element references are generation-scoped
stale element use returns typed error
successful actions return new observations
no raw JS
no raw DOM mutation
no coordinate click in v1
no site-specific operations
no native host-object leakage
sensitive values are not exposed
host grants may restrict operation subset
```
