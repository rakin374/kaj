# Agentic Kaj

Agentic Kaj extends the pure Kaj language with durable, typed units of work.
It keeps Pure Kaj's ordinary values, functions, modules, control flow, static
typing, and deterministic formatting, then adds runtime coordination features
around them.

```text
Pure Kaj
   ↓
Agentic Kaj
   ├── tasks
   ├── steps and lifecycle
   ├── contracts
   ├── human interaction
   ├── persistence and resume
   ├── capabilities
   ├── task composition
   ├── planning
   └── controlled replanning
```

The initial foundation is frozen as **Agentic Kaj Conformance 1**.

## The model in one minute

A `task` is a durable operation with its own identity and lifecycle. Named
`step` blocks create durable execution boundaries. Contracts state intent and
conditions. Human interactions and capability calls can suspend execution.
Tasks can start and await child tasks. A host may attach a planner, but every
proposed plan is parsed, resolved, type-checked, and authority-checked by Kaj
before it runs.

The core trust boundary is:

```text
planner proposes → Kaj validates → runtime executes
```

Kaj source can declare that a capability is required, but only the host can
grant that authority. Completed durable history cannot be rewritten by a
planner or replan.

## End-to-end example

This example combines contracts, a host capability, a durable step, human
confirmation, and child-task composition:

```kaj
capability Inventory {
    fn available(item: String) -> Bool
}

task CheckStock(item: String) -> Bool {
    use Inventory as inventory
    return inventory.available(item)
}

task Purchase(item: String) -> Result<String, String> {
    goal "Purchase {item} after checking stock and receiving approval"

    require {
        item != ""
    }

    invariant {
        item != ""
    }

    use Inventory as inventory

    step check {
        let stock_check = start CheckStock(item)
        let available = await stock_check

        if not available {
            return err("out of stock")
        }
    }

    step approve {
        let approved = confirm("Purchase {item}?")

        if not approved {
            return err("not approved")
        }
    }

    inform("Purchase approved for {item}")
    return ok(item)
}
```

The host must independently bind `Inventory` for every task that requires it.
If confirmation is unanswered, `Purchase` enters `waiting_for_human`. If the
process restarts, a persistent host can restore the same task and interaction
identity and continue from the committed boundary.

## Read in this order

1. [Tasks](tasks.md) — declarations, identity, and task execution.
2. [Steps and lifecycle](steps-and-lifecycle.md) — durable boundaries and states.
3. [Task contracts](task-contracts.md) — `goal`, `require`, `invariant`, and `success`.
4. [Human interaction](human-interaction.md) — `ask`, `choose`, `confirm`, `inform`, and `handoff`.
5. [Persistence and resume](persistence-resume.md) — snapshots and crash recovery.
6. [Capabilities](capabilities.md) — typed host operations and authority.
7. [Task composition](task-composition.md) — `start`, `TaskHandle<T>`, and `await`.
8. [Planner interface](planner-interface.md) — validated structured planning.
9. [Controlled replanning](controlled-replanning.md) — safe replacement of future work.
10. [Agentic conformance](agentic-conformance.md) — compatibility requirements.

## What remains Pure Kaj

Code inside tasks uses normal Kaj expressions, types, bindings, functions,
records, enums, lists, maps, `Optional`, `Result`, and module imports. Agentic
constructs do not weaken lexical scope or type checking. Runtime identities,
host bindings, snapshots, and lifecycle state are never part of source AST JSON.

## Current boundaries

Agentic Kaj Conformance 1 intentionally does not define task groups, distributed
scheduling, remote migration, exactly-once external effects, retry syntax,
vendor-specific planner APIs, or automatic contract mutation.
