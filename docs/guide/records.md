# Records

```kaj
type User {
    name: String
    age: Int
}

let user = User { name: "Alice", age: 30 }
print(user.name)
```

A record declaration creates a nominal type. Every field must be supplied exactly once and with a compatible value. Field order in construction does not change the declared layout.

```kaj
type Address { city: String }
type Profile { user: User address: Address }

let profile = Profile {
    user: user,
    address: Address { city: "Montreal" },
}
print(profile.address.city)
```

Records work in functions, lists, maps, and other records. Fields are immutable. You cannot assign `user.name = "Bob"`; a `var` binding may instead be rebound to a complete new record value.

Two record declarations with identical fields remain incompatible because record identity is nominal.

Reference: [record semantics](../language/records.md).
