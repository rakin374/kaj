# Functions

```kaj
fn add(a: Int, b: Int) -> Int {
    return a + b
}

print(add(2, b: 3))
```

Parameters and the return type are explicit. Calls may use positional arguments followed by named arguments. A parameter is immutable unless prefixed with `var`.

Functions are visible throughout their module, so forward references, self recursion, and mutual recursion work.

```kaj
fn factorial(n: Int) -> Int {
    if n <= 1 {
        return 1
    }
    return n * factorial(n - 1)
}

print(factorial(5))
```

A non-`None` function must return on every statically complete path. A function returning `None` may fall through or use bare `return`.

Reference: [function semantics](../language/functions.md).
