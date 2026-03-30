"""Tests for codio RAG integration."""
from __future__ import annotations

from pathlib import Path

import pytest

from codio.config import CodioConfig
from codio.models import LibraryCatalogEntry
from codio.rag import CODIO_CATALOG_SOURCE_ID, CODIO_NOTES_SOURCE_ID, owned_codio_sources


def _make_config(tmp_path: Path) -> CodioConfig:
    return CodioConfig(
        catalog_path=tmp_path / ".projio" / "codio" / "catalog.yml",
        profiles_path=tmp_path / ".projio" / "codio" / "profiles.yml",
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


def test_owned_codio_sources_python_glob(tmp_path):
    """Python libraries use **/*.py glob."""
    config = _make_config(tmp_path)
    lib_path = tmp_path / "src" / "mylib"
    lib_path.mkdir(parents=True)
    catalog = {
        "mylib": LibraryCatalogEntry(name="mylib", kind="internal", language="python", path="src/mylib"),
    }
    sources = owned_codio_sources(config, catalog)
    src_source = next(s for s in sources if s["id"] == "codio-src-mylib")
    assert str(src_source["glob"]).endswith("**/*.py")


def test_owned_codio_sources_matlab_glob(tmp_path):
    """MATLAB libraries use **/*.m glob."""
    config = _make_config(tmp_path)
    lib_path = tmp_path / "src" / "toolbox"
    lib_path.mkdir(parents=True)
    catalog = {
        "toolbox": LibraryCatalogEntry(name="toolbox", kind="external_mirror", language="matlab", path="src/toolbox"),
    }
    sources = owned_codio_sources(config, catalog)
    src_source = next(s for s in sources if s["id"] == "codio-src-toolbox")
    assert str(src_source["glob"]).endswith("**/*.m")


def test_owned_codio_sources_unknown_language_glob(tmp_path):
    """Unknown languages fall back to **/* glob."""
    config = _make_config(tmp_path)
    lib_path = tmp_path / "src" / "exotic"
    lib_path.mkdir(parents=True)
    catalog = {
        "exotic": LibraryCatalogEntry(name="exotic", kind="utility", language="fortran", path="src/exotic"),
    }
    sources = owned_codio_sources(config, catalog)
    src_source = next(s for s in sources if s["id"] == "codio-src-exotic")
    assert str(src_source["glob"]).endswith("**/*")


def test_sync_requires_indexio(tmp_path):
    """sync_codio_rag_sources raises ImportError when indexio is missing."""
    config = _make_config(tmp_path)
    from codio.rag import sync_codio_rag_sources
    # indexio is not installed in the test environment, so this should raise
    with pytest.raises(ImportError, match="indexio"):
        sync_codio_rag_sources(tmp_path, config=config)
