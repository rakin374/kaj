# Kaj Checkpoint 17 — Module Imports

**Audience:** Codex / implementation agent  
**Checkpoint:** 17  
**Goal:** Add local project module imports with dotted paths, module graph loading, qualified value/type access, and deterministic initialization.

---

# 1. Primary Instruction

Implement **Checkpoint 17 only**.

Before editing code, read:

```text
docs/language/imports.md
docs/getting-started/cli.md
docs/language/formatting.md
docs/internals/ast.md
docs/compiler/ast-json.md
docs/internals/name-resolution.md
docs/internals/interpreter.md
dev/plans/pure-language-v0.md
```

Also inspect all current semantic type-symbol/module-scope infrastructure.

Treat:

```text
docs/language/imports.md
```

as authoritative.

Do not implement remote packages, registries, manifests, or version resolution.

---

# 2. Required Syntax

Support:

```kaj
import foo
import foo.bar
```

No aliases.

No selective imports.

No relative imports.

---

# 3. Project Root

For CLI entry file:

```text
/path/project/main.kaj
```

set project root to:

```text
/path/project/
```

Resolve:

```text
foo     -> /path/project/foo.kaj
foo.bar -> /path/project/foo/bar.kaj
```

Centralize this behavior in one module loader/resolver.

---

# 4. AST — ImportDeclaration

Add/complete:

```text
ImportDeclaration
```

with:

```text
path segments
span
```

Do not store resolved absolute paths in AST.

---

# 5. Parser

Implement parsing for:

```text
"import" IDENTIFIER ("." IDENTIFIER)*
```

Examples:

```kaj
import foo
import foo.bar
import app.models.user
```

Reject malformed import paths through normal parse diagnostics.

---

# 6. AST JSON

Extend:

```text
serializer
deserializer
schemas/ast/v1.json
docs/compiler/ast-json.md
```

for import declarations if not already present.

Round-trip import syntax.

Do not include resolved paths/module graphs in AST JSON.

---

# 7. Formatter

Extend canonical formatter:

```kaj
import foo
import foo.bar
```

One import per line.

Preserve source order.

Do not auto-sort.

---

# 8. Module Loader

Add a dedicated local module loader.

Recommended conceptual API:

```python
load_module(
    logical_name: ModuleName,
    project_root: Path,
) -> LoadedModule
```

Responsibilities:

```text
logical-name validation
path construction
root-boundary validation
UTF-8 file loading
source-name/path retention
deduplication by canonical file identity
```

Do not combine semantic analysis and raw file I/O into one opaque function if clean separation is practical.

---

# 9. Module Name Representation

Use explicit representation:

```text
ModuleName(parts=("foo", "bar"))
```

or equivalent.

Do not pass dotted strings everywhere without structure if a simple value object improves correctness.

---

# 10. Path Resolution

Canonical mapping:

```text
foo.bar -> project_root / "foo" / "bar.kaj"
```

Normalize/canonicalize safely.

Reject escapes outside project root.

No search paths.

No Python import machinery.

---

# 11. Missing Module Diagnostic

Add:

```text
IMPORT_NOT_FOUND
```

Include:

```text
logical module name
importing file/span
attempted path where useful
```

This is a compile error.

---

# 12. Duplicate Import Diagnostic

Within one module, detect exact duplicate logical imports:

```kaj
import foo
import foo
```

Emit:

```text
IMPORT_DUPLICATE
```

Continue compilation safely.

---

# 13. Import Graph

Build the reachable module graph starting from the CLI entry source.

Track:

```text
module identity
logical module name
canonical path
AST
source text
imports/dependencies
```

Load each physical/logical module once.

---

# 14. Cycle Detection

Detect DFS/Tarjan-style dependency cycles.

Add:

```text
IMPORT_CYCLE
```

Report cycle chain where practical:

```text
a -> b -> c -> a
```

Do not attempt cyclic initialization.

---

# 15. Compile Pipeline Refactor

Checkpoint 16 currently compiles one source/program.

Refactor carefully so:

```text
compile entry module
```

becomes:

```text
load full graph
parse all modules
resolve/analyze graph
type-check graph
```

while preserving a single-file helper for:

```text
fmt
ast
tests
```

