# Workspace layout

After running `codio init`, the following structure is created in the project:

```
project-root/
  .codio/
    catalog.yml                             # library identity metadata
    profiles.yml                            # project-specific policy
  docs/
    reference/
      codelib/
        libraries/                          # curated library notes
          schema-tools.md                   # (one per library, optional)
          mne-python.md
```

## .codio/catalog.yml

Stores the library catalog — shared identity-level metadata for all known libraries. Keyed by library slug.

## .codio/profiles.yml

Stores project profiles — local policy for each library. Keyed by library slug, must reference existing catalog keys.

## Curated notes directory

Located at `docs/reference/codelib/libraries/` by default (configurable). Each file is a Markdown document covering scope, strengths, caveats, entry points, and integration patterns for one library.

Curated notes are optional. They are most valuable for tier1 and tier2 libraries that require project-specific interpretation beyond what the registry metadata captures.

## MCP tools

When codio is registered with projio's MCP server, agents can query the registry via structured tool calls:

| MCP tool | Purpose |
|----------|---------|
| `codio_list` | Filtered library listing |
| `codio_get` | Single library record |
| `codio_registry` | Full registry snapshot |
| `codio_vocab` | Controlled vocabulary |
| `codio_validate` | Consistency checks |
| `codio_discover` | Capability search |
