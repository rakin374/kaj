from dataclasses import fields, is_dataclass
from decimal import Decimal
from enum import Enum

from kaj.ast import Program
from kaj.lexer import Lexer
from kaj.parser import Parser


def parse(source: str) -> Program:
    lexed = Lexer(source).tokenize()
    assert not lexed.diagnostics
    parsed = Parser(lexed.tokens).parse()
    assert not parsed.diagnostics
    return parsed.program


def semantic_projection(value: object) -> object:
    if is_dataclass(value):
        return (
            type(value).__name__,
            tuple(
                (field.name, semantic_projection(getattr(value, field.name)))
                for field in fields(value)
                if field.name != "span"
            ),
        )
    if isinstance(value, tuple):
        return tuple(semantic_projection(item) for item in value)
    if isinstance(value, (str, int, bool, Decimal, type(None), Enum)):
        return value
    raise TypeError(type(value).__name__)
