# Library kinds and policies

Codio uses controlled vocabulary fields to classify libraries and express policy. This page explains what the values mean and when to use each one.

## Kind

The `kind` field describes what a library is.

| Value | Meaning | Example |
|-------|---------|---------|
| `internal` | Code owned by this project | `src/schema_tools/` |
| `external_mirror` | Local copy of an external codebase | A cloned repo kept for reference |
| `utility` | Shared utility library | Cross-project helper functions |

**Internal** libraries are the strongest candidates for reuse — they already exist in the project, have no external dependency risk, and are maintained locally.

**Mirrors** are reference material. They let you study an external library's source without depending on network access, but they may be out of date with upstream.

**Utilities** are shared code that doesn't belong to a single project. They sit between internal and external.

## Priority

The `priority` field expresses project investment.

| Value | Meaning |
|-------|---------|
| `tier1` | Core dependency, well-understood, documented |
| `tier2` | Important but not critical |
| `tier3` | Low priority, optional, or experimental |

Priority affects discovery ranking: tier1 candidates sort before tier2 and tier3.

## Runtime import

The `runtime_import` field states how a library participates in execution.

| Value | Meaning |
|-------|---------|
| `internal` | Imported directly at runtime |
| `pip_only` | Installed via pip but not imported directly by project code |
| `reference_only` | Referenced in docs or config only — not approved for import |

This distinction matters because a library that appears in the registry may not be appropriate for runtime use.

## Decision default

The `decision_default` field records the standing engineering decision for a library.

| Value | Meaning |
|-------|---------|
| `existing` | Use the internal implementation as-is |
| `wrap` | Wrap the external library behind project APIs |
| `direct` | Use the external library directly |
| `new` | Write new code (no suitable prior art) |

When `codio discover` finds a candidate, it recommends a decision based on the top candidate's `decision_default`.

## Status

The `status` field tracks lifecycle state.

| Value | Meaning |
|-------|---------|
| `active` | Currently in use |
| `candidate` | Under consideration for adoption |
| `deprecated` | Scheduled for removal |
