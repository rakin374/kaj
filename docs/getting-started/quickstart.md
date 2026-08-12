# Kaj Quickstart

Create `hello.kaj`:

```kaj
print("Hello, Kaj!")
```

Run it with `kaj run hello.kaj`. Use `kaj check`, `kaj fmt`, and `kaj ast` to check, format, or inspect its syntax tree.

## Values and bindings

```kaj
let name = "Alice"
let ready = true
let price: Decimal = 10
var count = 1
count += 1
```

`let` is immutable; `var` may be rebound. Kaj has `Bool`, `Int`, `Decimal`, `String`, `Bytes`, and `None`. There is no source-level bytes literal yet. Integer division produces a decimal: `5 / 2` is `2.5`.

## Control flow and functions

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}

if ready {
    print(add(2, 3))
} else {
    print(0)
}

while count < 3 {
    print(count)
    count += 1
}

for value in [1, 2, 3] {
    print(value)
}
```

Conditions must be `Bool`; Kaj has no implicit truthiness.

## Lists and maps

```kaj
let values = [1, 2, 3]
print(values[0])
print(values.count)

let ages = {"Alice": 30, "Bob": 40}
match ages["Alice"] {
    some(age) => print(age)
    none => print("missing")
}
```

Lists are homogeneous and zero-indexed. Map lookup returns `Optional<V>`, never a raw missing-key exception.

## Records and enums

```kaj
type User {
    name: String
    age: Int
}

enum Status {
    pending
    complete
}

let user = User { name: "Alice", age: 30 }
let status = Status.pending
print(user.name)

match status {
    pending => print("pending")
    complete => print("complete")
}
```

Records and enums are nominal. Record fields are immutable and enum matches must be exhaustive.

## Optional, Result, and newtypes

```kaj
newtype UserId = String

fn load() -> Result<Int, String> {
    return ok(10)
}

let id = UserId("user-123")
let maybe_name: Optional<String> = some("Alice")
print(id.value)

match load() {
    ok(value) => print(value)
    err(message) => print(message)
}
```

`UserId` is distinct from `String`. `Optional` uses `some`/`none`; `Result` uses `ok`/`err`. The `?` propagation operator is not implemented.

## Local modules

`math.kaj`:

```kaj
fn add(a: Int, b: Int) -> Int { return a + b }
```

`main.kaj`:

```kaj
import math
print(math.add(2, 3))
```

Run `kaj run main.kaj`. Imports are local to the entry file's project directory. Continue with [Your first program](first-program.md) or the [Guide](../guide/index.md).
