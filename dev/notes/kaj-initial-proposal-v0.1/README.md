# Kaj Initial Proposal v0.1

**Status:** Initial proposal / design baseline  
**Language:** Kaj  
**Source extension:** `.kaj`  
**Primary CLI:** `kaj`  
**Compiler-safe fallback alias:** `kajc`  
**Proposed license:** Apache License 2.0  
**Initial implementation:** standalone open-source reference compiler, initially in Python  
**First production host:** Berkbrain  
**First production capability/runtime:** Chalok Web

Kaj is a proposed strongly typed, human-readable programming language for intelligent agents and ordinary scripting. It is designed to express computation, long-running goal-directed work, external-world actions, observation, evidence-backed knowledge, human collaboration, verification, and eventually world-model-assisted planning across web, robotics, vision, audio, simulation, and other domains.

The name **Kaj** comes from the Bangla word **কাজ**, meaning **work**.

This documentation set is intentionally broad. It establishes the starting architecture from which Kaj should be built. It is not a claim that every syntax choice is permanently frozen.

## Core thesis

Kaj should be able to express ordinary programs:

```kaj
fn average(values: List<Decimal>) {
    return sum(values) / values.count
}

let result = average([10, 20, 30])
print(result)
```

and goal-directed agent programs:

```kaj
use web

task research_monitor {
    goal {
        "Find a strong 27-inch monitor under $300."
    }

    success {
        candidates.count >= 3
        every candidates.price is confirmed
    }

    step research {
        web.open("https://example.com")
        observe web.page as page
        extract candidates from page

        inform user
            "I found {candidates.count} candidates."
    }
}
```

and later physical-agent programs:

```kaj
use robot
use vision

task clear_table {
    observe vision.scene as room

    let cups = room.objects.filter(.kind == Cup)

    for cup in cups {
        let grasp = robot.plan_grasp(cup)
        require grasp.is_safe

        robot.grasp(cup, using: grasp)
        verify robot.holds(cup)

        robot.move_to(tray)
        robot.release(cup)
        verify cup.position is in tray
    }
}
```

Kaj is therefore **not a web DSL**. Web automation is simply its first major capability environment.

## Architectural position

```text
Natural-language intent
        ↓
Planner / LLM
        ↓
Structured Kaj AST
        ↓
Kaj compiler
        ↓
Validated Task IR
        ↓
Host runtime
        ↓
Capabilities / permissions / task memory / world models
        ↓
External environment
```

Human-authored Kaj follows the parallel route:

```text
.kaj source
    ↓
parser
    ↓
Kaj AST
    ↓
same compiler pipeline
```

The **AST is the canonical semantic representation**. Textual Kaj is the canonical human-readable source form. Structured JSON AST is the preferred initial LLM output format.

## Design-status vocabulary

- **Baseline** — part of the initial direction and should be implemented unless a concrete issue is discovered.
- **Proposed** — preferred design but still expected to evolve.
- **Deferred** — intentionally not required for the first compiler/runtime.

## Documentation map

1. `00-initial-proposal.md`
2. `01-vision-and-design-principles.md`
3. `02-language-and-execution-model.md`
4. `03-syntax-keywords-and-type-system.md`
5. `04-computation-tasks-effects-and-human-interaction.md`
6. `05-capabilities-world-models-and-runtime.md`
7. `06-ast-ir-and-llm-integration.md`
8. `07-compiler-architecture-and-project-layout.md`
9. `08-security-permissions-verification-and-recovery.md`
10. `09-tooling-open-source-governance-and-versioning.md`
11. `10-implementation-roadmap.md`
12. `11-examples.md`
13. `12-open-questions-and-kip-backlog.md`

## Non-goals for the first implementation

Kaj 0.x does not need to immediately become:

- a replacement for Python's library ecosystem,
- a native-code optimizing compiler,
- a robotics middleware stack,
- a browser engine,
- a world model,
- an AI model,
- a permission system,
- a database,
- or a universal planner.

The first milestone is a coherent language frontend, AST, type/effect system, generic Task IR, canonical formatter, runnable pure programs, and one useful environmental capability family: Web.

## Central architectural rule

> Kaj defines how programs express computation, goals, effects, evidence, interaction, and verification. Kaj source does not grant itself authority to perform external effects.

Compilation establishes meaning and validity. Host runtimes establish authorization and perform effects.
