# Loop Control and Ranges

**Status:** Authoritative for Kaj pure-language loop control and integer ranges

`break` terminates the nearest enclosing `for` or `while` loop. `continue` skips the rest of the current iteration of the nearest enclosing loop. Neither affects an outer loop, and `return` still exits the containing function.

Using either keyword outside a loop reports `CONTROL_BREAK_OUTSIDE_LOOP` or `CONTROL_CONTINUE_OUTSIDE_LOOP`.

```kaj
for value in range(0, 5) {
    if value == 3 { continue }
    print(value)
}
```

`range(start, end)` accepts exactly two `Int` arguments and produces an internal lazy `Range`. Iteration begins at `start` and excludes `end`. If `start >= end`, iteration is empty. Descending ranges and a step argument are not supported.

`Range` is iterable but is not a public generic type and is not a `List<Int>`. Wrong arity uses normal call diagnostics; non-`Int` bounds report `TYPE_MISMATCH`.
