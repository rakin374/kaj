from kaj.ast import GenericType, NewtypeDeclaration
from kaj.lexer import Lexer
from kaj.parser import Parser


def test_parses_newtype_declarations_and_spans() -> None:
    source = "newtype UserId = String\nnewtype UserIndex = Map<String, UserId>"
    lexed = Lexer(source).tokenize()
    parsed = Parser(lexed.tokens).parse()
    assert not lexed.diagnostics and not parsed.diagnostics
    first, second = parsed.program.statements
    assert isinstance(first, NewtypeDeclaration)
    assert (
        first.name == "UserId"
        and source[first.span.start.offset : first.span.end.offset] == source.splitlines()[0]
    )
    assert isinstance(second, NewtypeDeclaration)
    assert isinstance(second.underlying_type, GenericType)
