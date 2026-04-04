"""Indexio RAG source registration for codio."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from codio.config import CodioConfig, load_config

CODIO_NOTES_SOURCE_ID = "codio-notes"
CODIO_CATALOG_SOURCE_ID = "codio-catalog"
CODIO_SRC_PREFIX = "codio-src-"

# Maps catalog ``language`` field values to source-tree glob patterns.
# Languages not in this mapping fall back to ``**/*`` (all files).
_LANGUAGE_GLOB: dict[str, str] = {
    "python": "**/*.py",
    "matlab": "**/*.m",
    "r": "**/*.R",
    "julia": "**/*.jl",
    "javascript": "**/*.js",
    "typescript": "**/*.ts",
    "c": "**/*.c",
    "cpp": "**/*.cpp",
    "java": "**/*.java",
}
_DEFAULT_SOURCE_GLOB = "**/*"


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


def _load_repos(config: CodioConfig) -> dict[str, dict]:
    """Load repos.yml and return repo_id -> repo_info mapping."""
    if not config.repos_path.exists():
        return {}
    import yaml
    with open(config.repos_path) as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        return {}
    return data.get("repositories") or {}


# For notebook/doc-heavy repos, use a broad glob.
_NOTEBOOK_GLOB = "**/*.{py,ipynb,md}"


def owned_codio_sources(
    config: CodioConfig,
    catalog: dict | None = None,
) -> list[dict[str, object]]:
    """Return the list of codio-owned source definitions for indexio.

    When *catalog* is provided (dict of name -> LibraryCatalogEntry),
    source trees for libraries with non-empty ``path`` fields are included.
    The glob pattern for each source tree is derived from the library's
    ``language`` field (e.g. ``**/*.py`` for Python, ``**/*.m`` for MATLAB).
    Libraries with unknown or missing languages fall back to ``**/*``.

    Cloned mirrors (from repos.yml) are also registered when their
    ``local_path`` exists on disk, even if the catalog entry has no ``path``.
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

    # Build repo_id -> local_path lookup from repos.yml
    repos = _load_repos(config)
    repo_id_to_path: dict[str, Path] = {}
    for repo_id, info in repos.items():
        lp = info.get("local_path")
        if lp:
            full = config.project_root / lp
            if full.exists():
                repo_id_to_path[repo_id] = full

    registered_names: set[str] = set()

    if catalog:
        for name, entry in catalog.items():
            lang = (getattr(entry, "language", "") or "").lower()
            glob_pat = _LANGUAGE_GLOB.get(lang, _DEFAULT_SOURCE_GLOB)

            # Prefer explicit path from catalog
            if entry.path:
                lib_path = config.project_root / entry.path
                if not lib_path.exists():
                    continue
                sources.append({
                    "id": _source_id_for_library(name),
                    "corpus": "codelib",
                    "glob": str(lib_path / glob_pat),
                    "metadata": {"library": name, "kind": entry.kind},
                })
                registered_names.add(name)
                continue

            # Fall back to cloned mirror via repo_id
            repo_id = getattr(entry, "repo_id", None) or ""
            if repo_id and repo_id in repo_id_to_path:
                mirror_path = repo_id_to_path[repo_id]
                # Notebook-heavy repos get a broader glob
                if lang in ("jupyter notebook", ""):
                    glob_pat = _NOTEBOOK_GLOB
                sources.append({
                    "id": _source_id_for_library(name),
                    "corpus": "codelib",
                    "glob": str(mirror_path / glob_pat),
                    "metadata": {"library": name, "kind": entry.kind},
                })
                registered_names.add(name)

    return sources


def owned_source_ids(catalog: dict | None = None, config: CodioConfig | None = None) -> list[str]:
    """Return all codio-owned source IDs (for sync_owned_sources)."""
    ids = [CODIO_NOTES_SOURCE_ID, CODIO_CATALOG_SOURCE_ID]
    if catalog:
        repos = _load_repos(config) if config else {}
        for name, entry in catalog.items():
            if entry.path:
                ids.append(_source_id_for_library(name))
            elif getattr(entry, "repo_id", None) and (getattr(entry, "repo_id", "") in repos):
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
    Source-tree glob patterns are language-dependent (see
    :func:`owned_codio_sources`).

    *config_path* should point to the same indexio config used by
    ``indexio_build`` and ``rag_query`` — typically the path declared under
    ``indexio.config`` in ``.projio/config.yml``.  Callers (including the
    MCP tool) are responsible for resolving this path from the projio
    project config rather than relying on the built-in default.  The
    default fallback (``infra/indexio/config.yaml``) exists only for
    backwards compatibility and may not match the project's actual config
    location.

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
        owned_source_ids=owned_source_ids(catalog, config),
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
