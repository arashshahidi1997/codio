# Entity Model

This document defines the data entities in codio: what exists in the current
implementation, what is proposed to fill gaps identified during M1 review, and
how the entities relate to each other.

Throughout, **implemented** means the entity exists as a Pydantic model or
dataclass in `src/codio/` today. **Proposed** means the entity addresses a
concrete gap but has no model definition yet.

---

## 1. Current Entities

### 1.1 LibraryCatalogEntry

**File:** `src/codio/models.py`
**Storage:** `.codio/catalog.yml` under the `libraries:` key
**Purpose:** Shared, project-agnostic identity metadata for a code source.

| Field      | Type   | Default            | Description                              |
|------------|--------|--------------------|------------------------------------------|
| `name`     | `str`  | required           | Slug key; primary identifier             |
| `kind`     | `Kind` | required           | `internal`, `external_mirror`, `utility` |
| `language` | `str`  | `""`               | Dominant language                        |
| `repo_url` | `str`  | `""`               | Upstream repository URL                  |
| `pip_name` | `str`  | `""`               | Package manager name                     |
| `license`  | `str`  | `""`               | Software license                         |
| `path`     | `str`  | `""`               | Local path for internal code or mirrors  |
| `summary`  | `str`  | `""`               | Short description                        |

**Identity:** The `name` field is the primary key. It is a human-authored slug
(e.g. `scipy`, `internal-utils`, `pandas-mirror`). All other fields are
descriptive metadata.

**Known ambiguities:**

- `path` conflates package root, repository root, and arbitrary folder. There
  is no schema-level distinction.
- `repo_url` is informational. It is not used for cloning, syncing, or
  deduplication.
- There is no field for repository identity separate from library identity. A
  single repository may contain multiple libraries (monorepo), and a single
  library may be a subset of a repository (single package within a larger
  project).

### 1.2 ProjectProfileEntry

**File:** `src/codio/models.py`
**Storage:** `.codio/profiles.yml` under the `profiles:` key
**Purpose:** Project-local interpretation and policy for a cataloged library.

| Field              | Type              | Default              | Description                          |
|--------------------|-------------------|----------------------|--------------------------------------|
| `name`             | `str`             | required             | Must match a catalog key             |
| `priority`         | `Priority`        | `tier2`              | `tier1`, `tier2`, `tier3`            |
| `runtime_import`   | `RuntimeImport`   | `reference_only`     | `internal`, `pip_only`, `reference_only` |
| `decision_default` | `DecisionDefault` | `new`                | `existing`, `wrap`, `direct`, `new`  |
| `capabilities`     | `list[str]`       | `[]`                 | Free-form capability tags            |
| `curated_note`     | `str`             | `""`                 | Path to a curated note `.md` file    |
| `status`           | `Status`          | `active`             | `active`, `candidate`, `deprecated`  |
| `notes`            | `str`             | `""`                 | Short local comment                  |

**Constraint:** `name` must reference an existing catalog entry. The registry
validator enforces this (profile without catalog entry is an error).

### 1.3 LibraryRecord

**File:** `src/codio/models.py`
**Purpose:** Merged read-only view combining catalog and profile for a single
library. Not persisted; computed at query time by `Registry._merge()`.

Contains all fields from both `LibraryCatalogEntry` and `ProjectProfileEntry`,
plus:

| Field         | Type   | Description                                    |
|---------------|--------|------------------------------------------------|
| `has_profile` | `bool` | Whether a project profile was found for merging |

Constructed via `LibraryRecord.from_entries(catalog, profile)`.

### 1.4 RegistrySnapshot

**File:** `src/codio/models.py`
**Purpose:** Serializable payload containing the full registry state.

| Field       | Type                               | Description                       |
|-------------|-------------------------------------|-----------------------------------|
| `libraries` | `dict[str, LibraryCatalogEntry]`   | Catalog entries keyed by name     |
| `profiles`  | `dict[str, ProjectProfileEntry]`   | Profile entries keyed by name     |
| `version`   | `str`                              | Registry schema version (`0.1.0`) |

Returned by `Registry.snapshot()` and used by MCP tools (`codio_registry`).

### 1.5 ValidationResult

**File:** `src/codio/models.py`
**Purpose:** Output of `Registry.validate()`.

| Field      | Type         | Description              |
|------------|--------------|--------------------------|
| `valid`    | `bool`       | Pass/fail                |
| `errors`   | `list[str]`  | Blocking problems        |
| `warnings` | `list[str]`  | Non-blocking advisories  |

### 1.6 CodioConfig

