# Enums and Match

Enums define a closed set of variants:

```kaj
enum Message {
    quit
    text(value: String)
    move(x: Int, y: Int)
}

let message = Message.text(value: "hello")
```

Unit variants have no payload. Payload variants use named constructor arguments.

```kaj
match message {
    quit => print("quit")
    text(value) => print(value)
    move(x, y) => print(x + y)
}
```

Pattern bindings exist only inside their branch. The number of bindings must match the variant payload declaration.

Matches must be exhaustive. Omitting a variant reports `NON_EXHAUSTIVE_MATCH`. An exhaustive match whose branches all return can satisfy a function's definite-return requirement.

Only the selected branch executes, and the matched expression is evaluated once.

Reference: [enum and match semantics](../language/enums-and-match.md).
