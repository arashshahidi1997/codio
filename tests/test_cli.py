"""Tests for codio CLI and scaffold."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from codio.cli import main
from codio.scaffold import init_codio_scaffold


# ---------------------------------------------------------------------------
# Scaffold tests
# ---------------------------------------------------------------------------


def test_init_creates_scaffold(tmp_path):
    result = init_codio_scaffold(tmp_path)
    assert (tmp_path / ".codio" / "catalog.yml").exists()
    assert (tmp_path / ".codio" / "profiles.yml").exists()
    assert (tmp_path / ".codio" / "repos.yml").exists()
    assert (tmp_path / "docs" / "reference" / "codelib" / "libraries").is_dir()
    assert len(result.files_written) == 3


def test_init_skips_existing(tmp_path):
    init_codio_scaffold(tmp_path)
    result2 = init_codio_scaffold(tmp_path)
    assert len(result2.files_written) == 0


def test_init_force_overwrites(tmp_path):
    init_codio_scaffold(tmp_path)
    # Modify a file
    cat = tmp_path / ".codio" / "catalog.yml"
    cat.write_text("modified")
    result = init_codio_scaffold(tmp_path, force=True)
    assert len(result.files_written) == 3
    assert "modified" not in cat.read_text()


# ---------------------------------------------------------------------------
# CLI init command
# ---------------------------------------------------------------------------


def test_cli_init(tmp_path, capsys):
    main(["init", "--root", str(tmp_path)])
    assert (tmp_path / ".codio" / "catalog.yml").exists()
    out = capsys.readouterr().out
    assert ".codio" in out


def test_cli_init_force(tmp_path, capsys):
    main(["init", "--root", str(tmp_path)])
    main(["init", "--root", str(tmp_path), "--force"])
    out = capsys.readouterr().out
    assert "created" in out


# ---------------------------------------------------------------------------
# CLI list
# ---------------------------------------------------------------------------


def test_list_empty_registry(tmp_path, capsys):
    init_codio_scaffold(tmp_path)
    main(["list", "--root", str(tmp_path)])
    out = capsys.readouterr().out
    assert "No libraries found" in out


def test_list_with_filters(tmp_project, capsys):
    main(["list", "--root", str(tmp_project), "--kind", "internal"])
    out = capsys.readouterr().out
    assert "internal-utils" in out
    assert "numpy-mirror" not in out


def test_list_all(tmp_project, capsys):
    main(["list", "--root", str(tmp_project)])
    out = capsys.readouterr().out
    assert "internal-utils" in out
    assert "numpy-mirror" in out


# ---------------------------------------------------------------------------
# CLI get
# ---------------------------------------------------------------------------


def test_get_existing(tmp_project, capsys):
    main(["get", "internal-utils", "--root", str(tmp_project)])
    out = capsys.readouterr().out
    assert "internal-utils" in out
    assert "internal" in out


def test_get_missing(tmp_project):
    with pytest.raises(SystemExit, match="1"):
        main(["get", "nonexistent", "--root", str(tmp_project)])


# ---------------------------------------------------------------------------
# CLI validate
# ---------------------------------------------------------------------------


def test_validate(tmp_project, capsys):
    main(["validate", "--root", str(tmp_project)])
    out = capsys.readouterr().out
    # The fixture has no-profile-lib without a profile -> warning expected
    assert "WARNING" in out


# ---------------------------------------------------------------------------
# CLI vocab
# ---------------------------------------------------------------------------


def test_vocab(capsys):
    main(["vocab"])
    out = capsys.readouterr().out
    assert "kind" in out
    assert "runtime_import" in out


def test_vocab_field(capsys):
    main(["vocab", "--field", "kind"])
    out = capsys.readouterr().out
    assert "internal" in out
    assert "runtime_import" not in out


def test_vocab_unknown_field():
    with pytest.raises(SystemExit, match="1"):
        main(["vocab", "--field", "bogus"])


# ---------------------------------------------------------------------------
# CLI discover
# ---------------------------------------------------------------------------


def test_discover(tmp_project, capsys):
    main(["discover", "utilities", "--root", str(tmp_project)])
    out = capsys.readouterr().out
    assert "internal-utils" in out


def test_discover_no_match(tmp_project, capsys):
    main(["discover", "zzz-nonexistent", "--root", str(tmp_project)])
    out = capsys.readouterr().out
    assert "No candidates" in out


# ---------------------------------------------------------------------------
# CLI study
# ---------------------------------------------------------------------------


def test_study(tmp_project, capsys):
    main(["study", "internal-utils", "--root", str(tmp_project)])
    out = capsys.readouterr().out
    assert "internal-utils" in out
    assert "Strengths" in out


def test_study_missing(tmp_project):
    with pytest.raises(SystemExit, match="1"):
        main(["study", "nonexistent", "--root", str(tmp_project)])


# ---------------------------------------------------------------------------
# CLI compare
# ---------------------------------------------------------------------------


def test_compare(tmp_project, capsys):
    main(["compare", "internal-utils", "numpy-mirror", "--root", str(tmp_project)])
    out = capsys.readouterr().out
    assert "Comparing" in out
    assert "Recommendation" in out


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------


def test_cli_json_list(tmp_project, capsys):
    main(["list", "--root", str(tmp_project), "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) >= 2


def test_cli_json_get(tmp_project, capsys):
    main(["get", "internal-utils", "--root", str(tmp_project), "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["name"] == "internal-utils"


def test_cli_json_validate(tmp_project, capsys):
    main(["validate", "--root", str(tmp_project), "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "valid" in data
    assert "errors" in data


def test_cli_json_vocab(capsys):
    main(["vocab", "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "kind" in data


def test_cli_json_discover(tmp_project, capsys):
    main(["discover", "utilities", "--root", str(tmp_project), "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "candidates" in data


def test_cli_json_study(tmp_project, capsys):
    main(["study", "internal-utils", "--root", str(tmp_project), "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["name"] == "internal-utils"


def test_cli_json_compare(tmp_project, capsys):
    main(["compare", "internal-utils", "numpy-mirror", "--root", str(tmp_project), "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "libraries" in data


# ---------------------------------------------------------------------------
# CLI add-urls
# ---------------------------------------------------------------------------


def test_add_urls_single(tmp_project, capsys, monkeypatch):
    """add-urls registers a library from a GitHub URL."""
    monkeypatch.setattr(
        "codio.cli._fetch_github_meta",
        lambda url: {
            "description": "A wave analysis toolbox",
            "language": "Python",
            "license": {"spdx_id": "MIT"},
            "topics": ["neuroscience", "waves"],
        },
    )
    main(["add-urls", "https://github.com/BrainDynamicsUSYD/NeuroPattToolbox", "--root", str(tmp_project)])
    out = capsys.readouterr().out
    assert "neuropatttoolbox" in out
    assert "Added 1" in out

    # Verify it's in the registry
    main(["get", "neuropatttoolbox", "--root", str(tmp_project), "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["name"] == "neuropatttoolbox"
    assert data["kind"] == "external_mirror"
    assert data["repo_url"] == "https://github.com/BrainDynamicsUSYD/NeuroPattToolbox"
    assert data["license"] == "MIT"
    assert data["status"] == "candidate"
    assert "neuroscience" in data["capabilities"]


def test_add_urls_multiple(tmp_project, capsys, monkeypatch):
    """add-urls handles multiple URLs in one call."""
    monkeypatch.setattr("codio.cli._fetch_github_meta", lambda url: {})
    main([
        "add-urls",
        "https://github.com/mullerlab/generalized-phase",
        "https://github.com/preraulab/multitaper_toolbox",
        "--root", str(tmp_project),
    ])
    out = capsys.readouterr().out
    assert "generalized_phase" in out
    assert "multitaper_toolbox" in out
    assert "Added 2" in out


def test_add_urls_skip_existing(tmp_project, capsys, monkeypatch):
    """add-urls skips URLs whose library name already exists."""
    monkeypatch.setattr("codio.cli._fetch_github_meta", lambda url: {"language": "Python"})
    # Add first
    main(["add-urls", "https://github.com/owner/some-lib", "--root", str(tmp_project)])
    capsys.readouterr()
    # Add again — should skip
    main(["add-urls", "https://github.com/owner/some-lib", "--root", str(tmp_project)])
    out = capsys.readouterr().out
    assert "already in registry" in out
    assert "Added 0" in out


def test_add_urls_json(tmp_project, capsys, monkeypatch):
    """add-urls --json returns structured output."""
    monkeypatch.setattr("codio.cli._fetch_github_meta", lambda url: {"language": "MATLAB"})
    main([
        "add-urls",
        "https://github.com/navvab-afrashteh/OFAMM",
        "--root", str(tmp_project),
        "--json",
    ])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data) == 1
    assert data[0]["status"] == "added"
    assert data[0]["name"] == "ofamm"

    # Verify MATLAB → reference_only
    main(["get", "ofamm", "--root", str(tmp_project), "--json"])
    out = capsys.readouterr().out
    rec = json.loads(out)
    assert rec["runtime_import"] == "reference_only"
    assert rec["decision_default"] == "new"


def test_add_urls_bad_url(tmp_project, capsys, monkeypatch):
    """add-urls handles unparseable URLs gracefully."""
    monkeypatch.setattr("codio.cli._fetch_github_meta", lambda url: {})
    main(["add-urls", "not-a-url", "--root", str(tmp_project)])
    out = capsys.readouterr().out
    assert "cannot parse" in out
    assert "Added 0" in out


def test_add_urls_repos_yml(tmp_project, capsys, monkeypatch):
    """add-urls creates repo entries in repos.yml."""
    monkeypatch.setattr("codio.cli._fetch_github_meta", lambda url: {})
    main(["add-urls", "https://github.com/scipy/scipy", "--root", str(tmp_project)])
    capsys.readouterr()

    import yaml
    repos_path = tmp_project / ".codio" / "repos.yml"
    assert repos_path.exists()
    with open(repos_path) as f:
        data = yaml.safe_load(f)
    assert "scipy--scipy" in data["repositories"]
    assert data["repositories"]["scipy--scipy"]["hosting"] == "github"
    assert data["repositories"]["scipy--scipy"]["storage"] == "external"
