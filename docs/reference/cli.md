# CLI Commands

## codio init

Scaffold `.codio/` in a project.

```
codio init [--root DIR] [--force]
```

| Option | Description |
|--------|-------------|
| `--root DIR` | Project root (default: current directory) |
| `--force` | Overwrite existing files |

Creates `catalog.yml`, `profiles.yml`, and the curated notes directory.

## codio list

List libraries from the registry with optional filters.

```
codio list [--root DIR] [--kind KIND] [--language LANG] [--capability CAP]
           [--priority TIER] [--runtime-import POLICY] [--json]
```

| Option | Description |
|--------|-------------|
| `--kind` | Filter by kind: `internal`, `external_mirror`, `utility` |
| `--language` | Filter by programming language |
| `--capability` | Filter by capability tag |
| `--priority` | Filter by tier: `tier1`, `tier2`, `tier3` |
| `--runtime-import` | Filter by policy: `internal`, `pip_only`, `reference_only` |
| `--json` | Output as JSON array |

## codio get

Show the full merged record for a single library.

```
codio get NAME [--root DIR] [--json]
```

Exits with code 1 if the library is not found.

## codio validate

Run consistency checks on the registry.

```
codio validate [--root DIR] [--json]
```

Checks performed:

- Profile entries referencing non-existent catalog keys (errors)
- Invalid controlled vocabulary values (errors)
- Curated note paths that don't exist on disk (warnings)
- Catalog entries without profiles (warnings)

## codio vocab

Show controlled vocabulary for registry fields.

```
codio vocab [--field FIELD] [--json]
```

| Option | Description |
|--------|-------------|
| `--field` | Show a specific field: `kind`, `runtime_import`, `decision_default`, `priority`, `status` |

## codio discover

Search for libraries matching a capability query.

```
codio discover QUERY [--root DIR] [--language LANG] [--json]
```

Searches capability tags (exact match), library names (substring), and summaries (substring). Returns ranked candidates and a recommended engineering decision.

## codio study

Structured analysis of a single library.

```
codio study NAME [--root DIR] [--json]
```

Returns strengths, caveats, entry points, and integration notes derived from registry metadata. Exits with code 1 if the library is not found.

## codio compare

Compare multiple libraries.

```
codio compare NAME [NAME ...] [--root DIR] [--query QUERY] [--json]
```

| Option | Description |
|--------|-------------|
| `--query` | Optional context for the comparison |

Returns shared capabilities, distinguishing factors, and a recommendation.

## codio rag sync

Register codio-owned sources in the project's indexio config.

```
codio rag sync [--root DIR] [--config PATH] [--force-init]
```

| Option | Description |
|--------|-------------|
| `--config` | Path to indexio config file (default: `infra/indexio/config.yaml`) |
| `--force-init` | Reinitialize the indexio config from defaults |

Requires the `indexio` package to be installed.

## Common options

All commands that read the registry support:

- `--root DIR` — Override project root auto-detection
- `--json` — Machine-readable JSON output

Project root is auto-detected by walking up from the current directory looking for `.codio/`, `.projio/`, or `.git`.
