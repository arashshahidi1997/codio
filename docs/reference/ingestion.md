# Ingestion

This document defines how libraries and their source material enter codio's
registry.  It covers the current state (manual editing), the proposed ingestion
workflows for managed and attached repositories, the metadata artifacts each
workflow produces, and the failure modes to handle.

Throughout, **implemented** means behavior that exists in `src/codio/` today.
**Proposed** means a concrete design that has no code yet.

---

## 1. Current State (Implemented)

Codio has no ingestion workflow.  Libraries enter the registry through manual
YAML editing or programmatic calls to `skills/update.py`.

### Manual editing

A user adds a library by writing entries directly into two YAML files:

1. Add a keyed block to `.codio/catalog.yml` under `libraries:`.
2. Optionally add a matching block to `.codio/profiles.yml` under `profiles:`.
3. Run `codio validate` to check consistency.

There is no schema migration, no import command, and no guided wizard.
The user must know the controlled vocabulary values (`kind`, `priority`,
`runtime_import`, etc.) or consult `codio vocab`.

### Programmatic editing via `skills/update.py`

Three functions manipulate the registry from Python code:

- `add_library(registry, catalog_entry, profile_entry)` — inserts or
  overwrites a catalog entry and optional profile, then writes both YAML
  files to disk.
- `remove_library(registry, name)` — deletes a library from both catalog and
  profiles, writes to disk.
- `update_profile(registry, profile_entry)` — updates a profile for an
  existing catalog entry.

These functions are used by the `codelib-update` agent skill.  They operate
on in-memory `Registry` state and flush to YAML.  They do not clone
repositories, register indexio sources, or create curated notes.

### `codio init`

Scaffolds an empty `.codio/` directory with template `catalog.yml` and
`profiles.yml` files, plus the curated notes directory.  This creates the
registry structure but does not populate it with any library entries.

### `codio rag sync`

Registers two codio-owned sources with indexio: `codio-notes` (curated
Markdown files) and `codio-catalog` (the catalog YAML).  This is a
post-ingestion step — it makes existing registry content searchable but does
not add new libraries.  Source code trees are not registered.

### What is missing

- No command to add a library from a URL, package name, or local path.
- No repository cloning or management.
- No automatic indexio source registration when a library is added.
- No provenance tracking (when, how, or by whom an entry was created).
- No batch import from requirements files, lockfiles, or other manifests.

---

## 2. Workflow Stages

Ingestion follows a staged pipeline.  The stages differ based on storage
mode: **managed** (codio clones the repository), **attached** (codio records
an existing path), or **external** (metadata only, no local files).

### 2.1 Managed Repository Ingestion

A managed repository is one that codio clones into `.codio/mirrors/<repo_id>/`
and keeps synchronized with upstream.

**Stage 1: Discover.**  The user identifies a library to add.  This may come
from `codio discover`, from an agent's `codelib-discovery` skill, or from
direct user knowledge.  The inputs are: a repository URL, and optionally a
package name, subpath, and library slug.

**Stage 2: Register metadata.**  Create entries in the registry files:

- Add a `Repository` entry to `.codio/repos.yml` with `storage: managed`,
  the clone URL, hosting provider, and derived `repo_id` slug.
- Add a `LibraryCatalogEntry` to `.codio/catalog.yml` with the library slug,
  kind, language, repo URL, and a `repo_id` foreign key.
- Optionally add a `ProjectProfileEntry` to `.codio/profiles.yml` with
  initial priority, runtime import policy, and capabilities.

At this point the registry is consistent but the repository is not yet
cloned.  Validation will warn about the missing local path.

**Stage 3: Clone.**  Clone the repository into `.codio/mirrors/<repo_id>/`.
The clone target is deterministic: `<project_root>/.codio/mirrors/<repo_id>`.
Update the `Repository` entry's `local_path` field.  Update the catalog
entry's `path` field to point at the relevant subtree within the clone.

Clone options (shallow vs full, sparse checkout) are per-repository policy
decisions.  The default should be a shallow clone (`--depth 1`) to minimize
disk usage.  Full history can be fetched later if needed.

**Stage 4: Record code sources.**  Identify indexable subtrees within the
cloned repository.  For each relevant subtree (package root, examples
directory, test directory), create a proposed `CodeSource` entry linking
the `repo_id` to a subpath.

In the initial implementation, this step can be skipped — the catalog
entry's `path` field is sufficient to identify one source tree per library.
Explicit `CodeSource` entities are a future refinement.

