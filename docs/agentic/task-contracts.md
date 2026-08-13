# Task Contracts

Task contracts define the intent, preconditions, invariants, and completion criteria of Agentic Kaj tasks.

This document defines the initial semantics of:

```text
goal
require
invariant
success
```

Task contracts are evaluated by the Agentic Kaj runtime but are written using ordinary Kaj expressions and values.

---

## 1. Contract overview

A task may declare a contract around its execution.

Conceptually:

```kaj
task FindProduct(query: String, max_price: Decimal)
    -> Result<Product, FindProductError>
{
    goal "Find {query} for no more than {max_price}"

    require {
        max_price > 0
    }

    invariant {
        max_price > 0
    }

    step search {
        // ...
    }

    success(result: Product) {
        result.price <= max_price
    }

    return err(not_found)
}
```

The initial task contract has four distinct concepts:

```text
goal
require
invariant
success
```

They are not interchangeable.

---

## 2. `goal`

`goal` describes the task's intended outcome in human-readable form.

Example:

```kaj
goal "Find {query} for no more than {max_price}"
```

The goal is:

```text
human-readable
planner-visible
available to host UI/runtime inspection
immutable for the lifetime of a task instance
not itself proof of completion
```

A goal is descriptive intent.

It does not replace `success`.

---

## 3. Goal syntax

A task may declare at most one goal.

Initial syntax:

```kaj
goal "text"
```

String interpolation follows ordinary Kaj string semantics.

Example:

```kaj
task Research(topic: String) -> None {
    goal "Research {topic}"
    return none
}
```

The goal expression must type-check as `String`.

Invalid:

```kaj
goal 42
```

---

## 4. Goal placement

`goal` may appear only directly inside a task body.

It may not appear:

```text
inside fn
inside step
inside if
inside loop
inside match
inside another contract block
```

The initial model treats contract declarations as top-level task structure.

---

## 5. `require`

`require` defines a precondition that must be true before task execution begins.

Example:

```kaj
require {
    budget > 0
}
```

The body must evaluate to `Bool`.

If a requirement is false, the task does not begin normal execution.

---

## 6. Multiple requirements

A task may declare multiple `require` blocks.

All must evaluate to `true`.

Conceptually:

```text
require A
require B
require C

task starts only if:
A and B and C
```

Evaluation order is source order.

---

## 7. Requirement timing

Requirements are evaluated after:

```text
task definition resolution
argument validation
TaskInstance creation
```

and before:

```text
ready -> running
task body execution
step execution
```

Recommended lifecycle behavior:

```text
created
   ↓
requirements evaluated
   ├── all true -> ready
   └── any false -> failed
```

A failed requirement is a task contract failure.

It is not a domain-level `Result.err(...)`.

---

## 8. Requirement purity

Initial `require` expressions must be pure.

They may use:

```text
task parameters
immutable task-local values available before execution, if any
pure fn calls
ordinary pure Kaj expressions
```

They may not use:

```text
steps
human interaction
capabilities
task composition
planner operations
external effects
```

A requirement must not change the world.

---

## 9. `invariant`

An invariant defines a condition that must remain true throughout task execution.

Example:

```kaj
invariant {
    total_spend <= max_price
}
```

The invariant body must evaluate to `Bool`.

---

## 10. Multiple invariants

A task may declare multiple invariants.

All must remain true.

Evaluation order is source order.

---

## 11. Invariant timing

In the initial model, invariants are checked:

```text
after requirements pass
before task execution begins
after every completed step
before task completion
```

Conceptually:

```text
requirements pass
↓
check invariants
↓
run step
↓
check invariants
↓
run next step
↓
check invariants
↓
before completion
check invariants
```

Capability operations execute under the same invariant lifecycle rules.

---

## 12. Invariant violation

If an invariant evaluates to `false`, the task fails.

Conceptually:

```text
running
   ↓
invariant false
   ↓
failed
```

This is a runtime contract failure.

It is not:

```text
completed with Result.err(...)
```

---

## 13. Invariant purity

Initial invariants must be pure.

They may inspect Kaj state.

They may not perform external effects.

This ensures invariant evaluation itself does not change the task or environment.

---

## 14. `success`

`success` defines a machine-checkable completion criterion.

A natural-language goal describes intent.

A success condition determines whether a returned result satisfies the task contract.

Conceptually:

```text
goal
    "Find a product under $30"

success
    result.price <= 30
```

The runtime must not treat the goal string as proof that work is complete.

---

## 15. Success syntax

For a task returning a non-`None` value, success may bind the returned value:

```kaj
success(result: Product) {
    result.price <= max_price
}
```

The success body must evaluate to `Bool`.

The result parameter type must match the task's declared return type, or a deliberately supported success-view type if later introduced.

Initial rule:

```text
success parameter type == task return type
```

---

## 16. Success for `None`

For a `None` task, success may omit a result parameter:

```kaj
task Notify() -> None {
    success {
        true
    }

    return none
}
```

This provides a consistent completion contract for tasks without a meaningful result value.

---

## 17. Success timing

When a task is about to return normally:

```text
return value computed
↓
return type validated
↓
invariants checked
↓
success condition evaluated
```

If success is `true`:

```text
task -> completed
```

If success is `false`:

```text
task -> failed
```

The returned value may be retained in failure diagnostics/runtime inspection, but the task is not considered completed.

---

## 18. Missing success clause

A task is not required to declare `success` in the initial contract model.

If no success clause exists:

```text
a valid normal return is sufficient for completion
```

This preserves compatibility with tasks introduced before contracts.

---

## 19. One success clause

