import pytest

from kaj.formatting import format_program

from .conftest import parse, semantic_projection


def assert_round_trip(source: str) -> str:
    original = parse(source)
    formatted = format_program(original)
    reparsed = parse(formatted)
    assert semantic_projection(original) == semantic_projection(reparsed)
    assert format_program(reparsed) == formatted
    assert formatted == formatted.replace("\r\n", "\n")
    assert all(line == line.rstrip() for line in formatted.splitlines())
    assert not formatted or formatted.endswith("\n") and not formatted.endswith("\n\n")
    return formatted


@pytest.mark.parametrize(
    "source",
    [
        "let x=10 var y:Decimal=2.50 y+=x",
        'let s="quote: \\" slash: \\\\ newline: \\n tab: \\t café"',
        "let x=a+b*c let y=(a+b)*c let z=a-(b-c)",
        "let x=a**b**c let y=(a**b)**c let z=-2**2 let q=(-2)**2",
        "let x=not a and b let y=not(a and b) let z=f(x).field[0]",
        "fn add(var a:Int,b:List<Int>)->Int{return a+b[0]}",
        "if a{print(1)}else if b{print(2)}else{print(3)} while a{break} for x in xs{continue}",
        'let xs=[1,2,3] let m={"a":1,"b":2} send("x",priority:2)',
        'type User{name:String age:Int} let u=User{name:"A",age:1}',
        'enum Message{quit text(value:String) move(x:Int,y:Int)} let m=Message.text(value:"x")',
        'match m{quit=>print("q") text(v)=>{print(v)} move(x,y)=>print(x)}',
        'let x: Optional<Int> = some(1) let y: Result<Int, String> = err("bad")',
        'newtype UserId=String let id=UserId("a") print(id.value)',
        'let nested: List<Map<String, Optional<Int> > > = [{"a": some(1)}]',
    ],
)
def test_parse_format_parse_and_idempotence(source: str) -> None:
    assert_round_trip(source)


def test_exact_canonical_output_and_comment_loss() -> None:
    source = """// deliberately discarded
fn add(a:Int,b:Int)->Int{return a+b}
type User{name:String age:Int}
enum Status{pending complete}
newtype UserId=String
"""
    assert (
        format_program(parse(source))
        == """fn add(a: Int, b: Int) -> Int {
    return a + b
}

type User {
    name: String
    age: Int
}

enum Status {
    pending
    complete
}

newtype UserId = String
"""
    )


def test_decimal_string_and_empty_program() -> None:
    assert format_program(parse("")) == ""
    assert format_program(parse("let x=2.500 let y=1.0")) == "let x = 2.5\nlet y = 1.0\n"


def test_long_collections_use_deterministic_multiline_layout() -> None:
    formatted = assert_round_trip(
        'let values=["aaaaaaaaaaaaaaaaaaaaaaaaaaaa","bbbbbbbbbbbbbbbbbbbbbbbbbbbb","cccccccccccccccccccccccccccc"]'
    )
    assert "[\n" in formatted
    assert formatted.count(",\n") == 3
