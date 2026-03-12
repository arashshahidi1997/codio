# Quickstart

This tutorial walks through setting up codio in a project, registering libraries, and running discovery queries. By the end you will have a working `.codio/` registry with two libraries and an understanding of the discovery workflow.

## Prerequisites

- Python 3.11+
- codio installed: `pip install codio`
- A project directory to work in

## 1. Initialize the registry

Pick a project directory and scaffold the `.codio/` workspace:

```bash
cd ~/projects/my-project
codio init
```

This creates:

```
.codio/
  catalog.yml       # library identity metadata
  profiles.yml      # project-specific policy
docs/reference/codelib/libraries/   # curated notes directory
```

Both YAML files start empty. The next step is to populate them.

## 2. Register your first library

Open `.codio/catalog.yml` and add an internal library:

```yaml
libraries:
  schema-tools:
    kind: internal
    language: python
    path: src/schema_tools
    summary: Internal schema validation utilities
```

Now open `.codio/profiles.yml` and add its project profile:

```yaml
profiles:
  schema-tools:
    priority: tier1
    runtime_import: internal
    decision_default: existing
    capabilities: [schema-validation, data-models]
    status: active
```

This tells codio that `schema-tools` is a high-priority internal library. When someone searches for schema validation, codio will recommend reusing it.

## 3. Add an external library

Add a second entry — this time an external dependency:

```yaml
# append to .codio/catalog.yml under libraries:
  networkx:
    kind: external_mirror
    repo_url: https://github.com/networkx/networkx
    language: python
    pip_name: networkx
    license: BSD-3-Clause
    summary: Graph algorithms and data structures
```

```yaml
# append to .codio/profiles.yml under profiles:
  networkx:
    priority: tier2
    runtime_import: pip_only
    decision_default: direct
    capabilities: [graphs, network-analysis, shortest-path]
    status: active
```

## 4. Validate the registry

Check that everything is consistent:

```bash
codio validate
```

Expected output:

```
Registry is valid.
```

If a profile references a library not in the catalog, or uses an invalid vocabulary value, codio will report errors.

## 5. List registered libraries

```bash
codio list
```

```
  schema-tools                   kind=internal           lang=python    priority=tier1
  networkx                       kind=external_mirror    lang=python    priority=tier2
```

Filter by kind:

```bash
codio list --kind internal
```

## 6. Get a single library record

```bash
codio get schema-tools
```

This prints all catalog and profile fields merged into one view. Add `--json` for machine-readable output:

```bash
codio get schema-tools --json
```

## 7. Discover libraries by capability

This is the core workflow. You have a problem — search before implementing:

```bash
codio discover "schema-validation"
```

```
Query: schema-validation
Recommendation: existing — Internal library 'schema-tools' already provides this capability.

Candidates (1):
  schema-tools [tier1] — Capability match: schema-validation
```

Codio found `schema-tools`, noted it is internal and tier1, and recommended using the existing code.

Try a broader query:

```bash
codio discover "graphs"
```

```
Query: graphs
Recommendation: direct — Library 'networkx' is available with policy 'direct'.

Candidates (1):
  networkx [tier2] — Capability match: graphs
```

## 8. Study a library

For deeper analysis:

```bash
codio study networkx
```

```
networkx (external_mirror, python)
  Summary: Graph algorithms and data structures
  Strengths:
    - Source available locally as mirror
    - Declared capabilities: graphs, network-analysis, shortest-path
  Caveats:
    - Mirror may be out of date with upstream
  Entry points:
    - pip install networkx
  Integration: Can be used directly as a dependency. License: BSD-3-Clause.
```

## 9. Compare libraries

When multiple candidates exist for the same capability:

```bash
codio compare schema-tools networkx --query "data processing"
```

## 10. Write a curated note (optional)

For tier1 and tier2 libraries, create a curated note at the path referenced in the profile:

```bash
mkdir -p docs/reference/codelib/libraries
```

Create `docs/reference/codelib/libraries/schema-tools.md`:

```markdown
# schema-tools

## Scope
Internal schema validation for project data models.

## Strengths
- Zero external dependencies
- Covers all project-specific validation rules

## Caveats
- Not designed for general-purpose JSON Schema validation

## Entry points
- `src/schema_tools/validate.py` — main validation functions
- `src/schema_tools/models.py` — Pydantic model definitions

## Integration
Use directly. This is the canonical implementation for schema work in this project.
```

Update the profile to point to it:

```yaml
  schema-tools:
    priority: tier1
    runtime_import: internal
    decision_default: existing
    capabilities: [schema-validation, data-models]
    curated_note: docs/reference/codelib/libraries/schema-tools.md
    status: active
```

## 11. Check vocabulary

Not sure which values are allowed for `kind` or `priority`?

```bash
codio vocab
```

Or a specific field:

```bash
codio vocab --field decision_default
```

```
decision_default — Default engineering decision
  existing: Use the existing implementation as-is
  wrap: Wrap the external library with a thin adapter
  direct: Use the external library directly
  new: Write a new implementation from scratch
```

## What's next

- [How-to: Search for libraries](../how-to/discover.md) — more discovery patterns
- [How-to: Maintain the registry](../how-to/maintain.md) — keeping things up to date
- [Explanation: Two-layer registry model](../explanation/registry-model.md) — why catalog and profile are separate
- [Reference: CLI commands](../reference/cli.md) — full command syntax
