# Kaj Module Imports

**Status:** Authoritative for Kaj v0 local module-import semantics  
**Scope:** local project modules, dotted module paths, import visibility, module identity, dependency loading  
**Not covered:** remote packages, registries, version resolution, package manifests, dependency downloads, aliases, selective imports

---

# 1. Purpose

Kaj supports importing local modules within a project.

Examples:

```kaj
import foo
import foo.bar
```

Imports allow one Kaj source file to refer to declarations from another local Kaj module.

Checkpoint 17 is limited to local project modules.

---

# 2. Module Naming

A module has a dotted logical name.

Examples:

```text
foo
foo.bar
app.models.user
```

Each segment is an identifier.

Module names use:

```text
identifier ("." identifier)*
```

---

# 3. Source File Mapping

A module name maps to a local `.kaj` source file relative to the project root.

Canonical mapping:

```text
foo       -> foo.kaj
foo.bar   -> foo/bar.kaj
a.b.c     -> a/b/c.kaj
```

No package-directory `__init__.kaj` convention exists in v0.

A dotted name refers directly to one source file.

---

# 4. Project Root

Imports resolve relative to one project root.

For v0, when the CLI is given an entry file, the project root is the directory containing that entry file.

Example:

```text
project/
├── main.kaj
├── foo.kaj
└── util/
    └── math.kaj
```

Running:

```bash
kaj run project/main.kaj
```

uses:

```text
project/
```

as the import root.

Therefore:

```kaj
import foo
import util.math
```

resolve to:

```text
project/foo.kaj
project/util/math.kaj
```

A future project manifest may define roots differently.

---

# 5. Local-Only Resolution

Kaj v0 import resolution searches only the local project root.

Do not resolve from:

```text
network URLs
package registries
global package caches
environment package paths
Python modules
system library directories
```

---

# 6. Import Syntax

Supported:

```kaj
import foo
```

and:

```kaj
import foo.bar
```

No alias syntax:

```text
import foo as f
```

in v0.

No selective syntax:

```text
from foo import bar
import foo.{a, b}
```

in v0.

---

# 7. Import Binding

An import introduces a module binding in the importing module's value namespace.

Example:

```kaj
import foo
```

introduces:

```text
foo
```

as a module value/namespace binding.

Example:

```kaj
import foo.bar
```

introduces the top-level module name:

```text
foo
```

with nested module access:

```text
foo.bar
```

This allows qualified access that mirrors the dotted module path.

---

# 8. Qualified Access

Imported declarations are accessed through the imported module path.

Example:

```kaj
import math

let x = math.add(1, 2)
```

For nested modules:

```kaj
import util.math

let x = util.math.add(1, 2)
```

Imports do not inject all exported declarations directly into the local scope.

---

# 9. Exported Declarations

In Kaj v0, all top-level named declarations are exported by default unless they are compiler-internal.

This includes:

```text
functions
record types
enum types
newtypes
module-level immutable bindings where valid
module-level mutable bindings only if language rules permit them
```

There is no explicit `public`/`private` syntax yet.

A future visibility system may refine this.

---

# 10. Imported Types

Types declared in an imported module are accessed through qualified module paths in type position.

Example:

```kaj
import models

let user: models.User = models.make_user()
```

For nested modules:

```kaj
import app.models

let user: app.models.User = app.models.make_user()
```

The type resolver must support module-qualified type names.

---

# 11. Imported Values

Values/functions are accessed similarly:

```kaj
import math

let x = math.add(1, 2)
```

The name:

```text
math
```

resolves to the imported module namespace.

Then:

```text
add
```

is looked up in that module's exported value declarations.

---

# 12. No Unqualified Import Injection

This:

```kaj
import math
```

does not make:

```kaj
add(1, 2)
```

automatically refer to `math.add`.

The qualified path is required:

```kaj
math.add(1, 2)
```

This avoids import collisions and keeps dependency origin explicit.

---

# 13. Module Identity

