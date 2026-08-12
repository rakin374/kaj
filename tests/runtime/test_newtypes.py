def test_newtype_acceptance_and_nested_unwrap(run_source) -> None:
    result = run_source("""newtype UserId = String
newtype ExternalUserId = UserId
let id = ExternalUserId(UserId("abc"))
print(id.value.value)
""")
    assert result.execution is not None
    assert result.execution.runtime_error is None
    assert result.execution.output == "abc\n"


def test_newtype_decimal_promotion_and_map_key_lookup(run_source) -> None:
    result = run_source("""newtype Price = Decimal
newtype UserId = String
let price = Price(10)
print(price.value)
let users: Map<UserId, String> = {UserId("a"): "Alice"}
match users[UserId("a")] { some(name) => print(name) none => print("missing") }
match users[UserId("b")] { some(name) => print(name) none => print("missing") }
""")
    assert result.execution is not None
    assert result.execution.runtime_error is None
    assert result.execution.output == "10\nAlice\nmissing\n"
