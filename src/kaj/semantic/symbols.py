from dataclasses import dataclass
from enum import Enum, auto

from kaj.source import SourceSpan


class SymbolKind(Enum):
    BUILTIN_FUNCTION = auto()
    FUNCTION = auto()
    TASK = auto()
    LET_BINDING = auto()
    VAR_BINDING = auto()
    PARAMETER = auto()
    LOOP_VARIABLE = auto()
    PATTERN_BINDING = auto()
    MODULE = auto()
    CAPABILITY = auto()
    CAPABILITY_ALIAS = auto()


@dataclass(frozen=True)
class Symbol:
    id: int
    name: str
    kind: SymbolKind
    declaration_span: SourceSpan
