# Kaj by Example

## Hello and variables

```kaj
print("Hello, Kaj!")
let name = "Alice"
var count = 0
count += 1
```

## Arithmetic and conditions

```kaj
let half = 5 / 2
if half > 2.0 and not false { print(half) }
```

## Loops and functions

```kaj
fn square(value: Int) -> Int { return value * value }
for value in [1, 2, 3] { print(square(value)) }
```

## Recursion

```kaj
fn factorial(n: Int) -> Int {
    if n <= 1 { return 1 }
    return n * factorial(n - 1)
}
```

## Lists and maps

```kaj
let names = ["Alice", "Bob"]
let ages = {"Alice": 30}
print(names.count)
match ages["Bob"] { some(age) => print(age) none => print("missing") }
```

## Records, enums, and matching

```kaj
type User { name: String }
enum State { ready blocked(reason: String) }
let user = User { name: "Alice" }
let state = State.ready
match state { ready => print(user.name) blocked(reason) => print(reason) }
```

## Optional and Result

```kaj
let value: Optional<Int> = some(1)
let result: Result<Int, String> = ok(2)
match value { some(number) => print(number) none => print(0) }
match result { ok(number) => print(number) err(message) => print(message) }
```

## Newtypes

```kaj
newtype UserId = String
let id = UserId("u-1")
print(id.value)
```

## Modules

```kaj
import math
print(math.add(2, 3))
```

All complete examples are available in the repository's `examples/` directory. Start with the [Quickstart](../getting-started/quickstart.md), then use the focused guide pages for detail.
