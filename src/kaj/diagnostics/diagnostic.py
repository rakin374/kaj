from dataclasses import dataclass

from kaj.source import SourceSpan


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    span: SourceSpan
