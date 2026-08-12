# Operators

```kaj
let total = 2 + 3 * 4
let power = 2 ** 3
let quotient = 5 / 2
let ready = total >= 10 and not false
```

`5 / 2` has type `Decimal` and value `2.5`. Kaj promotes `Int` to `Decimal` where the numeric rules allow it.

## Precedence, highest first

| Level | Operators | Association |
|---|---|---|
| Power | `**` | right |
| Unary | `+`, `-`, `not` | prefix |
| Multiplicative | `*`, `/`, `%` | left |
| Additive | `+`, `-` | left |
| Comparison | `==`, `!=`, `<`, `<=`, `>`, `>=` | left |
| Boolean AND | `and` | left |
| Boolean OR | `or` | left |

Parentheses make grouping explicit. `and` and `or` short-circuit. Conditions and Boolean operators require `Bool`; values such as `0`, empty strings, and empty lists do not become false implicitly.

Reference: [primitive types and operators](../language/primitive-types.md).
