from dataclasses import FrozenInstanceError

import pytest

from kaj.source import SourceLocation, SourceSpan


def test_source_location_uses_zero_based_offset_and_one_based_line_column() -> None:
    location = SourceLocation(offset=0, line=1, column=1)

    assert location.offset == 0
    assert location.line == 1
    assert location.column == 1


def test_source_span_is_an_immutable_value() -> None:
    start = SourceLocation(0, 1, 1)
    span = SourceSpan(start, SourceLocation(3, 1, 4))

    assert span.start == start
    assert span.end.offset == 3
    with pytest.raises(FrozenInstanceError):
        span.start = SourceLocation(1, 1, 2)  # type: ignore[misc]
