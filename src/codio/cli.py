"""Argparse-based CLI for codio."""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path
from typing import Iterable


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="codio", description="Code reuse discovery tool")
    sub = p.add_subparsers(dest="command")

    # --- init ---------------------------------------------------------------
    p_init = sub.add_parser("init", help="Scaffold .codio/ in a project")
    p_init.add_argument("--root", type=Path, default=None, help="Project root")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing files")

    # --- list ---------------------------------------------------------------
    p_list = sub.add_parser("list", help="List libraries from registry")
    p_list.add_argument("--root", type=Path, default=None)
    p_list.add_argument("--kind", default=None)
    p_list.add_argument("--language", default=None)
    p_list.add_argument("--capability", default=None)
    p_list.add_argument("--priority", default=None)
    p_list.add_argument("--runtime-import", dest="runtime_import", default=None)
    p_list.add_argument("--json", dest="as_json", action="store_true")

    # --- get ----------------------------------------------------------------
    p_get = sub.add_parser("get", help="Show full record for a library")
    p_get.add_argument("name")
    p_get.add_argument("--root", type=Path, default=None)
    p_get.add_argument("--json", dest="as_json", action="store_true")

    # --- validate -----------------------------------------------------------
    p_val = sub.add_parser("validate", help="Validate registry consistency")
    p_val.add_argument("--root", type=Path, default=None)
    p_val.add_argument("--json", dest="as_json", action="store_true")

    # --- vocab --------------------------------------------------------------
    p_vocab = sub.add_parser("vocab", help="Show controlled vocabulary")
    p_vocab.add_argument("--field", default=None, help="Show a specific field only")
    p_vocab.add_argument("--json", dest="as_json", action="store_true")

    # --- discover -----------------------------------------------------------
    p_disc = sub.add_parser("discover", help="Search for libraries by capability")
    p_disc.add_argument("query")
    p_disc.add_argument("--root", type=Path, default=None)
    p_disc.add_argument("--language", default=None)
    p_disc.add_argument("--json", dest="as_json", action="store_true")

    # --- study --------------------------------------------------------------
    p_study = sub.add_parser("study", help="Structured analysis of a library")
    p_study.add_argument("name")
    p_study.add_argument("--root", type=Path, default=None)
    p_study.add_argument("--json", dest="as_json", action="store_true")

    # --- compare ------------------------------------------------------------
    p_cmp = sub.add_parser("compare", help="Compare multiple libraries")
    p_cmp.add_argument("names", nargs="+", metavar="NAME")
    p_cmp.add_argument("--root", type=Path, default=None)
    p_cmp.add_argument("--query", default="")
    p_cmp.add_argument("--json", dest="as_json", action="store_true")

    # --- add ----------------------------------------------------------------
    p_add = sub.add_parser("add", help="Add a library to the registry")
    p_add.add_argument("name", help="Library slug")
    p_add.add_argument("--kind", required=True, help="Library kind")
    p_add.add_argument("--language", default="", help="Dominant language")
    p_add.add_argument("--repo-url", dest="repo_url", default="", help="Upstream URL")
    p_add.add_argument("--pip-name", dest="pip_name", default="", help="Package name")
    p_add.add_argument("--path", default="", help="Local path")
    p_add.add_argument("--summary", default="", help="Short description")
    p_add.add_argument("--repo-id", dest="repo_id", default="", help="FK to repos.yml")
    p_add.add_argument("--priority", default="tier2")
    p_add.add_argument("--runtime-import", dest="runtime_import", default="reference_only")
    p_add.add_argument("--decision-default", dest="decision_default", default="new")
    p_add.add_argument("--capabilities", default="", help="Comma-separated capability tags")
    p_add.add_argument("--root", type=Path, default=None)
    p_add.add_argument("--json", dest="as_json", action="store_true")

    # --- add-urls -----------------------------------------------------------
    p_addurls = sub.add_parser("add-urls", help="Add libraries from git URLs")
    p_addurls.add_argument("urls", nargs="+", metavar="URL", help="Git repository URLs")
    p_addurls.add_argument("--clone", action="store_true", help="Also clone as managed mirrors")
    p_addurls.add_argument("--shallow", action="store_true", help="Shallow clone (--depth 1)")
    p_addurls.add_argument("--branch", default="main", help="Default branch")
    p_addurls.add_argument("--root", type=Path, default=None)
    p_addurls.add_argument("--json", dest="as_json", action="store_true")

    # --- attach -------------------------------------------------------------
    p_attach = sub.add_parser("attach", help="Attach an existing repo to the registry")
    p_attach.add_argument("repo_id", help="Repository slug (e.g. owner--repo)")
    p_attach.add_argument("local_path", help="Path to existing repo on disk")
    p_attach.add_argument("--url", default="", help="Remote URL (optional)")
    p_attach.add_argument("--hosting", default="local", help="Hosting provider")
    p_attach.add_argument("--branch", default="main", help="Default branch")
    p_attach.add_argument("--root", type=Path, default=None)
    p_attach.add_argument("--json", dest="as_json", action="store_true")

    # --- clone --------------------------------------------------------------
    p_clone = sub.add_parser("clone", help="Clone a repo as a managed mirror")
    p_clone.add_argument("url", help="Repository clone URL")
    p_clone.add_argument("--repo-id", dest="repo_id", default="", help="Override slug")
    p_clone.add_argument("--branch", default="main", help="Default branch")
    p_clone.add_argument("--shallow", action="store_true", help="Shallow clone (--depth 1)")
    p_clone.add_argument("--root", type=Path, default=None)
    p_clone.add_argument("--json", dest="as_json", action="store_true")

    # --- sync ---------------------------------------------------------------
    p_sync = sub.add_parser("sync", help="Pull updates for managed mirrors")
    p_sync.add_argument("repo_id", nargs="?", default=None, help="Specific repo to sync")
    p_sync.add_argument("--root", type=Path, default=None)
    p_sync.add_argument("--json", dest="as_json", action="store_true")

    # --- repos --------------------------------------------------------------
    p_repos = sub.add_parser("repos", help="List tracked repositories")
    p_repos.add_argument("--storage", default=None, help="Filter by storage mode")
    p_repos.add_argument("--root", type=Path, default=None)
    p_repos.add_argument("--json", dest="as_json", action="store_true")

    # --- rag ----------------------------------------------------------------
    p_rag = sub.add_parser("rag", help="Manage codio-owned RAG sources")
    rag_sub = p_rag.add_subparsers(dest="rag_cmd", required=True)
    rag_sync = rag_sub.add_parser("sync", help="Register codio sources in indexio config")
    rag_sync.add_argument("--root", type=Path, default=None)
    rag_sync.add_argument("--config", type=Path, default=None, help="Path to indexio config file")
    rag_sync.add_argument("--force-init", action="store_true", help="Reinitialize config")

    return p


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_root(args: argparse.Namespace) -> Path:
    if args.root is not None:
        return args.root.expanduser().resolve()
    from codio.paths import find_project_root
    return find_project_root()


