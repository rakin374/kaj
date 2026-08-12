from dataclasses import dataclass
from enum import Enum, auto

from kaj.source import SourceSpan


class SymbolKind(Enum):
    FUNCTION = auto()
    LET_BINDING = auto()
    VAR_BINDING = auto()
    PARAMETER = auto()
    LOOP_VARIABLE = auto()


@dataclass(frozen=True)
class Symbol:
    id: int
    name: str
    kind: SymbolKind
    declaration_span: SourceSpan
