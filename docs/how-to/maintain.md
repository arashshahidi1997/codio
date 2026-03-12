# Maintain the registry

## Add a new library

1. Add a catalog entry to `.codio/catalog.yml`:

```yaml
libraries:
  my-lib:
    kind: internal
    language: python
    path: src/my_lib
    summary: What this library does
```

2. Add a profile entry to `.codio/profiles.yml`:

```yaml
profiles:
  my-lib:
    priority: tier1
    runtime_import: internal
    decision_default: existing
    capabilities: [capability-a, capability-b]
    status: active
```

3. Validate:

```bash
codio validate
```

## Check allowed values

```bash
codio vocab --field kind
codio vocab --field priority
codio vocab --field decision_default
```

## Run a health check

```bash
codio validate
```

Codio checks:

- Profile entries that reference missing catalog keys (errors)
- Invalid vocabulary values (errors)
- Curated note paths that don't exist on disk (warnings)
- Catalog entries without profiles (warnings)

## Deprecate a library

Set the status to `deprecated` in the profile:

```yaml
profiles:
  old-lib:
    status: deprecated
```

## Register codio sources in indexio

If your project uses indexio for RAG, sync codio sources:

```bash
codio rag sync
```

This registers the catalog and curated notes as indexio corpus sources so they are searchable via `rag_query`.
