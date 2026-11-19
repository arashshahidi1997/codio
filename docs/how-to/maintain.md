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

## Restore and update managed mirrors

Managed mirrors (`storage: managed` in `repos.yml`) are local clones under
`.projio/codio/mirrors/`, which is gitignored. The project repository keeps
only `url`, `default_branch` and the pinned commit `ref`. After cloning a
project, restore them:

```bash
codio mirror sync
```

This clones every missing mirror at its pinned `ref` and records a `ref` for
any mirror that has none. To pull upstream changes and re-pin:

```bash
codio mirror sync --update
```

Commit the changed `repos.yml` to share the new pins. A mirror whose HEAD
differs from its pin is reported as `drift`.

### Mirrors committed as submodules

`codio mirror sync` warns when a mirror is committed in the project
repository (usually as a submodule picked up by `git add` or
`datalad save`). Move it back to the working tree only; the clone on disk
stays as it is:

```bash
codio mirror sync                      # records each mirror's ref first
git add .projio/codio/repos.yml
paths=$(git ls-files -s .projio/codio/mirrors | awk '{print $4}')
for p in $paths; do
  git config -f .gitmodules --remove-section "submodule.$p"
  git config --remove-section "submodule.$p" 2>/dev/null
done
git add .gitmodules                    # git rm refuses while .gitmodules is unstaged
for p in $paths; do git rm --cached -q "$p"; done
git commit -m "chore(codio): mirrors as gitignored local clones"
```

Make sure `.projio/codio/mirrors/` is in `.gitignore` (`projio sync` adds it).