Do not force `fmt`/`ast` to load imports.

---

# 16. Module Semantic Model

Add compiler-internal representation such as:

```text
SemanticModule
├── identity
├── name
├── path
├── AST
├── module scope
├── exported value symbols
├── exported type symbols
└── dependencies
```

Exact structure may differ.

---

# 17. Imported Module Symbols

An import declaration introduces a module namespace symbol in the importing module's value scope.

Add symbol kind, e.g.:

```text
MODULE
```

For:

```kaj
import foo
```

declare:

```text
foo -> ModuleSymbol(foo)
```

in module scope.

---

# 18. Dotted Import Binding

For:

```kaj
import foo.bar
```

the local module namespace chain must permit:

```text
foo.bar
```

qualified access.

Implementation choices include:

```text
nested module namespace objects
synthetic module path descriptors
member-resolution logic over imported path bindings
```

Do not inject `bar` alone as the local binding unless the language spec says so.

Top-level binding is `foo`.

---

# 19. Import/Local Name Collision

Existing same-scope duplicate rules apply.

Reject:

```kaj
import foo
let foo = 1
```

as duplicate value name.

Nested shadowing remains allowed.

---

# 20. Module Value Namespace

For:

```kaj
foo.add
```

if `foo` resolves to module namespace, member lookup resolves `add` from that module's exported value symbols.

Do not route module member access through record-field semantics.

---

# 21. Module Type Namespace

Support qualified type references:

```text
models.User
foo.bar.Item
```

This likely requires extending `TypeExpression` beyond a single identifier name.

Preferred AST model:

```text
NamedType(path=("models", "User"))
```

or equivalent.

If current `NamedType` stores a string, extend carefully and update AST JSON/formatter as necessary.

---

# 22. Imported Type Resolution

For:

```kaj
import models

let user: models.User = ...
```

resolve:

```text
models -> imported module namespace
User -> exported type symbol in models
```

Do not inject `User` unqualified into local type namespace.

---

# 23. Export Collection

For each module, collect top-level named declarations that are exported by v0 rules.

At minimum:

```text
functions
record types
enum types
newtypes
supported module bindings
```

Do not expose compiler-generated/builtin symbols as module exports.

---

# 24. Imported Function Calls

Required:

`math.kaj`:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

`main.kaj`:

```kaj
import math

print(math.add(2, 3))
```

must type-check and run:

```text
5
```

---

# 25. Imported Types

Required:

`models.kaj`:

```kaj
type User {
    name: String
}
```

`main.kaj`:

```kaj
import models

let user: models.User = models.User {
    name: "Alice"
}

print(user.name)
```

If record construction syntax currently assumes bare type identifiers, extend it to accept qualified type paths.

---

# 26. Qualified Constructors

Support qualified record/enum/newtype construction where types are imported.

Examples:

```kaj
models.User {
    name: "Alice"
}
```

```kaj
states.Status.pending
```

```kaj
ids.UserId("abc")
```

Semantic analysis must distinguish module qualification from value field access.

---

# 27. Enum Qualified Paths

Imported enum construction may require chains:

```text
states.Status.pending
```

where:

```text
states = module
Status = type
pending = variant
```

Do not flatten this incorrectly into ordinary runtime record members.

---

# 28. Module Member Type Checking

Add semantic member resolution cases:

```text
ModuleNamespace + value member
ModuleNamespace + nested imported module segment
```

Keep existing:

```text
RecordType field
List/Map count
Newtype value
```

working.

---

# 29. Cross-Module Function Signatures

All exported function signatures must be available before checking importing module call sites.

Compile dependencies before/declaratively before dependents as needed.

---

# 30. Cross-Module Type Identity

Record/enum/newtype nominal identity must include declaration/module identity.

Two different modules declaring:

```kaj
type User {
    name: String
}
```

produce distinct nominal types even if both are named `User`.

Do not compare types only by text name.

---

# 31. Cross-Module Newtypes

Likewise:

```text
a.UserId
b.UserId
```

are distinct if declared separately.

---

# 32. Module Cache

Cache loaded/parsed/analyzed modules by canonical identity within one compilation.

Repeated imports must not:

```text
reread unnecessarily
create duplicate type symbols
execute multiple times
```

---

# 33. Runtime Module Value