**File:** `src/codio/config.py`
**Purpose:** Runtime configuration resolved from `.projio/config.yml`.

| Field           | Type   | Default                                  |
|-----------------|--------|------------------------------------------|
| `catalog_path`  | `Path` | `.codio/catalog.yml`                     |
| `profiles_path` | `Path` | `.codio/profiles.yml`                    |
| `notes_dir`     | `Path` | `docs/reference/codelib/libraries/`      |
| `project_root`  | `Path` | current working directory                |

### 1.7 CodioRagSyncResult

**File:** `src/codio/rag.py`
**Purpose:** Outcome of registering codio sources in indexio.

| Field         | Type            | Description                        |
|---------------|-----------------|------------------------------------|
| `config_path` | `Path`          | Path to indexio config file        |
| `created`     | `bool`          | Whether the config was created     |
| `initialized` | `bool`          | Whether indexio was initialized    |
| `added`       | `tuple[str,...]`| Source IDs added                   |
| `updated`     | `tuple[str,...]`| Source IDs updated                 |
| `removed`     | `tuple[str,...]`| Source IDs removed                 |

### 1.8 Controlled Vocabulary Enums

**File:** `src/codio/vocab.py`

All enums inherit from `StrEnum` and carry a `description` property.

| Enum              | Values                                         | Used by         |
|-------------------|-------------------------------------------------|-----------------|
| `Kind`            | `internal`, `external_mirror`, `utility`        | Catalog `kind`  |
| `RuntimeImport`   | `internal`, `pip_only`, `reference_only`        | Profile         |
| `DecisionDefault` | `existing`, `wrap`, `direct`, `new`             | Profile         |
| `Priority`        | `tier1`, `tier2`, `tier3`                       | Profile         |
| `Status`          | `active`, `candidate`, `deprecated`             | Profile         |

---

## 2. Proposed Entities

The following entities address gaps identified during the M1 review. None of
these exist in code today.

### 2.1 Repository

A first-class entity representing a version-controlled repository, distinct
from any library it contains.

| Field         | Type   | Description                                      |
|---------------|--------|--------------------------------------------------|
| `repo_id`     | `str`  | Canonical slug (e.g. `scipy/scipy`, `internal/utils`) |
| `url`         | `str`  | Clone URL (HTTPS or SSH)                         |
| `hosting`     | `str`  | `github`, `gitlab`, `local`, `other`             |
| `storage`     | `str`  | `managed`, `attached`, `external`                |
| `local_path`  | `str`  | Filesystem path when cloned locally              |
| `default_branch` | `str` | e.g. `main`, `master`                          |

**Rationale:** The current model conflates repository identity with library
identity. A repository may contain multiple importable libraries (monorepo), or
a library may be a subset of a repository (single package within a larger
project). Making repository a first-class entity allows:

- Deduplication: two catalog entries pointing to the same repo share one
  `repo_id`.
- Sync policy: managed mirrors have clone/pull semantics tied to the repo, not
  the library.
- Provenance: recording how a code source entered codio requires knowing where
  it came from at the repository level.

### 2.2 CodeSource

A unit of code within a repository that codio tracks for intelligence purposes.
This replaces the ambiguous `path` field on `LibraryCatalogEntry`.

| Field         | Type   | Description                                      |
|---------------|--------|--------------------------------------------------|
| `source_id`   | `str`  | Unique slug within the registry                  |
| `repo_id`     | `str`  | FK to Repository                                 |
| `subpath`     | `str`  | Path within the repository (e.g. `src/scipy/linalg`) |
| `source_type` | `str`  | `package`, `module`, `script`, `notebook`, `config` |
| `indexable`   | `bool` | Whether this source should be sent to indexio    |

**Rationale:** The current `path` field on catalog entries is a flat string
with no semantic type. CodeSource introduces a structured pointer: a named
sub-tree within a known repository. This makes it possible to:

- Register multiple indexable units from the same repository.
- Distinguish between a package root and an examples directory.
- Drive `codio rag sync` from explicit source definitions rather than
  convention.

### 2.3 IndexSource

An indexio registration record owned by codio. Partially implemented today
via `rag.py` constants (`codio-notes`, `codio-catalog`), but not modeled as a
data entity.

| Field        | Type   | Description                                       |
|--------------|--------|---------------------------------------------------|
| `source_id`  | `str`  | Indexio source identifier                         |
| `corpus`     | `str`  | Indexio corpus name (e.g. `codelib`)              |
| `origin`     | `str`  | What this indexes: `notes`, `catalog`, `code`     |
| `glob`       | `str`  | File glob for multi-file sources                  |
| `path`       | `str`  | Single file path for single-file sources          |

