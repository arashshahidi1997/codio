# Library Workspace Layout

This document defines the on-disk layout that codio owns, both as implemented
today and as proposed for managed library workspaces. It is a reference
specification, not a tutorial.

Throughout, **implemented** means the behavior exists in `src/codio/` today.
**Proposed** means the layout addresses a concrete gap but has no code yet.

---

## 1. Current Layout (Implemented)

Running `codio init` in a project root creates the following:

```text
<project_root>/
  .codio/
    catalog.yml          # library identity metadata (LibraryCatalogEntry)
    profiles.yml         # project-specific policy (ProjectProfileEntry)
  docs/
    reference/
      codelib/
        libraries/       # curated note markdown files
```

### What each artifact is

| Path | Owner | Purpose |
|------|-------|---------|
| `.codio/catalog.yml` | codio | YAML dict under `libraries:` key. Each entry is a `LibraryCatalogEntry` keyed by library slug. |
| `.codio/profiles.yml` | codio | YAML dict under `profiles:` key. Each entry is a `ProjectProfileEntry` keyed by library slug. |
| `docs/reference/codelib/libraries/` | codio | Directory for curated note files. Profile entries reference these via `curated_note` field. |

### Configuration

All three paths are configurable via `.projio/config.yml` under the `codio`
section (see `src/codio/config.py`):

```yaml
# .projio/config.yml
codio:
  catalog_path: .codio/catalog.yml      # default
  profiles_path: .codio/profiles.yml    # default
  notes_dir: docs/reference/codelib/libraries/  # default
```

Paths are resolved relative to `project_root` (the directory containing
`.projio/` or the current working directory).

### What codio does not own today

Codio reads but does not own:

- `.projio/config.yml` — owned by projio.
- `infra/indexio/config.yaml` — codio writes its own source IDs
  (`codio-notes`, `codio-catalog`) but the file is shared with other tools.
- Source code directories referenced by catalog `path` fields — codio records
  the path but does not create, clone, or modify the code.

This is the complete set of codio-owned filesystem artifacts as of the current
implementation.

---

## 2. Candidate Managed-Workspace Layout (Proposed)

When codio manages a local clone of an external repository (storage mode
`managed` per the proposed Repository entity), it needs a deterministic
location for that clone. The proposed layout places managed repositories under
`.codio/mirrors/`.

### Proposed directory structure

```text
<project_root>/
  .codio/
    catalog.yml
    profiles.yml
    repos.yml                          # proposed: Repository entity storage
    mirrors/                           # proposed: managed clones root
      <repo_id>/                       # one directory per managed repository
        .git/
        <repo contents>
  docs/
    reference/
      codelib/
        libraries/
```

### Rationale for `.codio/mirrors/`

- **Single ownership root.** All codio-owned artifacts live under `.codio/`.
  This avoids ambiguity about which tool owns a top-level directory like
  `code/lib/repos/` or `libs/`.
- **Gitignore-friendly.** Projects can add `.codio/mirrors/` to `.gitignore`
  since managed clones are reproducible from their remote URLs.
- **No conflict with project source.** Managed clones are reference material,
  not project source code. Keeping them under `.codio/` makes this distinction
  clear in the filesystem hierarchy.
- **DataLad compatibility.** If the project uses DataLad for large file
  management, `.codio/mirrors/` can be registered as a DataLad subdataset or
  excluded entirely. Placing clones under a dot-directory avoids interference
  with DataLad's top-level tracking.

### Alternative considered: project-level `code/lib/repos/`

A top-level directory like `code/lib/repos/<repo_id>/` was considered. This
has the advantage of visibility (not hidden) and aligns with projects that
already use a `code/` tree for source organization. However, it introduces
ambiguity about ownership: is `code/lib/` owned by codio, by the project, or
by another tool? The `.codio/mirrors/` approach avoids this question entirely.

**Assumption:** This layout assumes codio operates within a single project
root. Multi-project workspaces (e.g., a monorepo containing multiple
independent codio registries) would need a separate convention. This document
does not address that case.

---

## 3. Naming and Identity Rules

### `repo_id` as filesystem path component

The `repo_id` slug from the proposed Repository entity doubles as the
directory name under `.codio/mirrors/`. This means `repo_id` values must be
valid filesystem path components.

### Slug conventions

