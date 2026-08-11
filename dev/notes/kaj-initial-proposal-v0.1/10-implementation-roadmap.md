# 10. Implementation Roadmap

## Phase 0 — Repository and design baseline

Create standalone Kaj repository with:

```text
README
LICENSE
NOTICE
CONTRIBUTING
SECURITY
GOVERNANCE
CHANGELOG
docs/
proposals/
schemas/
examples/
```

Publish the initial proposal and mark Kaj experimental.

## Phase 1 — Semantic AST and JSON schema

Build first:

- AST node model,
- versioned schema-constrained JSON,
- stable durable task node IDs,
- diagnostic schema,
- source locations optional.

Do **not** build raw textual parser first.

Reason: the first production LLM path can immediately use structured AST.

## Phase 2 — Core type system

Implement:

```text
Bool
Int
Decimal
String
Optional
List
Map
Result
Money
Percent
Duration
Url
Dynamic
```

Implement:

- literal/local inference,
- function parameter checking,
- return inference,
- no implicit truthiness,
- no silent incompatible coercions.

## Phase 3 — Core computation AST/interpreter

Implement semantics for:

```text
let
var
fn
return
if
else
for
while
break
continue
match
```

Initially AST can be tested directly before `.kaj` parser exists.

## Phase 4 — Task semantics

Implement:

```text
task
step
goal
success
invariant
require
expect
verify
```

Build internal task graph representation.

## Phase 5 — Human interaction semantics

Implement:

```text
inform
ask
choose
confirm
handoff
```

Each should lower into typed interaction IR.

## Phase 6 — Effect model and knowledge semantics

Implement:

```text
fn vs step effect restrictions
capability invocation
observe
learn
```

Compiler should reject forbidden world effects inside pure functions.

## Phase 7 — Generic Task IR

Implement normalized IR with:

- actions,
- observations,
- verification,
- requirements,
- human interactions,
- task control,
- memory mutation proposals,
- stable action IDs,
- versioning.

## Phase 8 — Canonical formatter

Build:

```text
AST → canonical Kaj source
```

At this stage an LLM can generate AST and developers can inspect real Kaj source without a parser yet.

## Phase 9 — Web capability v1

Define the first real capability around the actual browser workspace/runtime.

Use stable browser concepts such as:

- tab IDs,
- navigation,
- page interaction,
- observation,
- lifecycle results.

Avoid fictional APIs that the runtime cannot faithfully implement.

## Phase 10 — Berkbrain/Chalok host integration

Pipeline:

```text
user request
 ↓
LLM structured Kaj task patch
 ↓
Kaj compiler
 ↓
Task IR
 ↓
Chalok task memory
 ↓
permissions
 ↓
browser workspace
 ↓
verification
```

The server is the authoritative compilation/policy host.

## Phase 11 — Text lexer/parser

Implement `.kaj` parsing into the exact same AST.

Target round trip:

```text
source
 ↓
AST
 ↓
formatter
 ↓
canonical source
```

## Phase 12 — CLI

Implement:

```bash
kaj file.kaj
kaj check file.kaj
kaj fmt file.kaj
kaj ast file.kaj
kaj ir file.kaj
```

## Phase 13 — Basic standard library

Implement high-value modules/functions for:

- collections,
- math,
- strings/text,
- JSON,
- time,
- typed results.

## Phase 14 — REPL

Implement ordinary interactive computation.

## Phase 15 — Language server

Build `kajls` using the same compiler frontend.

## Phase 16 — Package/capability SDK

Stabilize third-party capability/provider contracts.

## Phase 17 — Generality experiments

Do not claim Kaj is universal until tested.

Build small experimental capabilities for:

```text
vision
robotics/simulation
audio
```

Use those experiments to improve the core language abstractions.

## Phase 18 — World-model host interface

Add optional prediction hooks.

Do not require a world model for ordinary Kaj execution.

## Phase 19 — Model specialization

After meaningful data exists:

- fine-tune models on Kaj AST/source,
- distill smaller planners,
- build domain-specialized planners,
- train world models from structured transitions.

## Recommended first package tree

```text
kaj/
├── kaj/
│   ├── ast/
│   ├── schema/
│   ├── types/
│   ├── compiler/
│   │   ├── validate.py
│   │   ├── resolve.py
│   │   ├── typecheck.py
│   │   ├── effects.py
│   │   ├── controlflow.py
│   │   └── lower.py
│   ├── ir/
│   ├── formatter/
│   ├── diagnostics/
│   └── capabilities/
│       └── core/
├── schemas/
├── tests/
└── examples/
```

## First implementation milestone (M0)

M0 succeeds when:

1. schema-valid AST can represent ordinary computation and a simple task,
2. compiler catches representative type/effect errors,
3. compiler lowers valid AST into deterministic Task IR,
4. formatter emits readable canonical Kaj,
5. golden tests lock the semantic baseline.

No browser automation is required to call the language frontend real.

## Kaj 0.1 milestone

Kaj 0.1 should add:

- source parser,
- `kaj` CLI,
- runnable ordinary Kaj,
- task semantics,
- initial Web capability contract,
- at least one real host integration.
