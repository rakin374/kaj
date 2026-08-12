# Kaj Language Support for VS Code

This local extension provides the initial editing experience for `.kaj` files:

- automatic Kaj language registration
- TextMate syntax highlighting
- line and block comment commands
- matching and auto-closing braces, brackets, parentheses, and quotes
- basic brace indentation
- **Format Document** through Kaj's canonical `kaj fmt`

It does not provide an LSP, live semantic diagnostics, completion, hover, go-to-definition, references, rename, or other semantic IDE features.

## Local development

1. Open `editors/vscode/` in VS Code.
2. Run `npm install`.
3. Run `npm run compile`.
4. Press `F5` and choose **Run Extension** if prompted.
5. In the Extension Development Host, open a `.kaj` file such as `playground/hello.kaj`.

The language indicator should display **Kaj**. This extension is not automatically published to the VS Code Marketplace.

## Formatting

The formatter provider runs the existing command:

```bash
kaj fmt <temporary-kaj-file>
```

The temporary copy prevents `Format Document` from allowing the CLI to rewrite your source file behind VS Code. The formatted text is returned as a normal editor edit. Save the document before formatting; dirty and untitled buffers are refused conservatively.

If `kaj` is installed on `PATH`, no configuration is needed. Development environments can set an explicit executable:

```json
{
  "kaj.executablePath": "/absolute/path/to/kaj/.venv/bin/kaj",
  "[kaj]": {
    "editor.defaultFormatter": "kaj-local.kaj-vscode",
    "editor.formatOnSave": true
  }
}
```

Formatter failures display the CLI's stderr. A missing executable produces a direct configuration/PATH error. Formatting style is not configurable because Kaj source formatting is canonical.

## Current language boundary

Highlighting follows the implemented pure Kaj language. It intentionally excludes future agentic syntax. `break` and `continue` are highlighted because the parser reserves them, but reaching either in the current reference interpreter produces `RUNTIME_INVALID_OPERATION`.

For exact syntax and behavior, use the repository's `docs/language/` reference.
