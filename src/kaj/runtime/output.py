from __future__ import annotations

import sys
from typing import Protocol, TextIO


class RuntimeOutput(Protocol):
    def write_line(self, text: str) -> None: ...


class StreamOutput:
    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = sys.stdout if stream is None else stream

    def write_line(self, text: str) -> None:
        self._stream.write(text + "\n")


class BufferOutput:
    def __init__(self) -> None:
        self._lines: list[str] = []

    def write_line(self, text: str) -> None:
        self._lines.append(text)

    @property
    def text(self) -> str:
        return "".join(line + "\n" for line in self._lines)
