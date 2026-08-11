# Kaj Documentation Guide

**Purpose:** Explain how Kaj documentation is organized, where different kinds of information belong, and how contributors should navigate the repository.

---

# 1. Overview

Kaj separates documentation into three major categories:

```text
docs/
    How Kaj works today.

proposals/
    How Kaj may change.

dev/
    How Kaj is currently being built.
```

This separation is intentional.

It prevents unfinished implementation notes, historical design discussions, and active language documentation from becoming mixed together.

The most important rule is:

> **If you want to know how Kaj currently works, read `docs/`.**

---

# 2. Documentation Structure

The recommended Kaj repository layout is:

```text
kaj/
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
├── SECURITY.md
├── CODE_OF_CONDUCT.md
├── mkdocs.yml
│
├── docs/
│   ├── index.md
│   │
│   ├── getting-started/
│   ├── language/
│   ├── compiler/
│   ├── internals/
│   ├── design/
│   ├── roadmap/
│   └── archive/
│
├── proposals/
│   ├── README.md
│   ├── TEMPLATE.md
│   ├── draft/
│   ├── accepted/
│   └── rejected/
│
├── dev/
│   ├── plans/
│   ├── decisions/
│   └── notes/
│
├── examples/
├── schemas/
├── src/
└── tests/
```

---

# 3. `docs/` — Current Kaj Documentation

`docs/` is the authoritative documentation for Kaj as it exists today.

If a language feature is implemented and supported, it should be documented here.

Do not put speculative or unfinished language behavior in the authoritative language reference.

---

## 3.1 `docs/getting-started/`

For new Kaj users.

Typical files:

```text
installation.md
hello-kaj.md
basic-syntax.md
first-program.md
```

These should answer questions such as:

- How do I install Kaj?
- How do I run a Kaj program?
- What does a simple Kaj program look like?
- What commands does the Kaj CLI expose?

This section should be tutorial-oriented rather than exhaustive.

---

## 3.2 `docs/language/`

This is the main language reference.

It describes the actual semantics of implemented Kaj features.

Example structure:

```text
docs/language/
├── index.md
├── lexical-structure.md
├── values-and-types.md
├── bindings-and-mutability.md
├── operators.md
├── strings.md
├── functions.md
├── scope.md
├── control-flow.md
├── lists-and-maps.md
├── records.md
├── enums.md
├── pattern-matching.md
├── optional-and-result.md
├── newtypes.md
└── modules.md
```

A language page should generally contain:

```text
Overview
Syntax
Semantics
Examples
Invalid examples
Type rules
Compiler diagnostics
Notes
```

Example:

```kaj
let x = 10
var y = 20
```

The documentation should clearly state:

```text
let
    creates an immutable binding

var
    creates a mutable binding
```

If behavior changes, this directory must be updated.

---

# 4. `docs/compiler/` — Toolchain Documentation

This section documents Kaj's compiler and developer-facing tools.

Typical files:

```text
cli.md
ast-json.md
diagnostics.md
formatter.md
versions.md
```

Examples of topics:

```text
kaj check
kaj run
kaj fmt
kaj ast
```

This section also explains the relationship between:

```text
.kaj source
Kaj AST
Kaj AST JSON
compiler output
```

This is user/tooling documentation, not low-level compiler implementation notes.

---

# 5. `docs/internals/` — Contributor Architecture

This section is for contributors working on Kaj itself.

Typical files:

```text
architecture.md
compiler-pipeline.md
lexer.md
parser.md
ast.md
resolver.md
type-checker.md
interpreter.md
formatter.md
testing.md
```

Example compiler pipeline:

```text
source
  ↓
lexer
  ↓
parser
  ↓
AST
  ↓
name resolution
  ↓
type checking
  ↓
semantic validation
  ↓
interpreter/runtime
```

Use this section to explain:

- how compiler components interact,
- internal invariants,
- implementation architecture,
- contributor-facing extension points.

Do not use it as a scratchpad.

---

# 6. `docs/design/` — Stable Design Principles

This section documents architectural principles that are broader than individual syntax rules.

Examples:

```text
language-philosophy.md
ast-first-design.md
static-typing.md
explicit-effects.md
agent-machine-interface.md
```

Examples of appropriate principles:

> Kaj source and Kaj AST JSON are two representations of the same program.

> Kaj should prefer explicit state changes and effects over hidden behavior.

