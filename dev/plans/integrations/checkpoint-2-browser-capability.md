# Kaj Integration Track — Checkpoint 2: Standard Browser Capability

**Track:** Kaj Integrations  
**Checkpoint:** 2  
**Recommended path:** `dev/plans/integrations/checkpoint-2-browser-capability.md`

---

# Goal

Implement and freeze the host-independent standard Browser capability contract.

Authoritative semantics:

```text
docs/capabilities/browser.md
```

This checkpoint builds on Integration Checkpoint 1.

Do not implement Chalok or Playwright adapters yet.

---

# Scope

Implement:

```text
std.capabilities.browser module
Browser@1 capability identity
ElementId
PageGeneration
BrowserElement
BrowserViewport
PageObservation
BrowserError
observe
navigate
click
type_text
select
scroll
standard import/export behavior
AST/type resolution through existing capability system
planner-visible schema compatibility
standard capability tests
docs integration
```

---

# Standard Module

Create:

```text
std.capabilities.browser
```

Recommended physical location:

```text
std/capabilities/browser.kaj
```

unless repository conventions strongly favor a package directory.

The logical module identity is authoritative.

---

# Capability Identity

Use:

```text
std.capabilities.browser.Browser@1
```

Verify it flows through:

```text
CapabilityIdentity
registry
binding descriptors
planner-visible schemas
persistence
```

---

# Supporting Types

Implement standard Kaj types conceptually:

```kaj
newtype ElementId = String
newtype PageGeneration = Int
```

Define:

```kaj
type BrowserViewport {
    width: Int
    height: Int
    scroll_x: Int
    scroll_y: Int
}
```

Define a minimal:

```kaj
type BrowserElement {
    id: ElementId
    role: String
    text: String
    enabled: Bool
    visible: Bool
}
```

If the current type system cleanly supports useful optional fields such as:

```text
name
value
placeholder
selected
checked
```

they may be added only if their semantics are explicitly documented and host-independent.

Do not bloat BrowserElement merely because Chalok currently exposes more data.

---

# PageObservation

Implement:

```kaj
type PageObservation {
    url: String
    title: String
    generation: PageGeneration
    viewport: BrowserViewport
    elements: List<BrowserElement>
}
```

Keep it deterministic and serializable.

---

# BrowserError

Implement an enum compatible with current Kaj enum syntax.

At minimum model:

```text
unavailable
invalid_url
navigation_failed(message: String)
element_not_found
stale_element
element_not_interactable
invalid_selection
action_failed(message: String)
```

Names should match the public spec unless the language's enum naming convention requires a mechanical adjustment.

Do not expose Python/Swift/Playwright error types.

---

# Browser Capability

Define:

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

Adapt multiline syntax only as required by the existing parser/formatter.

---

# Element Identity

Freeze:

```text
ElementId is opaque
ElementId is valid only for its PageGeneration
```

The standard contract must make stale-reference checking possible.

Do not make ElementId a CSS selector or XPath.

---

# Page Generation

Ensure `PageGeneration` is nominal and serializable.

The future adapter is responsible for changing generation whenever previously observed element references become unsafe.

Checkpoint 2 does not implement browser host invalidation logic.

It defines the contract.

---

# Successful Action Results

All mutating operations:

```text
navigate
click
type_text
select
scroll
```

return:

```text
Result<PageObservation, BrowserError>
```

This ensures callers receive an updated generation/state after every successful action.

---

# Sensitive Data Semantics

Do not standardize raw password/secret value exposure.

If BrowserElement later contains a `value` field, sensitive fields must be representable without revealing the secret.

Add tests/docs if such a field is included.

---

# Explicit Non-Features

Do not add:

```text
raw JavaScript evaluation
raw HTML
full DOM serialization
querySelector
XPath execution
coordinate click
file upload
download APIs
history/tab management
cookies
localStorage
screenshots
PDF access
site-specific actions
shopping actions
checkout
```

These may be future capabilities/versions.

---

# Standard Import Tests

Verify:

```kaj
import std.capabilities.browser
```

resolves.

Verify qualified use:

```kaj
use std.capabilities.browser.Browser as browser
```

resolves.

If ordinary import alias/unqualified rules exist, verify those too.

---

# Type Resolution Tests

Verify all supporting types resolve from the standard module.

At minimum:

```text
ElementId
PageGeneration
BrowserElement
BrowserViewport
PageObservation
BrowserError
Browser
```

---

# Capability Operation Type Tests

Verify exact signatures.

Examples:

```text
observe -> Result<PageObservation, BrowserError>
navigate(String) -> Result<PageObservation, BrowserError>
click(ElementId, PageGeneration) -> Result<PageObservation, BrowserError>
type_text(ElementId, PageGeneration, String)
select(ElementId, PageGeneration, String)
scroll(Int, Int)
```

Wrong arguments must fail at type checking.

---

# Capability Identity Tests

Verify the standard capability resolves to:

```text
module = std.capabilities.browser
name = Browser
major = 1
```

Ensure binding descriptor persistence preserves this identity.

---

# Planner Schema Compatibility