**Stage 5: Register in indexio.**  Extend `owned_codio_sources()` in
`rag.py` to include source trees from libraries with local paths.  The
source ID follows the pattern `codio-src-{library_name}`.  Run
`sync_codio_rag_sources()` to register the new sources.

This step is optional and requires indexio to be installed.  Ingestion
should succeed without it.

### 2.2 Attached Repository Registration

An attached repository already exists on the filesystem.  Codio records its
location but does not clone or modify it.

**Stage 1: Discover.**  Same as managed.  The key difference is the user
provides a local filesystem path instead of (or in addition to) a URL.

**Stage 2: Register metadata.**  Create entries in the registry files:

- Add a `Repository` entry to `.codio/repos.yml` with `storage: attached`,
  the local path, and optionally a remote URL.
- Add a `LibraryCatalogEntry` to `.codio/catalog.yml`.
- Optionally add a `ProjectProfileEntry`.

**Stage 3: Record path.**  Verify the local path exists and is accessible.
Record it in the `Repository` entry's `local_path` field and the catalog
entry's `path` field.  No cloning occurs.

If the path does not exist, the ingestion can still proceed (metadata is
recorded) but validation will produce a warning.

**Stage 4: Record code sources.**  Same as managed stage 4.  Identify
indexable subtrees within the attached repository.

**Stage 5: Register in indexio.**  Same as managed stage 5.

### 2.3 External (Metadata-Only) Registration

For libraries where no local code is needed — reference-only entries,
libraries available only via pip, or entries added for tracking purposes.

**Stage 1: Discover.**  User provides a library name and optionally a
package name, repo URL, or other metadata.

**Stage 2: Register metadata.**  Add catalog and profile entries.  No
`Repository` entry is required unless the user wants to record a remote
URL for future cloning.

There are no stages 3-5.  No local path, no code sources, no indexio
registration beyond the existing `codio-catalog` source.

### 2.4 Stage Summary

| Stage              | Managed              | Attached             | External    |
|--------------------|----------------------|----------------------|-------------|
| Discover           | URL + optional slug  | Local path + slug    | Slug + metadata |
| Register metadata  | repos.yml + catalog  | repos.yml + catalog  | catalog only |
| Clone / record path| `git clone` to mirrors | Verify path exists | None        |
| Record code sources| Identify subtrees    | Identify subtrees    | None        |
| Register in indexio| `codio-src-{name}`   | `codio-src-{name}`   | None        |

---

## 3. Metadata Artifacts

Each ingestion run creates or modifies the following files.

### 3.1 `.codio/catalog.yml`

A new entry under the `libraries:` key.  Required fields: `name`, `kind`.
Optional but recommended: `language`, `repo_url`, `pip_name`, `summary`,
`path`.

```yaml
libraries:
  scipy-linalg:
    kind: external_mirror
    language: python
    repo_url: https://github.com/scipy/scipy
    pip_name: scipy
    path: .codio/mirrors/scipy--scipy/scipy/linalg
    summary: Linear algebra routines from SciPy
```

### 3.2 `.codio/profiles.yml`

An optional entry under the `profiles:` key.  If omitted during ingestion,
validation will warn but the registry remains functional.  Default values
from the model apply (`priority: tier2`, `runtime_import: reference_only`,
`decision_default: new`, `status: active`).

```yaml
profiles:
  scipy-linalg:
    priority: tier1
    runtime_import: pip_only
    decision_default: existing
    capabilities:
      - linear-algebra
      - matrix-decomposition
```

### 3.3 `.codio/repos.yml` (proposed)

A new entry under the `repositories:` key.  Created only for managed and
attached storage modes.

```yaml
repositories:
  scipy--scipy:
    repo_id: scipy--scipy
    url: https://github.com/scipy/scipy.git
    hosting: github
    storage: managed
    local_path: .codio/mirrors/scipy--scipy
    default_branch: main
```

### 3.4 `.codio/mirrors/<repo_id>/` (managed only)

The cloned repository directory.  Codio owns this directory and may delete
and re-clone it.  Should be added to `.gitignore`.

### 3.5 Indexio source registration

When `codio rag sync` runs after ingestion, new source descriptors are
passed to `indexio.sync_owned_sources()`.  No new file is created by codio;
the indexio config file (`infra/indexio/config.yaml`) is updated by indexio's
own sync mechanism.

The new source descriptor for a library with a local path:

```python
{
    "id": "codio-src-scipy-linalg",
    "corpus": "codelib",
    "glob": ".codio/mirrors/scipy--scipy/scipy/linalg/**/*.py",
}
```

---

## 4. Provenance Rules

Ingestion should record how and when each entry was added, so that
maintenance operations (audit, cleanup, re-import) have context.