Add controlled runtime module namespace representation if needed:

```text
KajModuleValue
├── module identity
└── exported runtime bindings
```

or resolve module member expressions directly through module runtime environments.

Do not use Python modules.

---

# 34. Module Runtime Environment

Each module receives its own module environment.

Imported module member lookup reads from that module environment.

Do not merge all module globals into one global environment.

---

# 35. Initialization Order

Compute deterministic dependency-first order.

For each module:

```text
initialize dependencies first
initialize module once
```

For independent imports, source import order is tiebreaker.

---

# 36. Function Preinstallation Across Modules

Before executing a module's ordinary top-level statements, preinstall its top-level function values into that module environment as existing single-module semantics require.

Imported dependencies must already have their module environments initialized/available.

---

# 37. Runtime Imported Calls

For:

```kaj
math.add(2, 3)
```

runtime should retrieve the `math` module namespace/environment, then its `add` function value, then perform ordinary Kaj function call semantics.

---

# 38. Runtime Imported Values

If v0 permits module-level `let` exports:

`config.kaj`:

```kaj
let answer = 42
```

then:

```kaj
import config
print(config.answer)
```

should work.

Respect existing rules on module-level mutable bindings.

---

# 39. Initialization Exactly Once Test

Create a dependency with observable top-level print:

`dep.kaj`:

```kaj
print("dep")
```

Import it transitively/directly via multiple paths.

Verify output prints `dep` once.

---

# 40. Runtime Failure in Dependency

Dependency:

```kaj
print(1 / 0)
```

Entry imports it.

Expected:

```text
compile succeeds
run exits 2
runtime diagnostic points to dependency file
entry module does not execute afterward
```

---

# 41. Compile Failure in Dependency

Dependency with type error.

Entry imports it.

Expected:

```text
kaj check entry.kaj -> exit 1
kaj run entry.kaj -> exit 1
no runtime execution
diagnostic names dependency file
```

---

# 42. CLI Integration

Update:

```text
kaj check
kaj run
```

to use project-root/module-graph compilation.

Do not change:

```text
kaj fmt
kaj ast
```

beyond parser/formatter awareness of import syntax.

---

# 43. Project Root CLI Tests

Given:

```text
tmp/project/main.kaj
tmp/project/foo.kaj
```

running from any current working directory:

```bash
kaj run tmp/project/main.kaj
```

must resolve `import foo` relative to:

```text
tmp/project/
```

not process CWD.

This is important.

---

# 44. Security / Root Escape

Add tests ensuring crafted module names cannot resolve outside root.

Parser should already block slashes/dots beyond identifier separators, but module loader must still enforce root containment.

---

# 45. Symlink Handling

Where practical, canonicalize resolved file paths and ensure they remain under project root.

If a symlinked module points outside the root, reject it as invalid local-module resolution.

Use a clear import/path diagnostic.

A dedicated:

```text
IMPORT_OUTSIDE_PROJECT
```

is acceptable.

---

# 46. Duplicate Physical File Identity

If two logical paths resolve to the same canonical file due to symlinks/path normalization, avoid double initialization.

Diagnose ambiguous logical identity if necessary.

---

# 47. Diagnostics

Required:

```text
IMPORT_NOT_FOUND
IMPORT_DUPLICATE
IMPORT_CYCLE
```

Recommended if needed:

```text
IMPORT_UNKNOWN_MEMBER
IMPORT_OUTSIDE_PROJECT
```

Reuse existing:

```text
RESOLVE_DUPLICATE_NAME
TYPE_UNKNOWN_TYPE
TYPE_UNKNOWN_MEMBER
```

where appropriate.

---

# 48. Diagnostic Ordering Across Modules

Choose deterministic ordering.

Recommended:

```text
dependency traversal/source order
then source position within file
```

or preserve the compilation graph's deterministic visit order.

Do not rely on hash-map iteration order.

---

# 49. Error Recovery

Missing/cyclic modules should not crash graph construction.

Collect reachable diagnostics where practical, but avoid trying to semantically analyze a dependency whose AST/module load is unavailable in a way that creates cascades.

---

# 50. Required Tests — Parsing

Parse:

```kaj
import foo
import foo.bar
```

Verify path segments and spans.