def _make_registry(root: Path):
    from codio.config import load_config
    from codio.registry import Registry
    config = load_config(root)
    return Registry(config=config)


def _json_out(obj: object) -> None:
    print(json.dumps(obj, indent=2))


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def _cmd_init(args: argparse.Namespace) -> None:
    from codio.scaffold import init_codio_scaffold
    root = args.root.expanduser().resolve() if args.root else Path.cwd()
    result = init_codio_scaffold(root, force=args.force)
    if result.files_written:
        for f in result.files_written:
            print(f"  created {f.relative_to(result.root)}")
    else:
        print("  .codio/ already exists (use --force to overwrite)")
    print(f"Codio scaffold ready at {result.root / '.codio'}")


def _cmd_list(args: argparse.Namespace) -> None:
    root = _resolve_root(args)
    registry = _make_registry(root)
    records = registry.list(
        kind=args.kind,
        language=args.language,
        capability=args.capability,
        priority=args.priority,
        runtime_import=args.runtime_import,
    )
    if args.as_json:
        _json_out([r.model_dump() for r in records])
        return
    if not records:
        print("No libraries found.")
        return
    for r in records:
        line = f"  {r.name:<30s} kind={r.kind:<18s} lang={r.language:<10s} priority={r.priority}"
        print(line)


