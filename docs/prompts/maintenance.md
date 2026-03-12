# Codio Maintenance Prompts

Reusable prompts for common Codio development and maintenance tasks.
Copy a prompt below into a new Claude Code session.

Codio is a **tool for arbitrary projects** — it scaffolds `.codio/` in target
projects and provides CLI + MCP tools for code reuse discovery. It follows the
same patterns as its siblings `biblio` (papers) and `projio` (project orchestration).

---

## M1 — CLI + Scaffold + Templates (Foundation)

Add the user-facing shell to codio: CLI entry point, scaffold system, and YAML
templates. This is the foundation that all other features build on.

```
Read the Codio specs in docs/specs/codio/ and the existing implementation in src/codio/.

Also study the sibling projects for patterns to follow:
- biblio scaffold: /storage2/arash/projects/biblio/src/biblio/scaffold.py
- biblio CLI:      /storage2/arash/projects/biblio/src/biblio/cli.py
- projio init:     /storage2/arash/projects/projio/src/projio/init.py
- projio CLI:      /storage2/arash/projects/projio/src/projio/cli.py

Implement the following, matching the biblio/projio patterns:

### 1. Templates (src/codio/templates/)

Create YAML templates that `codio init` will write into target projects:

**src/codio/templates/codio/catalog.yml.tmpl**
```yaml
# Codio library catalog — project-agnostic identity metadata
# See: codio vocab --field kind  for allowed values
libraries: {}
```

**src/codio/templates/codio/profiles.yml.tmpl**
```yaml
# Codio project profiles — local policy for each library
# See: codio vocab --field priority  for allowed values
profiles: {}
```

### 2. Scaffold (src/codio/scaffold.py)

Follow biblio's scaffold.py pattern exactly:
- Use importlib.resources to locate templates
- ScaffoldResult dataclass with root + files_written
- init_codio_scaffold(project_root, *, force=False) -> ScaffoldResult
- Strip .tmpl suffix, write to .codio/ in target project
- Skip existing files unless force=True
- Also create the notes directory (from config.DEFAULT_NOTES_DIR)

### 3. CLI (src/codio/cli.py)

Argparse-based CLI following biblio's pattern. Commands:

  codio init [--root DIR] [--force]
      Scaffold .codio/ in a project (catalog.yml, profiles.yml, notes dir)

  codio list [--root DIR] [--kind KIND] [--language LANG] [--capability CAP] [--priority TIER] [--json]
      List libraries from registry with optional filters

  codio get NAME [--root DIR] [--json]
      Show full merged record for a single library

  codio validate [--root DIR] [--json]
      Run consistency checks on registry

  codio vocab [--field FIELD] [--json]
      Show controlled vocabulary (all fields or a specific one)

  codio discover QUERY [--root DIR] [--language LANG] [--json]
      Search for libraries matching a capability query

  codio study NAME [--root DIR] [--json]
      Structured analysis of a library

  codio compare NAME [NAME ...] [--root DIR] [--query QUERY] [--json]
      Compare multiple libraries

All commands that read the registry should:
- Auto-detect project root (walk up to find .codio/ or .projio/)
- Support --root override
- Support --json for machine-readable output
- Print human-readable tables/text by default

### 4. Entry point in pyproject.toml

Add to [project.scripts]:
  codio = "codio.cli:main"

Also add to [tool.setuptools.package-data]:
  codio = ["templates/**/*.tmpl"]

### 5. Tests

Add tests in tests/test_cli.py:
- test_init_creates_scaffold (tmp_path)
- test_init_force_overwrites
- test_list_empty_registry
- test_list_with_filters (use conftest fixtures)
- test_get_existing and test_get_missing
- test_validate
- test_vocab
- test_discover
- test_cli_json_flag (verify JSON output parses)

Run: make test
```

---

## M2 — Projio MCP Integration

Wire codio tools into projio's MCP server so Claude agents can query the
registry via structured tool calls.