> The compiler remains deterministic and does not depend on an LLM.

These documents explain the reasoning behind the architecture without necessarily defining every syntax detail.

---

# 7. `docs/roadmap/` — What Is Being Built

Roadmap files describe planned implementation stages.

Suggested files:

```text
status.md
pure-language.md
agent-layer.md
asset-layer.md
```

This directory answers:

> What exists today, and what is planned next?

It should not be treated as the current language specification.

A useful status file may contain:

```text
Feature               Status
--------------------------------
Lexer                 Implemented
Parser                In progress
Functions             Planned
Records               Planned
Agent tasks           Future
Capabilities          Future
Asset layer           Future
```

---

# 8. `docs/archive/` — Historical Documentation

Older design documents should be preserved rather than deleted when useful, but they should not remain mixed into current documentation.

Place outdated material under:

```text
docs/archive/
```

Archived documents should begin with a warning such as:

```text
ARCHIVED DESIGN DOCUMENT

This document reflects an earlier Kaj design and is not authoritative.

See `docs/language/` and accepted proposals for current behavior.
```

This preserves project history without confusing contributors.

---

# 9. `proposals/` — Kaj Improvement Proposals

`proposals/` contains proposed changes to Kaj.

A proposal should be used when changing public Kaj behavior, such as:

- syntax,
- semantics,
- type-system rules,
- AST schema,
- module behavior,
- capability semantics,
- agent semantics,
- asset semantics,
- public interoperability protocols.

Kaj uses lightweight **Kaj Improvement Proposals (KIPs)**.

Suggested structure:

```text
proposals/
├── README.md
├── TEMPLATE.md
├── draft/
├── accepted/
└── rejected/
```

Example:

```text
proposals/draft/KIP-0021-result-propagation.md
```

A KIP should normally contain:

```text
Summary
Motivation
Proposed syntax
Semantics
Examples
Alternatives
Compatibility
Open questions
```

---

# 10. Proposal Lifecycle

A simple lifecycle is sufficient:

```text
idea
  ↓
draft KIP
  ↓
discussion
  ↓
accepted or rejected
  ↓
implementation
  ↓
tests
  ↓
language documentation updated
```

Once a proposal is implemented, the authoritative description belongs in:

```text
docs/language/
```

The proposal remains as historical design context.

---

# 11. What Does Not Need a KIP

A KIP is generally not necessary for:

- bug fixes,
- performance improvements,
- refactors,
- documentation fixes,
- additional tests,
- purely internal compiler changes.

If the observable Kaj language does not change, a normal issue and pull request are usually sufficient.

---

# 12. `dev/` — Active Maintainer Work

`dev/` contains active implementation working material.

This is not the Kaj language reference.

Suggested structure:

```text
dev/
├── plans/
├── decisions/
└── notes/
```

Examples:

```text
dev/plans/pure-language-v0.md
dev/plans/parser-refactor.md
dev/decisions/parser-precedence.md
dev/notes/type-checker-investigation.md
```

This is where maintainers and coding agents may keep:

- checkpoint plans,
- implementation progress,
- TODOs,
- partial implementation notes,
- temporary technical decisions,
- investigation notes,
- verification commands,
- known implementation issues.

---

# 13. Codex / Agent Working Files

Coding agents may update `dev/` continuously.

For example:

```text
dev/plans/pure-language-v0.md
```

might contain:

```text
Current checkpoint:
    Parser

Completed:
    lexer
    source spans
    minimal AST

In progress:
    operator precedence

Implementation decisions:
    negative values use unary minus
    newlines are ordinary whitespace

Known issues:
    multiline strings not implemented

Verification:
    pytest tests/parser
```

These notes are useful to maintainers and contributors, but they are not authoritative language documentation.

When a working decision becomes a real Kaj rule, it should be moved or reflected in the proper public documentation.

---

# 14. Promotion Rule

Information should move through the repository as it becomes more stable.

Typical path:

```text
dev/
    implementation exploration

        ↓

proposals/
    public language/design proposal

        ↓

code + tests
    implemented behavior

        ↓

docs/
    authoritative behavior
```

Not every change needs every stage.

For example, a straightforward parser bug may go directly:

```text
issue
↓
implementation
↓
tests
↓
docs if necessary
```

---

# 15. Repository Root Files

## `README.md`

The project front door.

