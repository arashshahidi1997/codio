# Codio Implementation Plan

## Overview

Implement the Codio subsystem as a Python package (`src/codio/`) following the spec in `docs/specs/codio/`. The implementation is split into four phases, with Phase 1 as the foundation and Phases 2-3 parallelizable on top of it.

---

## Phase 1: Core Data Models & Registry (foundation — must complete first)

### 1A: Controlled Vocabulary (`src/codio/vocab.py`)
- Define enums/literals for `kind`, `runtime_import`, `decision_default`, `priority`, `status`
- Provide a `get_vocab()` function returning all allowed values with descriptions

### 1B: Data Models (`src/codio/models.py`)
- `LibraryCatalogEntry` — Pydantic model for catalog identity: name, kind, repo_url, language, pip_name, license, path, summary
- `ProjectProfileEntry` — Pydantic model for project profile: priority, runtime_import, decision_default, curated_note, capabilities, status, notes
- `LibraryRecord` — merged view combining catalog + profile for a single library
- `RegistrySnapshot` — full registry payload (all catalogs + profiles + metadata)

### 1C: Registry Loader (`src/codio/registry.py`)
- `load_catalog(path)` — parse YAML catalog file into dict of `LibraryCatalogEntry`
- `load_profiles(path)` — parse YAML profiles file into dict of `ProjectProfileEntry`
- `Registry` class — holds loaded catalog + profiles, provides:
  - `list(filters)` — filtered library listing
  - `get(name)` — single merged record
  - `snapshot()` — full registry payload
  - `validate()` — consistency checks (missing refs, bad vocab, broken note paths)

### 1D: Default Registry Paths & Config (`src/codio/config.py`)
- Default paths for catalog and profile YAML files
- Configuration loading from `.projio/config.yml` if present

**Dependencies:** PyYAML, Pydantic

---

## Phase 2: MCP Tools (parallelizable after Phase 1)

### `src/codio/mcp.py`
Implement MCP tool functions that wrap the Registry:

| Tool | Function | Description |
|------|----------|-------------|
| `codio_list` | `mcp_list(filters)` | Filtered library listing |
| `codio_get` | `mcp_get(name)` | Full merged record for one library |
| `codio_registry` | `mcp_registry()` | Full registry snapshot |
| `codio_vocab` | `mcp_vocab()` | Controlled vocabulary dump |
| `codio_validate` | `mcp_validate()` | Registry consistency validation |

Each function returns structured dict/JSON output suitable for agent consumption.

---

## Phase 3: Agent Skills (parallelizable after Phase 1)

Three skill modules, each independent:

### 3A: `src/codio/skills/discovery.py` — `codelib-discovery`
- `discover(query, registry)` — translate capability query into filtered registry search
- Return ranked candidates with evidence summary and recommended decision

### 3B: `src/codio/skills/update.py` — `codelib-update`
- `add_library(catalog_entry, profile_entry, registry)` — add/update catalog + profile
- `refresh_note(name, registry)` — validate/refresh curated note reference
- `validate_registry(registry)` — wrapper around registry validate

### 3C: `src/codio/skills/study.py` — `library-study`
- `study_library(name, registry, sources)` — structured analysis of a single library
- `compare_libraries(names, registry)` — comparative summary across candidates
- Output: capability summary, entry points, caveats, integration notes

---

## Phase 4: Tests

### `tests/test_vocab.py` — vocabulary enum coverage
### `tests/test_models.py` — model creation, validation, serialization
### `tests/test_registry.py` — loading, filtering, merging, validation
### `tests/test_mcp.py` — MCP tool outputs
### `tests/test_skills.py` — skill functions with fixture registries

---

## Dependency Additions to `pyproject.toml`

```toml
dependencies = ["pyyaml>=6.0", "pydantic>=2.0"]
```

---

## File Tree (new files)

```
src/codio/
├── __init__.py          (update: re-export public API)
├── vocab.py             (Phase 1A)
├── models.py            (Phase 1B)
├── registry.py          (Phase 1C)
├── config.py            (Phase 1D)
├── mcp.py               (Phase 2)
└── skills/
    ├── __init__.py       (Phase 3)
    ├── discovery.py      (Phase 3A)
    ├── update.py         (Phase 3B)
    └── study.py          (Phase 3C)
tests/
├── test_codio.py        (existing)
├── conftest.py          (shared fixtures)
├── test_vocab.py        (Phase 4)
├── test_models.py       (Phase 4)
├── test_registry.py     (Phase 4)
├── test_mcp.py          (Phase 4)
└── test_skills.py       (Phase 4)
```

## Parallelization Strategy

- **Phase 1A + 1D** can run in parallel (no interdependency)
- **Phase 1B** depends on 1A (models use vocab enums)
- **Phase 1C** depends on 1B (registry uses models)
- **Phase 2 and Phase 3 (all three skills)** can run in parallel once Phase 1 is complete — that's **4 parallel agents**
- **Phase 4 tests** can be split per-module and run in parallel