Using the existing planner-visible capability schema machinery, verify Browser@1 exposes:

```text
operation names
parameter types
return types
supporting type names
granted-operation subset
```

Do not add planner-specific Browser semantics.

---

# Mock Fixtures

Checkpoint 2 does not implement the full reference Browser adapter, but add lightweight contract fixtures sufficient to validate:

```text
Kaj types construct/serialize
BrowserError values construct
PageObservation values construct
CapabilityIdentity resolves
operation signatures are stable
```

The deterministic behavioral adapter comes in Checkpoint 3.

---

# Formatter

Run canonical formatting over:

```text
std/capabilities/browser.kaj
```

Ensure idempotence.

Do not introduce special formatting rules for standard capabilities.

---

# AST JSON

Verify standard capability declarations and supporting types serialize deterministically through existing AST JSON.

No runtime browser state appears in source AST JSON.

---

# Docs

Create/update:

```text
docs/capabilities/browser.md
docs/integrations/index.md
```

Update MkDocs navigation as appropriate.

Public docs contain stable Browser semantics only.

---

# Required Tests

Module/package:

```text
browser std module resolves
qualified Browser use resolves
supporting types resolve
unknown sibling capability still errors normally
```

Identity:

```text
Browser capability identity = std.capabilities.browser.Browser@1
identity persists through binding descriptor
```

Types:

```text
ElementId nominal
PageGeneration nominal
BrowserViewport construct/type-check
BrowserElement construct/type-check
PageObservation construct/type-check
BrowserError cases construct/type-check
```

Operations:

```text
observe signature
navigate signature
click signature
type_text signature
select signature
scroll signature
wrong argument count rejected
wrong argument type rejected
unknown operation rejected
```

Serialization/tooling:

```text
AST JSON deterministic
formatter idempotent
standard module import graph deterministic
```

Planner integration:

```text
Browser schema planner-visible
grant subset visible
no adapter/native fields exposed
```

Regression:

```text
Pure Kaj
Agentic Kaj Conformance
Integration Checkpoint 1
Integration Checkpoint 2
mkdocs build --strict
```

---

# Out of Scope

Do not implement:

```text
MockBrowserAdapter behavior
ChalokBrowserAdapter
Playwright adapter
WKWebView integration
real navigation
real clicking
real typing
real scrolling
browser request transport
browser safety approvals
real planner integration
persistent real browser session restoration
```

---

# Definition of Done

```text
[ ] std.capabilities.browser module exists
[ ] Browser@1 identity is correct

[ ] ElementId implemented
[ ] PageGeneration implemented
[ ] BrowserViewport implemented
[ ] BrowserElement implemented
[ ] PageObservation implemented
[ ] BrowserError implemented

[ ] observe signature frozen
[ ] navigate signature frozen
[ ] click signature frozen
[ ] type_text signature frozen
[ ] select signature frozen
[ ] scroll signature frozen

[ ] qualified use resolves
[ ] supporting types resolve
[ ] operation typing works
[ ] wrong arguments rejected

[ ] Browser identity persists in binding descriptor
[ ] planner-visible schema exposes contract correctly
[ ] no native adapter details leak

[ ] AST JSON deterministic
[ ] formatter idempotent

[ ] docs/capabilities/browser.md matches implementation
[ ] mkdocs navigation updated
[ ] mkdocs build --strict passes

[ ] Pure Kaj suite passes
[ ] Agentic Kaj suite/conformance passes
[ ] Integration Checkpoint 1 passes
[ ] Integration Checkpoint 2 tests pass
```

---

# Completion Report

```text
Kaj Integration Checkpoint 2 — Standard Browser Capability

Status:
COMPLETE / INCOMPLETE

Files changed:
- ...

Module:
- std.capabilities.browser: PASS/FAIL
- qualified use: PASS/FAIL
- Browser@1 identity: PASS/FAIL

Types:
- ElementId: PASS/FAIL
- PageGeneration: PASS/FAIL
- BrowserViewport: PASS/FAIL
- BrowserElement: PASS/FAIL
- PageObservation: PASS/FAIL
- BrowserError: PASS/FAIL

Operations:
- observe: PASS/FAIL
- navigate: PASS/FAIL
- click: PASS/FAIL
- type_text: PASS/FAIL
- select: PASS/FAIL
- scroll: PASS/FAIL
- wrong argument rejection: PASS/FAIL

Integration:
- binding descriptor identity: PASS/FAIL
- planner schema: PASS/FAIL
- AST JSON: PASS/FAIL
- formatter: PASS/FAIL

Documentation:
- browser.md: PASS/FAIL
- mkdocs navigation: PASS/FAIL
- mkdocs build --strict: PASS/FAIL

Regression:
- Pure Kaj: PASS/FAIL
- Agentic Kaj: PASS/FAIL
- Agentic Conformance: PASS/FAIL
- Integration Checkpoint 1: PASS/FAIL
- Integration Checkpoint 2: PASS/FAIL

Deferred intentionally:
- Browser reference adapter
- Chalok adapter
- real browser execution
- planner integration

Known issues:
- ...
```