Keep it short and useful:

- what Kaj is,
- current development status,
- small example,
- installation link,
- documentation link,
- GitHub contribution information.

Do not turn the root README into the complete Kaj specification.

---

## `CONTRIBUTING.md`

Explain:

- development setup,
- test commands,
- lint/type-check commands,
- repository structure,
- pull-request expectations,
- when a KIP is required,
- where documentation changes belong.

---

## `CHANGELOG.md`

Tracks changes between releases.

Suggested categories:

```text
Added
Changed
Fixed
Deprecated
Removed
Breaking
```

---

## `SECURITY.md`

Explain how security issues should be reported.

---

## `CODE_OF_CONDUCT.md`

Defines expected contributor behavior.

---

# 16. Tests as Executable Documentation

Kaj's tests should act as a second specification.

Recommended:

```text
tests/conformance/
├── bindings/
├── functions/
├── control-flow/
├── records/
├── enums/
├── pattern-matching/
└── diagnostics/
```

Examples:

```text
tests/conformance/bindings/let_reassignment_error.kaj
```

Expected result:

```text
ASSIGN_TO_IMMUTABLE
```

Kaj therefore has three complementary sources of truth:

```text
docs/language/
    human-readable semantics

schemas/
    machine-readable structure

tests/conformance/
    executable behavior
```

---

# 17. `examples/`

Examples are different from tests.

Use:

```text
examples/
├── hello.kaj
├── factorial.kaj
├── records.kaj
├── enums.kaj
└── pattern_matching.kaj
```

Examples should be:

- clean,
- readable,
- copyable,
- representative of recommended Kaj style.

Tests may intentionally contain malformed or unusual programs.

---

# 18. Viewing the Documentation

Kaj documentation is plain Markdown.

This makes it usable through several interfaces.

## GitHub

GitHub automatically renders `.md` files.

This is enough during early development.

## Obsidian

The repository or `docs/` directory can be opened directly as an Obsidian vault.

This is useful for maintainers working locally.

## MkDocs

Kaj should use MkDocs for a generated documentation website.

Local preview:

```bash
mkdocs serve
```

This provides:

- browser-based navigation,
- search,
- structured sections,
- readable code examples.

Later the same Markdown can be published to:

```text
docs.kaj-lang.org
```

No custom documentation frontend is required.

---

# 19. Source of Truth Rules

Use these rules whenever documentation conflicts.

## Current language behavior

Source:

```text
docs/language/
+
conformance tests
+
implemented compiler behavior
```

If these disagree, treat it as a project bug that should be resolved.

## Proposed future behavior

Source:

```text
proposals/draft/
```

## Accepted but not yet implemented behavior

Source:

```text
proposals/accepted/
+
roadmap/status
```

It should not be presented as currently supported Kaj syntax.

## Active implementation work

Source:

```text
dev/
```

This is not a public language guarantee.

---

# 20. Contributor Navigation

If you want to...

### Learn Kaj

Read:

```text
docs/getting-started/
docs/language/
examples/
```

### Use the Kaj compiler

Read:

```text
docs/compiler/
```

### Understand how Kaj is implemented

Read:

```text
docs/internals/
```

### Understand why Kaj was designed a certain way

Read:

```text
docs/design/
proposals/accepted/
```

### See what is planned

Read:

```text
docs/roadmap/
```

### Propose a language change

Read:

```text
proposals/README.md
proposals/TEMPLATE.md
```

### Work on the current implementation

Read:

```text
dev/plans/
CONTRIBUTING.md
docs/internals/
```

---

# 21. Documentation Update Rule

A user-visible Kaj behavior change is not complete until all relevant pieces agree:

```text
implementation
+
tests
+
language documentation
```

If a change affects public language semantics, update:

```text
docs/language/
```

If it changes compiler tooling, update:

```text
docs/compiler/
```

If it changes compiler architecture, update:

```text
docs/internals/
```

If it is still exploratory, keep it in:

```text
dev/
```

or:

```text
proposals/
```

---

# 22. Simple Mental Model

The entire documentation system can be remembered as:

```text
docs/
    What Kaj IS.

proposals/
    What Kaj COULD BECOME.

dev/
    What we are DOING RIGHT NOW.

tests/
    What Kaj MUST DO.

examples/
    How Kaj SHOULD LOOK.
```

That distinction should remain stable as the project grows.
