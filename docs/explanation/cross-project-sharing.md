# Cross-Project Sharing

This document explains how codio's registry metadata can be shared across
multiple projects, what sharing mechanisms are likely to work, and where
premature centralization would cause more harm than benefit.

The short version: catalog entries are shareable by design, profiles are
local by design, and codio should support sharing without requiring it.

---

## 1. Current portability

Codio already has portability properties that make cross-project sharing
feasible, even though no sharing tooling exists today.

**YAML files versioned with the project.**  The `.codio/catalog.yml` and
`.codio/profiles.yml` files are plain YAML committed alongside project
source.  They have no binary dependencies, no database state, and no
absolute paths in their schema.  Any tool that can read YAML can consume
them.

**Curated notes are project-relative Markdown.**  The `curated_note` field
on profile entries points to a relative path (by convention under
`docs/reference/codelib/libraries/`).  These Markdown files travel with the
repository and render in any Markdown viewer.

**Config integration is read-only and optional.**  Codio reads
`.projio/config.yml` for path overrides (`catalog_path`, `profiles_path`,
`notes_dir`) but does not write to it.  A project without `.projio/` works
fine; codio falls back to its defaults.  This means codio's portability is
not gated on projio adoption.

**No global state.**  Codio does not maintain a user-level config file, a
system-wide registry, or a daemon process.  All state lives under the
project root.  This makes codio's behavior reproducible across machines
and CI environments.

**Name slugs are human-authored.**  Library `name` values (the primary key
in the catalog) are chosen by the person writing the catalog, not generated
by codio.  This makes them readable and meaningful, but also means they
carry no global uniqueness guarantee.

---

## 2. Shareable vs local metadata

The catalog/profile separation is codio's central design decision, and it
maps directly onto the sharing question.

### Catalog: shareable

A `LibraryCatalogEntry` describes what a library *is*: name, kind,
language, repo URL, package name, license, local path, summary.  These
fields are project-agnostic.  The statement "scipy is an external Python
library licensed under BSD, available at `https://github.com/scipy/scipy`"
is true regardless of which project is consulting the registry.

Catalog entries are the natural unit of sharing.  Two projects that both
use scipy should be able to share the same catalog entry rather than
maintaining independent copies that drift apart.

Caveats:

- The `path` field is problematic for sharing.  It points to a local
  filesystem location that varies across projects and machines.  Shared
  catalog entries should either omit `path` or treat it as a default that
  the consuming project overrides.
- The `kind` field (`internal`, `external_mirror`, `utility`) may differ
  across projects.  A library that is `internal` in the project that
  authored it is `external_mirror` in a project that consumes it.  This
  is a category that arguably belongs in the profile, not the catalog,
  but changing it would be a schema migration.

### Profile: local

A `ProjectProfileEntry` describes how a specific project relates to a
library: priority tier, runtime import policy, decision default,
capability tags, status, curated note path.  These fields encode
project-specific engineering decisions.

Profiles should not be shared.  The statement "scipy is tier1, use
existing" is a policy decision made by one project's team.  Another
project may reasonably assign scipy to tier2 or set its decision default
to `wrap`.  Sharing profiles would impose one project's policy on
another.

### Curated notes: semi-shareable

Curated notes sit between catalog and profile.  A note explaining scipy's
linear algebra API and its threading behavior is broadly useful.  A note
explaining how *this project* wraps scipy's sparse solvers is
project-specific.

In practice, curated notes tend to start project-specific and become more
general over time as the author strips out local context.  Sharing them
requires editorial judgment, not automated tooling.

### Proposed entities

The entity model document proposes `Repository` as a first-class entity
with a `repo_id` slug.  Repository metadata (URL, hosting, default branch)
is inherently shareable — it describes the repository, not a project's
relationship to it.  If repository entities are implemented, they become
another natural unit of sharing alongside catalog entries.

The proposed `CodeSource` entity (a sub-tree within a repository) is
partially shareable.  The identity fields (`source_id`, `repo_id`,
`subpath`, `source_type`) are project-agnostic, but the `indexable` flag
is a local policy decision.

---

## 3. Likely sharing mechanisms

Several mechanisms could enable cross-project catalog sharing.  Each has
trade-offs.  None is clearly dominant, and codio should not commit to one
mechanism prematurely.

### Git submodules or subtrees

A shared catalog repository (e.g., `team-codelib-catalog`) containing a
`catalog.yml` file could be included as a git submodule or subtree in each
consuming project.  The `.projio/config.yml` override for `catalog_path`
already supports pointing codio at a non-default location.

Advantages: uses existing git tooling; changes to the shared catalog are
versioned and auditable; each project pins a specific commit of the shared
catalog.

