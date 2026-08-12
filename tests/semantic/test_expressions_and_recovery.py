from collections.abc import Callable

from kaj.semantic import ResolutionResult


def test_member_and_named_argument_labels_are_not_resolved(
    resolve_source: Callable[[str], ResolutionResult],
) -> None:
    result = resolve_source(
        "let user = 1\nlet send = 2\nlet message = 3\nlet value = 4\n"
        "user.name\nsend(message, priority: value)"
    )

    assert result.diagnostics == ()
    assert [reference.identifier.name for reference in result.references] == [
        "user",
        "send",
        "message",
        "value",
    ]


def test_assignment_and_collection_expressions_are_walked(
    resolve_source: Callable[[str], ResolutionResult],
) -> None:
    result = resolve_source(
        "let object = [0]\nlet index = 0\nlet value = 1\nobject[index] = {index: [value]}"
    )

    assert result.diagnostics == ()
    assert [reference.identifier.name for reference in result.references] == [
        "object",
        "index",
        "index",
        "value",
    ]


def test_initializer_resolves_before_declaration(
    resolve_source: Callable[[str], ResolutionResult],
) -> None:
    result = resolve_source("let x = x")

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["RESOLVE_UNKNOWN_NAME"]


def test_multiple_errors_are_deterministic_and_duplicate_keeps_original(
    resolve_source: Callable[[str], ResolutionResult],
) -> None:
    result = resolve_source("let x = missing_a\nlet x = missing_b\nx")

    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "RESOLVE_UNKNOWN_NAME",
        "RESOLVE_UNKNOWN_NAME",
        "RESOLVE_DUPLICATE_NAME",
    ]
    assert result.references[0].symbol is result.module_scope.lookup_local("x")