### 4.1 Provenance fields (proposed)

Three fields on `LibraryCatalogEntry` (or attached as a separate metadata
block):

| Field        | Type   | Values                              |
|--------------|--------|-------------------------------------|
| `added_by`   | `str`  | `manual`, `discovery`, `import`     |
| `added_date` | `str`  | ISO 8601 date (e.g. `2026-03-15`)   |
| `source_ref` | `str`  | Discovery session ID, import file path, or empty |

### 4.2 When provenance is recorded

- **Manual editing:** `added_by: manual`.  If the user edits YAML directly,
  provenance fields are optional.  The `add_library()` function should set
  `added_by: manual` and `added_date` to the current date when no provenance
  is provided.
- **Discovery workflow:** `added_by: discovery`.  When `codelib-discovery`
  identifies a candidate and the user confirms addition, `source_ref`
  records the query or session context.
- **Batch import:** `added_by: import`.  When importing from a requirements
  file or another registry, `source_ref` records the source file path.

### 4.3 Provenance is append-only

Provenance records the original addition.  Subsequent updates (changing
priority, adding capabilities, updating the path) do not modify provenance
fields.  If a library is removed and re-added, it gets new provenance.

### 4.4 Provenance is optional

Existing registries without provenance fields remain valid.  The fields
have empty-string defaults.  Validation does not require provenance.

---

## 5. Update and Sync Expectations

After initial ingestion, libraries need periodic maintenance.  The sync
behavior depends on storage mode.

### 5.1 Managed repositories

**What happens:** `codio sync` (or a future `codio update`) runs
`git pull` (or `git fetch` + reset for shallow clones) inside
`.codio/mirrors/<repo_id>/`.

**When to sync:** On-demand only.  Codio does not run background sync or
scheduled pulls.  The user or an agent invokes sync explicitly.

**After sync:**
- The local clone reflects the upstream state.
- If the library's `path` points to a subtree that no longer exists upstream,
  validation warns.
- If indexio sources are registered, `codio rag sync` should be re-run to
  trigger re-indexing of changed files.  Codio does not call indexio
  automatically after a git pull.

**What codio records:** The `Repository` entry does not track sync
timestamps or commit hashes.  The git repository itself is the source of
truth for its state (`git log`, `git rev-parse HEAD`).

### 5.2 Attached repositories

**What happens:** Codio re-validates that the recorded `local_path` exists
and is accessible.  Codio does not pull, fetch, or modify the repository.

**When to re-scan:** On `codio validate` or explicitly via a future
`codio check-paths` command.

**After re-scan:**
- If the path no longer exists, validation produces a warning.
- If source trees have changed (files added or removed), `codio rag sync`
  should be re-run to update indexio registrations.
- Codio does not detect file-level changes.  It only checks path existence.

### 5.3 External (metadata-only)

**What happens:** No filesystem operations.  The user manually updates
catalog fields (repo URL, pip name, summary) as needed.

**When to refresh:** Whenever the user or an agent updates the entry via
`add_library()` or direct YAML editing.

### 5.4 Indexio re-registration

After any sync or update that changes local paths or source trees, the user
should run `codio rag sync` to re-register sources with indexio.  Indexio
handles re-indexing based on file modification timestamps.

Codio does not track whether indexio sources are stale.  The responsibility
boundary is: codio registers sources, indexio manages indexes.

---

## 6. Failure Cases

### 6.1 Clone failure (managed)

**Cause:** Network error, invalid URL, authentication failure, disk full.

**Behavior:** The `Repository` entry in `repos.yml` is written before the
clone attempt (stage 2 completes before stage 3).  If the clone fails:

- The `local_path` field is either empty or points to a non-existent
  directory.
- The catalog entry exists with metadata but no usable local path.
- Validation warns about the missing path.
- No indexio sources are registered for this library.

**Recovery:** The user can retry the clone.  The metadata entries do not need
to be recreated.  If the clone directory was partially created, codio should
delete it before retrying.

### 6.2 Path not found (attached)

**Cause:** The user provided a path that does not exist, or the path was
valid at registration time but was later moved or deleted.

**Behavior:**
- The catalog and repos entries are written with the recorded path.
- Validation warns that the path does not exist.
- No indexio sources are registered for nonexistent paths.

**Recovery:** The user updates the `local_path` in `repos.yml` and the
`path` in `catalog.yml` to the correct location.

### 6.3 Partial ingestion

**Cause:** An error occurs mid-pipeline — for example, the catalog entry is
written but the profile write fails (disk error, permission issue).

