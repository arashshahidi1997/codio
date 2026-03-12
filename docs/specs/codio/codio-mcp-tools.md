# Codio MCP Tools

## Purpose

Codio requires a stable machine interface so agents can query library metadata and discovery results without re-implementing repository-specific parsing logic.

## Minimum Tools

### `codio_list(...)`

Returns a filtered list of known libraries. Typical filters may include capability, language, kind, priority, or runtime policy.

Expected output:

- library key
- short summary
- kind
- language
- priority
- runtime policy

### `codio_get(name)`

Returns the full structured record for one library, combining catalog metadata and project profile where available.

Expected output:

- identity metadata
- project profile fields
- curated note reference
- declared capabilities
- local path or mirror path

### `codio_registry()`

Returns the current normalized registry payload or a registry snapshot suitable for inspection and validation.

Expected output:

- library catalog entries
- project profile entries
- version or generation metadata when available

### `codio_vocab()`

Returns controlled vocabulary used by Codio fields such as `kind`, `priority`, `runtime_import`, and `decision_default`.

Expected output:

- allowed values
- field-level descriptions

### `codio_validate()`

Validates internal consistency of the Codio registry and reference layer.

Expected output:

- validation status
- missing references
- broken curated note paths
- unknown vocabulary values
- duplicate or conflicting entries

## Companion Retrieval Tools

Codio should integrate with corpus retrieval rather than replacing it.

```text
rag_query(corpus="code", query=...)
rag_query(corpus="docs", query=...)
```

Expected role:

- `rag_query(corpus="code", ...)` locates implementation evidence in source trees and mirrors
- `rag_query(corpus="docs", ...)` locates curated notes, conventions, and architecture references

## Tool Design Expectations

- Outputs should be structured and stable.
- Records should be easy to compose into agent planning steps.
- Tool semantics should be explicit about the difference between identity data, project policy, and search evidence.
- Retrieval tools should complement registry tools rather than duplicate them.
