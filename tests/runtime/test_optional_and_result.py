from decimal import Decimal

from kaj.runtime import KajEnumValue
from kaj.semantic import OptionalType, PrimitiveType


def test_optional_some_and_none_match(run_source) -> None:
    some = run_source("""type User { name: String }
let value: Optional<User> = some(User { name: "Alice" })
match value { some(user) => print(user.name) none => print("missing") }
""")
    missing = run_source("""type User { name: String }
let value: Optional<User> = none
match value { some(user) => print(user.name) none => print("missing") }
""")
    assert some.execution is not None and some.execution.output == "Alice\n"
    assert missing.execution is not None and missing.execution.output == "missing\n"


def test_result_variants_and_payload_promotions(run_source) -> None:
    ok = run_source("""let value: Result<Decimal, String> = ok(10)
match value { ok(number) => print(number) err(message) => print(message) }
""")
    err = run_source("""let value: Result<Int, Decimal> = err(2)
match value { ok(number) => print(number) err(error) => print(error) }
""")
    assert ok.execution is not None and ok.execution.output == "10\n"
    assert err.execution is not None and err.execution.output == "2\n"


def test_runtime_representation_distinguishes_optional_none() -> None:
    optional_none = KajEnumValue(OptionalType(PrimitiveType.INT), "none", ())
    assert optional_none is not None
    promoted = KajEnumValue(OptionalType(PrimitiveType.DECIMAL), "some", (Decimal(1),))
    assert promoted.payload == (Decimal(1),)
