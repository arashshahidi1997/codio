# Codio Vision

## What problem codio solves

Engineering projects accumulate reusable code across internal packages, utility modules, mirrored external libraries, and ad hoc scripts. Without a discovery layer, that prior art is invisible at decision time. Engineers reimplement existing solutions, adopt external dependencies without understanding project policy, or fail to notice that a curated wrapper already exists.

Codio is a standalone CLI tool and library that answers one question before implementation begins: **what code already exists that solves this problem?**

It is installed once and invoked inside any project. It does not require a specific language, package manager, or hosting platform. Its core data structure is a two-layer registry that separates library identity from project-specific policy, and its core workflow is structured discovery over that registry.

## Codio's role in the broader ecosystem

Codio is one of several sibling tools that share architectural patterns (src-layout, argparse CLI, YAML configs) but own distinct concerns:

| Tool | Concern | What it scaffolds |
|------|---------|-------------------|
| projio | Project orchestration and MCP server | `.projio/` |
| biblio | Bibliography and paper management | `bib/` |
| indexio | Semantic indexing and RAG retrieval | `infra/indexio/` |
| notio | Structured notes | project-specific |
| codio | Code reuse discovery | `.codio/` |

Codio's relationship to these siblings is integration, not dependency:

- **projio**: Codio reads optional overrides from `.projio/config.yml` and exposes MCP tools that projio's server can register. Codio does not depend on projio internals and must remain functional without it.
- **indexio**: Codio registers its own metadata sources (catalog YAML, curated notes) into indexio via `codio rag sync`. Codio does not implement indexing or retrieval internally; it delegates corpus search to indexio and consumes results.
- **biblio/notio**: No direct integration. Codio and these tools may coexist in the same project without interaction.

The guiding principle is that codio owns code-discovery concerns and delegates everything else. It should not become a thin wrapper around projio, nor should it duplicate indexio's retrieval capabilities.

## What codio should own

### Registry and metadata

Codio owns the two-layer registry model:

- **Library catalog** (`.codio/catalog.yml`): project-agnostic identity metadata including name, kind, language, repo URL, package name, license, local path, and summary.
- **Project profile** (`.codio/profiles.yml`): project-specific interpretation including priority tier, runtime import policy, decision default, capability tags, status, and curated note path.

This separation is codio's central design decision. The catalog describes what a library is. The profile describes how a specific project relates to that library. The same catalog entry should be reusable across projects; profiles are always local.

Codio also owns the controlled vocabulary that governs registry fields: `Kind`, `RuntimeImport`, `DecisionDefault`, `Priority`, and `Status`. These enums constrain metadata to values that support reliable filtering and machine consumption.

### Discovery workflow

Codio owns the discovery workflow: capability search, library inspection, structured comparison, and study. The current implementation (`discover`, `get`, `study`, `compare`) matches on capability tags, name substrings, and summary text against registry metadata. This is deliberately shallow -- curated metadata is more reliable than automated inference for engineering decisions, and shallow search keeps discovery cheap enough that people and agents actually use it.

### Scaffold and workspace layout

Codio owns the `.codio/` directory layout and the `codio init` scaffold that creates it. Future milestones may extend this to include a managed library workspace (a directory structure for code that codio installs, mirrors, or attaches). That workspace layout is not yet implemented, but codio is the correct owner because it is the tool that reasons about code source identity and location.

### Ingestion metadata

When codio gains repository ingestion capabilities (managed and attached modes, discussed below), it should own the ingestion metadata: provenance records, sync timestamps, source manifests, and update policies. This metadata describes how a code source entered the registry and how it stays current. It is distinct from the identity metadata in the catalog and the policy metadata in the profile.

### Code-intelligence boundary

Codio should own the boundary definition for code intelligence: what counts as an indexable unit, what metadata codio produces about code sources, and what queries codio can answer directly versus what it delegates to indexio. Codio should not implement its own full-text index or embedding store. It should define source manifests that external indexers consume, and it should interpret retrieval results in terms of its own entity model.

## What codio should NOT own

### Orchestration

Project-level orchestration -- task sequencing, multi-tool workflows, MCP server lifecycle -- belongs to projio. Codio exposes MCP tool functions that projio can register, but codio does not manage the server, route requests, or coordinate across tools.

### Runtime packaging

Codio records `pip_name` and `runtime_import` as metadata, but it does not install packages, manage virtual environments, or resolve dependency graphs. Those concerns belong to the project's package manager and build system.

