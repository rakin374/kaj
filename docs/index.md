# Kaj

Kaj is a strongly typed programming language designed for ordinary software and, over time, safe human-agent collaboration.

Kaj is in early pre-alpha development. The pure-language core is implemented; agentic semantics, capabilities, and asset semantics are not part of the current compiler.

## Choose a path

- **New to Kaj?** Start with [Installation](getting-started/installation.md), then take the [Quickstart](getting-started/quickstart.md).
- **Want working code?** Browse [Kaj by Example](guide/kaj-by-example.md) and the executable `examples/` corpus.
- **Building something?** Use the practical [Guide](guide/index.md).
- **Need exact semantics?** Read the normative [Language Reference](language/lexical-structure.md).

The [first-program tutorial](getting-started/first-program.md) builds a typed user directory using records, enums, maps, `Optional`, functions, and newtypes.

## Toolchain contributors

The [AST JSON specification](compiler/ast-json.md) documents the external compiler format. The [internal AST](internals/ast.md), [name resolver](internals/name-resolution.md), and [interpreter](internals/interpreter.md) describe implementation architecture.

Proposals describe possible changes; `dev/` contains implementation plans. Neither overrides the current documentation under `docs/`.
