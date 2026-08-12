from decimal import Decimal

from kaj.runtime import KajMapKey
from kaj.semantic import PrimitiveType


def test_map_acceptance_present_missing_and_count(run_source) -> None:
    result = run_source("""let ages = {"Alice": 30, "Bob": 40}
match ages["Alice"] { some(age) => print(age) none => print("missing") }
match ages["Charlie"] { some(age) => print(age) none => print("missing") }
print(ages.count)
""")
    assert result.execution is not None
    assert result.execution.runtime_error is None
    assert result.execution.output == "30\nmissing\n2\n"


def test_empty_map_and_contextual_numeric_promotions(run_source) -> None:
    result = run_source("""let empty: Map<String, Int> = {}
let values: Map<String, Decimal> = {"a": 1, "b": 2.5}
let keyed: Map<Decimal, String> = {1: "one", 2.5: "two"}
print(empty.count)
match values["a"] { some(value) => print(value) none => print("missing") }
match keyed[1] { some(value) => print(value) none => print("missing") }
""")
    assert result.execution is not None
    assert result.execution.runtime_error is None
    assert result.execution.output == "0\n1\none\n"


def test_duplicate_evaluated_keys_are_a_runtime_error(run_source) -> None:
    result = run_source('let values = {"a": 1, "a": 2}')
    assert result.execution is not None
    assert result.execution.runtime_error is not None
    assert result.execution.runtime_error.code == "RUNTIME_DUPLICATE_MAP_KEY"

    computed = run_source("""fn key(value: String) -> String { return value }
let values = {key("a"): 1, key("a"): 2}
""")
    assert computed.execution is not None
    assert computed.execution.runtime_error is not None
    assert computed.execution.runtime_error.code == "RUNTIME_DUPLICATE_MAP_KEY"


def test_runtime_keys_keep_bool_and_int_identity_distinct() -> None:
    assert KajMapKey(PrimitiveType.BOOL, True) != KajMapKey(PrimitiveType.INT, 1)
    assert len({KajMapKey(PrimitiveType.BOOL, True), KajMapKey(PrimitiveType.INT, 1)}) == 2
    assert KajMapKey(PrimitiveType.DECIMAL, Decimal("1.0")) == KajMapKey(
        PrimitiveType.DECIMAL, Decimal("1.00")
    )