### Full-text indexing internals

Codio delegates corpus search to indexio. It should not implement its own embedding pipeline, vector store, or chunk-and-retrieve logic. Codio's role is to define what sources exist and what metadata describes them; indexio's role is to make those sources searchable at the content level.

### Project configuration

Codio reads `.projio/config.yml` for optional path overrides, but it does not write to or manage that file. Project-level configuration (team settings, tool registration, workspace structure) belongs to projio or to the project itself.

### Repository hosting and mirroring infrastructure

Codio may record that a library is an `external_mirror` and point to a local path, but it should not implement git clone, DataLad get, or mirror synchronization as built-in subsystems. If codio gains managed-repository capabilities, the actual storage operations should be delegable to external tools (git, DataLad, etc.) rather than reimplemented inside codio.

## Design goals that constrain future milestones

These six goals are grounded in the current M1 implementation and should govern all subsequent design and implementation decisions.

### 1. Discovery-first engineering

Codio must make discovery the default step before implementation. The current `codio discover` command and the `codelib-discovery` agent skill already implement this pattern. Future capabilities (semantic search, repository-level analysis) must preserve the property that searching is cheaper than implementing.

Evidence from current implementation: `discover()` matches on capability tags, name substrings, and summary text. Results include priority and decision-default fields so that a user or agent can make an engineering decision without deep inspection. The `codelib-discovery` skill returns candidates with evidence and recommends a decision.

### 2. Agent usability

Codio must expose a stable, structured interface for AI agents. Agents default to implementation; they will write new code unless explicitly told to search first. Codio provides the structured query surface that makes "search before implement" a reliable agent behavior.

Evidence from current implementation: five MCP tools (`codio_list`, `codio_get`, `codio_registry`, `codio_vocab`, `codio_validate`) return JSON-shaped responses. The `discover` MCP tool supports capability search. Agent skills (`codelib-discovery`, `codelib-update`, `library-study`) wrap registry operations in structured workflows.

### 3. Reusable registry schema

The catalog/profile separation must remain stable. Catalog entries describe library identity and should be portable across projects. Profile entries describe project-specific policy and are always local.

Evidence from current implementation: `LibraryCatalogEntry` and `ProjectProfileEntry` are distinct Pydantic models. `LibraryRecord.from_entries()` merges them at query time. Validation checks that every profile key references an existing catalog key.

### 4. Project portability

Codio must work across repositories with different domains, language mixes, and dependency strategies. It must not assume Python, pip, or any single packaging system as the only target.

Evidence from current implementation: `language` is an explicit field rather than an assumed constant. `Kind` distinguishes internal, external_mirror, and utility without coupling to a specific package ecosystem. The scaffold templates are minimal YAML, not language-specific configuration.

### 5. Minimal maintenance burden

Registry updates and curated notes must be simple enough that teams keep them current. Only high-value metadata should be mandatory. Validation tooling should detect stale or broken references.

Evidence from current implementation: `codio validate` checks for broken profile-to-catalog references. Curated notes are optional (`curated_note` defaults to empty string). The controlled vocabulary constrains values to a small set, reducing ambiguity without requiring exhaustive documentation.

### 6. Reproducible knowledge

Codio should turn informal implementation memory into versioned, auditable project knowledge. A future user or agent should be able to reconstruct why a library was preferred, wrapped, or rejected.

Evidence from current implementation: `decision_default` records the standing engineering decision for each library-project pair. `status` tracks lifecycle state (active, candidate, deprecated). Registry files are plain YAML committed alongside project source, so they participate in version control.

## Present vs target capabilities

| Capability | Present (M1) | Target (future milestones) |
|------------|-------------|---------------------------|
| Library registry | Implemented: catalog + profile YAML, Pydantic models, merge logic, validation | Stable; extend with repo-level identity fields |
| CLI surface | Implemented: init, list, get, validate, vocab, discover, study, compare, rag sync | Add ingestion commands (add, attach, sync) |
| Controlled vocabulary | Implemented: Kind, RuntimeImport, DecisionDefault, Priority, Status | May extend Kind to cover repository vs. module vs. collection |
| Discovery | Implemented: keyword match on tags, names, summaries | Add semantic search via indexio delegation |
| MCP tools | Implemented: list, get, registry, vocab, validate, discover | Add ingestion and workspace-query tools |
| Agent skills | Implemented: discovery, study, update | Extend with ingestion-aware workflows |
| RAG integration | Implemented: registers notes and catalog as indexio sources | Register source trees, managed repos, attached repo metadata |
| Entity model | Library-centric; no distinct repository entity | Add repository as first-class entity; libraries become views over repositories |
| Managed repositories | Not implemented | Codio-owned workspace with installed/mirrored code sources |
| Attached repositories | Not implemented | Metadata-only link to repos that live elsewhere on disk |
| Ingestion workflow | Not implemented | Add, attach, sync, update commands with provenance tracking |
| Cross-project sharing | Not implemented; catalog is portable by schema but not by tooling | Shared catalog fragments, import/export, optional central registry |
| Code intelligence | Not implemented beyond metadata search | Source manifests, indexable-unit definitions, retrieval-to-entity mapping |
| Workspace layout | `.codio/` with catalog and profiles only | Extend to include `libs/` or equivalent for managed code sources |

