"""Managed mirrors: local, gitignored clones that codio restores on demand.

A managed mirror is a third-party repository codio clones for code reference
(reading, RAG indexing). Its working copy lives under ``mirrors_dir``
(``.projio/codio/mirrors/<repo_id>/``), which is gitignored: it is never part
of the parent repository's git history. ``repos.yml`` keeps what is needed
to rebuild it anywhere: ``url``, ``default_branch`` and the pinned commit
``ref``. ``sync_mirrors`` clones what is missing at that ref, records the ref
of mirrors that have none, and with ``update=True`` pulls and re-pins.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from codio.config import CodioConfig
from codio.models import RepositoryEntry
from codio.registry import load_repos, save_repos


def _git(*args: str, cwd: Path | None = None) -> str:
    out = subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
    )
    return out.stdout.strip()


def mirror_path(config: CodioConfig, entry: RepositoryEntry) -> Path:
    """Absolute path of a mirror's working copy."""
    if entry.local_path:
        p = Path(entry.local_path)
        return p if p.is_absolute() else config.project_root / p
    return config.mirrors_dir / entry.repo_id


def head_ref(path: Path) -> str:
    """Commit sha checked out in *path*."""
    return _git("rev-parse", "HEAD", cwd=path)


def tracked_in_parent(config: CodioConfig, path: Path) -> bool:
    """True when *path* is committed in the project repo (e.g. as a submodule).

    Mirrors belong in the working tree only; a gitlink means someone ran
    ``git add``/``datalad save`` on them despite the gitignore.
    """
    try:
        rel = path.relative_to(config.project_root)
    except ValueError:
        return False
    try:
        out = _git("ls-files", "--stage", "--", str(rel), cwd=config.project_root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return bool(out)


def _clone(entry: RepositoryEntry, dest: Path, *, shallow: bool) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["clone"]
    # A shallow clone cannot check out an older pinned commit.
    if shallow and not entry.ref:
        cmd += ["--depth", "1"]
    if entry.default_branch:
        cmd += ["-b", entry.default_branch]
    cmd += [entry.url, str(dest)]
    try:
        _git(*cmd)
        if entry.ref:
            _git("-c", "advice.detachedHead=false", "checkout", entry.ref, cwd=dest)
    except subprocess.CalledProcessError:
        if dest.exists():
            shutil.rmtree(dest)
        raise


def sync_mirrors(
    config: CodioConfig,
    repo_id: str | None = None,
    *,
    update: bool = False,
    shallow: bool = False,
) -> list[dict[str, object]]:
    """Bring managed mirrors in line with ``repos.yml``.

    For each managed repository (or only *repo_id*):

    - missing on disk: clone ``url`` (branch ``default_branch``) and check out
      ``ref`` when one is pinned; status ``cloned``.
    - present, ``update=False``: leave it; record ``ref`` from HEAD when none
      is pinned (status ``pinned``), report ``drift`` when HEAD differs from
      the pinned ref, otherwise ``ok``.
    - present, ``update=True``: ``git pull --ff-only`` on the default branch
      and pin the new HEAD; status ``updated``.

    Every result carries ``tracked_in_parent`` so callers can warn about
    mirrors committed into the project repository.
    """
    repos = load_repos(config.repos_path)
    targets = [e for e in repos.values() if e.storage == "managed"]
    if repo_id is not None:
        targets = [e for e in targets if e.repo_id == repo_id]
        if not targets:
            raise KeyError(f"No managed repo '{repo_id}' in {config.repos_path}")

    results: list[dict[str, object]] = []
    changed = False
    for entry in targets:
        path = mirror_path(config, entry)
        res: dict[str, object] = {"repo_id": entry.repo_id, "path": str(path)}
        try:
            if not (path / ".git").exists():
                if not entry.url:
                    res["status"] = "failed"
                    res["error"] = "no url recorded"
                    results.append(res)
                    continue
                if path.exists() and any(path.iterdir()):
                    res["status"] = "failed"
                    res["error"] = "path exists and is not a git repository"
                    results.append(res)
                    continue
                if path.exists():
                    path.rmdir()
                _clone(entry, path, shallow=shallow)
                res["status"] = "cloned"
            elif update:
                if entry.ref:
                    # A pinned mirror sits on a detached HEAD; return to the branch.
                    _git("checkout", entry.default_branch or "main", cwd=path)
                _git("pull", "--ff-only", cwd=path)
                res["status"] = "updated"
            else:
                head = head_ref(path)
                if not entry.ref:
                    res["status"] = "pinned"
                elif head != entry.ref:
                    res["status"] = "drift"
                    res["head"] = head
                else:
                    res["status"] = "ok"
            if res["status"] in ("cloned", "updated", "pinned"):
                new_ref = head_ref(path)
                if new_ref != entry.ref:
                    entry.ref = new_ref
                    changed = True
            res["ref"] = entry.ref
        except subprocess.CalledProcessError as exc:
            res["status"] = "failed"
            res["error"] = (exc.stderr or str(exc)).strip()
        res["tracked_in_parent"] = tracked_in_parent(config, path)
        results.append(res)

    if changed:
        save_repos(config.repos_path, repos)
    return results
