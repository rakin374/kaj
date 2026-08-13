# Human Interaction

Human interaction primitives allow an Agentic Kaj task to request information, request a choice, require confirmation, notify a human, or hand control to a human.

This document defines the initial semantics of:

```text
ask
choose
confirm
inform
handoff
```

These constructs operate within the task lifecycle and may suspend task execution while waiting for a human response.

---

## 1. Overview

A task may interact with a human during execution.

Example:

```kaj
task PlanTrip() -> String {
    let city = ask<String>("Where do you want to go?")

    let approved = confirm("Use {city} as the destination?")

    if not approved {
        return "cancelled"
    }

    inform("Destination confirmed")

    return city
}
```

Human interaction is a first-class Agentic Kaj runtime concept.

It is not implemented as ordinary console input/output.

---

## 2. Blocking versus non-blocking interaction

Initial primitives divide into two groups.

Blocking:

```text
ask
choose
confirm
handoff
```

These suspend task execution until the interaction is resolved.

Non-blocking:

```text
inform
```

This records/delivers information to the human but does not suspend the task.

---

## 3. `ask<T>`

`ask<T>` requests a typed value from a human.

Example:

```kaj
let city = ask<String>("Where are you going?")
```

The type parameter defines the required answer type.

Conceptually:

```text
ask<String>(...) -> String
ask<Int>(...)    -> Int
ask<Bool>(...)   -> Bool
```

The task pauses until a valid answer is supplied.

---

## 4. `ask<T>` suspension

When execution reaches:

```kaj
let city = ask<String>("Where are you going?")
```

the task transitions:

```text
running
   ↓
waiting_for_human
```

The runtime creates a pending human interaction record.

Execution does not continue until a response is received.

---

## 5. `ask<T>` response validation

The human response must be converted/validated as a value of `T`.

If the response is invalid for `T`, the task remains waiting.

The runtime reports a structured validation error to the host.

Invalid input does not:

```text
fail the task
resume the task with a malformed value
coerce arbitrarily
```

---

## 6. Supported `ask<T>` types

The initial implementation should support types that can be represented and validated as ordinary serializable Kaj values.

At minimum:

```text
Bool
Int
Decimal
String
Bytes if a practical transport encoding exists
None where meaningful
enums
newtypes
records
Optional
Result
List
Map
```

If the first host transport cannot safely support every type, the runtime may initially restrict accepted interaction types, but the restriction must be explicit and diagnosed statically or at task start.

---

## 7. `choose`

`choose` requests one value from an explicit finite set of choices.

Recommended syntax:

```kaj
let color = choose<String>(
    "Choose a color",
    ["red", "green", "blue"]
)
```

Conceptually:

```text
choose<T>(prompt: String, options: List<T>) -> T
```

The selected value must be one of the supplied options according to Kaj equality semantics.

---

## 8. Empty choice lists

A `choose` call with an empty option list is invalid.

It must fail before entering `waiting_for_human`.

Prefer static detection when the list is statically known to be empty; otherwise use a structured runtime interaction error.

---

## 9. `confirm`

`confirm` requests a yes/no approval.

Example:

```kaj
let approved = confirm("Continue?")
```

Type:

```text
confirm(String) -> Bool
```

The task waits for a human response.

Conceptually:

```text
approve -> true
reject  -> false
```

No implicit third state is introduced.

Cancellation is separate from rejection.

---

## 10. `inform`

`inform` sends information to the human without suspending the task.

Example:

```kaj
inform("Processing started")
```

Type:

```text
inform(String) -> None
```

The runtime records/emits the notification and immediately continues execution.

If delivery infrastructure is unavailable, the runtime should use a structured interaction/runtime failure policy defined by the host integration.

The initial reference runtime may simply record the event.

---

## 11. `handoff`

`handoff` explicitly transfers control to a human.

Example:

```kaj
handoff("Please complete the CAPTCHA in the browser")
```

The task enters:

```text
waiting_for_human
```

until the host reports that the handoff is complete.

The initial return type is:

```text
handoff(String) -> None
```

Once the human completes the handoff, execution resumes after the call.

---

## 12. `handoff` versus `ask`

`ask` requests a typed value.

`handoff` requests human action outside Kaj's typed value system.

Example:

```text
ask:
    "What city?"
    -> typed String

handoff:
    "Please complete the CAPTCHA"
    -> completion signal only
```

---

## 13. Human interaction state

Human interaction adds:

```text
waiting_for_human
```

to the task lifecycle.

Relevant transitions:

```text
running -> waiting_for_human
waiting_for_human -> running
waiting_for_human -> cancelled
waiting_for_human -> failed
```

The exact failure path is used only for interaction/runtime failure, not invalid user input.

---

## 14. Pending interaction identity

Every blocking human interaction has an opaque runtime identity.

Conceptually:

```text
InteractionId
```

A pending interaction record contains at least:

```text
interaction ID
task ID
interaction kind
prompt
expected type
options if choose
current status
```

The exact identifier encoding is host/runtime implementation detail.

---

## 15. One blocking interaction at a time

The initial task model allows at most one active blocking human interaction per task.

This keeps suspension/resume semantics deterministic.

