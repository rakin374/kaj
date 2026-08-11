# 2. Language and Execution Model

## 2.1 Kaj is a real runnable language

The normal user experience should be:

```bash
kaj hello.kaj
```

The internal implementation can be richer:

```text
source
  ↓
parse
  ↓
AST
  ↓
name resolution
  ↓
type/effect checking
  ↓
semantic validation
  ↓
Task IR / executable IR
  ↓
runtime
```

Kaj should not merely be a plan file consumed by Berkbrain.

## 2.2 Program categories

Kaj should support three overlapping categories.

### Ordinary computation

```kaj
let values = [10, 20, 30]
print(mean(values))
```

### Effectful scripts

```kaj
use filesystem

let content = filesystem.read("report.txt")
print(content)
```

### Goal-directed tasks

```kaj
use web

task research {
    goal {
        "Find three matching products."
    }

    success {
        products.count >= 3
    }

    ...
}
```

A file may combine all three.

## 2.3 Top-level execution

Proposed V0.x behavior: top-level executable statements run in source order.

```kaj
let name = "world"
print("Hello, {name}")
```

Running:

```bash
kaj hello.kaj
```

executes the program naturally.

Functions/tasks may be declared without automatically running.

Potential CLI later:

```bash
kaj file.kaj
kaj run file.kaj
kaj run file.kaj::research
```

## 2.4 Pure vs capability-dependent execution

Pure Kaj:

```kaj
fn square(x: Decimal) {
    return x * x
}

print(square(8))
```

can run on the ordinary runtime.

Capability-dependent Kaj:

```kaj
use web
web.open("https://example.com")
```

requires a provider implementing `web`.

Conceptually:

```text
Kaj language
+ runtime
+ capability provider
= executable effectful program
```

## 2.5 Runtime providers

A capability can have multiple providers.

```text
web
 ├── WKWebView provider
 ├── Playwright provider
 └── remote cloud-browser provider
```

The source program should target the capability contract, not one vendor/runtime.

## 2.6 Compilation strategy

Kaj initially does not need native machine-code compilation.

Early implementation can lower into typed IR interpreted/orchestrated by the runtime.

Long-term options may include:

- interpreter,
- bytecode VM,
- native compilation for pure code,
- JIT,
- robot/simulator-specific lowering,
- distributed runtime execution.

The language should not depend on one backend.

## 2.7 Deterministic semantics vs nondeterministic environments

Pure expression:

```kaj
let x = 2 + 2
```

must be deterministic.

External observation:

```kaj
observe vision.scene as room
```

depends on reality and time.

Kaj's effect system should preserve this distinction.

## 2.8 Host/runtime responsibilities

The compiler answers:

> Is this program valid and what does it mean?

The host runtime answers:

> Which capabilities exist, what authority exists, and how should valid effects be carried out?

Host responsibilities can include:

- task persistence,
- user permissions,
- authentication,
- browser/robot instances,
- secrets,
- task memory,
- world models,
- recovery,
- observability,
- usage accounting.

## 2.9 Hosted server authority

For Berkbrain/Chalok, authoritative compilation and policy should be server-side:

```text
user
 ↓
planner LLM
 ↓
structured Kaj AST
 ↓
server Kaj compiler
 ↓
Task IR
 ↓
server policy / permissions / safety
 ↓
authorized action envelope
 ↓
client browser runtime
```

Clients may locally parse/check for UX but should not become the sole authorization boundary for consequential actions.

## 2.10 Local execution

Kaj must remain usable outside Berkbrain.

Future possibilities:

```bash
kaj run research.kaj --runtime playwright
kaj run robot_task.kaj --runtime ros
kaj run simulation.kaj
```

## 2.11 Execution budgets

Every effectful host should impose budgets such as:

```text
max elapsed time
max actions
max loop iterations
max recursion depth
max model calls
max browser navigations
max external requests
max monetary exposure
```

Source can request limits, but source never overrides hard host limits.

## 2.12 Interruptibility

Long-running Kaj tasks must be:

- pausable,
- cancellable,
- supersedable,
- checkpointable,
- resumable,
- interruptible by human input.

## 2.13 Planning need not be whole-program upfront

In uncertain environments, Kaj hosts should support incremental task patches:

```text
initial task
 ↓
execute / observe
 ↓
planner adds or modifies task nodes
 ↓
validate patch
 ↓
continue
```

This is preferable to generating a rigid giant plan at the start.
