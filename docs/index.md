# Kaj

Kaj is a strongly typed programming language designed for ordinary software and, over time, safe human-agent collaboration.

Kaj is in early pre-alpha development. The pure-language core, synchronous
[task model](agentic/tasks.md), and named
[steps and lifecycle](agentic/steps-and-lifecycle.md), and
[task contracts](agentic/task-contracts.md), and typed
[human interaction](agentic/human-interaction.md) are implemented. Persistence across process
restart, capabilities, task composition, planning, replanning, and asset semantics are not yet part
of the compiler or reference runtime.

## Choose a path

- **New to Kaj?** Start with [Installation](getting-started/installation.md), then take the [Quickstart](getting-started/quickstart.md).
- **Want working code?** Browse [Kaj by Example](guide/kaj-by-example.md) and the executable `examples/` corpus.
- **Building something?** Use the practical [Guide](guide/index.md).
- **Need exact semantics?** Read the normative [Language Reference](language/lexical-structure.md).
- **Trying Agentic Kaj?** Start with the [Agentic Kaj overview](agentic/index.md).

The [first-program tutorial](getting-started/first-program.md) builds a typed user directory using records, enums, maps, `Optional`, functions, and newtypes.

## Toolchain contributors

The [AST JSON specification](compiler/ast-json.md) documents the external compiler format. The [internal AST](internals/ast.md), [name resolver](internals/name-resolution.md), and [interpreter](internals/interpreter.md) describe implementation architecture.

Proposals describe possible changes; `dev/` contains implementation plans. Neither overrides the current documentation under `docs/`.
