# Kaj VS Code Extension — Initial Editor Support

**Status:** Complete  
**Scope:** VS Code recognition for `.kaj`, syntax highlighting, language configuration, indentation/brackets, and formatter command integration  
**Out of scope:** LSP, semantic diagnostics, autocomplete, hover, go-to-definition, rename, references, package registry publishing

---

# 1. Goal

Create a minimal VS Code extension that makes Kaj pleasant to edit immediately.

The initial extension should provide:

```text
.kaj file recognition
Kaj language mode
syntax highlighting
comments
strings
numbers
keywords
operators
bracket matching
auto-closing pairs
basic indentation
formatter command integration
```

It should **not** implement semantic intelligence yet.

---

# 2. Architecture

Initial editor support:

```text
VS Code
   │
   ├── language registration
   ├── TextMate grammar
   ├── language configuration
   └── formatter bridge
          ↓
       kaj fmt
```

Later:

```text
VS Code extension
       │
       └── Kaj Language Server
              ↓
          lexer
          parser
          resolver
          type checker
```

The LSP is explicitly deferred.

---

# 3. Recommended Repository Layout

Add:

```text
editors/
└── vscode/
    ├── package.json
    ├── language-configuration.json
    ├── syntaxes/
    │   └── kaj.tmLanguage.json
    ├── src/
    │   └── extension.ts
    ├── tsconfig.json
    ├── README.md
    └── .vscodeignore
```

If avoiding TypeScript for the first version, `extension.js` is acceptable.

Prefer TypeScript if the repository is comfortable carrying a tiny Node-based editor package.

---

# 4. Language Registration

Register a language:

```json
{
  "id": "kaj",
  "aliases": ["Kaj", "kaj"],
  "extensions": [".kaj"]
}
```

VS Code should recognize any `.kaj` file automatically.

The language mode should display as:

```text
Kaj
```

---

# 5. File Association

Opening:

```text
hello.kaj
```

should automatically select the Kaj language mode.

No manual file association should be required.

---

# 6. TextMate Grammar

Use a TextMate grammar for syntax highlighting.

File:

```text
syntaxes/kaj.tmLanguage.json
```

Scope name:

```text
source.kaj
```

The grammar should highlight the language as it exists today.

Do not add future agentic keywords yet.

---

# 7. Current Kaj Keywords

Highlight current reserved keywords:

```text
let
var
fn
return
if
else
while
for
in
break
continue
true
false
none
and
or
not
type
enum
newtype
match
import
```

`break` and `continue` should still be highlighted because they are reserved syntax, even though the reference interpreter does not execute them yet.

Do not add future words such as:

```text
task
step
goal
ask
confirm
use
```

until they actually enter the language.

---

# 8. Type Highlighting

Highlight built-in types:

```text
Bool
Int
Decimal
String
Bytes
None
List
Map
Optional
Result
```

User-defined type names should receive a reasonable type/class scope when identifiable by syntax.

Examples:

```kaj
type User {
}
```

```kaj
enum Status {
}
```

```kaj
newtype UserId = String
```

The declared names:

```text
User
Status
UserId
```

should be highlighted as type declarations where practical.

---

# 9. Function Highlighting

Highlight:

```kaj
fn add(a: Int, b: Int) -> Int {
}
```

with:

```text
fn          keyword
add         function declaration
a / b       parameters
Int         type
```

Function call identifiers may use a function-call scope where the grammar can identify:

```kaj
add(1, 2)
```

Do not overcomplicate the regex grammar.

---

# 10. Strings

Support double-quoted strings.

Recognize escapes:

```text
\"
\\
\n
\r
\t
```

Do not add multiline-string grammar.

Do not add interpolation highlighting yet because interpolation semantics are deferred.

---

# 11. Numbers

Highlight:

```text
integer literals
decimal literals
```

Examples:

```text
0
42
100
1.0
2.5
0.125
```

Do not highlight unsupported forms as valid Kaj numeric literals:

```text
1.
.5
1e10
0xff
1_000
```

---

# 12. Comments

Support:

```kaj
// line comment
```

and:

```kaj
/*
block comment
*/
```

Block comments are not nested.

Language configuration should expose these comment forms to VS Code.

---

# 13. Operators

Highlight current operators:

```text
+
-
*
/
%
**
=
==
!=
<
<=
>
>=
+=
-=
*=
/=
->
=>
```

Word operators:

```text
and
or
not
```

are keywords/operators.

---

# 14. Delimiters

Recognize:

```text
( )
{ }
[ ]
,
:
.
```

Use standard punctuation scopes where appropriate.

---

# 15. Language Configuration

Create:

```text
language-configuration.json
```

Configure:

```text
line comments
block comments
brackets
auto-closing pairs
surrounding pairs
indentation rules
```

---

# 16. Auto-Closing Pairs

Support:

```text
{ }
[ ]
( )
" "
```

Typing an opening brace/parenthesis/bracket/quote should behave like normal VS Code languages.

---

# 17. Bracket Matching

Configure:

```text
{}
[]
()
```

so VS Code highlights matching pairs.

---

# 18. Indentation

Basic indentation should work after opening braces.

Example:

```kaj
if ready {
    print("ready")
}
```

Pressing Enter after:

```kaj
if ready {
```

should indent one level.

Closing:

```text
}
```

should outdent.

---

# 19. Formatter Integration

Add VS Code formatting support by delegating to Kaj's canonical formatter.

The extension should invoke:

```bash
kaj fmt <temporary-or-target-file>
```

or, preferably if a non-mutating formatter API/CLI mode exists later:

```bash
kaj fmt --stdout <file>
```

However, **do not invent `--stdout` if Kaj does not support it yet**.

For the current CLI, the extension may use the file-on-disk in-place formatter and then ask VS Code to reload/apply the changed contents.

---

# 20. Safer Formatter Integration Strategy

Because `kaj fmt` currently rewrites files in place, the first formatter integration should be conservative.

Recommended behavior:

1. require the document to be saved
2. run:

```bash
kaj fmt <absolute-path>
```

3. if exit code is `0`, reload document contents
4. if exit code is nonzero, show stderr in VS Code
5. do not modify unsaved buffers silently

This avoids temporary source drift.

---

# 21. Format Document

Register a document formatting provider for language:

```text
kaj
```

So users can invoke:

```text
Format Document
```

from VS Code.

Also support standard shortcut behavior where VS Code chooses the Kaj formatter.

---

# 22. Format on Save

The extension should work with VS Code's existing:

```json
"editor.formatOnSave": true
```

once selected as the formatter for Kaj.

Do not create a Kaj-specific competing format-on-save setting unless necessary.

---

# 23. Formatter Executable Discovery

Search for `kaj` using the user's normal environment/PATH.

If it cannot be found, show a concise error such as:

```text
Kaj formatter not found. Ensure `kaj` is installed and available on PATH.
```

Do not hardcode the user's development-machine path.

---

# 24. Workspace Virtual Environment

During local Kaj development, VS Code may not inherit an activated shell venv.

Provide an optional setting:

```text
kaj.executablePath
```

Example:

```json
{
  "kaj.executablePath": "/path/to/.venv/bin/kaj"
}
```

Default:

```text
kaj
```

This makes the extension usable both for developers and eventual installed Kaj distributions.

---

# 25. Extension Settings

Initial settings should remain minimal.

Recommended:

```text
kaj.executablePath
```

Do not add configuration for formatting style because Kaj formatting is canonical.

There should be no settings like:

```text
indent width
brace style
line width
quote style
```

unless the language formatter itself becomes configurable later.

Canonical formatting is a feature.

---

# 26. No Semantic Diagnostics Yet

Do not run:

```bash
kaj check
```

continuously on every edit in this milestone.

That would be a primitive substitute for an LSP and could create poor UX.

Semantic editor diagnostics belong to the Kaj Language Server milestone.

---

# 27. No Autocomplete Yet

Do not implement regex-based fake autocomplete.

Defer:

```text
completion
hover
go-to-definition
find references
rename
signature help
workspace symbols
document symbols
```