Disadvantages: git submodules are widely disliked for their UX friction;
subtrees create merge complexity; both require git discipline that many
teams lack.

### Symlinks

A simpler alternative in monorepo or co-located project setups: symlink
`.codio/catalog.yml` to a shared file elsewhere on the filesystem.  Codio
follows symlinks transparently because it reads files through standard
Python path operations.

Advantages: zero tooling overhead; works immediately.

Disadvantages: symlinks break across machines with different filesystem
layouts; not portable to Windows without additional configuration; no
versioning of the sharing relationship itself.

### Shared catalog repository with import/export

Codio could gain `codio catalog export` and `codio catalog import`
commands.  Export writes selected catalog entries to a standalone YAML
file.  Import merges entries from an external file into the local catalog,
with conflict resolution for duplicate names.

Advantages: explicit, auditable, does not require git submodules or
symlinks; works across organizations and hosting platforms.

Disadvantages: requires new CLI commands; import/export workflows are
manual and can drift; conflict resolution for name collisions needs
design.

### Template catalogs

A lighter variant of import/export: codio ships or references template
catalogs for common ecosystems (e.g., a "Python data science" template
with entries for numpy, scipy, pandas, matplotlib).  `codio init` could
optionally seed the catalog from a template.

Advantages: useful for bootstrapping new projects; reduces the cost of
starting a registry from scratch.

Disadvantages: templates go stale; maintaining ecosystem-specific templates
is an ongoing burden; templates may not match a project's actual
dependencies.

### Central registry service

A hosted service that stores canonical catalog entries, supports search,
and provides an API for fetching entries by name.  This is the most
capable option and the most dangerous.

Advantages: single source of truth; enables discovery across
organizational boundaries; supports namespace management.

Disadvantages: introduces a network dependency; requires authentication
and access control; creates a single point of failure; conflicts with
codio's design principle of local-first operation.

This option is listed for completeness.  It should not be pursued in the
near term.

---

## 4. How managed and attached repos affect sharing

The entity model proposes three storage modes for repositories: managed,
attached, and external.  Each mode interacts differently with sharing.

### External repositories

External repositories have metadata only — no local clone.  Their catalog
entries are fully shareable because they contain no filesystem-specific
information.  A shared catalog of external libraries is the simplest
sharing scenario.

### Managed repositories

Managed repositories are cloned into a codio-controlled workspace (e.g.,
`.codio/libs/<slug>/`).  The clone is local to one project's filesystem.
The catalog entry for a managed library includes a `path` that points to
this local clone.

Sharing the catalog entry requires the consuming project to either:

- Clone the same repository into its own managed workspace (the `path`
  will differ), or
- Treat the entry as external (ignore the `path`, use only the `repo_url`
  and identity metadata).

This means catalog entries for managed libraries are shareable in
identity but not in storage.  The consuming project must resolve the
`path` field locally.

### Attached repositories

Attached repositories already exist on the filesystem, managed by
something other than codio (a sibling project, a git submodule, DataLad).
The catalog entry records a `path` to the existing location.

Sharing attached-repository entries is more complex because:

- The attached path is specific to one machine's filesystem layout.
- Two projects may attach the same repository at different paths.
- The attachment relationship (which project "owns" the checkout) is
  implicit.

If codio adopts the proposed `repo_id` field, sharing becomes easier:
the `repo_id` identifies the repository portably, and each project
resolves the local path independently.  The shared catalog provides
identity; the local configuration provides storage.

### Implication for sharing design

The `path` field is the main obstacle to catalog sharing.  Any sharing
mechanism must handle the fact that `path` values are local.  Options:

- Strip `path` from shared catalog entries (the consuming project fills
  it in via profile or local override).
- Treat `path` as a hint or default that can be overridden.
- Introduce a `repo_id` field that provides stable identity independent
  of local paths, and resolve paths through a separate local mapping.

The third option aligns with the proposed entity model and is the most
robust long-term approach.

---

## 5. Risks of over-centralization

Sharing metadata is useful.  Centralizing metadata is risky.  The
distinction matters.

### Project autonomy

Each project should be able to maintain its own catalog without depending
on a shared source.  A shared catalog is an optimization, not a
requirement.  If the shared catalog becomes unavailable, stale, or
contentious, each project should be able to fork its portion and continue
independently.

### Slug collision

Library `name` slugs are human-authored and unique only within a single
catalog.  Two projects may independently create entries with the same
name but different meanings (e.g., `utils` in project A refers to a
different package than `utils` in project B).

Any sharing mechanism must address slug collision:

- Namespace prefixes (e.g., `projectA/utils`) add complexity and change
  the identity model.
- Merge-time conflict detection (refuse to import entries with colliding
  names) is simpler but requires manual resolution.