Each resolved source file corresponds to one logical module identity within a compilation.

If the same module is imported multiple times, it is loaded/compiled once and reused.

Module identity is based on its canonical resolved local path/module name within the project.

---

# 14. Import Graph

A program may form a directed module dependency graph.

Example:

```text
main -> foo
main -> util.math
foo  -> util.math
```

The compiler loads each module once and analyzes the complete reachable graph.

---

# 15. Transitive Imports

Imports are transitive for compilation/loading.

If:

```text
main imports foo
foo imports bar
```

the compiler loads `bar`.

However, `main` does not automatically gain a direct binding named `bar` unless `main` itself imports `bar`.

Module namespace visibility follows explicit imports.

---

# 16. Duplicate Imports

Importing the same module more than once in one source file is invalid or redundant.

Kaj v0 treats exact duplicate imports as a compile error.

Recommended diagnostic:

```text
IMPORT_DUPLICATE
```

This keeps source dependencies unambiguous.

---

# 17. Missing Module

If:

```kaj
import foo.bar
```

cannot resolve to:

```text
<project-root>/foo/bar.kaj
```

emit:

```text
IMPORT_NOT_FOUND
```

The diagnostic should identify the logical module name and attempted local path where practical.

---

# 18. Invalid Module Path

A module path must consist only of valid identifier segments.

Invalid module-path syntax is a parse error.

Path traversal syntax such as:

```text
..
/
\
```

is not part of Kaj import grammar.

The importer must not allow escaping the project root through crafted names.

---

# 19. Import Cycles

Import cycles are invalid in Kaj v0.

Example:

```text
a imports b
b imports a
```

or:

```text
a -> b -> c -> a
```

must produce:

```text
IMPORT_CYCLE
```

The diagnostic should show the cycle path where practical.

Cycle support may be reconsidered later if initialization semantics are formalized.

---

# 20. Module Initialization

A module's top-level executable statements are evaluated once when that module is loaded for execution.

Dependency modules are initialized before the importing module's top-level executable statements.

For:

```text
main imports foo
foo imports bar
```

a valid initialization order is:

```text
bar
foo
main
```

subject to dependency ordering.

---

# 21. Initialization Exactly Once

Each module executes its top-level initialization at most once per `kaj run` invocation.

Multiple import paths to the same module must not execute it repeatedly.

---

# 22. Deterministic Initialization Order

Module initialization order is deterministic and respects dependency order.

Where independent sibling dependencies exist, use source import order as the canonical tiebreaker.

Example:

```kaj
import a
import b
```

with no dependency between them initializes:

```text
a
b
current module
```

---

# 23. Compile-Time Analysis Order

The compiler may parse/load modules in any implementation order, but diagnostics and semantics must be deterministic.

All reachable modules must pass:

```text
lex
parse
resolution
type checking
```

before `kaj run` begins execution.

---

# 24. Compile Failure in Dependency

If an imported module contains a compile error, the whole entry program fails compilation.

`kaj run` must not execute any module.

`kaj check` exits with compile-error status.

Diagnostics identify the actual dependency file.

---

# 25. Runtime Failure in Dependency

If a dependency's top-level initialization produces a runtime error, `kaj run` fails with runtime-error status.

Output emitted before the failure remains observable.

No later dependent module initialization occurs after the failure.

---

# 26. Module Namespace Type

The compiler may represent an imported module using a dedicated semantic module-namespace type.

Conceptually:

```text
ModuleType
├── module identity
├── exported values
└── exported types
```

This is compiler-internal semantic structure.

It is not a user-declarable Kaj type.

---

# 27. Member Access on Modules

For:

```kaj
math.add
```

if `math` is a module namespace, `add` is resolved from the module's exported value namespace.

For:

```text
models.User
```

in type position, `User` is resolved from the module's exported type namespace.

Do not use ordinary record-field semantics for modules.

---

# 28. Unknown Imported Member

If a module does not export a requested member:

```kaj
import math

math.missing
```

the compiler emits an unknown-member/name diagnostic.

