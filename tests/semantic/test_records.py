from collections.abc import Callable

from kaj.semantic import ListType, PrimitiveType, RecordType, TypeCheckResult


def test_record_definition_and_construction(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source(
        'type User { name: String age: Int tags: List<String> }\n'
        'let user = User { tags: ["admin"], age: 30, name: "Alice" }'
    )
    user = result.resolution.module_scope.lookup_local("user")
    assert user is not None
    record_type = result.type_of_symbol(user)
    assert isinstance(record_type, RecordType)
    definition = result.record_definition(record_type)
    assert definition is not None

    assert [field.name for field in definition.fields] == ["name", "age", "tags"]
    assert definition.fields[2].type == ListType(PrimitiveType.STRING)
    assert result.diagnostics == ()


def test_forward_and_recursive_record_types(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source(
        "type User { address: Address }\n"
        "type Address { owner: User city: String }"
    )
    assert result.diagnostics == ()
    assert len(result.records) == 2


def test_duplicate_type_and_declared_fields(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source(
        "type User { name: String name: String }\n"
        "type User { age: Int }"
    )
    assert [item.code for item in result.diagnostics] == [
        "TYPE_DUPLICATE_TYPE_NAME",
        "TYPE_DUPLICATE_FIELD",
    ]


def test_unknown_field_type(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("type User { profile: Missing }")
    assert [item.code for item in result.diagnostics] == ["TYPE_UNKNOWN_TYPE"]


def test_constructor_shape_diagnostics(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source(
        "type User { name: String age: Int }\n"
        'User { name: "A", name: "B", extra: true }'
    )
    assert [item.code for item in result.diagnostics] == [
        "TYPE_DUPLICATE_FIELD",
        "TYPE_UNKNOWN_FIELD",
        "TYPE_MISSING_FIELD",
    ]


def test_constructor_unknown_type_and_wrong_field_type(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source(
        'type User { age: Int }\nUser { age: 1.5 }\nMissing { value: "x" }'
    )
    assert [item.code for item in result.diagnostics] == [
        "TYPE_MISMATCH",
        "TYPE_UNKNOWN_TYPE",
    ]


def test_field_promotion_and_access(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source(
        "type Price { amount: Decimal }\n"
        "let price = Price { amount: 10 }\nlet amount = price.amount"
    )
    amount = result.resolution.module_scope.lookup_local("amount")
    assert amount is not None

    assert result.type_of_symbol(amount) is PrimitiveType.DECIMAL
    assert result.diagnostics == ()


def test_nested_access_and_unknown_field(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source(
        "type Address { city: String }\n"
        "type User { address: Address }\n"
        'let user = User { address: Address { city: "NY" } }\n'
        "let city = user.address.city\nuser.email"
    )
    city = result.resolution.module_scope.lookup_local("city")
    assert city is not None

    assert result.type_of_symbol(city) is PrimitiveType.STRING
    assert [item.code for item in result.diagnostics] == ["TYPE_UNKNOWN_FIELD"]


def test_nominal_assignability_and_list_homogeneity(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source(
        "type User { name: String } type Customer { name: String }\n"
        'let user = User { name: "A" }\n'
        "let customer: Customer = user\n"
        'let mixed = [user, Customer { name: "B" }]'
    )
    assert [item.code for item in result.diagnostics] == [
        "TYPE_MISMATCH",
        "TYPE_MISMATCH",
    ]


def test_record_functions_and_lists(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source(
        "type User { name: String }\n"
        "fn greet(user: User) -> String { return user.name }\n"
        'fn make() -> User { return User { name: "A" } }\n'
        "let users = [make()]\nlet greeting = greet(users[0])"
    )
    assert result.diagnostics == ()


def test_field_assignment_is_rejected(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source(
        'type User { name: String } var user = User { name: "A" } user.name = "B"'
    )
    assert [item.code for item in result.diagnostics] == [
        "TYPE_FIELD_ASSIGNMENT_NOT_SUPPORTED"
    ]
