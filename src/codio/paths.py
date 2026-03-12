from __future__ import annotations

from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    """Walk up from *start* looking for a codio or projio project root.

    Detection order:
    1. ``.codio/catalog.yml`` — strongest signal
    2. ``.projio/config.yml`` — projio-managed project
    3. ``.git`` or ``pyproject.toml`` — generic project root
    4. Fallback to the resolved *start* directory
    """
    if start is None:
        start = Path.cwd()
    start = start.expanduser().resolve()

    current = start if start.is_dir() else start.parent
    while True:
        if (current / ".codio" / "catalog.yml").exists():
            return current
        if (current / ".projio" / "config.yml").exists():
            return current
        if (current / ".git").exists() or (current / "pyproject.toml").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    return start
