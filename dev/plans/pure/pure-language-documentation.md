# Kaj Documentation Milestone — Pure Language Guide

**Status:** Complete  
**Purpose:** Turn the completed pure-language specification into a clear, user-facing guide for learning and using Kaj  
**Audience:** New Kaj users, application developers, educators, tooling authors, and AI systems generating Kaj  
**Scope:** Pure Kaj only  
**Out of scope:** Agentic Kaj, capabilities/effects, task semantics, planning, AST patches, remote packages, package registry

---

# 1. Goal

The pure Kaj language is now implemented and covered by the conformance suite.

The next step is to make Kaj understandable and usable without requiring readers to study compiler specifications.

Kaj documentation should have three distinct layers:

```text
Getting Started
    ↓
learn Kaj quickly

Guide
    ↓
learn how to use each language feature

Language Reference
    ↓
precise authoritative semantics
```

The existing `docs/language/` documents remain the authoritative specification.

This milestone adds the user-facing learning layer above them.

---

# 2. Documentation Architecture

Use:

```text
docs/
├── index.md
│
├── getting-started/
│   ├── installation.md
│   ├── quickstart.md
│   ├── first-program.md
│   └── cli.md
│
├── guide/
│   ├── index.md
│   ├── kaj-by-example.md
│   ├── variables.md
│   ├── types.md
│   ├── operators.md
│   ├── control-flow.md
│   ├── functions.md
│   ├── lists.md
│   ├── maps.md
│   ├── records.md
│   ├── enums-and-match.md
│   ├── optional-and-result.md
│   ├── newtypes.md
│   └── modules.md
│
├── language/
│   └── authoritative language specifications
│
├── compiler/
├── internals/
├── design/
├── roadmap/
└── archive/
```

Also maintain:

```text
examples/
```

as an executable example corpus.

---

# 3. Documentation Roles

## `docs/getting-started/`

Answers:

```text
How do I install Kaj?
How do I run a program?
What does Kaj code look like?
How do I get productive quickly?
```

These pages should minimize compiler terminology.

---

## `docs/guide/`

Answers:

```text
How do variables work?
How do I define a function?
How do I use Optional?
How do I create records?
How do modules work?
```

These pages should be practical and example-driven.

---

## `docs/language/`

Answers:

```text
What are the exact semantics?
What is assignable to what?
What diagnostics are guaranteed?
What is the precise runtime behavior?
```

These remain normative and should not become tutorial pages.

---

## `examples/`

Contains runnable `.kaj` files demonstrating correct Kaj.

These examples serve:

```text
human learning
documentation validation
regression testing
AI generation examples
future training/evaluation corpora
```

---

# 4. Documentation Style

User-facing docs should be:

```text
example first
short explanation second
precise rule third
```

Avoid opening a tutorial page with compiler architecture.

Prefer:

```kaj
let name = "Alice"
print(name)
```

followed by:

```text
`let` creates an immutable binding.
```

instead of starting with resolver/type-environment terminology.

---

# 5. Cross-Linking

Every practical guide page should link to the corresponding authoritative language reference.

Example:

```text
Guide: docs/guide/lists.md
Reference: docs/language/lists.md
```

The guide teaches usage.

The language page specifies exact behavior.

---

# 6. `docs/index.md`

The documentation landing page should introduce Kaj in one sentence.

Recommended positioning:

```text
Kaj is a strongly typed programming language designed for ordinary software
and, over time, safe human-agent collaboration.
```

The page should immediately offer three routes:

```text
New to Kaj
→ Quickstart

Want examples
→ Kaj by Example

Need exact semantics
→ Language Reference
```

Also include contributor links to compiler/internals docs without making them dominant.

---

# 7. Installation Guide

Create:

```text
docs/getting-started/installation.md
```

Cover the currently supported installation/development path.

Include:

```text
Python requirement
repository installation if still required
editable install if appropriate
virtual environment workflow
verifying installation
```

Verification:

```bash
kaj --version
```

Do not document installation mechanisms that do not actually exist yet.

If Kaj is not published as a package, say so clearly.

---

# 8. Quickstart

Create:

```text
docs/getting-started/quickstart.md
```

This should teach the majority of pure Kaj in approximately 10–15 minutes.

Recommended progression:

```text
1. Hello world
2. let and var
3. primitive values
4. arithmetic and comparisons
5. if / while / for
6. functions
7. lists
8. maps
9. records
10. enums and match
11. Optional
12. Result
13. newtypes
14. imports
15. CLI workflow
```

