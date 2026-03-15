"""Indexio RAG source registration for codio."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from codio.config import CodioConfig, load_config

CODIO_NOTES_SOURCE_ID = "codio-notes"
CODIO_CATALOG_SOURCE_ID = "codio-catalog"
CODIO_SRC_PREFIX = "codio-src-"


@dataclass(frozen=True)
class CodioRagSyncResult:
    config_path: Path
    created: bool
    initialized: bool
    added: tuple[str, ...]
    updated: tuple[str, ...]
    removed: tuple[str, ...]


def _source_id_for_library(name: str) -> str:
    """Return the indexio source ID for a library's source tree."""
    return f"{CODIO_SRC_PREFIX}{name}"


def resolve_source_id(source_id: str) -> str | None:
    """Map an indexio source ID back to a library name, or None."""
    if source_id.startswith(CODIO_SRC_PREFIX):
        return source_id[len(CODIO_SRC_PREFIX):]
    return None


def owned_codio_sources(
    config: CodioConfig,
    catalog: dict | None = None,
) -> list[dict[str, object]]:
    """Return the list of codio-owned source definitions for indexio.

    When *catalog* is provided (dict of name -> LibraryCatalogEntry),
    source trees for libraries with non-empty ``path`` fields are included.
    """
    sources: list[dict[str, object]] = [
        {
            "id": CODIO_NOTES_SOURCE_ID,
            "corpus": "codelib",
            "glob": str(config.notes_dir / "**/*.md"),
        },
        {
            "id": CODIO_CATALOG_SOURCE_ID,
            "corpus": "codelib",
            "path": str(config.catalog_path),
        },
    ]

    if catalog:
        for name, entry in catalog.items():
            if not entry.path:
                continue
            lib_path = config.project_root / entry.path
            if not lib_path.exists():
                continue
            sources.append({
                "id": _source_id_for_library(name),
                "corpus": "codelib",
                "glob": str(lib_path / "**/*.py"),
                "metadata": {"library": name, "kind": entry.kind},
            })

    return sources


def owned_source_ids(catalog: dict | None = None) -> list[str]:
    """Return all codio-owned source IDs (for sync_owned_sources)."""
    ids = [CODIO_NOTES_SOURCE_ID, CODIO_CATALOG_SOURCE_ID]
    if catalog:
        for name, entry in catalog.items():
            if entry.path:
                ids.append(_source_id_for_library(name))
    return ids


def sync_codio_rag_sources(
    project_root: Path,
    config: CodioConfig | None = None,
    *,
    config_path: Path | None = None,
    force_init: bool = False,
    catalog: dict | None = None,
) -> CodioRagSyncResult:
    """Register codio-owned sources in the project's indexio config.

    When *catalog* is provided, source trees for libraries with local
    paths are included alongside the standard notes and catalog sources.

    Raises ``ImportError`` if the indexio package is not installed.
    """
    if config is None:
        config = load_config(project_root)

    try:
        from indexio import sync_owned_sources  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "codio rag sync requires the indexio package. Install with: pip install indexio"
        ) from exc

    # Default indexio config path follows the projio convention.
    if config_path is None:
        config_path = project_root / "infra" / "indexio" / "config.yaml"

    result = sync_owned_sources(
        config_path,
        root=project_root,
        owned_source_ids=owned_source_ids(catalog),
        sources=owned_codio_sources(config, catalog),
        force_init=force_init,
    )

    return CodioRagSyncResult(
        config_path=result.config_path,
        created=result.created,
        initialized=result.initialized,
        added=tuple(result.added),
        updated=tuple(result.updated),
        removed=tuple(result.removed),
    )
