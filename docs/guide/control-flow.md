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

`break` terminates the nearest loop and `continue` skips to its next iteration. Both work in `for` and `while`; using either outside a loop is a compile error.

```kaj
for value in range(0, 10) {
    if value == 2 { continue }
    if value == 5 { break }
    print(value)
}
```

Ranges are ascending and end-exclusive. If the start is at least the end, the range is empty.

References: [functions](../language/functions.md), [lists](../language/lists.md), [enums and match](../language/enums-and-match.md), and the [interpreter contract](../internals/interpreter.md).
