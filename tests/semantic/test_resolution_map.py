from collections.abc import Callable

from kaj.ast import ExpressionStatement, Identifier, Program
from kaj.semantic import Resolver
from kaj.serialization import ast_from_json, ast_to_json


def test_symbol_for_uses_identifier_node_identity(parse_program: Callable[[str], Program]) -> None:
    program = parse_program("let x = 1\nx")
    statement = program.statements[1]
    assert isinstance(statement, ExpressionStatement)
    identifier = statement.expression
    assert isinstance(identifier, Identifier)
    result = Resolver().resolve(program)

    assert result.symbol_for(identifier) is result.module_scope.lookup_local("x")
    equal_but_distinct = Identifier(span=identifier.span, name=identifier.name)
    assert equal_but_distinct == identifier
    assert result.symbol_for(equal_but_distinct) is None


def test_ast_json_round_trip_has_equivalent_resolution(
    parse_program: Callable[[str], Program],
) -> None:
    program = parse_program("let x = 1\nfn f(a: Int) -> Int { return x + a }")
    restored = ast_from_json(ast_to_json(program))

    original_result = Resolver().resolve(program)
    restored_result = Resolver().resolve(restored)

    assert [symbol.name for symbol in original_result.symbols] == [
        symbol.name for symbol in restored_result.symbols
    ]
    assert [reference.symbol.id for reference in original_result.references] == [
        reference.symbol.id for reference in restored_result.references
    ]
    assert original_result.diagnostics == restored_result.diagnostics
