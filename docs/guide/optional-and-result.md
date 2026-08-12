# Optional and Result

## Optional

`Optional<T>` represents a value that may be absent:

```kaj
let nickname: Optional<String> = some("Ali")
let missing: Optional<String> = none

match nickname {
    some(name) => print(name)
    none => print("missing")
}
```

The literal `none` by itself has primitive type `None`; context such as an annotation, function return, or collection element gives it `Optional<T>` meaning.

## Result

`Result<T, E>` represents success or failure:

```kaj
fn load() -> Result<Int, String> {
    return ok(42)
}

match load() {
    ok(value) => print(value)
    err(message) => print(message)
}
```

`ok` and `err` generally need contextual type information because one type argument is absent from the constructor call. Both `Optional` and `Result` matches are exhaustive and their payload bindings are branch-local.

Kaj v0 has no `?` propagation operator; errors are handled explicitly with `match`.

Reference: [Optional and Result semantics](../language/optional-and-result.md).
