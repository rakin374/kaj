def test_unit_enum_match(run_source) -> None:
    result = run_source("""enum Status { pending complete }
let status = Status.pending
match status { pending => print("pending") complete => print("complete") }
""")
    assert result.execution is not None
    assert result.execution.output == "pending\n"


def test_payload_binding_uses_declaration_order(run_source) -> None:
    result = run_source("""enum Pair { pair(left: String, right: String) }
let pair = Pair.pair(right: "right", left: "left")
match pair { pair(a, b) => { print(a) print(b) } }
""")
    assert result.execution is not None
    assert result.execution.output == "left\nright\n"