**Rationale:** Currently `rag.py` hard-codes two source definitions. As codio
tracks more code sources (per 2.2), the set of indexio registrations should be
derived from the entity model, not maintained as constants.

### 2.4 Provenance (metadata, not a standalone entity)

A set of fields recording how and when a catalog entry was added. Could be
attached to `LibraryCatalogEntry` or `Repository` rather than modeled as a
separate entity.

| Field          | Type   | Description                                    |
|----------------|--------|------------------------------------------------|
| `added_by`     | `str`  | `manual`, `discovery`, `import`                |
| `added_date`   | `str`  | ISO date                                       |
| `source_ref`   | `str`  | Discovery session ID, import file, or empty    |

---

## 3. Canonical Identifiers

The question of which identifiers are primary keys versus descriptive metadata
is central to the entity model.

### Current state

| Entity               | Primary key | Notes                                   |
|----------------------|-------------|-----------------------------------------|
| `LibraryCatalogEntry`| `name`      | Human-authored slug, globally unique within registry |
| `ProjectProfileEntry`| `name`      | FK to catalog `name`                    |
| `LibraryRecord`      | `name`      | Inherited from catalog                  |

All other identifiers (`repo_url`, `pip_name`, `path`) are metadata. None are
used for joins, lookups, or deduplication.

### Proposed state

| Entity       | Primary key  | Notes                                       |
|--------------|--------------|---------------------------------------------|
| `Repository` | `repo_id`    | Canonical slug; used for deduplication      |
| `CodeSource` | `source_id`  | Unique within registry; references `repo_id`|
| `IndexSource`| `source_id`  | Matches indexio's source identifier         |
| `Catalog`    | `name`       | Unchanged; gains optional FK to `repo_id`   |

**Should `repo_id` become the primary key for catalog entries?** No. A library
and a repository are different things. The library `name` remains the primary
key in the catalog. The `repo_id` becomes an optional foreign key linking a
library to its source repository. Libraries without a repository (e.g.
reference-only entries, conceptual groupings) remain valid.

**`repo_url` and `pip_name` remain metadata.** They are useful for display and
for humans, but they are not stable identifiers. URLs change when repositories
move. Package names can differ from library names (e.g. `scikit-learn` vs
`sklearn`). The `repo_id` slug is the stable canonical reference.

---

## 4. Entity Relationships

```
Repository (repo_id)
  |
  +--< CodeSource (source_id, repo_id)
  |      |
  |      +--- indexed by --> IndexSource (source_id)
  |
  +--< LibraryCatalogEntry (name, repo_id?)
           |
           +--< ProjectProfileEntry (name)
           |
           +--- merged into --> LibraryRecord (name)
           |
           +--- curated_note --> .md file on disk
```

Key relationships:

- **Catalog to Profile:** one-to-one. A profile's `name` must match a catalog
  entry. A catalog entry may exist without a profile (warned, not an error).
- **Catalog to Repository (proposed):** many-to-one. Multiple catalog entries
  may reference the same `repo_id` (e.g. different packages in a monorepo).
  The FK is optional; entries without a repository are valid.
- **Repository to CodeSource (proposed):** one-to-many. A repository contains
  one or more trackable code sources.
- **CodeSource to IndexSource (proposed):** one-to-one or one-to-zero. A code
  source may or may not be registered in indexio.
- **LibraryRecord:** derived, not stored. Always computed from catalog + profile
  at query time.

---

## 5. Ownership Rules

Codio distinguishes between data it owns (writes, validates, can modify) and
data it references (reads, links to, does not modify).

### Owned by codio

| Artifact                | Location                               | Writable |
|-------------------------|----------------------------------------|----------|
| Library catalog         | `.codio/catalog.yml`                   | Yes      |
| Project profiles        | `.codio/profiles.yml`                  | Yes      |
| Curated notes           | `docs/reference/codelib/libraries/*.md`| Yes      |
| Indexio source registrations | `infra/indexio/config.yaml` (codio-owned IDs only) | Yes |

### Referenced by codio

| Artifact                | Location                               | Access   |
|-------------------------|----------------------------------------|----------|
| Project config          | `.projio/config.yml`                   | Read     |
| Source code (internal)  | Varies per `path` field                | Read     |
| Upstream repositories   | Remote URLs per `repo_url`             | Read     |
| Indexio query results   | Via `indexio` API                       | Read     |

### Proposed ownership for new entities

