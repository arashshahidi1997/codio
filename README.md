# codio

Code intelligence and reuse discovery for research repositories.

Codio answers a practical question before implementation begins:
*What code already exists that solves this problem?*

It maintains a two-layer registry — a **catalog** of library identity (name, language, repo, license) and a **project profile** of local policy (priority, runtime import rules, capability tags) — so agents and humans can search before they build.

## Install

```bash
pip install codio
```

## Quick start

```bash
codio init                          # scaffold .codio/ in your project
codio list                          # list registered libraries
codio discover "signal-processing"  # search by capability
codio get mylib                     # full library record
codio validate                      # check registry consistency
codio vocab                         # show controlled vocabulary
codio study mylib                   # structured library analysis
codio compare lib1 lib2             # compare libraries side-by-side
```

## Registry model

Codio separates **what a library is** from **how your project uses it**:

- **Catalog** (`.codio/catalog.yml`) — shared, project-agnostic metadata: name, kind, language, repo URL, package name, license, local source paths.
- **Profile** (`.codio/profiles.yml`) — project-local interpretation: priority tier, runtime import policy, decision default, capability tags, curated note path.

Fields use a controlled vocabulary (`codio vocab`): `kind` (internal, external_mirror, utility), `runtime_import` (internal, pip_only, reference_only), `decision_default` (existing, wrap, direct, new), `priority` (tier1, tier2, ...).

## MCP integration

Codio exposes tools through the projio MCP server:

| Tool | Description |
|------|-------------|
| `codio_list` | Filtered library listing |
| `codio_get` | Full library record |
| `codio_registry` | Full registry snapshot |
| `codio_vocab` | Controlled vocabulary |
| `codio_validate` | Registry consistency check |
| `codio_discover` | Capability search across libraries |
| `codio_add_urls` | Add libraries from GitHub/GitLab URLs |

## Agent skills

- **codelib-discovery** — search before implement: returns candidates with evidence and recommends a decision (reuse, wrap, depend, or implement new).
- **codelib-update** — maintain registry and curated notes.
- **library-study** — deep parallel analysis of external libraries.

## Ecosystem

Codio is part of the [projio](https://github.com/arashshahidi1997/projio) ecosystem alongside [indexio](https://github.com/arashshahidi1997/indexio) (semantic search), [biblio](https://github.com/arashshahidi1997/biblio) (bibliography), and [notio](https://github.com/arashshahidi1997/notio) (structured notes).

## Documentation

See the [full documentation](docs/index.md) for tutorials, how-to guides, and reference.

```bash
pip install codio[dev]
mkdocs serve
```
