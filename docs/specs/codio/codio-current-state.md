# Codio Current State

## Purpose of this document

This document records what `codio` currently is, what it is not, and why a design/spec effort is needed now. It is grounded in the repository as it exists in M1 and avoids assuming future capabilities are already implemented.

## What codio currently is

Codio is currently a small Python package and CLI for project-local code reuse discovery.

The implemented center of gravity is a two-layer registry:

- `.codio/catalog.yml` stores identity metadata for libraries
- `.codio/profiles.yml` stores project-specific policy and capability tags

The package loads these YAML files, merges records, validates them, and exposes them through:

- an argparse CLI in `src/codio/cli.py`
- in-process MCP helper functions in `src/codio/mcp.py`
- a small set of skill-style helper modules in `src/codio/skills/`

Codio also scaffolds a default workspace layout and can register codio-owned sources into an `indexio` config via `codio rag sync`.

## What codio currently is not

Codio is not yet a general repository-ingestion system.

It does not currently implement:

- managed repository installation into a codio-owned library workspace
- attached-repository analysis for arbitrary external or internal repos
- a first-class repo entity with `repo_id` or slug-level identity distinct from library entries
- code crawling, parsing, or indexing logic inside codio itself
- retrieval over source trees inside this repository
- DataLad-backed ingestion or durable mirror management
- cross-project registry sharing beyond file-level portability of the YAML schema
- orchestration logic for broader ecosystem workflows

The current implementation is registry-centered, not repository-centered.

## Current repository structure

At a high level, the repository is organized as:

```text
src/codio/
  cli.py
  config.py
  models.py
  mcp.py
  paths.py
  rag.py
  registry.py
  scaffold.py
  vocab.py
  skills/
  templates/
tests/
docs/
  explanation/
  how-to/
  prompts/
  reference/
  specs/codio/
```

### Package and module structure

The Python package is compact and coherent:

- `src/codio/cli.py`: user-facing CLI with `init`, `list`, `get`, `validate`, `vocab`, `discover`, `study`, `compare`, and `rag sync`
- `src/codio/config.py`: default paths and optional `.projio/config.yml` overrides
- `src/codio/models.py`: Pydantic models for catalog entries, profile entries, merged records, validation results, and registry snapshots
- `src/codio/registry.py`: YAML loading, merge logic, filtering, and validation
- `src/codio/vocab.py`: controlled vocabularies for `kind`, `runtime_import`, `decision_default`, `priority`, and `status`
- `src/codio/scaffold.py`: `.codio/` scaffold creation from packaged templates
- `src/codio/rag.py`: `indexio` source registration for codio-owned notes and catalog files
- `src/codio/mcp.py`: JSON-shaped wrappers around registry operations
- `src/codio/paths.py`: project root detection via walk-up logic (`.codio/catalog.yml` > `.projio/config.yml` > `.git` > `pyproject.toml`)
- `src/codio/skills/`: light analysis/update helpers built on registry metadata

### CLI structure

The CLI is present and tested. It is a thin shell over the registry and skill helpers, not a heavy orchestration layer.

Implemented subcommands:

- `codio init`
- `codio list`
- `codio get`
- `codio validate`
- `codio vocab`
- `codio discover`
- `codio study`
- `codio compare`
- `codio rag sync`

### Documentation structure

The docs are already split by function:

- `docs/tutorials/`: onboarding
- `docs/how-to/`: task-oriented use
- `docs/explanation/`: design rationale for the current registry model
- `docs/reference/`: CLI/config/workspace reference
- `docs/specs/codio/`: higher-level concept and architecture docs
- `docs/prompts/`: generic implementation prompt material

This is a useful base for design work because it separates current user docs from more aspirational spec material.

## Current abstractions and evidence

### Code sources

Codio currently models code sources indirectly as library records. The main identity object is a library name, not a repository.

Evidence:

- `LibraryCatalogEntry` includes `name`, `kind`, `repo_url`, `path`, and summary metadata
- `Kind` distinguishes `internal`, `external_mirror`, and `utility`
- `Status` distinguishes `active`, `candidate`, and `deprecated` lifecycle states
- the workspace docs describe internal packages, utilities, and mirrors as tracked assets

Current implication:

- Codio can describe a code source at the library level
- Codio does not yet distinguish a repository from a package, module collection, or mirror

### Repo ingestion

There is no implemented repository ingestion workflow in codio today.

Closest related pieces:

- `codio init` scaffolds local registry files
- `codio rag sync` writes codio-owned source definitions into `indexio`
- `LibraryCatalogEntry.path` can point at local code or mirrors, but codio does not populate or manage those paths

Current implication:

- repository presence is assumed or manually registered
- codio does not install, mirror, attach, sync, or update repositories

### Indexing

Indexing is only present as an integration point, not as an internal subsystem.

Evidence:

- `src/codio/rag.py` defines codio-owned source definitions for `indexio`
- the RAG sync operation only registers:
  - the curated-notes glob
  - the catalog YAML file

Current implication:

- codio can tell `indexio` about some codio-owned metadata sources
- codio does not currently register source trees, mirror repos, or attached repos as first-class index targets
- there is no internal indexing state, schema, or refresh workflow in this repo

### Metadata and registries

This is codio's strongest implemented area.

Implemented concepts:

- controlled vocabulary for classification and policy
- stable catalog/profile separation
- merged `LibraryRecord` views
- validation for broken references and missing profile/catalog relationships
- YAML templates and scaffold behavior

