# 13. Repository Starter Files

This document contains suggested starter text. It is not legal advice.

## README opening

```markdown
# Kaj

Kaj is an open-source programming language for intelligent agents and ordinary scripting.

Kaj combines general computation with first-class constructs for goal-directed tasks, external capabilities, observation, verification, and human collaboration.

```bash
kaj hello.kaj
```

Kaj is currently experimental. Syntax and semantics may change during the 0.x series.
```

## CONTRIBUTING.md starter

```markdown
# Contributing to Kaj

Kaj is in early language-design and implementation development.

Contributions are welcome in compiler implementation, tests, documentation, examples, diagnostics, tooling, and language-design discussion.

Substantial changes to language syntax, semantics, type system, Task IR, or capability contracts should begin as a Kaj Improvement Proposal (KIP).

By submitting a contribution, you agree that your contribution may be distributed under the project's license and that you have the right to submit it.
```

## SECURITY.md starter

```markdown
# Security

Please do not open a public issue for vulnerabilities that could enable unsafe external effects, permission bypass, secret exposure, or arbitrary code execution.

Report security issues privately through the repository's configured security reporting channel.

Kaj source and Kaj capability packages should be treated as potentially untrusted input by host runtimes.
```

## GOVERNANCE.md starter

```markdown
# Governance

Kaj is currently maintained under a maintainer-led governance model.

Significant changes to syntax, semantics, the type system, Task IR, or capability model should be proposed through the Kaj Improvement Proposal (KIP) process.

The maintainers make final acceptance decisions while Kaj is in early development.

The governance model may evolve if the project develops a broader independent community.
```

## KIP template

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

## Capability / effect implications

## Security considerations

## Alternatives considered

## Compatibility

## Open questions
```

## NOTICE

If Apache-2.0 is selected, create the project `NOTICE` appropriate to the final copyright holder and legal setup.