| Convention | Example | Filesystem path |
|------------|---------|-----------------|
| Flat slug | `scipy` | `.codio/mirrors/scipy/` |
| Namespaced slug | `scipy--scipy` | `.codio/mirrors/scipy--scipy/` |
| Owner-repo with separator | `scikit-learn--scikit-learn` | `.codio/mirrors/scikit-learn--scikit-learn/` |

Rules:

1. **Characters:** lowercase ASCII letters, digits, hyphens. The double-hyphen
   `--` serves as the namespace separator (replacing `/` which is not valid in
   directory names).
2. **No nested directories.** The mirrors directory is flat. `repo_id`
   `scipy--scipy` maps to `.codio/mirrors/scipy--scipy/`, not
   `.codio/mirrors/scipy/scipy/`.
3. **Uniqueness:** `repo_id` must be unique within a single registry. Two
   catalog entries may reference the same `repo_id` (monorepo case), but two
   Repository entries may not share a `repo_id`.
4. **Derivation from URL:** For repositories cloned from a remote, the
   suggested default derivation is `<owner>--<repo>` extracted from the clone
   URL (e.g., `https://github.com/scipy/scipy` becomes `scipy--scipy`). For
   local-only repositories, the slug is user-chosen.

### Mapping from `repo_id` to local path

For managed repositories, the local path is deterministic:

```
local_path = <project_root> / .codio / mirrors / <repo_id>
```

This path is recorded in the Repository entity's `local_path` field but can
always be reconstructed from `repo_id` and `project_root`. The recorded path
serves as a cache; the canonical source of truth is the `repo_id` plus the
mirrors root convention.

---

## 4. Required Metadata Alongside Managed Repos

Managed clones are bare git repositories (or standard clones — this is an
unresolved question). Codio does not store additional metadata files inside the
cloned repository directory. All metadata lives in the registry files.

### Repository-level metadata (in `.codio/repos.yml`)

Each managed repository has an entry in the proposed `repos.yml` file:

```yaml
# .codio/repos.yml
repositories:
  scipy--scipy:
    repo_id: scipy--scipy
    url: https://github.com/scipy/scipy.git
    hosting: github
    storage: managed
    local_path: .codio/mirrors/scipy--scipy
    default_branch: main
```

### What is not stored alongside the clone

- **Sync state** (last pull timestamp, current HEAD) — can be derived from the
  git repository itself via `git log` or `git rev-parse`.
- **Codio-specific config** — no `.codio.yml` or similar file is placed inside
  the managed clone. The clone is a faithful mirror of upstream.
- **Index artifacts** — indexio indexes are stored in `infra/indexio/`, not
  alongside the source.

### CodeSource pointers

When a catalog entry references a specific subtree within a managed
repository, the proposed CodeSource entity records the subpath:

```yaml
# Example: catalog entry referencing a code source
libraries:
  scipy-linalg:
    name: scipy-linalg
    kind: external_mirror
    repo_url: https://github.com/scipy/scipy
    path: .codio/mirrors/scipy--scipy/scipy/linalg
```

In the proposed model, this `path` would be replaced by a `source_id`
referencing a CodeSource entity that combines `repo_id: scipy--scipy` with
`subpath: scipy/linalg`. The current `path` field on `LibraryCatalogEntry`
continues to work as a plain string in the interim.

---

## 5. Attached Repository Layout

An attached repository is one that already exists on the filesystem. Codio
records its location but does not clone, pull, or modify it.

### What codio stores

A Repository entry with `storage: attached`:

```yaml
repositories:
  internal--utils:
    repo_id: internal--utils
    url: ""
    hosting: local
    storage: attached
    local_path: /home/user/projects/internal-utils
    default_branch: main
```

### What codio does not do for attached repos

- **No cloning.** The directory must already exist.
- **No syncing.** Codio does not run `git pull` or any git operations.
- **No directory creation.** If `local_path` does not exist, validation warns
  but codio does not create it.
- **No ownership.** The attached directory is not under `.codio/`. It may be
  anywhere on the filesystem.

### Key difference from managed repos

| Aspect | Managed | Attached |
|--------|---------|----------|
| Clone location | `.codio/mirrors/<repo_id>/` | Anywhere; user-specified |
| Created by codio | Yes | No |
| Updated by codio | Yes (sync commands) | No |
| Path deterministic | Yes (derived from `repo_id`) | No (recorded as-is) |
| Safe to delete `.codio/mirrors/` | Yes (re-cloneable) | N/A |
| Absolute vs relative path | Relative to project root | May be absolute or relative |

