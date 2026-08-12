from collections.abc import Callable

from kaj.ast import BinaryExpression, FunctionDeclaration, GenericType, ReturnStatement
from kaj.parser import ParserResult


def test_function_declaration(parse: Callable[[str], ParserResult]) -> None:
    source = "fn add(a: Int, b: Int) -> Int { return a + b }"
    function = parse(source).program.statements[0]

    assert isinstance(function, FunctionDeclaration)
    assert function.name == "add"
    assert [parameter.name for parameter in function.parameters] == ["a", "b"]
    assert all(not parameter.mutable for parameter in function.parameters)
    returned = function.body.statements[0]
    assert isinstance(returned, ReturnStatement)
    assert isinstance(returned.value, BinaryExpression)


def test_mutable_parameter(parse: Callable[[str], ParserResult]) -> None:
    source = "fn normalize(var value: Decimal) -> Decimal { return value }"
    function = parse(source).program.statements[0]

    assert isinstance(function, FunctionDeclaration)
    assert function.parameters[0].mutable is True


def test_nested_generic_parameter_and_return_types(parse: Callable[[str], ParserResult]) -> None:
    source = "fn copy(x: Map<String, List<Int>>) -> Optional<List<Int>> { return none }"
    function = parse(source).program.statements[0]

    assert isinstance(function, FunctionDeclaration)
    assert isinstance(function.parameters[0].type_annotation, GenericType)
    assert isinstance(function.return_type, GenericType)