Keep sections short.

The goal is familiarity, not exhaustive specification.

---

# 9. Quickstart — Hello World

Begin with:

```kaj
print("Hello, Kaj!")
```

Run:

```bash
kaj run hello.kaj
```

Output:

```text
Hello, Kaj!
```

Then show:

```bash
kaj check hello.kaj
kaj fmt hello.kaj
kaj ast hello.kaj
```

This introduces the toolchain immediately.

---

# 10. Quickstart — Bindings

Show:

```kaj
let name = "Alice"
var count = 1

count = count + 1
```

Explain:

```text
let = immutable binding
var = rebindable binding
```

Do not introduce mutation beyond what pure Kaj supports.

---

# 11. Quickstart — Primitive Types

Show examples of:

```kaj
let ready = true
let count = 10
let price = 12.5
let name = "Alice"
let missing = none
```

Mention:

```text
Bool
Int
Decimal
String
Bytes
None
```

Only show `Bytes` syntax if source literal/construction support is actually user-facing at this point.

Do not invent unsupported bytes literal syntax.

---

# 12. Quickstart — Numeric Rules

Show:

```kaj
let x = 5 / 2
print(x)
```

Explain that Kaj produces:

```text
2.5
```

because:

```text
Int / Int -> Decimal
```

Also show:

```kaj
let price: Decimal = 10
```

as valid promotion.

---

# 13. Quickstart — Control Flow

Show:

```kaj
if ready {
    print("ready")
} else {
    print("not ready")
}
```

Then:

```kaj
var count = 0

while count < 3 {
    print(count)
    count += 1
}
```

Then:

```kaj
for value in [1, 2, 3] {
    print(value)
}
```

---

# 14. Quickstart — Functions

Show:

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}

print(add(2, 3))
```

Then briefly mention:

```text
explicit parameter types
explicit return types
recursion supported
named arguments supported
```

---

# 15. Quickstart — Lists

Show:

```kaj
let values = [1, 2, 3]

print(values.count)

for value in values {
    print(value)
}
```

Also:

```kaj
let first = values[0]
```

Mention zero-based indexing.

---

# 16. Quickstart — Maps

Show:

```kaj
let ages = {
    "Alice": 30,
    "Bob": 40
}
```

Then emphasize safe lookup:

```kaj
match ages["Alice"] {
    some(age) => print(age)
    none => print("missing")
}
```

Explain:

```text
Map<K,V>[K] -> Optional<V>
```

---

# 17. Quickstart — Records

Show:

```kaj
type User {
    name: String
    age: Int
}

let user = User {
    name: "Alice",
    age: 30,
}

print(user.name)
```

Explain:

```text
records are nominal
all fields are required
fields are immutable in pure Kaj v0
```

---

# 18. Quickstart — Enums and Match

Show:

```kaj
enum Status {
    pending
    complete
}

let status = Status.pending

match status {
    pending => print("pending")
    complete => print("complete")
}
```

Then payload enum:

```kaj
enum Message {
    quit
    text(value: String)
}
```

Mention exhaustive matching.

---

# 19. Quickstart — Optional

Show:

```kaj
let maybe_name: Optional<String> = some("Alice")
```

and:

```kaj
let missing_name: Optional<String> = none
```

Then matching:

```kaj
match maybe_name {
    some(name) => print(name)
    none => print("missing")
}
```

Explain primitive `None` vs contextual `Optional.none` briefly.

---

# 20. Quickstart — Result

Show:

```kaj
fn parse_value() -> Result<Int, String> {
    return ok(10)
}
```

Then:

```kaj
match parse_value() {
    ok(value) => print(value)
    err(message) => print(message)
}
```

Explicitly note:

```text
`?` is not part of pure Kaj yet.
```

---

# 21. Quickstart — Newtypes

Show:

```kaj
newtype UserId = String

let id = UserId("user-123")
print(id.value)
```

Explain:

```text
UserId != String
```

and:

```text
two newtypes with the same underlying type remain incompatible
```

---

# 22. Quickstart — Modules

Project:

```text
project/
├── main.kaj
└── math.kaj
```

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

Run:

```bash
kaj run project/main.kaj
```

Explain that imports are currently local project modules only.

---

# 23. First Program Tutorial

Create:

```text
docs/getting-started/first-program.md
```

This should build one meaningful program from start to finish.

Recommended program:

```text
small user directory
```

Use:

```text
newtype UserId
record User
enum UserStatus
Map<UserId, User>
Optional lookup
functions
match
```

The tutorial should grow the program incrementally.

---

# 24. First Program — Final Example

A strong final example:

```kaj
newtype UserId = String

