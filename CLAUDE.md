# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Test Commands

```bash
make test              # run all tests (pytest, uses PYTHONPATH=src)
PYTHONPATH=src python -m pytest tests/test_codio.py -q          # single test file
PYTHONPATH=src python -m pytest tests/test_codio.py::test_import -q  # single test
make build             # build distribution
make clean             # remove build artifacts
```

Python ≥ 3.11 required. Package source lives in `src/codio/` (src-layout via setuptools).

## What Codio Is

Codio is a **standalone CLI tool and library** for code intelligence and reuse discovery. It is installed once and invoked inside any project — it is NOT a framework or a self-contained registry. It answers: "What code already exists that solves this problem?" before new implementation begins.

When you run `codio init` in a project, it scaffolds a `.codio/` directory with registry files. The CLI and MCP tools then operate on that project's registry.

### Ecosystem Siblings

Codio follows the same architectural patterns as its sibling tools:

| Tool | Purpose | Scaffolds | CLI entry |
|------|---------|-----------|-----------|
| **projio** | Project orchestration | `.projio/` | `projio init` |
| **biblio** | Bibliography/papers | `bib/` | `biblio init` |
| **indexio** | Semantic indexing/RAG | `infra/indexio/` | `indexio init-config` |
| **codio** | Code reuse discovery | `.codio/` | `codio init` |

All tools share: src-layout, argparse CLI, YAML configs, projio MCP integration.

## Architecture

### Two-Layer Registry Model

The core data model separates **library identity** (catalog) from **project-specific policy** (profile):

- **Library Catalog** (`.codio/catalog.yml`) — shared, project-agnostic metadata: name, kind, language, repo URL, package name, license, local path.
- **Project Profile** (`.codio/profiles.yml`) — local interpretation: priority tier, runtime import policy, decision default, capability tags, curated note path.

Profile entries must reference existing catalog keys.

### Controlled Vocabulary

Fields use controlled values (see `src/codio/vocab.py`):
- `kind`: `internal`, `external_mirror`, `utility`
- `runtime_import`: `internal`, `pip_only`, `reference_only`
- `decision_default`: `existing`, `wrap`, `direct`, `new`
- `priority`: `tier1`, `tier2`, etc.

### Layered Architecture (bottom to top)

1. **Physical code** — internal packages, utilities, mirrors, examples (in the target project)
2. **Library catalog** — identity metadata registry (`.codio/catalog.yml`)
3. **Project profile** — local policy layer (`.codio/profiles.yml`)
4. **Curated notes** — narrative guidance docs for important libraries (`docs/reference/codelib/libraries/`)
5. **Corpus search** — code/doc retrieval via indexio integration
6. **MCP tools** — structured machine interface, registered in projio's MCP server
7. **Agent skills** — `codelib-discovery`, `codelib-update`, `library-study`

### CLI Surface

```
codio init       — scaffold .codio/ in a target project
codio list       — filtered library listing
codio get        — single library full record
codio validate   — registry consistency checks
codio vocab      — show controlled vocabulary
codio discover   — search for libraries matching a capability
codio study      — structured analysis of a library
codio compare    — compare multiple libraries
codio rag sync   — register codio sources in indexio
```

### MCP Tool Surface

Five core tools exposed via projio's MCP server: `codio_list`, `codio_get`, `codio_registry`, `codio_vocab`, `codio_validate`. Plus `codio_discover` for capability search. Companion `rag_query` tools for corpus retrieval via indexio.

### Agent Skills

- `codelib-discovery` — search before implement; returns candidates with evidence and recommends a decision
- `codelib-update` — maintain registry and curated notes
- `library-study` — deep parallel analysis of external libraries

## Source Layout

```
src/codio/
├── __init__.py       # public API exports
├── cli.py            # argparse CLI (codio command)
├── config.py         # CodioConfig, load from .projio/config.yml
├── models.py         # Pydantic models (catalog, profile, record, snapshot)
├── vocab.py          # controlled vocabulary enums
├── registry.py       # Registry class (load, query, validate)
├── mcp.py            # MCP tool functions (called by projio MCP server)
├── scaffold.py       # init_codio_scaffold (templates → .codio/)
├── rag.py            # indexio source registration
├── templates/codio/  # YAML templates for scaffold
│   ├── catalog.yml.tmpl
│   └── profiles.yml.tmpl
└── skills/
    ├── discovery.py  # codelib-discovery skill
    ├── update.py     # codelib-update skill
    └── study.py      # library-study skill
```

## Project Context

This is a `projio`-managed workspace (see `.projio/config.yml`). Part of a broader ecosystem alongside `biblio` (papers), `notio` (notes), `indexio` (RAG), and `texio` (text retrieval). Specs live in `docs/specs/codio/`. Implementation prompts live in `docs/prompts/maintenance.md`.