### External repositories (no local clone)

Repositories with `storage: external` have no `local_path`. They exist in the
registry as metadata only (URL, hosting, default branch). Catalog entries
referencing external repositories cannot use path-based operations (e.g.,
indexing source code) but can still participate in discovery via curated notes
and capability tags.

---

## 6. Relationship to Current Catalog and Profile Files

### Backward compatibility

The proposed layout is additive. Nothing about the existing `.codio/catalog.yml`
and `.codio/profiles.yml` schema changes. Specifically:

- **`catalog.yml` keeps the `libraries:` top-level key.** No structural change.
- **`profiles.yml` keeps the `profiles:` top-level key.** No structural change.
- **The `path` field on `LibraryCatalogEntry` remains a plain string.** It can
  point to a managed mirror path (e.g., `.codio/mirrors/scipy--scipy/scipy/linalg`)
  or to any other local directory, exactly as today.

### New file: `repos.yml`

The Repository entity is stored in a new file, `.codio/repos.yml`, rather than
adding a section to `catalog.yml`. Rationale:

- **Separation of concerns.** Repository identity is distinct from library
  identity. A repository may contain multiple libraries. Mixing them in one
  file would require a schema version bump and migration logic.
- **Independent lifecycle.** Repositories can be added or removed without
  editing the catalog. A managed mirror can exist before any catalog entries
  reference it.
- **Simpler validation.** Catalog validation and repository validation are
  independent passes. Cross-referencing (catalog `repo_id` FK to repository
  `repo_id` PK) is a separate check.

### Migration path

1. **No migration required for existing registries.** The absence of
   `repos.yml` and `.codio/mirrors/` is the current state. Codio continues to
   work without them.
2. **Opt-in managed mirrors.** When a user runs a future `codio clone` or
   `codio mirror add` command, codio creates `repos.yml` and
   `.codio/mirrors/` on demand.
3. **Gradual adoption of `repo_id`.** Catalog entries gain an optional
   `repo_id` field. Entries without `repo_id` continue to use the `path` and
   `repo_url` fields as unstructured metadata, as they do today.
4. **Scaffold update.** `codio init` does not create `repos.yml` or
   `.codio/mirrors/` unless the user opts in. The default scaffold remains
   minimal (catalog + profiles + notes directory).

### Config additions

Two new config fields (with defaults):

```yaml
# .projio/config.yml (proposed additions)
codio:
  repos_path: .codio/repos.yml                  # default
  mirrors_dir: .codio/mirrors/                   # default
```

These follow the same pattern as `catalog_path`, `profiles_path`, and
`notes_dir`: relative to `project_root`, overridable in `.projio/config.yml`.

---

## 7. Unresolved Questions

### 7.1 Storage ownership boundary

When codio clones a repository into `.codio/mirrors/<repo_id>/`, who owns the
git state? Codio created it, but it is a full git repository with its own
`.git/` directory, branches, and potentially uncommitted changes (if a user
edits files there). Options:

- **Codio owns it fully.** Codio may delete and re-clone at any time. Users
  should not make local modifications. This is the simplest model.
- **Codio owns the clone, users may branch.** Codio manages the default branch
  but users can create local branches for experimentation. This requires codio
  to avoid force-resetting.
- **Shared ownership.** Codio tracks upstream but the user is responsible for
  the working tree. This blurs the line between managed and attached.

Recommendation: start with full ownership (option 1). Document that managed
mirrors are ephemeral reference copies.

### 7.2 Durability and `.gitignore`

Should `.codio/mirrors/` be gitignored by default? Arguments for: managed
clones are large, reproducible, and should not be committed to the host
project. Arguments against: if the project uses DataLad, the mirrors might be
tracked as DataLad subdatasets for reproducibility.

The scaffold should add `.codio/mirrors/` to `.gitignore` by default but
document how to override this for DataLad workflows.

### 7.3 Workspace root assumptions

The entire layout assumes a single `project_root` containing `.codio/`. This
assumption breaks in at least two scenarios:

- **Monorepo with multiple codio registries.** Each sub-project might have its
  own `.codio/` directory. The mirrors directory would need to be per-registry
  or shared with deduplication.
- **Detached registry.** A codio registry stored outside the project it
  describes (e.g., a team-shared catalog in a separate repository). The
  `project_root` for config resolution differs from the root containing the
  code.