enum UserStatus {
    active
    suspended(reason: String)
}

type User {
    id: UserId
    name: String
    status: UserStatus
}

fn describe(user: User) -> String {
    match user.status {
        active => return user.name
        suspended(reason) => return reason
    }
}

let users: Map<UserId, User> = {
    UserId("001"): User {
        id: UserId("001"),
        name: "Alice",
        status: UserStatus.active,
    },
}

match users[UserId("001")] {
    some(user) => print(describe(user))
    none => print("User not found")
}
```

Expected:

```text
Alice
```

This program should be executable and included in `examples/`.

---

# 25. CLI Guide

Keep:

```text
docs/getting-started/cli.md
```

as the user-facing CLI guide while preserving its authoritative behavior.

Ensure practical examples exist for:

```bash
kaj check program.kaj
kaj run program.kaj
kaj fmt program.kaj
kaj ast program.kaj
kaj --version
```

Also explain exit classes:

```text
0 success
1 compile error
2 runtime error
64 CLI misuse
```

---

# 26. Guide Index

Create:

```text
docs/guide/index.md
```

Organize by learning path:

```text
Core Syntax
- variables
- types
- operators
- control flow
- functions

Data
- lists
- maps
- records

Tagged Types
- enums and match
- Optional and Result

Type Safety
- newtypes

Programs
- modules
```

---

# 27. Variables Guide

Create:

```text
docs/guide/variables.md
```

Cover:

```text
let
var
type annotations
assignment
compound assignment
scope
shadowing
immutable parameters
var parameters
```

Examples should demonstrate valid usage and common invalid usage.

Do not turn the page into resolver documentation.

---

# 28. Types Guide

Create:

```text
docs/guide/types.md
```

Cover:

```text
Bool
Int
Decimal
String
Bytes
None
List<T>
Map<K,V>
Optional<T>
Result<T,E>
record types
enum types
newtypes
```

Explain nominal vs primitive/container types at a user level.

---

# 29. Operators Guide

Create:

```text
docs/guide/operators.md
```

Cover:

```text
+ - * / % **
== != < <= > >=
and or not
```

Include precedence table in user-friendly form.

Explicitly call out:

```kaj
5 / 2
```

→ Decimal.

Also explain:

```text
no implicit truthiness
```

---

# 30. Control Flow Guide

Create:

```text
docs/guide/control-flow.md
```

Cover:

```text
if
else
while
for
match
return
break
continue
```

Only document runtime behavior actually implemented.

If `break`/`continue` remain unsupported at runtime despite syntax, do not present them as usable until implementation matches.

---

# 31. Functions Guide

Create:

```text
docs/guide/functions.md
```

Cover:

```text
declarations
parameters
return types
named arguments
recursion
forward function references
mutability of parameters
return behavior
```

Show factorial as the primary recursion example.

---

# 32. Lists Guide

Create:

```text
docs/guide/lists.md
```

Cover:

```text
literal syntax
homogeneous typing
empty typed lists
indexing
count
for iteration
nested lists
numeric promotion
immutability
```

---

# 33. Maps Guide

Create:

```text
docs/guide/maps.md
```

Cover:

```text
literal syntax
Map<K,V>
allowed key types
safe lookup
Optional return
count
empty typed maps
numeric promotion
immutable map behavior
```

Make safe lookup the centerpiece.

---

# 34. Records Guide

Create:

```text
docs/guide/records.md
```

Cover:

```text
type declaration
construction
field access
nominal identity
nested records
records in functions/lists/maps
whole-value rebinding
field immutability
```

---

# 35. Enums and Match Guide

Create:

```text
docs/guide/enums-and-match.md
```

Cover:

```text
unit variants
payload variants
construction
match
pattern bindings
branch scope
exhaustiveness
definite return
```

Show `NON_EXHAUSTIVE_MATCH` as a common compiler diagnostic.

---

# 36. Optional and Result Guide

Create:

```text
docs/guide/optional-and-result.md
```

Cover both standard tagged types.

Optional:

```text
some
none
matching
safe absence
```

Result:

```text
ok
err
matching
explicit error handling
```

Explicitly state:

```text
No `?` propagation yet.
```

---

# 37. Newtypes Guide

Create:

```text
docs/guide/newtypes.md
```

Cover:

```text
nominal wrapper meaning
construction
.value
incompatibility
function boundaries
record fields
map keys
```

Use:

```kaj
newtype UserId = String
newtype OrderId = String
```

to show why this is useful.

---

# 38. Modules Guide

Create:

```text
docs/guide/modules.md
```

Cover:

```text
import foo
import foo.bar
qualified calls
qualified types
entry-file project root
transitive dependencies
local-only behavior
```

Explicitly state what does not exist yet:

```text
remote packages
registry resolution
aliases
selective imports
relative imports
```

---

# 39. Kaj by Example

Create:

```text
docs/guide/kaj-by-example.md
```

This page should be a dense catalog of small examples with minimal explanation.

Recommended sections:

```text
Hello world
Variables
Arithmetic
Conditionals
Loops
Functions
Recursion
Lists
Maps
Records
Enums
Pattern matching
Optional
Result
Newtypes
Modules
```

Each example should be runnable where possible.

---

# 40. Example Corpus

Create/expand:

```text
examples/
```

Recommended files:

```text
examples/
├── hello.kaj
├── variables.kaj
├── arithmetic.kaj
├── control-flow.kaj
├── factorial.kaj
├── lists.kaj
├── maps.kaj
├── records.kaj
├── enums.kaj
├── optional.kaj
├── result.kaj
├── newtypes.kaj
├── user-directory.kaj
└── modules/
    ├── main.kaj
    └── math.kaj
