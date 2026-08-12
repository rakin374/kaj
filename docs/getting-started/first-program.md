# Your First Kaj Program

This tutorial builds a small typed user directory. Save the final program as `user-directory.kaj`.

## Model identity and state

A newtype prevents an arbitrary string from being used where a user identifier is required:

```kaj
newtype UserId = String

enum UserStatus {
    active
    suspended(reason: String)
}
```

Now define the record:

```kaj
type User {
    id: UserId
    name: String
    status: UserStatus
}
```

## Describe a user

Matching is exhaustive, so both states produce a string:

```kaj
fn describe(user: User) -> String {
    match user.status {
        active => return user.name
        suspended(reason) => return reason
    }
}
```

## Store and retrieve users

```kaj
let users: Map<UserId, User> = {
    UserId("001"): User {
        id: UserId("001"),
        name: "Alice",
        status: UserStatus.active,
    },
}

match users[UserId("001")] {
    some(user) => print(describe(user))
    none => print("User not found")
}
```

Map lookup returns `Optional<User>`, forcing the missing case to be handled. Run it:

```bash
kaj check user-directory.kaj
kaj fmt user-directory.kaj
kaj run user-directory.kaj
```

The output is `Alice`. The complete executable source lives at `examples/user-directory.kaj`.

Learn the pieces in more depth in the [records](../guide/records.md), [maps](../guide/maps.md), [enums and match](../guide/enums-and-match.md), and [newtypes](../guide/newtypes.md) guides.
