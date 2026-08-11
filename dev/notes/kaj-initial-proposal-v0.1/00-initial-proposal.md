# 0. Kaj Initial Language Proposal

## Proposal statement

Kaj is an independent, open-source programming language for ordinary computation and intelligent-agent work.

Its distinctive focus is the reliable expression of:

- goals,
- plans,
- computation,
- loops and recursion,
- mathematics,
- external-world actions,
- observations,
- evidence-backed knowledge,
- human collaboration,
- verification,
- recovery,
- and optional world-model prediction.

Kaj should remain general enough for web agents, robotics, vision/navigation, audio systems, simulation, API automation, filesystem work, and future environments.

## Initial technical direction

```text
Paradigm:
  imperative core + declarative contracts

Typing:
  strongly typed, static-by-default, aggressively inferred

State:
  immutable `let` by default, explicit `var`

Computation:
  functions, math, collections, loops, recursion, pattern matching

Agent semantics:
  task, step, goal, success, require, expect, verify

Human semantics:
  ask, choose, confirm, inform, handoff

Knowledge semantics:
  observe, learn, provenance, conflict preservation

Effects:
  explicit and capability-based

Capabilities:
  `use web`, later vision/robot/audio/etc.

Model integration:
  LLM initially emits schema-constrained Kaj AST JSON

Compilation:
  AST/source → typed semantic AST → Task IR

Execution:
  Task IR → host policy/runtime → capability provider

World models:
  optional predict-before-act and verify-after-act layer

CLI:
  `kaj file.kaj`

Source extension:
  `.kaj`
```

## First implementation philosophy

Build semantics from the inside out:

```text
AST
→ type system
→ effect model
→ task semantics
→ Task IR
→ formatter
→ Web capability
→ host integration
→ source parser
→ CLI/editor tooling
```

This lets Kaj immediately serve model-generated plans without freezing source syntax prematurely.

## Project boundary

Kaj should be its own repository and project.

```text
Kaj
 ↑
Berkbrain
 ↑
Chalok
```

Kaj must not depend on Berkbrain, Chalok, FastAPI, PostgreSQL, or WebKit.

Berkbrain is the first host. Chalok Web is the first production capability/runtime.

## Initial open-source posture

Proposed:

```text
Apache-2.0
maintainer-led governance
public Kaj Improvement Proposal (KIP) process
public specification
public reference compiler
public conformance tests
```

A foundation is not required at project inception.

## Definition of success for Kaj 0.1

Kaj 0.1 should make it possible to:

1. represent typed ordinary programs and tasks as AST,
2. reject invalid type/effect combinations,
3. lower valid programs into deterministic Task IR,
4. emit canonical human-readable `.kaj` source,
5. run ordinary pure Kaj computations,
6. express task contracts and structured human interactions,
7. define one real capability family: Web,
8. integrate with a host runtime without Kaj depending on that host.
