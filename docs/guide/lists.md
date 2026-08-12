# Lists

```kaj
let values = [10, 20, 30]
print(values[0])
print(values.count)
```

Safe edge access returns `Optional<T>`:

```kaj
match values.first { some(value) => print(value) none => print("empty") }
match values.last { some(value) => print(value) none => print("empty") }
```

A list is homogeneous and uses zero-based indexing. Negative or out-of-range indices report `RUNTIME_INDEX_OUT_OF_BOUNDS`.

An empty list needs context:

```kaj
let empty: List<String> = []
let matrix: List<List<Int>> = [[1, 2], [3, 4]]
let prices: List<Decimal> = [1, 2.5]
```

Context may promote `Int` elements to `Decimal`. Lists are immutable values: there is no append, element assignment, or concatenation operation in Kaj v0. A `var` list binding may be rebound to another compatible list.

```kaj
for value in values {
    print(value)
}
```

Reference: [list semantics](../language/lists.md).