This registry model is concrete, test-covered, and documented across code and docs.

### Search and retrieval

Search is currently shallow and metadata-driven.

Evidence:

- `discover()` matches on:
  - capability tags
  - library name substrings
  - summary substrings
- `study_library()` and `compare_libraries()` derive structured summaries from registry metadata

Current implication:

- codio supports structured discovery over declared metadata
- it does not yet perform semantic retrieval over code bodies, examples, tests, or note contents from within codio itself

### Integration points with other packages

The repo contains clear but narrow integration points:

- `.projio/config.yml` overrides are read by `load_config()`
- `codio rag sync` assumes `indexio.sync_owned_sources()`
- `docs/explanation/ecosystem-links.md` positions codio alongside sibling packages

Current implication:

- codio is aware of ecosystem context
- integration is currently loose and file/config based
- there is no deep dependency on `projio` internals in the implementation

## Current strengths

- The implemented scope is small, understandable, and test-covered.
- The registry model is explicit and already useful for project-local discovery.
- The CLI surface is coherent and aligned with the current implementation.
- The docs already distinguish explanation, reference, and spec material.
- The package avoids hard-coding a single programming language or package manager.
- The current code keeps policy metadata separate from identity metadata, which is a good basis for later cross-project use.

## Current limitations

- The core entity is still a library record rather than a repository or code source.
- `external_mirror` exists as a classification, but mirror lifecycle and storage are out of scope.
- Attached-repository analysis is not implemented.
- Codio-owned indexing is limited to notes and catalog metadata, not source trees.
- Discovery quality depends on manually curated capability tags and summaries.
- There is no canonical entity model for repo slug, source kind, workspace membership, or provenance.
- There is no documented library workspace layout for managed repositories.
- There is no ingestion specification for adding external repos or linking internal repos.

## Missing concepts that matter for redesign

The repository does not yet define several concepts that the future direction will require:

- `repo_id` or canonical repository slug
- distinction between repository, library, package, module, and note
- managed vs attached repository handling
- source ownership and storage policy
- provenance for how a code source entered codio
- sync/update policy for managed mirrors
- indexable units for code intelligence
- boundaries between codio metadata and external retrievers such as `indexio`

These are not implementation bugs. They are missing design concepts.

## Major design tensions

### Library-centric model vs repository-centric future

Current codio is optimized around library registry entries. The future direction described for the ecosystem requires codio to reason about repositories as first-class objects. A redesign has to decide whether libraries remain primary or become derived views over repository-backed sources.

### Project-local simplicity vs cross-project sharing

The current `.codio/` layout is simple and local. Cross-project reuse intelligence will require some metadata to remain portable while other metadata becomes workspace- or installation-specific.

### Lightweight metadata search vs real code intelligence

The current discovery flow is easy to maintain because it depends on YAML metadata. Semantic retrieval and source analysis will be more powerful, but they introduce ingestion cost, indexing rules, provenance questions, and update workflows.

### Codio-owned management vs analysis-in-place

The future managed/attached split is not represented in the current code. That distinction affects identity, storage layout, update semantics, and which subsystem owns physical repository state.

### Ecosystem integration vs codio autonomy

Codio already touches `.projio` config and `indexio`, but the implementation stays relatively independent. Future integration should preserve that modularity rather than turning codio into a thin wrapper around another package's internal assumptions.

## Architectural ambiguities in the current repo

- The word "library" currently covers several different things: internal packages, utility code, local code collections, and mirrored repositories.
- `path` exists on catalog entries, but the repo does not define whether it points to a package root, repo root, or arbitrary local folder.
- `repo_url` is available, but there is no rule for when it is descriptive metadata versus operational source-of-truth.
- `codio rag sync` suggests codio-owned sources, but the actual owned sources are only notes and catalog metadata, not code repositories.
- The specs in `docs/specs/codio/` describe a larger architecture than the code currently implements, but there is no explicit boundary document separating "current" from "target".

## Why a redesign/spec effort is needed now

Codio already has enough implementation to establish patterns, terminology, and constraints. It also now sits close to a broader ecosystem direction where repository ingestion, shared code libraries, and semantic retrieval matter.

Without a design pass, the next implementation steps would likely overload the existing library registry with repository-management concerns that it was not designed to carry. M1 is therefore needed to:

- document the actual starting point
- separate implemented behavior from intended architecture
- define missing entities before adding new runtime features
- clarify how managed and attached repositories should coexist
- keep codio modular as it integrates with `indexio`, `projio`, and shared workspace conventions

## M7 design-doc execution

The M7 prompt pack (`docs/prompts/m7/`) was executed against the M1 baseline to produce the following design documents:

- `docs/explanation/vision.md` — codio vision, scope, and design goals
- `docs/reference/entity-model.md` — entity definitions, canonical identifiers, ownership rules
- `docs/reference/library-layout.md` — managed-workspace layout specification
- `docs/reference/ingestion.md` — ingestion workflow, provenance, and sync rules
- `docs/explanation/code-intelligence.md` — code-intelligence boundary and indexing design
- `docs/explanation/cross-project-sharing.md` — shareable vs local metadata, sharing mechanisms
- `docs/specs/codio/codio-design-review.md` — updated coherence review

These documents are design artifacts, not implementation. They separate present capabilities from target design.

## Prompt-pack placement

Design prompts live under `docs/prompts/` following the repository's existing prompt convention. The M7 pack is at `docs/prompts/m7/`.