A task cannot create a second blocking interaction while one is already pending.

---

## 16. Interaction statuses

A blocking interaction has a runtime status such as:

```text
pending
answered
completed
cancelled
failed
```

The exact internal state names are implementation-defined, but behavior must remain deterministic.

---

## 17. Invalid responses

Invalid responses do not complete the interaction.

Example:

```kaj
let age = ask<Int>("Age?")
```

Human response:

```text
"abc"
```

The runtime:

```text
keeps interaction pending
reports validation failure
does not resume task
```

A later valid response may satisfy the same interaction.

---

## 18. User cancellation

The host may cancel a pending human interaction.

Initial rule:

```text
cancelling the pending blocking interaction cancels the task
```

This keeps the first model simple.

Later Agentic Kaj may support recoverable interaction cancellation.

---

## 19. Interaction timeout

Timeout behavior is host-controlled and is not required in the initial language semantics.

If a host applies a timeout, the outcome must be represented as either:

```text
task cancellation
or
structured runtime interaction failure
```

The source program does not implicitly choose a timeout.

---

## 20. Interaction prompts

Prompts must evaluate to `String`.

Examples:

```kaj
ask<String>("Name?")
confirm("Continue?")
inform("Done")
handoff("Please finish setup")
```

String interpolation uses ordinary Kaj semantics.

---

## 21. `choose` options

`choose<T>` options are ordinary Kaj values of type `T`.

Example:

```kaj
enum Shipping {
    standard
    express
}

let mode = choose<Shipping>(
    "Shipping method",
    [Shipping.standard, Shipping.express]
)
```

The runtime may render these values using deterministic Kaj display semantics unless the host provides a richer UI mapping.

---

## 22. Purity and interaction

Human interaction primitives are Agentic effects.

They are therefore not permitted inside pure task contract clauses:

```text
goal
require
invariant
success
```

They are also not permitted inside ordinary `fn`.

They may appear only during task execution.

---

## 23. Functions cannot perform human interaction

Invalid:

```kaj
fn get_name() -> String {
    return ask<String>("Name?")
}
```

Human interaction requires task lifecycle state and suspension semantics.

Only tasks may perform these operations.

---

## 24. Steps and interaction

Blocking human interactions may occur inside steps.

Example:

```kaj
step approval {
    let approved = confirm("Proceed?")

    if not approved {
        return err("rejected")
    }
}
```

If the task suspends during the step, the step remains:

```text
running
```

while the task is:

```text
waiting_for_human
```

After a valid response, the task returns to `running` and continues the same step.

---

## 25. Step completion and interactions

A step is not completed merely because an interaction was created.

The step completes only when its body finishes normally.

Conceptually:

```text
step running
task running

confirm(...)
↓
step running
task waiting_for_human

human responds
↓
task running
step still running

step body finishes
↓
step completed
```

---

## 26. Pause and human waiting

A task already in:

```text
waiting_for_human
```

does not separately transition to `paused`.

The host may still cancel it.

Explicit pause semantics apply to executable task progress, not unresolved human interactions.

---

## 27. Resume

A valid human response resumes execution at the exact interaction suspension point.

Example:

```kaj
let city = ask<String>("City?")
print(city)
```

After the answer is supplied, `city` is bound to the validated Kaj value and execution continues with:

```kaj
print(city)
```

The interaction call is not re-executed.

---

## 28. Runtime representation

The runtime should represent human interactions explicitly.

Conceptually:

```text
HumanInteraction
    id
    task_id
    kind
    prompt
    expected_type
    options
    status
    response
```

These are runtime entities.

They are not part of source AST JSON beyond the source call expressions themselves.

---

## 29. Host responsibility

The Kaj runtime produces structured interaction requests.

The host application decides how to present them.

Examples:

```text
terminal prompt
mobile sheet
desktop dialog
web form
voice interface
notification
browser overlay
```

Kaj semantics do not depend on a specific UI.

---

## 30. Host response

The host returns a structured response referencing:

```text
task ID
interaction ID
response value or completion signal
```

The runtime validates the response before resuming the task.

---

## 31. Interaction persistence

Human interaction state is serializable and survives process restart. Durable
storage and restore behavior are defined by
[Persistence and Resume](persistence-resume.md).

---

## 32. Diagnostics and runtime errors

Human interaction should distinguish:

```text
invalid response
interaction cancelled
interaction runtime failure
unsupported interaction type
invalid choose options
duplicate response
unknown interaction ID
```

Invalid user input should not be reported as a compiler error.

Static misuse should be diagnosed before runtime where possible.

---

## 33. Summary

The initial human-interaction model freezes:

```text
ask<T>
    typed blocking request
    returns T

choose<T>
    blocking selection
    returns one supplied T

confirm
    blocking approval
    returns Bool

inform
    non-blocking notification
    returns None

handoff
    blocking human action
    returns None after completion

blocking interaction:
    running -> waiting_for_human -> running

one blocking interaction per task
invalid response keeps task waiting
interaction cancellation cancels task
functions cannot perform human interaction
contract clauses cannot perform human interaction
steps may contain interactions
step remains running during wait
no process-restart persistence yet
```