Neither scenario is addressed by this layout. They are noted as future design
constraints.

### 7.4 DataLad interaction

This project uses DataLad (evidenced by `[DATALAD]` commits in the git
history). DataLad manages datasets as git/git-annex repositories and tracks
subdatasets. Potential interactions:

- **Managed clones as subdatasets.** If `.codio/mirrors/<repo_id>/` is
  registered as a DataLad subdataset, DataLad tracks its state and can
  reproduce it. This is useful for reproducibility but adds complexity to
  codio's sync operations (must go through DataLad, not raw git).
- **Annex conflicts.** If the host project uses git-annex, files in
  `.codio/mirrors/` might be annexed unintentionally. The `.gitignore`
  approach (section 7.2) avoids this, but a DataLad-aware workflow might
  want explicit `.codio/mirrors/**` entries in `.gitattributes`.
- **Lock files.** DataLad operations create lock files. If codio runs
  `git pull` inside a managed mirror while DataLad is operating on the
  parent dataset, there may be contention.

Resolution requires input from the DataLad integration design. For now,
codio should treat managed mirrors as plain git clones and document the
DataLad interaction as an integration point, not a built-in feature.

### 7.5 Shallow clones and partial checkouts

Managed mirrors of large repositories (e.g., CPython, Linux kernel) may be
impractical as full clones. Options:

- **Shallow clone** (`git clone --depth 1`): small footprint, but `git log`
  and blame are limited.
- **Partial clone with sparse checkout**: only materializes the subtrees
  referenced by CodeSource entries. Complex to manage but space-efficient.
- **No clone; metadata only**: treat the repository as `external` and rely on
  indexio corpus queries for code intelligence. Simplest but loses local
  file access.

This is a policy decision per repository, not a layout question. The layout
supports any of these options since the `.codio/mirrors/<repo_id>/` directory
is just a git working tree regardless of clone depth.

### 7.6 `repos.yml` vs. a section in `catalog.yml`

Section 6 recommends a separate `repos.yml` file. The alternative is a
`repositories:` top-level key in `catalog.yml`. Arguments for a section in
`catalog.yml`:

- Fewer files to manage.
- Atomic reads: loading the catalog also loads repository metadata.
- Simpler scaffold.

Arguments for a separate file (current recommendation):

- Repository and library are different entities with different lifecycles.
- A repository can exist before any library references it (e.g., cloned for
  exploration, not yet cataloged).
- Schema evolution is independent.

This remains an open question pending implementation experience.

### 7.7 Cleanup and garbage collection

If a catalog entry referencing a managed mirror is deleted, should codio
automatically delete the clone? Options:

- **Manual cleanup.** `codio mirror prune` removes clones with no catalog
  references.
- **Automatic cleanup.** Deleting the last catalog entry referencing a
  `repo_id` triggers clone removal. Risky if the deletion was accidental.
- **No cleanup.** Clones persist until the user manually deletes
  `.codio/mirrors/<repo_id>/`.

Recommendation: manual cleanup via an explicit command, with a dry-run mode.

---

## 8. Summary of Proposed Filesystem Artifacts

```text
<project_root>/
  .codio/
    catalog.yml              # implemented: library identity metadata
    profiles.yml             # implemented: project-specific policy
    repos.yml                # proposed: Repository entity storage
    mirrors/                 # proposed: managed clone root
      <repo_id>/             # proposed: one per managed repository
        <repo contents>
  docs/
    reference/
      codelib/
        libraries/           # implemented: curated note markdown files
          <library-slug>.md
  .projio/
    config.yml               # referenced: codio config section
  infra/
    indexio/
      config.yaml            # referenced: codio writes owned source IDs
```

Ownership summary:

| Artifact | Status | Owner | Writable by codio |
|----------|--------|-------|-------------------|
| `.codio/catalog.yml` | Implemented | codio | Yes |
| `.codio/profiles.yml` | Implemented | codio | Yes |
| `docs/reference/codelib/libraries/` | Implemented | codio | Yes |
| `.codio/repos.yml` | Proposed | codio | Yes |
| `.codio/mirrors/<repo_id>/` | Proposed | codio | Yes (clone/sync) |
| `.projio/config.yml` | Implemented | projio | No (read only) |
| `infra/indexio/config.yaml` | Implemented | shared | Codio-owned IDs only |
