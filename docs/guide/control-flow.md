# Control Flow

## Conditions

```kaj
if ready {
    print("ready")
} else if retrying {
    print("retrying")
} else {
    print("stopped")
}
```

Every condition must be `Bool`.

## Loops

```kaj
var count = 0
while count < 3 {
    print(count)
    count += 1
}

for value in [1, 2, 3] {
    print(value)
}
```

`for` iterates lists in order. Its loop binding is immutable and scoped to the loop body.

## Match and return

`match` selects an enum, `Optional`, or `Result` branch; see [Enums and match](enums-and-match.md). `return` exits the current function and may appear inside nested blocks.

`break` and `continue` are recognized by the parser, but Kaj v0's reference runtime does not execute them yet. Executing either reports `RUNTIME_INVALID_OPERATION`; do not use them in runnable programs.

References: [functions](../language/functions.md), [lists](../language/lists.md), [enums and match](../language/enums-and-match.md), and the [interpreter contract](../internals/interpreter.md).
