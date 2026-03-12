# Initialize a project registry

## Scaffold in the current directory

```bash
codio init
```

Creates `.codio/catalog.yml`, `.codio/profiles.yml`, and the curated notes directory.

## Scaffold in a specific directory

```bash
codio init --root /path/to/project
```

## Overwrite existing files

If `.codio/` already exists and you want to reset to the default templates:

```bash
codio init --force
```

## What gets created

```
.codio/
  catalog.yml                           # empty library catalog
  profiles.yml                          # empty project profiles
docs/reference/codelib/libraries/       # curated notes directory
```

The catalog and profiles start with empty `libraries: {}` and `profiles: {}` blocks. Edit them directly to add entries.

## With projio integration

If your project uses projio, codio reads its configuration from `.projio/config.yml`:

```yaml
codio:
  enabled: true
  catalog_path: .codio/catalog.yml
  profiles_path: .codio/profiles.yml
  notes_dir: docs/reference/codelib/libraries/
```

These paths override the defaults when present. All codio commands auto-detect the projio config.