Reject malformed syntax.

---

# 51. Required Tests — AST JSON

Round-trip import declarations.

Validate schema.

Ensure no resolved filesystem path appears in JSON.

---

# 52. Required Tests — Formatter

Input messy import whitespace.

Canonical:

```kaj
import foo
import foo.bar
```

Verify imports remain source ordered.

---

# 53. Required Tests — Module Resolution

Resolve:

```text
foo
foo.bar
a.b.c
```

to correct local paths.

Test missing module.

Test root relative behavior independent of current working directory.

---

# 54. Required Tests — Duplicate Imports

Reject:

```kaj
import foo
import foo
```

with:

```text
IMPORT_DUPLICATE
```

---

# 55. Required Tests — Cycle Detection

Direct cycle:

```text
a -> b -> a
```

Indirect:

```text
a -> b -> c -> a
```

Both emit:

```text
IMPORT_CYCLE
```

No infinite recursion.

---

# 56. Required Tests — Qualified Function Call

`math.kaj`:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}
```

`main.kaj`:

```kaj
import math

print(math.add(2, 3))
```

→ `5`.

---

# 57. Required Tests — Qualified Types

Imported record type in:

```text
annotation
construction
function parameter if applicable
```

Verify nominal identity.

---

# 58. Required Tests — Nested Module

Files:

```text
util/math.kaj
main.kaj
```

Use:

```kaj
import util.math
print(util.math.add(2, 3))
```

→ `5`.

---

# 59. Required Tests — Transitive Imports

`main -> foo -> bar`.

Main should compile/run with graph loaded.

Main cannot refer to `bar` unqualified or as direct local import namespace unless it imports it.

---

# 60. Required Tests — Shared Dependency

Graph:

```text
main -> a
main -> b
a -> common
b -> common
```

Verify `common` loaded/analyzed/initialized once.

---

# 61. Required Tests — Dependency Compile Error

Ensure entry fails with exit 1 and dependency path in diagnostic.

---

# 62. Required Tests — Dependency Runtime Error

Ensure entry run exits 2 and stops subsequent initialization.

---

# 63. Required Tests — Initialization Order

Construct observable modules.

Verify dependency-first/source-import-order behavior exactly.

Example expected sequence:

```text
common
a
b
main
```

for a suitable graph.

---

# 64. Required Tests — Nominal Identity Across Modules

`a.kaj` and `b.kaj` each declare:

```kaj
newtype Id = String
```

Verify:

```text
a.Id != b.Id
```

Likewise for records/enums if convenient.

---

# 65. Required Tests — Imported Module Shadowing

Top-level duplicate:

```kaj
import foo
let foo = 1
```

must fail.

Nested shadowing should follow normal lexical rules if syntax permits.

---

# 66. Required Tests — No Remote Resolution

Ensure names are treated only as local module names.

Do not make network calls.

No registry fallback.

---

# 67. Suggested Files

Likely add:

```text
src/kaj/modules/
├── __init__.py
├── names.py
├── loader.py
├── graph.py
└── module.py
```

and extend:

```text
src/kaj/ast/
src/kaj/parser/
src/kaj/serialization/
src/kaj/formatter.py
src/kaj/semantic/resolver.py
src/kaj/semantic/type_checker.py
src/kaj/runtime/interpreter.py
src/kaj/pipeline.py
src/kaj/cli.py
```

Use existing repo structure rather than forcing these exact paths.

---

# 68. Suggested Implementation Order

### Step 1
Read `docs/language/imports.md`.

### Step 2
Add/complete ImportDeclaration AST/parser/JSON/formatter.

### Step 3
Implement ModuleName + safe local path resolution.

### Step 4
Implement module loader/cache.

### Step 5
Build dependency graph and cycle detection.

### Step 6
Add semantic module representation and module symbols.

### Step 7
Integrate imports into resolver scopes.

### Step 8
Extend type syntax/resolution for qualified type paths.

### Step 9
Implement qualified imported value/member resolution.

### Step 10
Ensure cross-module function/type signatures available.

### Step 11
Refactor compile pipeline to graph compilation.

### Step 12
Implement module runtime environments/namespaces.

### Step 13
Implement deterministic initialization.

### Step 14
Update `kaj check`/`kaj run`.

### Step 15
Add dependency/error/security tests.

### Step 16
Run full verification.

### Step 17
Update:

```text
dev/plans/pure-language-v0.md
```

Do not add remote/package registry work.

---

# 69. Verification

Run:

```bash
pytest
ruff check .
mypy src
kaj --version
python -m kaj --version
```

Also run end-to-end local import fixtures through:

```bash
kaj check
kaj run
kaj fmt
kaj ast
```

where relevant.

All Checkpoints 0-16 must remain passing.

---

# 70. Definition of Done

Checkpoint 17 is complete only when:

```text
[ ] import declaration AST implemented
[ ] parser supports import foo
[ ] parser supports import foo.bar
[ ] AST JSON supports imports
[ ] formatter supports imports

