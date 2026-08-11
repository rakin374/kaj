# 12. Open Questions and KIP Backlog

Kaj should not pretend every decision is settled. These questions should drive the first Kaj Improvement Proposals.

## 12.1 Static vs dynamic typing

Current preferred direction:

```text
static by default
strongly typed
heavy inference
explicit Dynamic/Any escape hatch
```

Still test whether function parameter types can be inferred more often without creating confusing whole-program inference.

## 12.2 `fn` purity

Should every `fn` be pure by definition?

Options:

1. `fn` pure, effects only in `step`,
2. explicit effect annotations on `fn`,
3. another construct such as `proc`,
4. inferred effect sets.

Initial proposal favors pure/default `fn` and effectful `step`.

## 12.3 What exactly is a `step`?

Need formal rules for:

- return values,
- local state,
- retries,
- dependencies,
- resumability,
- concurrency,
- recursion,
- whether steps can exist outside tasks.

## 12.4 Task return values

Should this be legal?

```kaj
task research(topic: String) -> Report {
    ...
}
```

Likely yes, but define result/completion semantics.

## 12.5 `when`

Do not make `when` a redundant `if`.

Possible future meanings:

- event/reactive handler,
- wait-until trigger,
- pattern guard.

## 12.6 Async/concurrency

Likely future needs:

```text
parallel for
spawn
await
race
```

Need safe semantics for side effects.

## 12.7 Cancellation

How do effectful tasks clean up on cancellation?

## 12.8 Exceptions vs Result

Need distinction between:

- programming failures,
- expected environmental outcomes,
- task blocking,
- host infrastructure failures.

Likely prefer typed Result/enums for normal capability outcomes.

## 12.9 Ranges

Choose canonical syntax:

```text
1 through 3
1..3
1..<3
```

or a carefully specified combination.

## 12.10 Object/type model

Do not prematurely reserve:

```text
class
struct
trait
protocol
interface
```

Need first decide Kaj's actual semantics.

## 12.11 Generic constraints

Need trait/type-class/protocol-like model only when real use cases demand it.

## 12.12 Module system

Need:

- file/module mapping,
- imports,
- package visibility,
- public/private APIs.

Likely eventually needs `pub` or equivalent.

## 12.13 Numeric overflow and precision

Specify:

- integer overflow behavior,
- Decimal precision,
- Decimal rounding,
- Money rounding,
- currency minor units.

## 12.14 Physical units

Need design for:

- syntax,
- dimensions,
- conversions,
- user-defined units,
- robotics coordinate frames.

## 12.15 Observation syntax

Current proposal:

```kaj
observe web.page as page
```

Need formal source and metadata semantics.

## 12.16 `learn`

Need define:

- where it is legal,
- how scope is selected,
- what evidence is required,
- whether model inference can ever be directly durable,
- how conflicts are represented.

Likely source proposes knowledge; host memory policy validates it.

## 12.17 Fact state predicates

Readable:

```kaj
invoice.amount is confirmed
```

Need determine whether `confirmed`, `conflicted`, `stale`, etc. are contextual grammar or ordinary enum/state APIs.

## 12.18 Contract block semantics

Likely lines in:

```kaj
success { ... }
expect { ... }
invariant { ... }
```

are implicitly ANDed, but this should be formally defined.

## 12.19 Human interaction syntax

Compare:

```kaj
ask user "Age?" as age: Int
```

vs:

```kaj
let age: Int = ask user "Age?"
```

The task-oriented form is currently preferred but both deserve evaluation.

## 12.20 Capability manifest/package format

Need stable provider declaration and trust model.

## 12.21 Capability trust

Distinguish:

- pure Kaj package,
- native plugin,
- remote provider,
- privileged hardware provider.

## 12.22 Python interoperability

Potentially extremely useful because of NumPy/PyTorch/scientific libraries.

But arbitrary Python calls can bypass Kaj's effect model.

Interop needs explicit trust/effect semantics.

## 12.23 Native FFI

Eventually needed for robotics/science/system integration.

Potential C ABI/Rust/Python paths should be evaluated later.

## 12.24 Web capability boundary

Must align with actual browser workspace semantics: stable tab IDs, navigation lifecycle, page actions, site-initiated popups, external schemes, action results, and recovery.

## 12.25 World-model hook granularity

Should world models predict:

- individual IR actions,
- action groups,
- entire steps,
- alternative candidate plans?

Start with individual consequential actions and expand experimentally.

## 12.26 Recovery in language vs host

Most recovery belongs to the host.

Potential future syntax such as:

```kaj
on uncertain { ... }
```

should not be added until real patterns justify it.

## 12.27 Source-level capability requirements

Source may declare needed effects/capabilities, but never grant authorization.

## 12.28 Compiler implementation language

Start in Python.

Consider Rust only when stability, embedding, performance, or cross-platform packaging justify migration.

## 12.29 KIP backlog

Suggested initial sequence:

```text
KIP-0001 Core Goals and Design Principles
KIP-0002 Lexical Grammar and Keywords
KIP-0003 Type System
KIP-0004 Functions, Control Flow, and Math
KIP-0005 Effect Model
KIP-0006 Task and Step Semantics
KIP-0007 Contracts and Verification
KIP-0008 Human Interaction
KIP-0009 Observation and Fact Model
KIP-0010 Capability System
KIP-0011 Kaj AST Schema
KIP-0012 Task IR
KIP-0013 Compiler Architecture
KIP-0014 Host Runtime Interface
KIP-0015 Web Capability v1
KIP-0016 World Model Interface
```

## 12.30 Guiding rule for unresolved choices

Prefer the option that:

1. makes invalid agent behavior harder to express,
2. remains pleasant for ordinary scripting,
3. stays readable to humans,
4. stays easy for models to generate,
5. compiles into precise typed semantics,
6. does not unnecessarily bind Kaj to one host or capability.
