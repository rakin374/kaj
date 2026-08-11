# 7. Compiler Architecture and Project Layout

## 7.1 Kaj is a standalone project

Kaj should not live inside the Berkbrain monorepo as an internal feature.

Recommended projects:

```text
Projects/
├── kaj/
├── berkbrain/
├── berkbrain-integration/
├── berkbrain-chalok/
├── berkbrain-prism/
└── berkbrain-sonic/
```

## 7.2 Dependency direction

```text
Kaj
 ↑
Berkbrain
 ↑
Chalok integration
```

Never the reverse.

Kaj must not import:

- Berkbrain models,
- FastAPI,
- SQLAlchemy,
- Chalok sessions,
- WebKit,
- user accounts.

## 7.3 Suggested repository layout

```text
kaj/
├── README.md
├── LICENSE
├── NOTICE
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
│
├── docs/
├── proposals/
├── grammar/
├── schemas/
├── examples/
│
├── kaj/
│   ├── ast/
│   ├── parser/
│   ├── types/
│   ├── compiler/
│   ├── ir/
│   ├── formatter/
│   ├── diagnostics/
│   └── capabilities/
│
├── tests/
└── pyproject.toml
```

## 7.4 Initial implementation language

Recommendation: Python reference compiler initially.

Reasons:

- fast iteration,
- existing backend ecosystem,
- easy AST/schema work,
- Pydantic-style validation available,
- compiler performance is not the bottleneck yet.

Do not start with LLVM or a Rust rewrite simply because Kaj is called a compiler.

## 7.5 Compiler pipeline

```text
source / AST JSON
    ↓
parse or deserialize
    ↓
schema validation
    ↓
name resolution
    ↓
type checking
    ↓
effect checking
    ↓
control-flow validation
    ↓
capability resolution
    ↓
semantic validation
    ↓
Task IR lowering
```

## 7.6 Compiler determinism

The compiler itself should not call an LLM.

Given the same:

```text
AST
compiler version
capability definitions
compilation environment
```

it should produce the same diagnostics/IR.

## 7.7 Compilation environment

The compiler should not query application databases.

Instead hosts supply an explicit compilation environment.

Conceptually:

```python
CompilationEnvironment(
    language_version=...,
    capabilities=...,
    symbols=...,
    types=...,
    host_features=...,
)
```

This keeps the compiler reusable and testable.

## 7.8 Compiler vs permission engine

Compiler:

> Is this program valid?

Permission engine:

> May this valid effect execute for this user and state?

Example:

```kaj
web.submit(payment)
```

can compile successfully while runtime returns:

```text
ASK
```

or:

```text
DENY
```

## 7.9 Compiler vs world model

Compiler:

> What does the proposed action mean?

World model:

> What is likely to happen?

Do not mix these responsibilities.

## 7.10 Compiler vs task memory

Compiler validates structure/types/references.

Task memory owns canonical durable state and evidence.

## 7.11 Host runtime responsibilities

Host runtimes may own:

- user identity,
- task persistence,
- run lifecycle,
- permission decisions,
- capability providers,
- task memory,
- human interaction delivery,
- secrets,
- world models,
- recovery,
- logs/metrics,
- billing/usage.

## 7.12 Berkbrain integration

Suggested host package:

```text
berkbrain/backend/app/kaj_runtime/
├── planner_adapter.py
├── compiler_adapter.py
├── execution_service.py
├── task_memory_adapter.py
├── permission_adapter.py
└── world_model_adapter.py
```

Berkbrain imports Kaj as a dependency.

## 7.13 Hosted Chalok path

```text
User request
 ↓
Chalok planner
 ↓
Kaj AST patch
 ↓
Kaj compiler
 ↓
Task IR
 ↓
Task memory
 ↓
PermissionEngine
 ↓
Browser workspace runtime
 ↓
Observation / verification
```

## 7.14 Text parser order

Do **not** make raw-text parsing the first implementation milestone.

Recommended order:

```text
AST JSON
→ compiler
→ Task IR
→ formatter
→ host integration
→ textual parser
```

This provides immediate production value while the source grammar remains fluid.

## 7.15 CLI architecture

Target UX:

```bash
kaj hello.kaj
kaj run hello.kaj
kaj check hello.kaj
kaj fmt .
kaj ast file.kaj
kaj ir file.kaj
```

`kaj hello.kaj` should be the simplest and canonical execution form.

## 7.16 Namespace collision fallback

Canonical executable is `kaj`.

Official fallback/compiler alias can be `kajc`.

Installers should never silently overwrite an unrelated existing `kaj` executable.

## 7.17 Formatter

Kaj should have one canonical formatter.

```bash
kaj fmt .
```

This reduces style fragmentation and creates cleaner datasets for model training.

## 7.18 Language server

Future `kajls` should provide LSP editor intelligence:

- errors,
- autocomplete,
- hover types,
- go to definition,
- find references,
- rename,
- code actions,
- capability completion.

It must reuse the compiler frontend rather than implementing its own parser/type checker.

## 7.19 Possible future Rust core

If Kaj becomes broadly embedded and portability/performance matter:

```text
Kaj compiler core (Rust)
 ├── Python bindings
 ├── Swift bindings
 ├── CLI
 ├── server runtime
 └── robotics runtime
```

This is explicitly deferred.
