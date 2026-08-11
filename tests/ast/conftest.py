import pytest

from kaj.source import SourceLocation, SourceSpan


@pytest.fixture
def span() -> SourceSpan:
    return SourceSpan(SourceLocation(0, 1, 1), SourceLocation(1, 1, 2))