A dedicated diagnostic such as:

```text
IMPORT_UNKNOWN_MEMBER
```

is acceptable, or the existing member diagnostic may be reused consistently.

The important rule is that failure occurs statically.

---

# 29. Qualified Type Paths

Type expressions must support module-qualified type references.

Examples:

```text
models.User
foo.bar.ResultRecord
```

A qualified type path is not the same as a value `MemberAccessExpression`; it belongs to type syntax/semantic resolution.

The AST/type-expression representation should preserve the full qualified name structure.

---

# 30. Same-Name Modules and Values

An import binding occupies the importing module's value namespace.

Therefore:

```kaj
import foo
let foo = 10
```

is a same-scope duplicate and invalid under normal name-resolution rules.

Nested scopes may shadow imported module bindings according to normal lexical shadowing rules.

---

# 31. Type Name Collisions

Imported type declarations do not populate the importing module's unqualified type namespace.

Therefore:

```kaj
import models
```

does not directly declare `User` locally.

The type remains:

```text
models.User
```

This avoids cross-module type-name collisions.

---

# 32. Relative Imports

Relative syntax such as:

```text
import .foo
import ..foo
```

is not supported in v0.

All import names are project-root-relative logical names.

---

# 33. Remote Imports

Not supported:

```text
URL imports
Git imports
registry packages
version constraints
```

Do not infer or search remote dependencies.

---

# 34. Standard Library Imports

Checkpoint 17 does not define an external standard-library package namespace.

Language-standard builtins/types such as:

```text
print
Optional
Result
```

remain provided through existing language/compiler mechanisms.

They are not local import files.

---

# 35. Source File Encoding

Imported modules are UTF-8 Kaj source files and use the same lexical rules as the entry module.

---

# 36. Module Paths and File-System Safety

The resolver must normalize paths and ensure resolved files remain under the project root.

A dotted module path cannot escape the root.

Symlink behavior should be handled defensively; canonicalized resolved paths should be checked against the root where practical.

---

# 37. File Uniqueness

Two logical module names must not resolve to the same canonical source file in one compilation.

If path normalization/symlinks cause that ambiguity, treat the canonical file as one module identity and diagnose conflicting logical names if necessary.

Do not initialize one physical file multiple times.

---

# 38. `kaj check`

`kaj check entry.kaj` compiles the full reachable local import graph.

Success means every reachable module passes compile-time analysis.

---

# 39. `kaj run`

`kaj run entry.kaj` compiles the full graph, then initializes dependencies and executes the entry module.

---

# 40. `kaj fmt`

`kaj fmt file.kaj` formats only the requested source file.

It does not recursively format imported modules.

Formatting remains a single-file AST operation.

---

# 41. `kaj ast`

`kaj ast file.kaj` emits the AST JSON for only the requested source file.

It does not include imported module ASTs in the same JSON document.

Imports appear as normal `import` declarations in that file's AST.

---

# 42. Import AST

The AST represents imports explicitly.

Conceptually:

```text
ImportDeclaration
├── path_segments
└── span
```

Example:

```kaj
import foo.bar
```

stores:

```text
["foo", "bar"]
```

or an equivalent structured dotted path.

Do not store resolved file-system paths in the syntax AST.

---

# 43. AST JSON

Import declarations are represented in AST JSON as syntax only.

Example conceptual form:

```json
{
  "kind": "import_declaration",
  "path": ["foo", "bar"],
  "span": ...
}
```

Do not serialize:

```text
resolved absolute path
loaded module AST
module graph
semantic module identity
```

into the source AST JSON.

---

# 44. Formatter

Canonical formatting:

```kaj
import foo
import foo.bar
```

One import per line.

Imports preserve source order.

The formatter does not sort imports automatically in v0.

---

# 45. Source of Truth

For Kaj v0 local-module imports:

```text
docs/language/imports.md
```

defines the enduring language behavior.

Compiler, CLI, and runtime implementations must conform to it.
