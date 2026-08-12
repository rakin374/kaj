import json
from pathlib import Path

import jsonschema

from kaj.lexer import Lexer
from kaj.parser import Parser
from kaj.serialization import ast_from_json_value, ast_to_json_value


def test_newtype_round_trip_and_schema() -> None:
    lexed = Lexer("newtype UserIndex = Map<String, Int>").tokenize()
    parsed = Parser(lexed.tokens).parse()
    assert not lexed.diagnostics and not parsed.diagnostics
    encoded = ast_to_json_value(parsed.program)
    schema = json.loads((Path(__file__).parents[2] / "schemas" / "ast" / "v1.json").read_text())
    jsonschema.validate(encoded, schema)
    assert ast_from_json_value(json.loads(json.dumps(encoded))) == parsed.program
