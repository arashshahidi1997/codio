"""Indexio RAG source registration for codio."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from codio.config import CodioConfig, load_config

CODIO_NOTES_SOURCE_ID = "codio-notes"
CODIO_CATALOG_SOURCE_ID = "codio-catalog"
CODIO_OWNED_SOURCE_IDS = (CODIO_NOTES_SOURCE_ID, CODIO_CATALOG_SOURCE_ID)


@dataclass(frozen=True)
class CodioRagSyncResult:
    config_path: Path
    created: bool
    initialized: bool
    added: tuple[str, ...]
    updated: tuple[str, ...]
    removed: tuple[str, ...]


def owned_codio_sources(config: CodioConfig) -> list[dict[str, object]]:
    """Return the list of codio-owned source definitions for indexio."""
    return [
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


def sync_codio_rag_sources(
    project_root: Path,
    config: CodioConfig | None = None,
    *,
    config_path: Path | None = None,
    force_init: bool = False,
) -> CodioRagSyncResult:
    """Register codio-owned sources in the project's indexio config.

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
        owned_source_ids=list(CODIO_OWNED_SOURCE_IDS),
        sources=owned_codio_sources(config),
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