[ ] module-name representation implemented
[ ] project root derived from entry-file directory
[ ] foo -> foo.kaj resolution implemented
[ ] foo.bar -> foo/bar.kaj resolution implemented
[ ] local-only resolution enforced
[ ] project-root escape prevented

[ ] module loader implemented
[ ] canonical module/file identity implemented
[ ] modules loaded once
[ ] duplicate imports diagnosed
[ ] missing imports diagnosed
[ ] import cycles diagnosed

[ ] module graph compilation implemented
[ ] dependency compile errors fail whole program
[ ] diagnostics retain dependency filenames

[ ] module namespace symbols implemented
[ ] import introduces top-level module binding
[ ] dotted imports support qualified nested access
[ ] local same-scope collisions rejected

[ ] exported value namespace implemented
[ ] exported type namespace implemented
[ ] imports do not inject unqualified declarations

[ ] qualified imported function access works
[ ] qualified imported module values work
[ ] qualified type references work
[ ] imported record construction works
[ ] imported enum construction works
[ ] imported newtype construction works

[ ] nominal type identity includes declaration/module identity
[ ] same-named types in different modules remain distinct

[ ] module runtime environment implemented
[ ] imported runtime member access works
[ ] dependencies initialize before importers
[ ] independent dependency order follows source import order
[ ] each module initializes once

[ ] dependency runtime failures propagate as runtime errors
[ ] later initialization stops after runtime failure

[ ] kaj check compiles full graph
[ ] kaj run compiles/runs full graph
[ ] kaj fmt remains single-file
[ ] kaj ast remains single-file

[ ] IMPORT_NOT_FOUND implemented
[ ] IMPORT_DUPLICATE implemented
[ ] IMPORT_CYCLE implemented
[ ] no Python import machinery used
[ ] no network/package registry resolution used

[ ] nested module fixture passes
[ ] transitive import fixture passes
[ ] shared dependency initializes once
[ ] cycle fixtures fail cleanly
[ ] root-relative behavior independent of CWD

[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes
[ ] Checkpoints 0-16 remain passing

[ ] no remote package support added
[ ] no package registry support added
[ ] no version constraints added
[ ] no package manifest required
[ ] no alias/selective/relative imports added

[ ] dev/plans/pure-language-v0.md updated
```

---

# 71. Completion Report

When finished, report:

```text
Checkpoint 17 — Complete / Incomplete

Files added:
- ...

Files changed:
- ...

Import AST/parser:
- ...

Module resolution:
- ...

Project root behavior:
- ...

Dependency graph:
- ...

Cycle handling:
- ...

Semantic module namespace:
- ...

Qualified value/type access:
- ...

Runtime module environments:
- ...

Initialization order:
- ...

CLI integration:
- ...

Diagnostics:
- ...

Acceptance:
- import foo: PASS/FAIL
- import foo.bar: PASS/FAIL
- qualified function call: PASS/FAIL
- qualified type use: PASS/FAIL
- transitive imports: PASS/FAIL
- shared dependency once: PASS/FAIL
- cycle rejection: PASS/FAIL

Verification:
- pytest: PASS/FAIL
- ruff check .: PASS/FAIL
- mypy src: PASS/FAIL
- kaj check: PASS/FAIL
- kaj run: PASS/FAIL
- kaj fmt: PASS/FAIL
- kaj ast: PASS/FAIL

Decisions/deviations:
- ...

Known issues:
- ...
```

Do not implement remote/package registry resolution.
