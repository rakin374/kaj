# Strings, Interpolation, and Conversion

**Status:** Authoritative for Kaj pure-language interpolation and explicit text/bytes conversion

Ordinary strings may contain Kaj expressions in braces:

```kaj
let name = "Alice"
let count = 2
print("{name} has {count + 1} items")
```

Expressions are evaluated left to right and rendered with Kaj display rules. Functions and module namespaces are not displayable interpolation values and report `TYPE_INTERPOLATION_NOT_DISPLAYABLE`. Literal braces are doubled: `"{{ready}}"`. Malformed interpolation reports `PARSE_INVALID_INTERPOLATION`.

`String(value)` explicitly converts `Bool`, `Int`, `Decimal`, or `String`. Kaj does not add arbitrary implicit string coercion.

```kaj
let encoded: Bytes = utf8_encode("café")
let decoded: Result<String, String> = utf8_decode(encoded)
```

`utf8_encode(String) -> Bytes` uses UTF-8. `utf8_decode(Bytes) -> Result<String, String>` returns `ok(text)` or `err(message)` and never silently repairs invalid bytes. Kaj v0 has no bytes literal.
