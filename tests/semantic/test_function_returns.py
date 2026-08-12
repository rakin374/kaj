from collections.abc import Callable

import pytest

from kaj.semantic import TypeCheckResult


@pytest.mark.parametrize(
    "source",
    [
        "fn f() -> Int { return 1 }",
        "fn f() -> Decimal { return 1 }",
        "fn f() -> None { return }",
        "fn f() -> None { return none }",
        "fn f() -> None {}",
        "fn f(x: Bool) -> Int { if x { return 1 } else { return 2 } }",
        (
            "fn f(x: Int) -> Int { if x == 0 { return 0 } "
            "else if x == 1 { return 1 } else { return 2 } }"
        ),
    ],
)
def test_valid_returns(check_source: Callable[[str], TypeCheckResult], source: str) -> None:
    assert check_source(source).diagnostics == ()


@pytest.mark.parametrize(
    "source",
    [
        'fn f() -> Int { return "bad" }',
        "fn f() -> Int { return 2.5 }",
        "fn f() -> Int { return }",
        "fn f() -> None { return 1 }",
    ],
)
def test_incompatible_returns(check_source: Callable[[str], TypeCheckResult], source: str) -> None:
    result = check_source(source)
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["TYPE_MISMATCH"]


def test_return_outside_function(check_source: Callable[[str], TypeCheckResult]) -> None:
    result = check_source("return 1")
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "TYPE_RETURN_OUTSIDE_FUNCTION"
    ]


@pytest.mark.parametrize(
    "source",
    [
        "fn f() -> Int { let x = 1 }",
        "fn f(x: Bool) -> Int { if x { return 1 } }",
        "fn f(x: Int) -> Int { if x == 0 { return 0 } else if x == 1 { return 1 } }",
        "fn f() -> Int { while true { return 1 } }",
        "fn f() -> Int { for x in items { return 1 } }",
    ],
)
def test_conservative_missing_return(
    check_source: Callable[[str], TypeCheckResult], source: str
) -> None:
    result = check_source(source)
    assert "TYPE_MISSING_RETURN" in [diagnostic.code for diagnostic in result.diagnostics]


def test_later_direct_return_satisfies_function(
    check_source: Callable[[str], TypeCheckResult],
) -> None:
    result = check_source("fn f(x: Bool) -> Int { if x { return 1 } return 2 }")
    assert result.diagnostics == ()
