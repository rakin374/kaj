# Kaj Integrations

The Integration Track connects Agentic Kaj to real host applications through standard capability packages and host adapters.

## Documents

- [Standard Capability Architecture](standard-capabilities.md) — how standard capabilities are identified, packaged, imported, registered, bound, persisted, and implemented by hosts
- [Standard Browser Capability](../capabilities/browser.md) — frozen `Browser@1` contract, supporting types, and operation signatures
- [Browser Reference Adapter](browser-reference-adapter.md) — deterministic mock host for `Browser@1` used in integration tests

## Scope

Integration documentation covers host/runtime architecture for external systems. It does not redefine Agentic Kaj task, lifecycle, contract, or planner semantics.

The first production integration target is Chalok browser automation. Checkpoint 1 established the reusable standard capability architecture. Checkpoint 2 freezes the host-independent `Browser@1` contract. Checkpoint 3 adds the deterministic Browser Reference Adapter used to validate `Browser@1` semantics without a real browser engine.