- **Repository metadata:** Owned by codio. Stored in a new registry file
  (e.g. `.codio/repos.yml`) or as a section within `catalog.yml`.
- **CodeSource definitions:** Owned by codio. Derived from repository + catalog
  entries, or explicitly declared.
- **IndexSource registrations:** Owned by codio within the indexio config.
  The `sync_codio_rag_sources` function already uses an owned-source-ID
  pattern to avoid touching other tools' registrations.
- **Managed repository clones:** Filesystem artifacts owned by the target
  project (not by codio's registry). Codio records their location and sync
  policy but does not own the git state.

### Managed vs Attached Repositories

Two storage modes for repositories with local clones:

- **Managed:** Codio cloned this repository and is responsible for keeping it
  updated. The `storage` field is `managed`. Sync commands (`codio sync`) pull
  upstream changes. The local path is deterministic (e.g.
  `.codio/mirrors/<repo_id>/`).
- **Attached:** The repository already exists on the filesystem (e.g. a sibling
  project, a git submodule, a manually cloned directory). Codio records the
  path but does not clone or pull. The `storage` field is `attached`.
- **External:** No local clone. Codio has metadata only. The `storage` field is
  `external`.

---

## 6. Derived Views

These are not persisted entities. They are computed from the registry at
query time.

### 6.1 LibraryRecord (implemented)

Merge of catalog + profile. Used by `codio get` and `codio list`. See
section 1.3.

### 6.2 Filtered Library List (implemented)

`Registry.list()` accepts filters: `kind`, `language`, `capability`,
`priority`, `runtime_import`. Returns `list[LibraryRecord]`.

### 6.3 Discovery Candidates (partially implemented)

`codio discover` searches for libraries matching a capability query. The
current implementation filters by capability tags on profiles. Proposed
enhancement: also search curated notes and code sources via indexio corpus
queries, returning ranked candidates with evidence snippets.

### 6.4 Registry Snapshot (implemented)

`RegistrySnapshot` containing all catalog entries and profiles. Used by the
`codio_registry` MCP tool for bulk export.

### 6.5 Validation Report (implemented)

`ValidationResult` with errors and warnings. Checks: orphan profiles, invalid
vocab values, missing curated note files, catalog entries without profiles.

### 6.6 Proposed: Repository Summary

Aggregate view grouping all catalog entries by `repo_id`. Would show which
libraries come from the same repository, their collective status, and sync
state for managed mirrors.

### 6.7 Proposed: Index Coverage Report

Which code sources are registered in indexio and which are not. Derived from
cross-referencing CodeSource entities with IndexSource registrations.

---

## 7. Open Questions

These items require resolution in later milestones.

1. **Repository storage location.** Should repository metadata live in a
   separate `.codio/repos.yml` file, or as a new top-level section in
   `catalog.yml`? A separate file avoids schema migration but adds another
   file to manage.

2. **CodeSource granularity.** Is the right unit a Python package, a directory
   tree, a single module, or a file glob? Different use cases (indexing,
   discovery, import analysis) may need different granularities.

3. **Slug conventions for `repo_id`.** Should it follow GitHub's `owner/repo`
   convention, or use a flat namespace? Flat slugs are simpler but risk
   collision. Namespaced slugs require a hosting-provider convention for
   local-only repositories.

4. **Provenance tracking scope.** Should provenance be recorded for every
   catalog entry, or only for entries added via automated discovery? Manual
   entries have implicit provenance (the author), so formal tracking may add
   overhead without value.

5. **Sync policy model.** Managed mirrors need a sync policy: frequency,
   branch tracking, conflict resolution. This may warrant its own entity or
   may be fields on Repository. The design depends on whether codio will
   invoke git operations directly or delegate to an external tool.

6. **Multi-project catalog sharing.** The current model assumes one catalog per
   project. If multiple projects share a catalog (e.g. via a git submodule or
   symlink), the profile layer still varies per project, but the catalog
   identity semantics change. This affects whether `repo_id` uniqueness is
   per-catalog or global.

7. **Capability taxonomy.** Capabilities are currently free-form strings on
   profiles. As discovery improves, a controlled vocabulary or hierarchical
   taxonomy for capabilities may be needed. This interacts with indexio's
   corpus structure.

8. **Version pinning.** Neither catalog nor profile tracks which version of a
   library is in use. For managed mirrors this is implicit (whatever is
   cloned). For pip-installed libraries, the version comes from
   `requirements.txt` or `pyproject.toml`, not from codio. Whether codio
   should record version information or defer to existing package management
   tools is an open question.
