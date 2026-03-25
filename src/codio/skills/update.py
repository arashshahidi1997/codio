from __future__ import annotations

import datetime
import re
import yaml
from pathlib import Path
from typing import Any

from codio.models import LibraryCatalogEntry, ProjectProfileEntry, RepositoryEntry, ValidationResult
from codio.registry import Registry, load_repos, save_repos


def add_library(
    registry: Registry,
    catalog_entry: LibraryCatalogEntry,
    profile_entry: ProjectProfileEntry | None = None,
) -> None:
    """Add or update a library in the registry (in-memory and on disk).

    Updates the YAML files on disk to persist changes.
    """
    registry._catalog[catalog_entry.name] = catalog_entry
    if profile_entry is not None:
        registry._profiles[profile_entry.name] = profile_entry
    _write_catalog(registry._config.catalog_path, registry._catalog)
    if profile_entry is not None:
        _write_profiles(registry._config.profiles_path, registry._profiles)


def remove_library(registry: Registry, name: str) -> bool:
    """Remove a library from catalog and profile. Returns True if found."""
    found = name in registry._catalog
    registry._catalog.pop(name, None)
    registry._profiles.pop(name, None)
    _write_catalog(registry._config.catalog_path, registry._catalog)
    _write_profiles(registry._config.profiles_path, registry._profiles)
    return found


def update_profile(
    registry: Registry,
    profile_entry: ProjectProfileEntry,
) -> bool:
    """Update a project profile. Returns False if library not in catalog."""
    if profile_entry.name not in registry._catalog:
        return False
    registry._profiles[profile_entry.name] = profile_entry
    _write_profiles(registry._config.profiles_path, registry._profiles)
    return True


def validate_registry(registry: Registry) -> ValidationResult:
    """Run validation on the registry."""
    return registry.validate()


def _write_catalog(path: Path, catalog: dict[str, LibraryCatalogEntry]) -> None:
    """Write catalog entries to YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"libraries": {}}
    for name, entry in catalog.items():
        d = entry.model_dump(mode="json", exclude={"name"}, exclude_defaults=False)
        data["libraries"][name] = {k: v for k, v in d.items() if v != "" and v != []}
    with open(path, "w") as fh:
        yaml.dump(data, fh, default_flow_style=False, sort_keys=False)


def _write_profiles(path: Path, profiles: dict[str, ProjectProfileEntry]) -> None:
    """Write profile entries to YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"profiles": {}}
    for name, entry in profiles.items():
        d = entry.model_dump(mode="json", exclude={"name"}, exclude_defaults=False)
        data["profiles"][name] = {k: v for k, v in d.items() if v != "" and v != []}
    with open(path, "w") as fh:
        yaml.dump(data, fh, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# URL ingestion helpers (extracted from cli.py for reuse by MCP tools)
# ---------------------------------------------------------------------------

def guess_hosting(url: str) -> str:
    """Guess the hosting provider from a repository URL."""
    if "github.com" in url:
        return "github"
    if "gitlab" in url:
        return "gitlab"
    return "other"


def fetch_github_meta(url: str) -> dict[str, Any]:
    """Fetch repository metadata from GitHub API. Returns {} on failure."""
    m = re.search(r"github\.com/([^/]+)/([^/.]+?)(?:\.git)?$", url)
    if not m:
        return {}
    owner, repo = m.group(1), m.group(2)
    try:
        import json as _json
        import urllib.request

        req = urllib.request.Request(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "codio"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return _json.loads(resp.read())
    except Exception:
        return {}


def add_urls(
    registry: Registry,
    urls: list[str],
    *,
    clone: bool = False,
    shallow: bool = False,
    branch: str = "main",
) -> list[dict[str, str]]:
    """Add libraries from repository URLs to the registry.

    Parses each URL to extract owner/repo, fetches GitHub metadata when
    available, creates catalog + profile + repository entries.

    Returns a list of result dicts per URL with keys:
        url, name, status ("added"|"exists"|"error"), repo_id, reason.
    """
    import subprocess

    repos = load_repos(registry._config.repos_path)
    today = datetime.date.today().isoformat()
    results: list[dict[str, str]] = []

    for url in urls:
        url = url.strip()
        if not url:
            continue

        m = re.search(r"[/:]([^/:]+)/([^/.]+?)(?:\.git)?$", url)
        if not m:
            results.append({"url": url, "status": "error", "reason": "cannot parse URL"})
            continue

        repo_id = f"{m.group(1)}--{m.group(2)}".lower()
        lib_name = m.group(2).lower().replace("-", "_")

        if lib_name in registry._catalog:
            results.append({"url": url, "name": lib_name, "status": "exists"})
            continue

        hosting = guess_hosting(url)
        gh_meta = fetch_github_meta(url) if hosting == "github" else {}

        language = gh_meta.get("language", "").lower()
        summary = gh_meta.get("description", "") or ""
        license_name = ""
        if gh_meta.get("license") and isinstance(gh_meta["license"], dict):
            license_name = gh_meta["license"].get("spdx_id", "") or ""
        pip_name = m.group(2).lower() if language == "python" else ""

        runtime_import = "pip_only" if language == "python" else "reference_only"

        catalog_entry = LibraryCatalogEntry(
            name=lib_name,
            kind="external_mirror",
            language=language,
            repo_url=url,
            pip_name=pip_name,
            license=license_name,
            summary=summary[:200] if summary else "",
            repo_id=repo_id,
            added_by="import",
            added_date=today,
        )

        topics = gh_meta.get("topics", []) or []
        caps = [t for t in topics if t] if topics else []

        profile_entry = ProjectProfileEntry(
            name=lib_name,
            priority="tier2",
            runtime_import=runtime_import,
            decision_default="wrap" if language == "python" else "new",
            capabilities=caps,
            status="candidate",
        )

        add_library(registry, catalog_entry, profile_entry)

        # Register repo entry
        storage = "external"
        local_path = ""

        if clone:
            clone_dir = registry._config.mirrors_dir / repo_id
            if not clone_dir.exists():
                clone_cmd = ["git", "clone"]
                if shallow:
                    clone_cmd += ["--depth", "1"]
                clone_cmd += ["-b", branch, url, str(clone_dir)]
                try:
                    subprocess.run(clone_cmd, check=True, capture_output=True, text=True)
                    storage = "managed"
                    local_path = str(clone_dir.relative_to(registry._config.project_root))
                except subprocess.CalledProcessError:
                    pass
            else:
                storage = "managed"
                local_path = str(clone_dir.relative_to(registry._config.project_root))

        repo_entry = RepositoryEntry(
            repo_id=repo_id,
            url=url,
            hosting=hosting,
            storage=storage,
            local_path=local_path,
            default_branch=branch,
        )
        repos[repo_id] = repo_entry
        results.append({"url": url, "name": lib_name, "status": "added", "repo_id": repo_id})

    save_repos(registry._config.repos_path, repos)
    return results
