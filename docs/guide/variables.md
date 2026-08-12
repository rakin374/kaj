# Variables

```kaj
let name = "Alice"
var visits: Int = 0
visits += 1
```

`let` creates an immutable binding. `var` creates a binding that can be assigned a new value of the same type. An annotation is optional when the initializer determines the type.

```kaj
let price: Decimal = 10
var message = "hello"
message = "welcome"
```

Assigning to `let` reports `ASSIGN_TO_IMMUTABLE`. Compound assignment supports `+=`, `-=`, `*=`, `/=`, `%=`, and `**=` when the corresponding operation is valid.

Bindings belong to lexical scopes. A nested block may shadow an outer name, but the same scope cannot declare it twice.

```kaj
let value = 1
if true {
    let value = 2
    print(value)
}
print(value)
```

Function parameters are immutable unless declared `var`:

```kaj
fn increment(var value: Int) -> Int {
    value += 1
    return value
}
```

Reference: [name resolution](../internals/name-resolution.md) and [primitive types](../language/primitive-types.md).