def _cmd_get(args: argparse.Namespace) -> None:
    root = _resolve_root(args)
    registry = _make_registry(root)
    record = registry.get(args.name)
    if record is None:
        print(f"Library '{args.name}' not found in registry.", file=sys.stderr)
        raise SystemExit(1)
    if args.as_json:
        _json_out(record.model_dump())
        return
    d = record.model_dump()
    for key, value in d.items():
        print(f"  {key}: {value}")


def _cmd_validate(args: argparse.Namespace) -> None:
    root = _resolve_root(args)
    registry = _make_registry(root)
    result = registry.validate()
    if args.as_json:
        _json_out(result.model_dump())
        return
    if result.valid:
        print("Registry is valid.")
    else:
        print("Registry has errors:")
    for e in result.errors:
        print(f"  ERROR: {e}")
    for w in result.warnings:
        print(f"  WARNING: {w}")


def _cmd_vocab(args: argparse.Namespace) -> None:
    from codio.vocab import get_vocab
    vocab = get_vocab()
    if args.field:
        if args.field not in vocab:
            print(f"Unknown field '{args.field}'. Available: {', '.join(vocab)}", file=sys.stderr)
            raise SystemExit(1)
        vocab = {args.field: vocab[args.field]}
    if args.as_json:
        _json_out(vocab)
        return
    for field_name, info in vocab.items():
        print(f"{field_name} — {info['description']}")
        for val, desc in info["values"].items():
            print(f"  {val}: {desc}")


def _cmd_discover(args: argparse.Namespace) -> None:
    from codio.skills.discovery import discover
    root = _resolve_root(args)
    registry = _make_registry(root)
    result = discover(args.query, registry, language=args.language)
    if args.as_json:
        _json_out(dataclasses.asdict(result))
        return
    print(f"Query: {result.query}")
    print(f"Recommendation: {result.recommended_decision} — {result.reasoning}")
    if result.candidates:
        print(f"\nCandidates ({len(result.candidates)}):")
        for c in result.candidates:
            print(f"  {c.name} [{c.priority}] — {c.relevance_reason}")
    else:
        print("No candidates found.")


def _cmd_study(args: argparse.Namespace) -> None:
    from codio.skills.study import study_library
    root = _resolve_root(args)
    registry = _make_registry(root)
    analysis = study_library(args.name, registry)
    if analysis is None:
        print(f"Library '{args.name}' not found in registry.", file=sys.stderr)
        raise SystemExit(1)
    if args.as_json:
        _json_out(dataclasses.asdict(analysis))
        return
    print(f"{analysis.name} ({analysis.kind}, {analysis.language})")
    print(f"  Summary: {analysis.summary}")
    if analysis.strengths:
        print("  Strengths:")
        for s in analysis.strengths:
            print(f"    - {s}")
    if analysis.caveats:
        print("  Caveats:")
        for c in analysis.caveats:
            print(f"    - {c}")
    if analysis.entry_points:
        print("  Entry points:")
        for ep in analysis.entry_points:
            print(f"    - {ep}")
    print(f"  Integration: {analysis.integration_notes}")


def _cmd_compare(args: argparse.Namespace) -> None:
    from codio.skills.study import compare_libraries
    root = _resolve_root(args)
    registry = _make_registry(root)
    result = compare_libraries(args.names, registry, query=args.query)
    if args.as_json:
        _json_out(dataclasses.asdict(result))
        return
    print(f"Comparing: {', '.join(a.name for a in result.libraries)}")
    print(f"Recommendation: {result.recommendation}")
    if result.shared_capabilities:
        print(f"Shared capabilities: {', '.join(result.shared_capabilities)}")
    if result.distinguishing_factors:
        print(f"Distinguishing: {', '.join(result.distinguishing_factors)}")


