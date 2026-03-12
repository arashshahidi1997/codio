"""Tests for codio RAG integration."""
from __future__ import annotations

from pathlib import Path

import pytest

from codio.config import CodioConfig
from codio.rag import CODIO_CATALOG_SOURCE_ID, CODIO_NOTES_SOURCE_ID, owned_codio_sources


def _make_config(tmp_path: Path) -> CodioConfig:
    return CodioConfig(
        catalog_path=tmp_path / ".codio" / "catalog.yml",
        profiles_path=tmp_path / ".codio" / "profiles.yml",
        notes_dir=tmp_path / "docs" / "reference" / "codelib" / "libraries",
        project_root=tmp_path,
    )


def test_owned_codio_sources_structure(tmp_path):
    config = _make_config(tmp_path)
    sources = owned_codio_sources(config)
    assert len(sources) == 2

    notes_src = sources[0]
    assert notes_src["id"] == CODIO_NOTES_SOURCE_ID
    assert notes_src["corpus"] == "codelib"
    assert "**/*.md" in str(notes_src["glob"])

    catalog_src = sources[1]
    assert catalog_src["id"] == CODIO_CATALOG_SOURCE_ID
    assert catalog_src["corpus"] == "codelib"
    assert "catalog.yml" in str(catalog_src["path"])


def test_owned_codio_sources_ids_unique(tmp_path):
    config = _make_config(tmp_path)
    sources = owned_codio_sources(config)
    ids = [s["id"] for s in sources]
    assert len(ids) == len(set(ids))


def test_sync_requires_indexio(tmp_path):
    """sync_codio_rag_sources raises ImportError when indexio is missing."""
    config = _make_config(tmp_path)
    from codio.rag import sync_codio_rag_sources
    # indexio is not installed in the test environment, so this should raise
    with pytest.raises(ImportError, match="indexio"):
        sync_codio_rag_sources(tmp_path, config=config)