- A `repo_id` or `repo_url` field provides an alternative identity
  dimension for deduplication, but only for entries that have a
  repository.

### Stale shared catalogs

A shared catalog that is not actively maintained becomes misleading.
Entries may reference libraries that have been deprecated, moved, or
renamed.  Consuming projects that trust the shared catalog inherit
these errors.

Mitigation: `codio validate` should detect stale entries (missing
curated notes, broken paths, deprecated status without a replacement).
If a shared catalog is imported, validation should run automatically.

### Policy leakage

If sharing mechanisms are not careful about the catalog/profile
boundary, project-specific policy can leak into shared metadata.  For
example, if `kind` is shared but reflects a project-local perspective
(internal vs. external), consuming projects inherit an incorrect
classification.

The cleanest solution is to keep sharing strictly at the catalog level
and never share profiles.  Fields that blur the catalog/profile boundary
(like `kind`) should be documented with sharing-aware guidance.

### Coordination overhead

Shared catalogs require someone to maintain them.  In organizations,
this often becomes a governance question: who approves additions, who
reviews updates, who resolves conflicts.  This overhead is justified
only when the number of consuming projects is large enough to amortize
the cost.

For small teams or solo developers, project-local catalogs with
occasional manual copying are simpler and sufficient.

---

## 6. Migration from the current model

Any sharing capability must be backward-compatible with the current
`.codio/` layout.

### No breaking changes to schema

The current `catalog.yml` and `profiles.yml` schemas should remain valid
without modification.  A project that does not use sharing should see no
difference in codio's behavior.

### Gradual adoption

Sharing features should be opt-in:

1. A project starts with `codio init` and a local catalog (current
   behavior, unchanged).
2. Optionally, the project imports entries from an external catalog
   file or shared repository.
3. Imported entries merge into the local `catalog.yml`.  The project
   retains full ownership of its local copy.
4. The project creates local profile entries for imported catalog entries
   as needed.

At no point does the local catalog become a read-only view of a remote
source.  The project always owns its `.codio/` directory.

### Schema additions, not changes

If sharing requires new fields (e.g., `repo_id` on catalog entries,
`source` provenance metadata), these should be added as optional fields
with defaults that preserve current behavior.  Existing catalogs that
lack these fields remain valid.

### Import provenance

When entries are imported from an external source, codio could record
provenance metadata (`added_by: import`, `source_ref: <origin>`).  This
is informational, not structural — it helps maintainers understand where
an entry came from but does not change how codio processes it.

### Validation across shared boundaries

`codio validate` should handle catalogs that contain a mix of locally
authored and imported entries.  Validation rules (orphan profiles,
invalid vocab values, missing curated notes) apply uniformly regardless
of entry origin.

---

## 7. Compatibility with current codio usage

The single-project, local-only workflow is codio's primary use case.
Sharing is an extension, not a replacement.

### Default behavior unchanged

`codio init` creates a local `.codio/` directory with template catalog
and profile files.  This behavior should not change.  There should be
no prompt asking whether the user wants to connect to a shared catalog.

### No required network access

Codio must remain fully functional offline and without network access.
Sharing mechanisms that involve fetching from a remote service must be
optional and clearly gated behind explicit commands.

### Single-project workflows remain first-class

The commands `codio list`, `codio get`, `codio discover`, `codio validate`,
and `codio study` should work identically whether the catalog was authored
locally, imported from a shared source, or assembled from multiple sources.
The registry abstraction hides the origin of entries.

### Performance

Sharing should not degrade codio's performance for single-project use.
The registry loads two YAML files and merges them in memory.  Adding
import/export capabilities or shared-catalog resolution should not slow
down the common case where everything is local.

### Documentation

When sharing features are implemented, they should be documented as an
advanced workflow.  The getting-started path remains: `codio init`,
edit `catalog.yml`, edit `profiles.yml`, run `codio discover`.  Sharing
is something teams adopt after the local workflow is established and
the catalog has grown large enough to justify the coordination cost.

---

## Summary

Codio's catalog/profile separation already establishes the right boundary
for sharing: catalog entries describe identity (shareable), profiles
describe policy (local).  The main obstacle to catalog sharing is the
`path` field, which encodes local filesystem state.  The proposed
`repo_id` entity provides a portable identity that decouples sharing from
storage.

Multiple sharing mechanisms are viable (git submodules, import/export,
template catalogs), and codio should support the simplest ones first
without committing to a central registry.  The risks of over-centralization
— slug collision, stale metadata, policy leakage, governance overhead —
are real and increase with the degree of centralization.

The guiding principle: sharing should be an opt-in optimization that
builds on the local workflow, not a prerequisite for using codio.
