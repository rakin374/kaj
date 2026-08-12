from kaj.ast import BindingDeclaration
from kaj.lexer import Lexer
from kaj.parser import Parser
from kaj.semantic import NewtypeType, PrimitiveType, Resolver, TypeChecker


def check(source: str):
    lexed = Lexer(source).tokenize()
    parsed = Parser(lexed.tokens).parse()
    assert not lexed.diagnostics and not parsed.diagnostics
    resolved = Resolver(include_builtins=True).resolve(parsed.program)
    checked = TypeChecker(resolved).check(parsed.program)
    return parsed.program, resolved, checked


def codes(source: str) -> list[str]:
    _, resolved, checked = check(source)
    return [item.code for item in (*resolved.diagnostics, *checked.diagnostics)]


def test_nominal_identity_construction_and_explicit_conversion() -> None:
    program, resolution, checked = check(
        'newtype UserId = String newtype OrderId = String let id = UserId("abc")'
    )
    assert not resolution.diagnostics and not checked.diagnostics
    binding = program.statements[2]
    assert isinstance(binding, BindingDeclaration)
    symbol = resolution.symbol_for_declaration(binding)
    assert symbol is not None
    user_id = checked.type_of_symbol(symbol)
    assert isinstance(user_id, NewtypeType)
    assert user_id != PrimitiveType.STRING
    assert codes(
        'newtype UserId = String newtype OrderId = String let user = UserId("x") let order: OrderId = user'
    ) == ["TYPE_MISMATCH"]
    assert codes('newtype UserId = String let id: UserId = "x"') == ["TYPE_MISMATCH"]
    assert codes('newtype UserId = String let raw: String = UserId("x")') == ["TYPE_MISMATCH"]
    assert codes('newtype UserId = String let raw: String = UserId("x").value') == []


def test_constructor_rules_promotion_and_members() -> None:
    assert codes("newtype Price = Decimal let price = Price(10)") == []
    assert codes("newtype UserId = String let id = UserId(1)") == ["TYPE_MISMATCH"]
    assert codes("newtype UserId = String let id = UserId()") == ["TYPE_MISSING_ARGUMENT"]
    assert codes('newtype UserId = String let id = UserId(value: "x")') == [
        "TYPE_UNKNOWN_NAMED_ARGUMENT"
    ]
    assert codes('newtype UserId = String let x = UserId("a").missing') == ["TYPE_UNKNOWN_MEMBER"]


def test_recursive_newtypes_and_shared_type_namespace() -> None:
    assert codes("newtype A = A") == ["TYPE_RECURSIVE_NEWTYPE"]
    assert codes("newtype A = B newtype B = A") == [
        "TYPE_RECURSIVE_NEWTYPE",
        "TYPE_RECURSIVE_NEWTYPE",
    ]
    assert codes("newtype A = B newtype B = String") == []
    assert codes("type UserId { value: String } newtype UserId = String") == [
        "TYPE_DUPLICATE_TYPE_NAME"
    ]


def test_newtypes_integrate_without_inherited_operators() -> None:
    valid = """newtype UserId = String
type User { id: UserId }
enum Event { found(id: UserId) }
fn echo(id: UserId) -> UserId { return id }
let user = User { id: UserId("a") }
let ids = [UserId("a"), UserId("b")]
let maybe: Optional<UserId> = some(UserId("a"))
let result: Result<UserId, String> = ok(UserId("a"))
"""
    assert codes(valid) == []
    assert "TYPE_MISMATCH" in codes("newtype Count = Int let value = Count(1) + Count(2)")
    assert "TYPE_MISMATCH" in codes('newtype UserId = String let ids = [UserId("a"), "b"]')


def test_newtype_map_keys_follow_underlying_eligibility() -> None:
    assert (
        codes('newtype UserId = String let users: Map<UserId, String> = {UserId("a"): "Alice"}')
        == []
    )
    assert codes("newtype BadKey = List<Int> let values: Map<BadKey, String> = {}") == [
        "TYPE_INVALID_MAP_KEY_TYPE"
    ]