# ---------------------------------------------------------------------------
# Ingestion handlers
# ---------------------------------------------------------------------------

def _cmd_add(args: argparse.Namespace) -> None:
    from codio.models import LibraryCatalogEntry, ProjectProfileEntry
    from codio.skills.update import add_library

    root = _resolve_root(args)
    registry = _make_registry(root)

    catalog_entry = LibraryCatalogEntry(
        name=args.name,
        kind=args.kind,
        language=args.language,
        repo_url=args.repo_url,
        pip_name=args.pip_name,
        path=args.path,
        summary=args.summary,
        repo_id=args.repo_id,
        added_by="manual",
        added_date=_today(),
    )
    caps = [c.strip() for c in args.capabilities.split(",") if c.strip()] if args.capabilities else []
    profile_entry = ProjectProfileEntry(
        name=args.name,
        priority=args.priority,
        runtime_import=args.runtime_import,
        decision_default=args.decision_default,
        capabilities=caps,
    )
    add_library(registry, catalog_entry, profile_entry)

    if args.as_json:
        _json_out({"added": args.name})
    else:
        print(f"Added library '{args.name}' to registry.")


def _cmd_add_urls(args: argparse.Namespace) -> None:
    import re
    import subprocess

    from codio.config import load_config
    from codio.models import LibraryCatalogEntry, ProjectProfileEntry, RepositoryEntry
    from codio.registry import load_repos, save_repos
    from codio.skills.update import add_library

    root = _resolve_root(args)
    config = load_config(root)
    registry = _make_registry(root)
    repos = load_repos(config.repos_path)

    results = []
    for url in args.urls:
        url = url.strip()
        if not url:
            continue

        # Derive repo_id from URL
        m = re.search(r"[/:]([^/:]+)/([^/.]+?)(?:\.git)?$", url)
        if not m:
            results.append({"url": url, "status": "error", "reason": "cannot parse URL"})
            continue
        repo_id = f"{m.group(1)}--{m.group(2)}".lower()
        # Library name: just the repo part, lowercased with underscores
        lib_name = m.group(2).lower().replace("-", "_")

        # Skip if already in catalog
        if lib_name in registry._catalog:
            results.append({"url": url, "name": lib_name, "status": "exists"})
            continue

        hosting = _guess_hosting(url)

        # Fetch metadata from GitHub API if applicable
        gh_meta = _fetch_github_meta(url) if hosting == "github" else {}

        language = gh_meta.get("language", "").lower()
        summary = gh_meta.get("description", "") or ""
        license_name = ""
        if gh_meta.get("license") and isinstance(gh_meta["license"], dict):
            license_name = gh_meta["license"].get("spdx_id", "") or ""
        pip_name = ""
        # For Python repos, guess pip name from repo name
        if language == "python":
            pip_name = m.group(2).lower()

        # Determine runtime_import from language
        if language in ("python",):
            runtime_import = "pip_only"
        else:
            runtime_import = "reference_only"

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
            added_date=_today(),
        )

        # GitHub topics → capability tags
        topics = gh_meta.get("topics", []) or []
        caps = [t for t in topics if t] if topics else []

        profile_entry = ProjectProfileEntry(
            name=lib_name,
            priority="tier2",
            runtime_import=runtime_import,
            decision_default="wrap" if language in ("python",) else "new",
            capabilities=caps,
            status="candidate",
        )

        add_library(registry, catalog_entry, profile_entry)

        # Register repo entry
        storage = "external"
        local_path = ""

        if args.clone:
            clone_dir = config.mirrors_dir / repo_id
            if not clone_dir.exists():
                clone_cmd = ["git", "clone"]
                if args.shallow:
                    clone_cmd += ["--depth", "1"]
                clone_cmd += ["-b", args.branch, url, str(clone_dir)]
                try:
                    subprocess.run(clone_cmd, check=True, capture_output=True, text=True)
                    storage = "managed"
                    local_path = str(clone_dir.relative_to(config.project_root))
                except subprocess.CalledProcessError:
                    # Clone failed — still register as external
                    pass
            else:
                storage = "managed"
                local_path = str(clone_dir.relative_to(config.project_root))

        repo_entry = RepositoryEntry(
            repo_id=repo_id,
            url=url,
            hosting=hosting,
            storage=storage,
            local_path=local_path,
            default_branch=args.branch,
        )
        repos[repo_id] = repo_entry

        results.append({"url": url, "name": lib_name, "status": "added", "repo_id": repo_id})

    save_repos(config.repos_path, repos)

    if args.as_json:
        _json_out(results)
    else:
        for r in results:
            if r["status"] == "added":
                print(f"  + {r['name']:<30s} {r['url']}")
            elif r["status"] == "exists":
                print(f"  = {r['name']:<30s} already in registry")
            else:
                print(f"  ! {r['url']:<30s} {r.get('reason', 'error')}")
        added = [r for r in results if r["status"] == "added"]
        print(f"\nAdded {len(added)} librar{'y' if len(added) == 1 else 'ies'}.")


