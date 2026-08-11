from dataclasses import dataclass


@dataclass(frozen=True)
class SourceLocation:
    """A position in source text.

    Offsets are zero-based. Lines and columns are one-based.
    """

    offset: int
    line: int
    column: int


@dataclass(frozen=True)
class SourceSpan:
    """A half-open source range: ``[start, end)``."""

    start: SourceLocation
    end: SourceLocation
