from kaj.ast import (
    EnumConstructionExpression,
    EnumDeclaration,
    ExpressionStatement,
    MatchStatement,
)
from kaj.lexer import Lexer
from kaj.parser import Parser


def parse(source: str):
    lexed = Lexer(source).tokenize()
    assert not lexed.diagnostics
    result = Parser(lexed.tokens).parse()
    assert not result.diagnostics
    return result.program


def test_parses_enum_construction_and_match() -> None:
    program = parse("""enum Message { quit text(value: String) move(x: Int, y: Int) }
Message.text(value: "hello")
match Message.quit { quit => print("quit") text(value) => print(value) move(a, b) => print(a) }
""")
    declaration, construction, match = program.statements
    assert isinstance(declaration, EnumDeclaration)
    assert [variant.name for variant in declaration.variants] == ["quit", "text", "move"]
    assert isinstance(construction, ExpressionStatement)
    assert isinstance(construction.expression, EnumConstructionExpression)
    assert construction.expression.arguments is not None
    assert isinstance(match, MatchStatement)
    assert [case.pattern.variant_name for case in match.cases] == ["quit", "text", "move"]
    assert [binding.name for binding in match.cases[2].pattern.bindings] == ["a", "b"]