```

Every example should compile.

Runnable examples should execute successfully.

---

# 41. Examples as Tests

Add a test that discovers documented `.kaj` examples and verifies:

```text
kaj check -> success
```

for all examples intended to be valid.

For examples with expected output, optionally maintain metadata/test assertions.

This prevents documentation from drifting away from the language.

---

# 42. Invalid Examples

User-facing guides may show short invalid snippets when teaching errors.

Clearly mark them as invalid.

Do not place intentionally invalid source files in the normal valid `examples/` corpus unless they are in a separate directory such as:

```text
examples/invalid/
```

with explicit expected diagnostic metadata.

---

# 43. Documentation Code Accuracy

Every code block presented as valid Kaj must conform to the completed pure-language implementation.

Do not invent future syntax.

Particularly avoid accidentally documenting:

```text
?
closures
methods
classes
traits
remote imports
mutable record fields
map mutation
map iteration
wildcard match
pattern guards
```

before they exist.

---

# 44. Terminology

Use consistent user-facing terms:

```text
binding
type
record
enum
variant
payload
pattern
module
newtype
Optional
Result
```

Avoid switching unpredictably between:

```text
record/object/class
variant/case/member
module/package
```

unless explicitly explaining the difference.

---

# 45. Diagnostics in Guides

Teach important compiler errors where helpful.

Examples:

```text
TYPE_MISMATCH
NON_EXHAUSTIVE_MATCH
RESOLVE_UNKNOWN_NAME
ASSIGN_TO_IMMUTABLE
IMPORT_NOT_FOUND
```

But do not turn every tutorial into a diagnostic catalog.

The conformance suite and specs remain the exhaustive source.

---

# 46. AI-Friendly Documentation

Because Kaj is intended to be generated by agents later, docs/examples should be machine-friendly.

Prefer:

```text
complete code
consistent formatting
explicit types where educationally useful
small focused examples
stable headings
canonical syntax
```

Avoid prose-only descriptions of core syntax.

The example corpus may later serve evaluation/training use.

---

# 47. MkDocs Navigation

Update:

```text
mkdocs.yml
```

with a clear navigation tree such as:

```text
Home
Getting Started
  Installation
  Quickstart
  First Program
  CLI

Guide
  Overview
  Kaj by Example
  Variables
  Types
  Operators
  Control Flow
  Functions
  Lists
  Maps
  Records
  Enums and Match
  Optional and Result
  Newtypes
  Modules

Language Reference
  Lexical Structure
  Primitive Types
  Functions
  Lists
  Records
  Enums and Match
  Optional and Result
  Maps
  Newtypes
  Formatting
  Imports

