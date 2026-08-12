from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModuleName:
    parts: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.parts or any(not part.isidentifier() for part in self.parts):
            raise ValueError("Module names require identifier segments.")

    @property
    def dotted(self) -> str:
        return ".".join(self.parts)

    def relative_path(self) -> Path:
        return Path(*self.parts[:-1], self.parts[-1] + ".kaj")