**Behavior:** Codio's YAML writes are not transactional.  If `catalog.yml`
is written but `profiles.yml` is not, the registry is in a valid but
incomplete state (catalog entry without a profile produces a validation
warning, not an error).

**Cleanup:** Run `codio validate` to identify inconsistencies.  Use
`remove_library()` to cleanly remove a partially-ingested entry, or
complete the ingestion by adding the missing profile.

### 6.4 Duplicate entry

**Cause:** The user attempts to add a library with a `name` that already
exists in the catalog.

**Behavior:** `add_library()` overwrites the existing entry.  This is
intentional — it allows updates.  However, it means accidental name
collisions silently replace data.

**Mitigation:** A future ingestion command should check for existing entries
and prompt for confirmation before overwriting.  The current `add_library()`
function does not have this guard.

### 6.5 `repo_id` collision

**Cause:** Two different repositories produce the same `repo_id` slug
(unlikely with the `<owner>--<repo>` convention, but possible with manual
slugs).

**Behavior:** The second `repos.yml` entry overwrites the first.  This
may cause one library to point at the wrong repository.

**Mitigation:** Validate `repo_id` uniqueness during ingestion.  The
registry validator should check that each `repo_id` in `repos.yml`
appears at most once.

### 6.6 Indexio not installed

**Cause:** `codio rag sync` is called but the `indexio` package is not
available.

**Behavior:** `sync_codio_rag_sources()` raises `ImportError` with a
message directing the user to install indexio.

**Impact on ingestion:** Stages 1-4 succeed.  Only stage 5 (indexio
registration) fails.  The library is fully registered in codio's own
metadata; it is just not searchable via corpus retrieval.

---

## 7. Explicit Non-Goals for First Implementation

The initial ingestion implementation should be minimal and focused.  The
following are explicitly deferred.

### No dependency resolution

Codio does not parse `requirements.txt`, `pyproject.toml`, `setup.cfg`, or
lockfiles to discover transitive dependencies.  If a library depends on
other libraries, those are separate ingestion actions.

### No language-specific analysis

Codio does not run AST parsers, type checkers, or language-specific
analyzers during ingestion.  It does not extract function signatures, class
hierarchies, or import graphs.  Source trees are registered as file globs;
any language-aware processing belongs to indexio's chunking layer.

### No automatic capability tagging

Ingested libraries receive empty capability lists by default.  Codio does
not infer capabilities from code, documentation, or package metadata.
Capability tags are added manually or by agent skills after ingestion.

### No DataLad requirement

The ingestion workflow uses plain `git clone` and `git pull` for managed
repositories.  DataLad is not required, invoked, or assumed.  Projects
that use DataLad can integrate managed mirrors as subdatasets through their
own DataLad workflows, but codio does not manage that integration.

### No batch import from package managers

There is no `codio import-requirements` command.  Importing all libraries
from a requirements file is a future feature that builds on the single-
library ingestion pipeline.

### No automatic re-indexing

Cloning or syncing a managed repository does not automatically trigger
indexio re-indexing.  The user must run `codio rag sync` separately.
Automatic chaining of ingestion and indexing is a future convenience.

### No conflict resolution for managed mirrors

If a managed clone has local modifications (which should not happen under
the full-ownership model), `git pull` may fail with merge conflicts.  The
first implementation does not handle this — the recommended recovery is
to delete the mirror directory and re-clone.

### No multi-project catalog sharing

Ingestion operates on a single project's `.codio/` directory.  Sharing
catalog entries across projects (via symlinks, git submodules, or a central
registry) is out of scope.

---

## 8. Integration Points

### With projio

Projio can invoke codio ingestion via the `codio` CLI or by calling
`add_library()` directly.  Projio does not need to understand codio's
internal metadata format — it passes through a library slug and minimal
metadata, and codio handles the rest.

### With indexio

Codio produces source descriptors; indexio consumes them.  The contract is
`indexio.sync_owned_sources()`.  Ingestion extends the set of owned sources
but does not change the contract.

### With agent skills

The `codelib-discovery` skill may trigger ingestion when it identifies a
candidate library that is not yet in the registry.  The `codelib-update`
skill already uses `add_library()` and can be extended to invoke the full
ingestion pipeline (clone, record sources, register in indexio) rather than
just metadata insertion.

### With external tools

Any tool that can construct a `LibraryCatalogEntry` and call `add_library()`
can integrate with codio's ingestion.  The entry point is the Python API
in `skills/update.py`, not the CLI.  A future CLI command (`codio add`)
would wrap this API with argument parsing and interactive prompts.
