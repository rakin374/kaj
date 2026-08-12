from collections.abc import Callable

from .conftest import PipelineResult


def output(result: PipelineResult) -> str:
    assert result.execution is not None
    assert result.execution.runtime_error is None
    return result.execution.output


def test_record_acceptance_program(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source(
        "type User { name: String age: Int }\n"
        'let user = User { name: "Alice", age: 30 }\nprint(user.name)'
    )
    assert output(result) == "Alice\n"


def test_independent_and_nested_records(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source(
        "type Address { city: String } type User { name: String address: Address }\n"
        'let a = User { name: "Alice", address: Address { city: "NY" } }\n'
        'let b = User { address: Address { city: "LA" }, name: "Bob" }\n'
        "print(a.name)\nprint(a.address.city)\nprint(b.name)\nprint(b.address.city)"
    )
    assert output(result) == "Alice\nNY\nBob\nLA\n"


def test_record_field_promotion(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source(
        "type Price { amount: Decimal } let price = Price { amount: 5 } "
        "print(price.amount / 2)"
    )
    assert output(result) == "2.5\n"


def test_list_of_records_and_record_function(
    run_source: Callable[[str], PipelineResult],
) -> None:
    result = run_source(
        "type User { name: String }\n"
        "fn name(user: User) -> String { return user.name }\n"
        'let users = [User { name: "A" }, User { name: "B" }]\n'
        "for user in users { print(name(user)) }"
    )
    assert output(result) == "A\nB\n"


def test_var_record_rebinding(run_source: Callable[[str], PipelineResult]) -> None:
    result = run_source(
        'type User { name: String } var user = User { name: "A" } '
        'user = User { name: "B" } print(user.name)'
    )
    assert output(result) == "B\n"


def test_constructor_fields_evaluate_in_source_order(
    run_source: Callable[[str], PipelineResult],
) -> None:
    result = run_source(
        "type Pair { first: None second: None }\n"
        'let pair = Pair { second: print("second-source-first"), '
        'first: print("first-source-second") }'
    )
    assert output(result) == "second-source-first\nfirst-source-second\n"