to the LSP.

---

# 28. README

Create:

```text
editors/vscode/README.md
```

Explain:

```text
what the extension supports
how to run/install it locally
how to select Kaj language mode
how formatting works
how to configure kaj.executablePath
what is intentionally not supported yet
```

---

# 29. Local Development Workflow

Document a local VS Code extension development flow.

Typical workflow:

```text
open editors/vscode in VS Code
install npm dependencies
build/compile
launch Extension Development Host
open a .kaj file
verify syntax highlighting
```

Do not assume publication to the VS Code Marketplace.

---

# 30. Package Metadata

`package.json` should include:

```text
name
displayName
description
version
publisher placeholder/local dev value
engines.vscode
categories
activationEvents if required
contributes.languages
contributes.grammars
contributes.configuration
```

Keep metadata minimal.

Do not publish automatically.

---

# 31. Syntax Highlighting Examples

Use a fixture such as:

```kaj
newtype UserId = String

enum Status {
    active
    suspended(reason: String)
}

type User {
    id: UserId
    name: String
    status: Status
}

fn describe(user: User) -> String {
    match user.status {
        active => return user.name
        suspended(reason) => return reason
    }
}

let user = User {
    id: UserId("001"),
    name: "Alice",
    status: Status.active,
}

print(describe(user))
```

This fixture exercises:

```text
keywords
types
functions
record declarations
enum declarations
match
constructors
strings
member access
```

---

# 32. Additional Grammar Fixture

Use another file with:

```kaj
let values = [1, 2, 3]

let ages = {
    "Alice": 30,
    "Bob": 40,
}

if values.count > 0 {
    print("has values")
}
```

This tests:

```text
lists
maps
numbers
strings
operators
member access
conditionals
```

---

# 33. Testing Syntax Grammar

At minimum, manually validate TextMate highlighting in the Extension Development Host.

If practical, add grammar tokenization tests using an existing lightweight TextMate test utility.

Do not add a large testing framework just for syntax highlighting unless needed.

---

# 34. Formatter Tests

Unit-test formatter command construction.

Where practical, create a temporary `.kaj` file and invoke the configured Kaj executable.

Verify:

```text
success reloads formatted contents
failure does not silently overwrite editor state
stderr is surfaced
missing executable produces a clear error
```

---

# 35. File Recognition Acceptance

Opening:

```text
playground/hello.kaj
```

must show:

```text
Kaj
```

as the active language mode.

---

# 36. Highlighting Acceptance

This:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

must visibly distinguish:

```text
keyword
function
parameters
types
operator
```

using the active VS Code theme.

The extension does not control exact colors.

---

# 37. Comment Acceptance

VS Code comment toggling should use:

```text
//
```

for line comments.

Block comment configuration should use:

```text
/* */
```

---

# 38. Formatter Acceptance

Given:

```kaj
fn add(a:Int,b:Int)->Int{
return a+b
}
```

running:

```text
Format Document
```

should result in:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

assuming the file is saved and `kaj` executable is configured.

---

# 39. Current `break` / `continue` Status

Highlight:

```text
break
continue
```

as keywords because they are reserved parser syntax.

Do not describe them in the extension README as fully executable control flow.

Current interpreter behavior remains:

```text
execution reaching break/continue -> RUNTIME_INVALID_OPERATION
```

The extension should not hide or reinterpret this language behavior.

---

# 40. Suggested Files

Create:

```text
editors/vscode/package.json
editors/vscode/language-configuration.json
editors/vscode/syntaxes/kaj.tmLanguage.json
editors/vscode/src/extension.ts
editors/vscode/tsconfig.json
editors/vscode/README.md
editors/vscode/.vscodeignore
```

Optional:

```text
editors/vscode/test/
```

---

# 41. Suggested Implementation Order

### Step 1
Create VS Code extension package skeleton.

### Step 2
Register the Kaj language and `.kaj` extension.

### Step 3
Create language configuration.

### Step 4
Implement TextMate grammar.

### Step 5
Verify file recognition/highlighting manually.

