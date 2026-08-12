from dataclasses import dataclass

from kaj.source import SourceSpan


@dataclass(frozen=True)
class RuntimeErrorInfo:
    code: str
    message: str
    span: SourceSpan


class RuntimeFailure(Exception):
    def __init__(self, error: RuntimeErrorInfo) -> None:
        super().__init__(error.message)
        self.error = error