def _fetch_github_meta(url: str) -> dict:
    """Fetch repository metadata from GitHub API. Returns {} on failure."""
    import re
    m = re.search(r"github\.com/([^/]+)/([^/.]+?)(?:\.git)?$", url)
    if not m:
        return {}
    owner, repo = m.group(1), m.group(2)
    try:
        import urllib.request
        import json as _json
        req = urllib.request.Request(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "codio"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return _json.loads(resp.read())
    except Exception:
        return {}


def _cmd_attach(args: argparse.Namespace) -> None:
    from codio.config import load_config
    from codio.models import RepositoryEntry
    from codio.registry import load_repos, save_repos

    root = _resolve_root(args)
    config = load_config(root)

    entry = RepositoryEntry(
        repo_id=args.repo_id,
        url=args.url,
        hosting=args.hosting,
        storage="attached",
        local_path=args.local_path,
        default_branch=args.branch,
    )

    repos = load_repos(config.repos_path)
    repos[args.repo_id] = entry
    save_repos(config.repos_path, repos)

    if args.as_json:
        _json_out({"attached": args.repo_id, "local_path": args.local_path})
    else:
        print(f"Attached repository '{args.repo_id}' at {args.local_path}")


def _cmd_clone(args: argparse.Namespace) -> None:
    import re
    import subprocess

    from codio.config import load_config
    from codio.models import RepositoryEntry
    from codio.registry import load_repos, save_repos

    root = _resolve_root(args)
    config = load_config(root)

    # Derive repo_id from URL if not provided
    repo_id = args.repo_id
    if not repo_id:
        # Extract owner/repo from URL
        m = re.search(r"[/:]([^/:]+)/([^/.]+?)(?:\.git)?$", args.url)
        if m:
            repo_id = f"{m.group(1)}--{m.group(2)}".lower()
        else:
            print("Cannot derive repo_id from URL. Use --repo-id.", file=sys.stderr)
            raise SystemExit(1)

    clone_dir = config.mirrors_dir / repo_id
    if clone_dir.exists():
        print(f"Mirror directory already exists: {clone_dir}", file=sys.stderr)
        raise SystemExit(1)

    # Record metadata first
    entry = RepositoryEntry(
        repo_id=repo_id,
        url=args.url,
        hosting=_guess_hosting(args.url),
        storage="managed",
        local_path=str(clone_dir.relative_to(config.project_root)),
        default_branch=args.branch,
    )
    repos = load_repos(config.repos_path)
    repos[repo_id] = entry
    save_repos(config.repos_path, repos)

    # Clone
    clone_cmd = ["git", "clone"]
    if args.shallow:
        clone_cmd += ["--depth", "1"]
    clone_cmd += ["-b", args.branch, args.url, str(clone_dir)]

    try:
        subprocess.run(clone_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        print(f"Clone failed: {exc.stderr.strip()}", file=sys.stderr)
        # Clean up partial clone dir
        import shutil
        if clone_dir.exists():
            shutil.rmtree(clone_dir)
        raise SystemExit(1)

    if args.as_json:
        _json_out({"cloned": repo_id, "path": str(clone_dir)})
    else:
        print(f"Cloned '{repo_id}' into {clone_dir}")


def _cmd_sync(args: argparse.Namespace) -> None:
    import subprocess

    root = _resolve_root(args)
    registry = _make_registry(root)
    repos = registry.list_repos(storage="managed")

    if args.repo_id:
        repos = [r for r in repos if r.repo_id == args.repo_id]
        if not repos:
            print(f"No managed repo '{args.repo_id}' found.", file=sys.stderr)
            raise SystemExit(1)

    if not repos:
        print("No managed repositories to sync.")
        return

    results = []
    for repo in repos:
        if not repo.local_path:
            continue
        repo_path = registry._config.project_root / repo.local_path
        if not repo_path.exists():
            results.append({"repo_id": repo.repo_id, "status": "missing"})
            continue
        try:
            subprocess.run(
                ["git", "-C", str(repo_path), "pull", "--ff-only"],
                check=True, capture_output=True, text=True,
            )
            results.append({"repo_id": repo.repo_id, "status": "synced"})
        except subprocess.CalledProcessError as exc:
            results.append({"repo_id": repo.repo_id, "status": "failed", "error": exc.stderr.strip()})

    if args.as_json:
        _json_out(results)
    else:
        for r in results:
            status = r["status"]
            if status == "synced":
                print(f"  {r['repo_id']}: synced")
            elif status == "missing":
                print(f"  {r['repo_id']}: local path missing")
            else:
                print(f"  {r['repo_id']}: failed — {r.get('error', '')}")


def _cmd_repos(args: argparse.Namespace) -> None:
    root = _resolve_root(args)
    registry = _make_registry(root)
    repos = registry.list_repos(storage=args.storage)

    if args.as_json:
        _json_out([r.model_dump() for r in repos])
        return
    if not repos:
        print("No repositories tracked.")
        return
    for r in repos:
        line = f"  {r.repo_id:<30s} storage={r.storage:<10s} path={r.local_path}"
        print(line)


def _guess_hosting(url: str) -> str:
    if "github.com" in url:
        return "github"
    if "gitlab" in url:
        return "gitlab"
    return "other"


def _today() -> str:
    from datetime import date
    return date.today().isoformat()


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def _cmd_rag(args: argparse.Namespace) -> None:
    from codio.rag import sync_codio_rag_sources
    root = _resolve_root(args)
    registry = _make_registry(root)
    try:
        result = sync_codio_rag_sources(
            root, config_path=args.config, force_init=args.force_init,
            catalog=registry._catalog,
        )
    except ImportError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
    print(f"Config: {result.config_path}")
    if result.created:
        print("  Created new indexio config")
    if result.added:
        print(f"  Added: {', '.join(result.added)}")
    if result.updated:
        print(f"  Updated: {', '.join(result.updated)}")
    if result.removed:
        print(f"  Removed: {', '.join(result.removed)}")
    if not result.added and not result.updated and not result.removed:
        print("  No changes needed")


_COMMANDS = {
    "init": _cmd_init,
    "list": _cmd_list,
    "get": _cmd_get,
    "validate": _cmd_validate,
    "vocab": _cmd_vocab,
    "discover": _cmd_discover,
    "study": _cmd_study,
    "compare": _cmd_compare,
    "add": _cmd_add,
    "add-urls": _cmd_add_urls,
    "attach": _cmd_attach,
    "clone": _cmd_clone,
    "sync": _cmd_sync,
    "repos": _cmd_repos,
    "rag": _cmd_rag,
}


def main(argv: Iterable[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command is None:
        parser.print_help()
        raise SystemExit(0)

    handler = _COMMANDS.get(args.command)
    if handler is None:
        parser.print_help()
        raise SystemExit(1)

    handler(args)