A task may declare at most one `success` clause.

Invalid:

```kaj
success(result: Int) {
    result > 0
}

success(result: Int) {
    result < 10
}
```

If multiple conditions are required, combine them with ordinary Kaj Boolean logic:

```kaj
success(result: Int) {
    result > 0 and result < 10
}
```

---

## 20. Success purity

The success condition must be pure.

It may inspect:

```text
task parameters
task state visible in ordinary Kaj values
returned result
pure fn calls
```

It may not:

```text
invoke capabilities
ask humans
start tasks
modify external state
```

The initial purity analysis permits ordinary pure expressions, constructors, pure builtins, and
local user functions that themselves contain no assignment and call only pure functions or
builtins. `print`, task invocation, qualified imported calls, and functions containing assignment
are conservatively rejected in contracts. This is intentionally smaller than a future effect
system and may be generalized only when Kaj gains explicit effect metadata.

---

## 21. Contract declaration placement

Contract declarations may appear only directly inside task bodies.

They are not ordinary executable statements.

The parser/semantic model should treat them as task-level declarations.

Recommended structural ordering for readability:

```text
goal
require
invariant
steps/body
success
```

But the language need not require this exact textual order if the implementation can collect contract declarations deterministically.

---

## 22. Contract declarations are not first-class values

The following concepts are not ordinary variables or callables:

```text
goal
require
invariant
success
```

They cannot be referenced, assigned, passed to functions, or called.

---

## 23. Contract scope

Contract expressions may access task parameters.

Example:

```kaj
task Buy(limit: Decimal) -> Decimal {
    require {
        limit > 0
    }

    success(result: Decimal) {
        result <= limit
    }

    return limit
}
```

They follow ordinary name resolution for permitted visible values.

---

## 24. Mutable state and invariants

Invariants may inspect task-local mutable variables that remain in scope at invariant evaluation points.

Example:

```kaj
task Count() -> Int {
    var count = 0

    invariant {
        count >= 0
    }

    step increment {
        count = count + 1
    }

    return count
}
```

The runtime evaluates the invariant against the current task environment.

---

## 25. Contract evaluation failure

If evaluating a contract expression itself causes an unrecoverable Kaj runtime error, the task fails.

Examples:

```text
require evaluation runtime failure
invariant evaluation runtime failure
success evaluation runtime failure
```

These are runtime contract-evaluation failures.

They must not be silently converted to `false`.

---

## 26. Requirement false versus requirement evaluation error

These are distinct:

```text
require evaluates to false
    -> requirement violation

require evaluation crashes
    -> contract evaluation failure
```

Both fail the task, but diagnostics should distinguish them.

---

## 27. Success false versus success evaluation error

Likewise:

```text
success evaluates to false
    -> success condition not satisfied

success evaluation crashes
    -> contract evaluation failure
```

---

## 28. Contract lifecycle effects

The initial lifecycle interaction is:

```text
TaskInstance created
↓
state = created

requirements evaluated
├── fail -> failed
└── pass

state = ready
↓
initial invariants checked
├── fail -> failed
└── pass

state = running
↓
steps/body execute

after completed step:
check invariants

before normal completion:
check invariants
check success if present

all pass:
completed
```

---

## 29. Paused tasks

Normal task pause semantics remain unchanged.

Pausing does not itself re-evaluate contracts.

On resume, the runtime may re-check invariants before continuing if required for safety.

Initial rule:

```text
resume from paused -> check invariants -> running
```

If an invariant fails during resume validation, the task fails instead of resuming.

---

## 30. Cancelled tasks

Cancellation does not evaluate success.

A cancelled task remains:

```text
cancelled
```

It is not completed even if its success condition would have been true.

---

## 31. Contract failure and domain `Result`

Contract failure is distinct from a returned `Result.err(...)`.

Example:

```kaj
task Find() -> Result<Int, String> {
    success(result: Result<Int, String>) {
        true
    }

    return err("not found")
}
```

If the success condition accepts that returned value, the task may complete normally.

Contract semantics operate on the declared task result as a Kaj value.

---

## 32. Goal and planner behavior

The goal is planner-visible structured task metadata. Planner access does not
change its contract semantics or permit the planner to modify it.

---

## 33. Runtime representation

The runtime should represent task contracts separately from ordinary task statements.

Conceptually:

```text
TaskDefinition
    goal
    requirements
    invariants
    success
    body/steps
```

Task-instance runtime data may record:

```text
requirement violation
invariant violation
success failure
contract evaluation failure
```

These are runtime data, not source AST fields beyond the declarations themselves.

---

## 34. AST representation

Contract declarations are source-level syntax and therefore appear in the AST.

Conceptually:

```text
GoalClause
RequireClause
InvariantClause
SuccessClause
```

or equivalent nodes appropriate to the existing AST design.

Runtime evaluation outcomes do not appear in AST JSON.

---

## 35. Determinism

Contract evaluation order must be deterministic.

Freeze:

```text
requirements: source order
invariants: source order
success: one clause
```

No host-dependent ordering is permitted.

---

## 36. Summary

The initial task-contract model freezes:

```text
goal:
    one optional String intent
    immutable
    descriptive, not proof of success

require:
    zero or more
    Bool
    pure
    evaluated before task runs
    false -> task failed

invariant:
    zero or more
    Bool
    pure
    checked before execution,
    after each completed step,
    before completion,
    and before resume
    false -> task failed

success:
    zero or one
    Bool
    pure
    evaluated against returned result
    false -> task failed

contract failures are distinct from Result.err(...)
contract expressions use ordinary Kaj typing
contract declarations live directly inside task bodies
```