```
Read the existing codio MCP functions: /storage2/arash/projects/codio/src/codio/mcp.py
Read projio's MCP server and how it integrates biblio:
- /storage2/arash/projects/projio/src/projio/mcp/server.py
- /storage2/arash/projects/projio/src/projio/mcp/biblio.py
- /storage2/arash/projects/projio/src/projio/mcp/rag.py

Add codio tools to projio's MCP server:

### 1. Create /storage2/arash/projects/projio/src/projio/mcp/codio.py

Register these tools on the FastMCP server:
- codio_list(kind, language, capability, priority, runtime_import) -> filtered listing
- codio_get(name) -> full merged record
- codio_registry() -> full snapshot
- codio_vocab() -> controlled vocabulary
- codio_validate() -> validation results
- codio_discover(query, language) -> discovery candidates + recommendation

Each tool should:
- Load config from PROJIO_ROOT env var (like rag.py does)
- Construct a codio Registry from config paths
- Call the corresponding codio.mcp function
- Return JSON-serializable dict

### 2. Register in server.py

Import and register the codio tools in the FastMCP server, following
the same conditional pattern used for biblio (try import, skip if unavailable).

### 3. Update projio's pyproject.toml

Add codio to optional dependencies:
  codio = ["codio"]

### 4. Update projio config template

Add a codio section to BASE_PROJIO_CONFIG in projio/init.py:
  codio:
    enabled: true
    catalog_path: .codio/catalog.yml
    profiles_path: .codio/profiles.yml
    notes_dir: docs/reference/codelib/libraries/

Run projio tests: cd /storage2/arash/projects/projio && make test
Run codio tests: cd /storage2/arash/projects/codio && make test
```

---

## M3 — Indexio Integration (Code Corpus)

Register codio-owned sources in indexio so code and library docs are
searchable via RAG.

```
Read indexio's sync_owned_sources pattern:
- /storage2/arash/projects/indexio/src/indexio/edit.py
- /storage2/arash/projects/projio/src/projio/mcp/rag.py

Add a `codio rag sync` CLI command that registers codio-owned sources
in the project's indexio config:

### 1. src/codio/rag.py

def sync_codio_rag_sources(project_root: Path, config: CodioConfig) -> dict:
    - Build source list from registry:
      - source_id="codio-notes", corpus="codelib", glob=notes_dir/**/*.md
      - source_id="codio-catalog", corpus="codelib", path=catalog_path
    - Call indexio.sync_owned_sources() with owned_source_ids=["codio-notes", "codio-catalog"]
    - Return sync result

### 2. Add CLI command

  codio rag sync [--root DIR]
      Register codio sources in indexio config

### 3. Tests

Test that sync_codio_rag_sources produces correct source configs.
Mock indexio.sync_owned_sources if indexio is not installed.

Run: make test
```

---

## M4 — Onboard a Library (Operational)

Use after M1 is complete. This is for onboarding libraries into a target
project's `.codio/` registry.

```
Read the target project's .codio/catalog.yml and .codio/profiles.yml.
Read src/codio/vocab.py for allowed values.

Onboard the following library:

- Name: <LIBRARY_SLUG>
- Kind: <internal | external_mirror | utility>
- Language: <language>
- Repo URL: <url or empty>
- Pip name: <package name or empty>
- Summary: <one-line description>

Project profile:
- Priority: <tier1 | tier2 | tier3>
- Runtime import: <internal | pip_only | reference_only>
- Decision default: <existing | wrap | direct | new>
- Capabilities: <comma-separated tags>

Steps:
1. Add catalog entry to .codio/catalog.yml
2. Add profile entry to .codio/profiles.yml
3. Run `codio validate --root <project>` to confirm consistency
4. If tier1/tier2, create curated note at docs/reference/codelib/libraries/<name>.md
5. Run tests if in the codio repo: make test
```

---

## M5 — Write/Refresh a Curated Library Note

```
Read the target project's .codio/ registry and the library's source code or docs.

Write (or refresh) the curated note for: <LIBRARY_NAME>
Location: docs/reference/codelib/libraries/<LIBRARY_NAME>.md

Cover:
- Scope: what it does and doesn't do
- Strengths: why it's in the registry
- Caveats: limitations, version constraints
- Entry points: key modules/functions/classes
- Integration pattern: how this project uses it (wrap, direct, internal)
- Example usage snippet

Run `codio validate` when done.
```

---

## M6 — Registry Health Check

```
Read the target project's .codio/ registry files.

Perform a full health check:
1. Run codio validate (or the Python validation)
2. Check every tier1/tier2 library has a curated note on disk
3. Check every library with a local path has code at that path
4. List libraries with no capabilities in their profile
5. Summarize findings and suggest fixes
```