### Step 6
Add `kaj.executablePath` setting.

### Step 7
Implement document formatting provider.

### Step 8
Handle missing executable / formatter errors cleanly.

### Step 9
Add README and local development instructions.

### Step 10
Add lightweight tests where practical.

### Step 11
Verify against real files in `playground/`.

---

# 42. Definition of Done

The initial Kaj VS Code extension is complete when:

```text
[ ] editors/vscode exists

[ ] .kaj files automatically use Kaj language mode
[ ] language displays as Kaj

[ ] current Kaj keywords highlighted
[ ] primitive/container types highlighted
[ ] integer literals highlighted
[ ] decimal literals highlighted
[ ] strings highlighted
[ ] supported escapes highlighted
[ ] line comments highlighted
[ ] block comments highlighted
[ ] operators highlighted
[ ] function declarations reasonably highlighted
[ ] type declarations reasonably highlighted

[ ] brackets configured
[ ] auto-closing pairs work
[ ] surrounding pairs work
[ ] comment toggling works
[ ] basic brace indentation works

[ ] Format Document registered for Kaj
[ ] formatter delegates to canonical `kaj fmt`
[ ] formatter respects configured executable path
[ ] missing Kaj executable shows clear error
[ ] formatter failures surface stderr
[ ] unsaved documents are handled safely

[ ] canonical formatting remains controlled by Kaj, not extension settings
[ ] VS Code format-on-save can use the Kaj formatter

[ ] README documents local use
[ ] README documents kaj.executablePath
[ ] README clearly says semantic IDE features are not implemented yet

[ ] no LSP added
[ ] no fake semantic diagnostics added
[ ] no autocomplete added
[ ] no future agentic keywords added
[ ] no unsupported syntax highlighted as current language behavior

[ ] playground Kaj files are pleasant to edit
```

---

# 43. Future Milestone — Kaj Language Server

Do not implement this now, but preserve a clear next step.

Future architecture:

```text
VS Code
   ↓ LSP
Kaj Language Server
   ↓
lexer
parser
resolver
type checker
```

Future features:

```text
live diagnostics
hover types
go-to-definition
find references
rename
completion
signature help
document symbols
workspace symbols
```

The existing compiler frontend and source spans should be reused.

---

# 44. Codex Prompt

Use:

```text
Implement the Kaj VS Code extension described in
dev/plans/vscode-extension.md.

Create the extension under editors/vscode/.

Implement only:
- .kaj language registration
- TextMate syntax highlighting
- language configuration
- bracket/comment/indent behavior
- Format Document integration using the existing `kaj fmt`
- optional `kaj.executablePath` configuration
- local extension README

Treat the current Kaj language documentation as authoritative for syntax.

Do not implement an LSP, semantic diagnostics, autocomplete, hover,
go-to-definition, rename, references, or future agentic syntax.

Remember that `break` and `continue` are reserved/parser-supported syntax
but are not executable in the current reference interpreter.
```

---

# 45. Completion Report

When finished, report:

```text
Kaj VS Code Extension — Complete / Incomplete

Files added:
- ...

Language registration:
- .kaj recognition: PASS/FAIL
- Kaj language mode: PASS/FAIL

Syntax highlighting:
- keywords: PASS/FAIL
- types: PASS/FAIL
- functions: PASS/FAIL
- numbers: PASS/FAIL
- strings: PASS/FAIL
- comments: PASS/FAIL
- operators: PASS/FAIL

Editor behavior:
- brackets: PASS/FAIL
- auto-close: PASS/FAIL
- indentation: PASS/FAIL
- comment toggle: PASS/FAIL

Formatting:
- Format Document: PASS/FAIL
- kaj executable discovery: PASS/FAIL
- kaj.executablePath: PASS/FAIL
- formatter error handling: PASS/FAIL

Documentation:
- README: PASS/FAIL
- local development instructions: PASS/FAIL

Deferred intentionally:
- LSP
- diagnostics
- completion
- hover
- go-to-definition
- rename
- references

Known issues:
- ...
```
