"""Tests for M7 features: entity model, repos, ingestion, expanded RAG."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from codio.config import CodioConfig, load_config
from codio.models import (
    CodeSourceEntry,
    LibraryCatalogEntry,
    LibraryRecord,
    RepositoryEntry,
    RegistrySnapshot,
)
from codio.registry import Registry, load_repos, save_repos
from codio.vocab import AddedBy, Hosting, Kind, SourceType, Storage, get_vocab


# ---------------------------------------------------------------------------
# New vocab enums
# ---------------------------------------------------------------------------


def test_storage_enum():
    assert Storage.managed == "managed"
    assert Storage.attached == "attached"
    assert Storage.external == "external"
    assert Storage.managed.description


def test_hosting_enum():
    assert Hosting.github == "github"
    assert Hosting.local == "local"


def test_source_type_enum():
    assert SourceType.package == "package"
    assert SourceType.tree == "tree"


def test_added_by_enum():
    assert AddedBy.manual == "manual"
    assert AddedBy.discovery == "discovery"
    assert AddedBy.import_ == "import"


def test_new_vocabs_in_get_vocab():
    vocab = get_vocab()
    assert "storage" in vocab
    assert "hosting" in vocab
    assert "source_type" in vocab
    assert "added_by" in vocab
    assert "managed" in vocab["storage"]["values"]


# ---------------------------------------------------------------------------
# New entity models
# ---------------------------------------------------------------------------


def test_repository_entry():
    repo = RepositoryEntry(
        repo_id="scipy--scipy",
        url="https://github.com/scipy/scipy.git",
        hosting="github",
        storage="managed",
        local_path=".codio/mirrors/scipy--scipy",
        default_branch="main",
    )
    assert repo.repo_id == "scipy--scipy"
    assert repo.storage == "managed"
    assert repo.hosting == "github"


def test_repository_entry_defaults():
    repo = RepositoryEntry(repo_id="local-lib")
    assert repo.url == ""
    assert repo.hosting == "other"
    assert repo.storage == "external"
    assert repo.local_path == ""
    assert repo.default_branch == "main"


def test_code_source_entry():
    src = CodeSourceEntry(
        source_id="scipy-linalg-src",
        repo_id="scipy--scipy",
        subpath="scipy/linalg",
        source_type="package",
        indexable=True,
    )
    assert src.source_id == "scipy-linalg-src"
    assert src.repo_id == "scipy--scipy"
    assert src.source_type == "package"


def test_catalog_entry_new_fields():
    entry = LibraryCatalogEntry(
        name="scipy",
        kind="external_mirror",
        repo_id="scipy--scipy",
        added_by="manual",
        added_date="2026-03-15",
    )
    assert entry.repo_id == "scipy--scipy"
    assert entry.added_by == "manual"
    assert entry.added_date == "2026-03-15"


def test_catalog_entry_new_fields_default():
    entry = LibraryCatalogEntry(name="x", kind="internal")
    assert entry.repo_id == ""
    assert entry.added_by == ""
    assert entry.added_date == ""


def test_library_record_carries_repo_id():
    cat = LibraryCatalogEntry(name="x", kind="internal", repo_id="my--repo")
    rec = LibraryRecord.from_entries(cat)
    assert rec.repo_id == "my--repo"


def test_snapshot_includes_repos():
    cat = LibraryCatalogEntry(name="a", kind="internal")
    repo = RepositoryEntry(repo_id="a--repo")
    snap = RegistrySnapshot(
        libraries={"a": cat},
        profiles={},
        repositories={"a--repo": repo},
    )
    assert "a--repo" in snap.repositories
    assert snap.version == "0.2.0"


# ---------------------------------------------------------------------------
# Config additions
# ---------------------------------------------------------------------------


def test_config_has_repos_path():
    cfg = CodioConfig()
    assert cfg.repos_path == Path(".codio/repos.yml")
    assert cfg.mirrors_dir == Path(".codio/mirrors/")


def test_load_config_repos_overrides(tmp_path):
    projio_dir = tmp_path / ".projio"
    projio_dir.mkdir()
    config_data = {"codio": {"repos_path": "custom/repos.yml"}}
    with open(projio_dir / "config.yml", "w") as f:
        yaml.dump(config_data, f)

    cfg = load_config(tmp_path)
    assert cfg.repos_path == tmp_path / "custom" / "repos.yml"


# ---------------------------------------------------------------------------
# repos.yml loading / saving
# ---------------------------------------------------------------------------


def test_load_repos_missing_file(tmp_path):
    result = load_repos(tmp_path / "nonexistent.yml")
    assert result == {}


def test_load_and_save_repos(tmp_path):
    repos_path = tmp_path / "repos.yml"
    repos = {
        "scipy--scipy": RepositoryEntry(
            repo_id="scipy--scipy",
            url="https://github.com/scipy/scipy.git",
            hosting="github",
            storage="managed",
            local_path=".codio/mirrors/scipy--scipy",
        ),
        "local--utils": RepositoryEntry(
            repo_id="local--utils",
            storage="attached",
            local_path="/home/user/utils",
        ),
    }
    save_repos(repos_path, repos)
    assert repos_path.exists()

    loaded = load_repos(repos_path)
    assert "scipy--scipy" in loaded
    assert loaded["scipy--scipy"].storage == "managed"
    assert "local--utils" in loaded
    assert loaded["local--utils"].storage == "attached"


# ---------------------------------------------------------------------------
# Registry repo queries + validation
# ---------------------------------------------------------------------------


@pytest.fixture
def project_with_repos(tmp_path):
    """Project with catalog, profiles, AND repos."""
    codio_dir = tmp_path / ".codio"
    codio_dir.mkdir()

    catalog = {"libraries": {
        "scipy-linalg": {
            "kind": "external_mirror",
            "language": "python",
            "repo_id": "scipy--scipy",
        },
        "orphan-ref": {
            "kind": "internal",
            "repo_id": "nonexistent--repo",
        },
    }}
    profiles = {"profiles": {
        "scipy-linalg": {"priority": "tier1"},
    }}
    repos = {"repositories": {
        "scipy--scipy": {
            "url": "https://github.com/scipy/scipy.git",
            "hosting": "github",
            "storage": "managed",
            "local_path": ".codio/mirrors/scipy--scipy",
        },
    }}

    for name, data in [("catalog.yml", catalog), ("profiles.yml", profiles), ("repos.yml", repos)]:
        with open(codio_dir / name, "w") as f:
            yaml.dump(data, f)

    return tmp_path


def _make_registry_from(project_root):
    cfg = CodioConfig(
        catalog_path=project_root / ".codio" / "catalog.yml",
        profiles_path=project_root / ".codio" / "profiles.yml",
        repos_path=project_root / ".codio" / "repos.yml",
        project_root=project_root,
    )
    return Registry(config=cfg)


def test_registry_loads_repos(project_with_repos):
    reg = _make_registry_from(project_with_repos)
    repos = reg.list_repos()
    assert len(repos) == 1
    assert repos[0].repo_id == "scipy--scipy"


def test_registry_list_repos_filter(project_with_repos):
    reg = _make_registry_from(project_with_repos)
    managed = reg.list_repos(storage="managed")
    assert len(managed) == 1
    external = reg.list_repos(storage="external")
    assert len(external) == 0


def test_registry_get_repo(project_with_repos):
    reg = _make_registry_from(project_with_repos)
    repo = reg.get_repo("scipy--scipy")
    assert repo is not None
    assert repo.storage == "managed"
    assert reg.get_repo("nonexistent") is None


def test_registry_snapshot_includes_repos(project_with_repos):
    reg = _make_registry_from(project_with_repos)
    snap = reg.snapshot()
    assert "scipy--scipy" in snap.repositories


def test_validate_warns_missing_repo_id(project_with_repos):
    reg = _make_registry_from(project_with_repos)
    result = reg.validate()
    warnings = [w for w in result.warnings if "nonexistent--repo" in w]
    assert len(warnings) == 1


def test_validate_warns_missing_managed_path(project_with_repos):
    reg = _make_registry_from(project_with_repos)
    result = reg.validate()
    warnings = [w for w in result.warnings if "managed local_path" in w]
    assert len(warnings) == 1  # mirrors dir doesn't exist


# ---------------------------------------------------------------------------
# Expanded RAG
# ---------------------------------------------------------------------------


def test_owned_sources_with_catalog(tmp_path):
    from codio.rag import owned_codio_sources, owned_source_ids

    # Create a library path that exists
    lib_dir = tmp_path / "src" / "utils"
    lib_dir.mkdir(parents=True)

    cfg = CodioConfig(
        catalog_path=tmp_path / ".codio" / "catalog.yml",
        profiles_path=tmp_path / ".codio" / "profiles.yml",
        notes_dir=tmp_path / "docs" / "notes",
        project_root=tmp_path,
    )
    catalog = {
        "utils": LibraryCatalogEntry(name="utils", kind="internal", path="src/utils"),
        "remote-only": LibraryCatalogEntry(name="remote-only", kind="external_mirror"),
    }

    sources = owned_codio_sources(cfg, catalog)
    # notes + catalog + utils source tree (remote-only has no path)
    assert len(sources) == 3
    src_ids = [s["id"] for s in sources]
    assert "codio-src-utils" in src_ids
    assert "codio-src-remote-only" not in src_ids

    ids = owned_source_ids(catalog)
    assert "codio-src-utils" in ids


def test_resolve_source_id():
    from codio.rag import resolve_source_id

    assert resolve_source_id("codio-src-scipy") == "scipy"
    assert resolve_source_id("codio-notes") is None
    assert resolve_source_id("other-thing") is None


# ---------------------------------------------------------------------------
# CLI: codio add
# ---------------------------------------------------------------------------


def test_cli_add(tmp_project):
    from codio.cli import main

    main([
        "add", "pandas",
        "--kind", "external_mirror",
        "--language", "python",
        "--summary", "Data analysis library",
        "--priority", "tier1",
        "--capabilities", "dataframes,csv",
        "--root", str(tmp_project),
    ])

    # Verify it's in the catalog
    with open(tmp_project / ".codio" / "catalog.yml") as f:
        cat = yaml.safe_load(f)
    assert "pandas" in cat["libraries"]
    assert cat["libraries"]["pandas"]["kind"] == "external_mirror"

    # Verify profile was created
    with open(tmp_project / ".codio" / "profiles.yml") as f:
        prof = yaml.safe_load(f)
    assert "pandas" in prof["profiles"]
    assert prof["profiles"]["pandas"]["priority"] == "tier1"


def test_cli_add_json(tmp_project, capsys):
    from codio.cli import main

    main([
        "add", "mylib",
        "--kind", "internal",
        "--root", str(tmp_project),
        "--json",
    ])
    import json
    out = json.loads(capsys.readouterr().out)
    assert out["added"] == "mylib"


# ---------------------------------------------------------------------------
# CLI: codio attach
# ---------------------------------------------------------------------------


def test_cli_attach(tmp_project):
    from codio.cli import main

    # Create a directory to attach
    repo_dir = tmp_project / "external" / "myrepo"
    repo_dir.mkdir(parents=True)

    main([
        "attach", "my--repo", str(repo_dir),
        "--url", "https://github.com/me/myrepo",
        "--hosting", "github",
        "--root", str(tmp_project),
    ])

    repos = load_repos(tmp_project / ".codio" / "repos.yml")
    assert "my--repo" in repos
    assert repos["my--repo"].storage == "attached"
    assert repos["my--repo"].url == "https://github.com/me/myrepo"


# ---------------------------------------------------------------------------
# CLI: codio repos
# ---------------------------------------------------------------------------


def test_cli_repos_empty(tmp_project, capsys):
    from codio.cli import main

    main(["repos", "--root", str(tmp_project), "--json"])
    import json
    out = json.loads(capsys.readouterr().out)
    assert out == []


def test_cli_repos_with_data(project_with_repos, capsys):
    from codio.cli import main

    main(["repos", "--root", str(project_with_repos), "--json"])
    import json
    out = json.loads(capsys.readouterr().out)
    assert len(out) == 1
    assert out[0]["repo_id"] == "scipy--scipy"


# ---------------------------------------------------------------------------
# Scaffold includes repos.yml
# ---------------------------------------------------------------------------


def test_scaffold_creates_repos_yml(tmp_path):
    from codio.scaffold import init_codio_scaffold

    init_codio_scaffold(tmp_path)
    repos_yml = tmp_path / ".codio" / "repos.yml"
    assert repos_yml.exists()
    with open(repos_yml) as f:
        data = yaml.safe_load(f)
    assert "repositories" in data
