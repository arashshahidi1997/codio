"""Managed mirrors: gitignored local clones restored from repos.yml (url + ref)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from codio.cli import main
from codio.config import load_config
from codio.mirrors import sync_mirrors
from codio.models import RepositoryEntry
from codio.registry import load_repos, save_repos


def _git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=cwd, check=True, capture_output=True, text=True,
    ).stdout.strip()


def _commit(repo: Path, name: str) -> str:
    (repo / name).write_text(name)
    _git("add", name, cwd=repo)
    _git("commit", "-q", "-m", name, cwd=repo)
    return _git("rev-parse", "HEAD", cwd=repo)


@pytest.fixture
def upstream(tmp_path):
    repo = tmp_path / "upstream" / "lib"
    repo.mkdir(parents=True)
    _git("init", "-q", "-b", "main", cwd=repo)
    first = _commit(repo, "a.py")
    second = _commit(repo, "b.py")
    return repo, first, second


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "proj"
    (root / ".projio" / "codio").mkdir(parents=True)
    _git("init", "-q", "-b", "main", cwd=root)
    (root / ".gitignore").write_text(".projio/codio/mirrors/\n")
    return root


def _register(root: Path, upstream_path: Path, ref: str = "") -> None:
    config = load_config(root)
    save_repos(config.repos_path, {
        "acme--lib": RepositoryEntry(
            repo_id="acme--lib",
            url=str(upstream_path),
            hosting="other",
            storage="managed",
            local_path=".projio/codio/mirrors/acme--lib",
            default_branch="main",
            ref=ref,
        ),
    })


def test_ref_round_trips_through_repos_yml(project, upstream):
    _register(project, upstream[0], ref=upstream[1])
    repos = load_repos(load_config(project).repos_path)
    assert repos["acme--lib"].ref == upstream[1]


def test_sync_clones_missing_mirror_at_pinned_ref(project, upstream):
    repo, first, _second = upstream
    _register(project, repo, ref=first)
    results = sync_mirrors(load_config(project))
    assert results[0]["status"] == "cloned"
    mirror = project / ".projio/codio/mirrors/acme--lib"
    assert _git("rev-parse", "HEAD", cwd=mirror) == first
    assert (mirror / "a.py").exists() and not (mirror / "b.py").exists()
    assert results[0]["tracked_in_parent"] is False


def test_sync_pins_unpinned_mirror(project, upstream):
    repo, _first, second = upstream
    _register(project, repo)
    assert sync_mirrors(load_config(project))[0]["status"] == "cloned"
    assert load_repos(load_config(project).repos_path)["acme--lib"].ref == second
    # A second run finds it in place and pinned.
    assert sync_mirrors(load_config(project))[0]["status"] == "ok"


def test_existing_mirror_without_ref_is_pinned_without_network(project, upstream):
    repo, _first, second = upstream
    _register(project, repo)
    sync_mirrors(load_config(project))
    _register(project, "/nonexistent/url")  # ref cleared, url unusable
    res = sync_mirrors(load_config(project))[0]
    assert res["status"] == "pinned" and res["ref"] == second


def test_drift_reported_and_update_repins(project, upstream):
    repo, first, _second = upstream
    _register(project, repo, ref=first)
    sync_mirrors(load_config(project))
    third = _commit(repo, "c.py")
    mirror = project / ".projio/codio/mirrors/acme--lib"
    _git("checkout", "-q", "main", cwd=mirror)
    _git("pull", "-q", "--ff-only", cwd=mirror)
    res = sync_mirrors(load_config(project))[0]
    assert res["status"] == "drift" and res["head"] == third
    # Without --update the pin is left alone.
    assert load_repos(load_config(project).repos_path)["acme--lib"].ref == first

    _git("checkout", "-q", first, cwd=mirror)
    res = sync_mirrors(load_config(project), update=True)[0]
    assert res["status"] == "updated" and res["ref"] == third
    assert load_repos(load_config(project).repos_path)["acme--lib"].ref == third


def test_tracked_in_parent_is_flagged(project, upstream):
    repo, first, _ = upstream
    _register(project, repo, ref=first)
    sync_mirrors(load_config(project))
    _git("add", "-f", ".projio/codio/mirrors/acme--lib", cwd=project)
    res = sync_mirrors(load_config(project))[0]
    assert res["tracked_in_parent"] is True


def test_failed_clone_leaves_no_directory(project, tmp_path):
    _register(project, tmp_path / "does-not-exist")
    res = sync_mirrors(load_config(project))[0]
    assert res["status"] == "failed"
    assert not (project / ".projio/codio/mirrors/acme--lib").exists()


def test_unknown_repo_id_raises(project, upstream):
    _register(project, upstream[0])
    with pytest.raises(KeyError):
        sync_mirrors(load_config(project), "nope--nope")


def test_cli_mirror_sync_json(project, upstream, capsys):
    repo, first, _ = upstream
    _register(project, repo, ref=first)
    main(["mirror", "sync", "--root", str(project), "--json"])
    out = json.loads(capsys.readouterr().out)
    assert out[0]["status"] == "cloned" and out[0]["ref"] == first


def test_cli_mirror_sync_exits_nonzero_on_failure(project, tmp_path, capsys):
    _register(project, tmp_path / "does-not-exist")
    with pytest.raises(SystemExit) as exc:
        main(["mirror", "sync", "--root", str(project)])
    assert exc.value.code == 1


def test_cli_clone_records_ref(project, upstream, capsys):
    repo, _first, second = upstream
    main(["clone", str(repo), "--repo-id", "acme--lib", "--root", str(project)])
    assert load_repos(load_config(project).repos_path)["acme--lib"].ref == second
