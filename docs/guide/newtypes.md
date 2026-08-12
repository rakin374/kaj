# Newtypes

```kaj
newtype UserId = String
newtype OrderId = String

let user_id = UserId("u-1")
let order_id = OrderId("o-1")
print(user_id.value)
```

A newtype is a nominal wrapper. `UserId`, `OrderId`, and `String` are three incompatible types even though both wrappers use `String` underneath.

Construction is explicit and takes one compatible value. `.value` explicitly unwraps one layer. Kaj does not implicitly wrap or unwrap newtypes, and operators of the underlying type are not inherited.

Newtypes make boundaries precise:

```kaj
fn find_user(id: UserId) -> Optional<String> {
    return some(id.value)
}

type Order { owner: UserId }
let scores: Map<UserId, Int> = {UserId("u-1"): 10}
```

Recursive newtype cycles are rejected.

Reference: [newtype semantics](../language/newtypes.md).
