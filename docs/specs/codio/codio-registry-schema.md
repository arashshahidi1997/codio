# Codio Registry Schema

## Purpose

Codio uses a two-layer registry model to separate stable library identity from project-specific interpretation. This separation is required to keep metadata reusable across projects while still allowing local policy decisions.

## Two-Layer Model

### Library Catalog

The library catalog stores shared identity-level metadata.

Example:

```yaml
libraries:
  mne-python:
    kind: external_mirror
    repo_url: https://github.com/mne-tools/mne-python
    language: python
    pip_name: mne
    license: BSD-3-Clause
```

Recommended fields:

| Field | Meaning |
|---|---|
| `kind` | identity class such as `internal`, `external_mirror`, or `utility` |
| `repo_url` | canonical upstream repository URL when applicable |
| `language` | dominant implementation language |
| `pip_name` | package manager name when relevant |
| `license` | declared software license |
| `path` | local path for internal code or local mirror |
| `summary` | short identity description |

### Project Profile

The project profile stores local interpretation and policy.

Example:

```yaml
profiles:
  mne-python:
    priority: tier1
    runtime_import: pip_only
    decision_default: wrap
    curated_note: docs/reference/codelib/libraries/mne-python.md
```

Recommended fields:

| Field | Meaning |
|---|---|
| `priority` | project priority tier |
| `runtime_import` | runtime policy such as `internal`, `pip_only`, `reference_only` |
| `decision_default` | default engineering decision such as `existing`, `wrap`, `direct`, `new` |
| `curated_note` | path to the curated library note |
| `capabilities` | declared high-level capability tags |
| `status` | lifecycle state such as `active`, `candidate`, or `deprecated` |
| `notes` | short local comment |

## Why Catalog and Profile Must Be Separate

The two layers solve different problems.

- The **library catalog** answers what a library is.
- The **project profile** answers how the project should use it.

If these concerns are merged, shared metadata becomes hard to reuse and local policy becomes hard to compare across projects. Separation also makes it possible to keep one canonical library identity while multiple projects define different priorities, runtime rules, and default decisions.

## Schema Rules

- Library keys must be stable slugs.
- A profile entry must reference an existing catalog key.
- Identity metadata should avoid project-local judgments.
- Project profiles may be absent for low-priority catalog entries.
- `runtime_import` and `decision_default` must use controlled vocabulary.
- Paths in `curated_note` should be repository-relative.

## Minimal Example

```yaml
libraries:
  local-schema-tools:
    kind: internal
    language: python
    path: src/schema_tools
    summary: Internal schema validation utilities

  networkx:
    kind: external_mirror
    repo_url: https://github.com/networkx/networkx
    language: python
    pip_name: networkx
    license: BSD-3-Clause

profiles:
  local-schema-tools:
    priority: tier1
    runtime_import: internal
    decision_default: existing
    capabilities: [schema-validation]

  networkx:
    priority: tier2
    runtime_import: pip_only
    decision_default: direct
    capabilities: [graphs]
    curated_note: docs/reference/codelib/libraries/networkx.md
```
