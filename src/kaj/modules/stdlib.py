from __future__ import annotations

from pathlib import Path

from kaj.modules.names import ModuleName

STDLIB_ROOT_NAME = "std"


def stdlib_root() -> Path:
    package_root = Path(__file__).resolve().parents[2]
    repo_std = package_root.parent / STDLIB_ROOT_NAME
    if repo_std.is_dir():
        return repo_std
    bundled = Path(__file__).resolve().parent / "bundled_std"
    return bundled


def resolve_stdlib_module(name: ModuleName) -> Path | None:
    if not name.parts or name.parts[0] != STDLIB_ROOT_NAME:
        return None
    relative = Path(*name.parts[1:-1], name.parts[-1] + ".kaj")
    candidate = (stdlib_root() / relative).resolve()
    try:
        candidate.relative_to(stdlib_root().resolve())
    except ValueError:
        return None
    return candidate if candidate.is_file() else None
