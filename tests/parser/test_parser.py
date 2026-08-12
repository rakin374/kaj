from kaj.ast import BindingDeclaration, FunctionDeclaration
from kaj.lexer import Lexer
from kaj.parser import Parser


def test_realistic_program() -> None:
    source = """fn add(a: Int, b: Int) -> Int {
    return a + b
}
let total = add(10, 20)
if total > 20 {
    print(total)
}
"""
    lexer_result = Lexer(source, filename="program.kaj").tokenize()
    result = Parser(lexer_result.tokens, filename="program.kaj").parse()

    assert lexer_result.diagnostics == []
    assert result.diagnostics == ()
    assert len(result.program.statements) == 3
    assert isinstance(result.program.statements[0], FunctionDeclaration)
    assert isinstance(result.program.statements[1], BindingDeclaration)


def test_parser_can_be_reused_without_duplicate_results() -> None:
    tokens = Lexer("let x = 1").tokenize().tokens
    parser = Parser(tokens)

    first = parser.parse()
    second = parser.parse()

    assert first == second


def test_recovery_collects_multiple_parser_errors() -> None:
    source = """let = 10
let y = 20
fn add(a Int) -> Int {
    return a
}
let z = 30
"""
    lexer_result = Lexer(source).tokenize()
    result = Parser(lexer_result.tokens).parse()

    assert len(result.diagnostics) >= 2
    assert any(
        isinstance(statement, BindingDeclaration) and statement.name == "y"
        for statement in result.program.statements
    )
    assert any(
        isinstance(statement, BindingDeclaration) and statement.name == "z"
        for statement in result.program.statements
    )
