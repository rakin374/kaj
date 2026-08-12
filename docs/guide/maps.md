# Maps

Map lookup is safe and explicit:

```kaj
let ages = {"Alice": 30, "Bob": 40}

match ages["Alice"] {
    some(age) => print(age)
    none => print("missing")
}
```

For `Map<K, V>`, lookup has type `Optional<V>`. A missing key produces `none`, not a host-language exception.

```kaj
let empty: Map<String, Int> = {}
let prices: Map<String, Decimal> = {"one": 1, "two": 2.5}
print(prices.count)
```

Supported key types are `Bool`, `Int`, `Decimal`, `String`, `Bytes`, and newtypes whose underlying type ultimately resolves to one of those. Map literals evaluate in source order; duplicate evaluated keys are a runtime error.

Maps are immutable but iterable in insertion order:

```kaj
for entry in ages {
    print("{entry.key}: {entry.value}")
}
```

Reference: [map semantics](../language/maps.md).
