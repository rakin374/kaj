# Types

Kaj checks types before execution.

| Kind | Examples |
|---|---|
| Primitive | `Bool`, `Int`, `Decimal`, `String`, `Bytes`, `None` |
| Container | `List<T>`, `Map<K, V>` |
| Standard tagged | `Optional<T>`, `Result<T, E>` |
| Nominal | records, enums, newtypes |

```kaj
let enabled: Bool = true
let count: Int = 3
let price: Decimal = 3.5
let name: String = "Kaj"
let absent: None = none
```

`Bytes` is a semantic primitive type, but Kaj v0 has no user-facing bytes literal syntax.

```kaj
let names: List<String> = ["Alice", "Bob"]
let ages: Map<String, Int> = {"Alice": 30}
let nickname: Optional<String> = none
let outcome: Result<Int, String> = ok(42)
```

Containers are invariant. Records, enums, and newtypes are nominal: two declarations with the same shape or underlying type remain different types.

References: [primitive types](../language/primitive-types.md), [lists](../language/lists.md), [maps](../language/maps.md), [records](../language/records.md), [enums](../language/enums-and-match.md), and [newtypes](../language/newtypes.md).