## Why managed and attached repository modes matter

The current entity model is library-centric. A `LibraryCatalogEntry` has a `name`, a `kind`, and optional fields like `repo_url` and `path`. This works for a curated registry of known libraries, but it conflates several distinct concepts:

- A **repository** is a versioned collection of source code with a URL, branch state, and commit history.
- A **library** is a logical unit of reusable functionality, which may span part of a repository, an entire repository, or multiple repositories.
- A **mirror** is a local copy of an external repository, managed for offline access or controlled versioning.
- A **module** or **package** is a language-level unit within a repository.

The current model uses `Kind` (internal, external_mirror, utility) to partially distinguish these, but a single flat record cannot represent the relationship between a repository and the libraries it contains.

### Two modes of repository tracking

Future codio design distinguishes two modes for how codio relates to a code source:

**Managed mode**: Codio owns the physical presence of the code. It installs or mirrors a repository into a codio-controlled workspace directory (e.g., `.codio/mirrors/<repo_id>/`). Codio is responsible for the initial clone, update schedule, and storage layout. This mode is appropriate for external dependencies that the project wants to inspect, index, or reference locally.

**Attached mode**: The code already exists on disk, managed by some other tool or workflow. Codio only records metadata about it -- location, identity, provenance -- without taking ownership of the physical files. This mode is appropriate for internal packages, monorepo subdirectories, or repositories managed by DataLad or other version-control tooling.

### Why this distinction matters

The managed/attached distinction affects several design decisions:

1. **Identity**: Managed repositories need a canonical `repo_id` or slug that codio assigns. Attached repositories already have an identity in their host system; codio needs to reference it without creating a conflicting identifier.

2. **Storage**: Managed repositories require a workspace layout specification. Attached repositories require only a path reference, but that path must be validated and may be relative or absolute.

3. **Update semantics**: Managed repositories have an update policy (pull schedule, branch tracking, version pinning) that codio must define. Attached repositories update through their own mechanisms; codio only needs to detect staleness.

4. **Ingestion provenance**: Both modes need provenance records (how did this source enter codio, when, from where), but managed mode also needs storage provenance (where is the clone, what commit is checked out).

5. **Indexing scope**: Managed repositories are fully available for source-tree indexing. Attached repositories may or may not be available depending on disk state, network mounts, or DataLad annex status.

### What remains uncertain

Several questions about the managed/attached model are deliberately left open:

- Whether `repository` should become the primary entity, with libraries as derived views, or whether libraries and repositories should remain parallel entities with explicit relationships.
- Whether managed storage should use a flat directory under `.codio/mirrors/` or a more structured layout with namespace prefixes.
- Whether codio should implement clone/pull operations directly or always delegate to an external tool (git, DataLad, a project-specific script).
- How attached-repository paths should handle portability across machines where the absolute path differs.
- Whether a single code source can be both managed and attached in different projects simultaneously (the answer is likely yes, but the identity-resolution rules need design).

These are design questions, not implementation bugs. They require explicit decisions in future milestones (M2 for entity model, M3 for workspace layout and ingestion) before code is written.

## Summary

Codio is a code-discovery tool. Its current implementation is a registry-driven metadata system with a CLI, MCP tools, and agent skills. That implementation is small, coherent, and test-covered.

The path forward extends codio from a library registry into a repository-aware discovery platform, without abandoning the properties that make the current design useful: cheap search, structured metadata, catalog/profile separation, and ecosystem modularity. The managed/attached repository distinction is the key design concept that enables this extension. It has not been implemented, but understanding why it matters is necessary for all subsequent design and implementation work.
