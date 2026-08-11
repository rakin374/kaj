# 9. Tooling, Open Source, Governance, and Versioning

# 9.1 Developer experience

Kaj should feel like a normal programming language from the shell.

Canonical:

```bash
kaj hello.kaj
```

Recommended early commands:

```bash
kaj run hello.kaj
kaj check hello.kaj
kaj fmt .
kaj ast file.kaj
kaj ir file.kaj
kaj version
```

Later:

```bash
kaj test
kaj repl
kaj capabilities
kaj doctor
```

## 9.2 Source extension

```text
.kaj
```

## 9.3 REPL

Eventually:

```bash
kaj repl
```

or perhaps bare `kaj` with no file.

Pure computation works locally; effectful capabilities require attached providers.

## 9.4 Language server

Future:

```text
kajls
```

using LSP.

Potential features:

- diagnostics,
- autocomplete,
- hover types,
- go to definition,
- find references,
- rename,
- capability-operation completion,
- task/step navigation.

## 9.5 Package system

Kaj may eventually need a native package ecosystem.

Possible manifest:

```text
kaj.toml
```

Conceptual:

```toml
[package]
name = "example"
version = "0.1.0"

[dependencies]
kaj-web = "1"
```

Exact format is deferred.

## 9.6 Standard library

Initial stdlib should remain small and high quality.

Likely modules:

```text
collections
math
json
text
time
result
```

Do not attempt Python-scale coverage immediately.

## 9.7 Testing

Language/compiler repo should heavily use golden fixtures:

```text
source.kaj
expected.ast.json
expected.ir.json
expected.diagnostics.json
```

Kaj may later gain native test syntax.

## 9.8 Conformance suite

Third-party compilers/runtimes should eventually prove compatibility through public conformance tests.

Possible levels:

```text
Kaj Core
Kaj Task
Kaj Web Capability v1
```

# 9.9 Open-source position

Kaj should be independent and open source from the beginning.

Proposed code license:

```text
Apache License 2.0
```

Reasons include permissive adoption and explicit patent-grant language.

This is a project proposal, not legal advice.

## 9.10 Copyright

Choose the initial copyright holder deliberately before publication.

Possible form:

```text
Copyright © 2026 <owner>
```

## 9.11 Trademark/name

Code licensing and the Kaj project name are separate issues.

Open-sourcing the compiler does not require immediately filing a federal trademark.

The project should avoid implying that the source-code license automatically grants ownership of the Kaj brand/logo.

## 9.12 Contributions

Simple initial model:

- contributions are provided under the project's Apache-2.0 terms,
- contributors certify they have the right to submit them,
- a DCO-style sign-off process may be added.

A complicated CLA is not required at inception.

## 9.13 Governance

Initial governance can be maintainer-led.

Suggested statement:

> Kaj is currently maintained by the Kaj project maintainers. Significant changes to syntax, semantics, type system, Task IR, or capability contracts should be proposed through a Kaj Improvement Proposal. Maintainers make final acceptance decisions while Kaj is in early development.

## 9.14 Kaj Improvement Proposals

Use **KIP** as the proposal process.

Potential first proposals:

```text
KIP-0001 Core Language and Principles
KIP-0002 Lexical Grammar
KIP-0003 Type System
KIP-0004 Functions and Effect Model
KIP-0005 Task and Step Semantics
KIP-0006 Contracts and Verification
KIP-0007 Human Interaction
KIP-0008 Observation and Fact Model
KIP-0009 Capability System
KIP-0010 Kaj AST Schema
KIP-0011 Task IR
KIP-0012 Web Capability v1
KIP-0013 Compiler Architecture
KIP-0014 Host Runtime Interface
KIP-0015 World Model Interface
```

## 9.15 Version components independently

Track separate versions for:

```text
Kaj language
AST schema
Task IR
capabilities
reference compiler
```

Example:

```text
Kaj language 0.1
AST v1
Task IR v1
web capability v1
compiler 0.1.3
```

## 9.16 Persisted metadata

```json
{
  "language": "kaj",
  "language_version": "0.1",
  "ast_schema_version": 1,
  "task_ir_version": 1,
  "capabilities": {
    "web": 1
  }
}
```

## 9.17 Compatibility policy

During `0.x`:

- syntax may change,
- semantics may change,
- AST/IR may change,
- formatter output may change.

Changes should still be documented.

Before `1.0`, define:

- source compatibility,
- deprecation policy,
- AST compatibility,
- IR compatibility,
- capability compatibility.

## 9.18 Specification vs implementation

Distinguish:

```text
Kaj Language Specification
```

from:

```text
Kaj Reference Compiler
```

A third party should be able to implement a conforming compiler/runtime.

## 9.19 Foundation

No foundation is needed initially.

Potential evolution only if scale requires it:

```text
maintainer-led
  ↓
steering committee
  ↓
neutral foundation / consortium
```

## 9.20 Repository starter files

Recommended:

```text
README.md
LICENSE
NOTICE
CONTRIBUTING.md
SECURITY.md
CHANGELOG.md
GOVERNANCE.md
CODE_OF_CONDUCT.md
```

## 9.21 Minimal KIP template

```markdown
# KIP-NNNN: Title

Status: Draft
Author:
Created:
Target version:

## Summary
## Motivation
## Design
## Syntax
## Static semantics
## Runtime semantics
## AST representation
## IR lowering
## Capability/effect implications
## Security considerations
## Alternatives
## Compatibility
## Open questions
```
