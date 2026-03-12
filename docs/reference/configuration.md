# Configuration

## Default paths

Codio uses these defaults when no configuration file is present:

| Setting | Default |
|---------|---------|
| Catalog | `.codio/catalog.yml` |
| Profiles | `.codio/profiles.yml` |
| Notes directory | `docs/reference/codelib/libraries/` |

## Projio integration

When a `.projio/config.yml` exists in the project root, codio reads its `codio` section:

```yaml
codio:
  enabled: true
  catalog_path: .codio/catalog.yml
  profiles_path: .codio/profiles.yml
  notes_dir: docs/reference/codelib/libraries/
```

All paths are resolved relative to the project root.

## Project root detection

Codio auto-detects the project root by walking up from the current directory. It looks for (in order):

1. `.codio/catalog.yml` — strongest signal
2. `.projio/config.yml` — projio-managed project
3. `.git` or `pyproject.toml` — generic project root

Use `--root DIR` on any command to override detection.

## Catalog schema

```yaml
libraries:
  <library-slug>:
    kind: internal | external_mirror | utility
    language: <string>
    repo_url: <url>           # optional
    pip_name: <package>       # optional
    license: <string>         # optional
    path: <local-path>        # optional
    summary: <string>         # optional
```

## Profile schema

```yaml
profiles:
  <library-slug>:
    priority: tier1 | tier2 | tier3
    runtime_import: internal | pip_only | reference_only
    decision_default: existing | wrap | direct | new
    capabilities: [<tag>, ...]     # optional
    curated_note: <path>           # optional
    status: active | candidate | deprecated
    notes: <string>                # optional
```

Profile keys must reference existing catalog keys.
