from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Iterator, Tuple

try:  # Python >= 3.11
    from importlib.resources.abc import Traversable
except Exception:  # pragma: no cover
    Traversable = Any

from codio.config import DEFAULT_NOTES_DIR

TEMPLATE_PACKAGE = "codio"
TEMPLATE_ROOT = Path("templates/codio")


@dataclass(frozen=True)
class ScaffoldResult:
    root: Path
    files_written: tuple[Path, ...]


def _template_dir() -> Traversable:
    return resources.files(TEMPLATE_PACKAGE).joinpath(str(TEMPLATE_ROOT))


def _iter_template_files(root: Traversable) -> Iterator[Tuple[Path, Traversable]]:
    def _recurse(node: Traversable, rel: Path) -> Iterator[Tuple[Path, Traversable]]:
        for child in node.iterdir():
            child_rel = rel / child.name
            if child.is_dir():
                yield from _recurse(child, child_rel)
            else:
                yield child_rel, child

    return _recurse(root, Path())


def init_codio_scaffold(
    project_root: str | Path,
    *,
    target_dir: str | Path | None = None,
    force: bool = False,
) -> ScaffoldResult:
    """Scaffold codio registry files with starter YAML templates.

    *target_dir* overrides the default ``.codio/`` location.  When called
    from ``projio add codio``, this is typically ``.projio/codio/``.
    """
    project_root = Path(project_root).expanduser().resolve()
    codio_dir = Path(target_dir) if target_dir is not None else project_root / ".codio"
    if not codio_dir.is_absolute():
        codio_dir = project_root / codio_dir

    tpl_root = _template_dir()
    if not tpl_root.is_dir():
        raise FileNotFoundError(
            f"Missing template dir in package: {TEMPLATE_PACKAGE}/{TEMPLATE_ROOT}"
        )

    files_written: list[Path] = []
    for rel, entry in _iter_template_files(tpl_root):
        if rel.name.endswith(".tmpl"):
            rel = rel.with_suffix("")
        dest = codio_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and not force:
            continue
        data = entry.read_bytes()
        dest.write_bytes(data)
        files_written.append(dest)

    # Ensure dir exists even if everything already present.
    codio_dir.mkdir(parents=True, exist_ok=True)
    # Also create the notes directory.
    (project_root / DEFAULT_NOTES_DIR).mkdir(parents=True, exist_ok=True)

    return ScaffoldResult(root=project_root, files_written=tuple(files_written))
