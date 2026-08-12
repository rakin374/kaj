# Value Equality and Display

**Status:** Authoritative for structured equality and deterministic display

Kaj supports equality-capable primitives plus `Optional`, `Result`, enums, and newtypes when their payload or underlying types support equality. Tagged values compare tags and payloads. Enums and newtypes require the same nominal declaration. Lists, maps, records, ranges, functions, and modules are not equality-comparable.

`print` and interpolation use deterministic Kaj display, never Python `repr` or host object identity. Direct strings are unquoted; nested strings are quoted and escaped.

```text
[1, 2, 3]
{"Alice": 30, "Bob": 40}
some(10)
err("bad")
Status.ready
Status.blocked(reason: "review")
UserId("abc")
User { id: UserId("u1"), name: "Alice" }
```

Lists and records preserve stored order; maps use insertion order. Decimal display is non-exponential and preserves its exact stored scale. Bytes display as lowercase hexadecimal inside `bytes("...")`.