Compiler
Internals
Design
Roadmap
```

---

# 48. Link Validation

Ensure all internal documentation links resolve.

Where practical, use MkDocs build as validation:

```bash
mkdocs build
```

Broken navigation or links should be fixed before completion.

---

# 49. Documentation Build

The complete documentation site must build successfully.

Run:

```bash
mkdocs build
```

No broken configuration.

Warnings should be reviewed rather than ignored blindly.

---

# 50. Suggested Implementation Order

### Step 1
Audit existing docs and examples.

### Step 2
Update `docs/index.md`.

### Step 3
Create installation + quickstart.

### Step 4
Create first-program tutorial.

### Step 5
Create guide index.

### Step 6
Create core syntax guides.

### Step 7
Create collections/data guides.

### Step 8
Create enums/Optional/Result/newtype guides.

### Step 9
Create module guide.

### Step 10
Create Kaj-by-example page.

### Step 11
Create executable example corpus.

### Step 12
Add example validation tests.

### Step 13
Update MkDocs navigation.

### Step 14
Cross-link guide ↔ reference pages.

### Step 15
Run documentation build and full test suite.

---

# 51. Definition of Done

This documentation milestone is complete when:

```text
[ ] docs/index.md provides clear entry paths

[ ] installation guide exists
[ ] quickstart exists
[ ] first-program tutorial exists
[ ] CLI guide is complete/current

[ ] guide/index.md exists
[ ] kaj-by-example.md exists
[ ] variables guide exists
[ ] types guide exists
[ ] operators guide exists
[ ] control-flow guide exists
[ ] functions guide exists
[ ] lists guide exists
[ ] maps guide exists
[ ] records guide exists
[ ] enums-and-match guide exists
[ ] optional-and-result guide exists
[ ] newtypes guide exists
[ ] modules guide exists

[ ] guide pages link to authoritative reference docs
[ ] language spec docs remain normative and are not rewritten into tutorial plans

[ ] executable examples corpus exists
[ ] examples cover all major pure-language features
[ ] every valid example passes `kaj check`
[ ] runnable examples execute successfully

[ ] one large user-directory example exists
[ ] one multi-module example exists

[ ] no future/agentic syntax is documented as current behavior
[ ] no `?` documented as implemented
[ ] no mutable record fields documented
[ ] no map mutation/iteration documented
[ ] no remote package support documented

[ ] MkDocs navigation updated
[ ] internal links resolve
[ ] `mkdocs build` succeeds

[ ] pytest passes
[ ] ruff check . passes
[ ] mypy src passes

[ ] pure Kaj is learnable without reading compiler internals
```

---

# 52. Recommended Final User Journey

A new user should be able to follow:

```text
docs/index.md
    ↓
getting-started/installation.md
    ↓
getting-started/quickstart.md
    ↓
getting-started/first-program.md
    ↓
guide/kaj-by-example.md
    ↓
specific guide pages
    ↓
language reference when precision is needed
```

---

# 53. Why This Milestone Matters

This milestone creates the stable human-facing surface for pure Kaj before agentic constructs expand the language.

It gives Kaj:

```text
an implementation
a conformance suite
a specification
a tutorial path
an example corpus
```

That creates a clean baseline from which agentic Kaj can evolve without making the core language difficult to understand.

---

# 54. Completion Report

When finished, report:

```text
Pure Kaj Documentation Milestone — Complete / Incomplete

Pages added:
- ...

Pages changed:
- ...

Examples added:
- ...

Guide coverage:
- installation: PASS/FAIL
- quickstart: PASS/FAIL
- first program: PASS/FAIL
- variables: PASS/FAIL
- types: PASS/FAIL
- operators: PASS/FAIL
- control flow: PASS/FAIL
- functions: PASS/FAIL
- lists: PASS/FAIL
- maps: PASS/FAIL
- records: PASS/FAIL
- enums/match: PASS/FAIL
- Optional/Result: PASS/FAIL
- newtypes: PASS/FAIL
- modules: PASS/FAIL
- Kaj by Example: PASS/FAIL

Example validation:
- valid examples compile: PASS/FAIL
- runnable examples execute: PASS/FAIL
- module example: PASS/FAIL

Documentation:
- MkDocs navigation: PASS/FAIL
- MkDocs build: PASS/FAIL
- internal links: PASS/FAIL

Verification:
- pytest: PASS/FAIL
- ruff check .: PASS/FAIL
- mypy src: PASS/FAIL

Future syntax accidentally documented:
- ...

Known documentation gaps:
- ...

Ready to begin agentic Kaj documentation/design work: YES/NO
```
