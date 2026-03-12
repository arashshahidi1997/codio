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
# Dispatch
# ---------------------------------------------------------------------------

def _cmd_rag(args: argparse.Namespace) -> None:
    from codio.rag import sync_codio_rag_sources
    root = _resolve_root(args)
    try:
        result = sync_codio_rag_sources(
            root, config_path=args.config, force_init=args.force_init,
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
