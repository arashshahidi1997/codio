# Handoff: `projio init-flow` — Pipeline Flow Scaffolding

**Origin:** codio project, 2026-03-19
**Target:** projio (or projio/packages/pipeio — see architectural note below)
**Status:** ready for implementation

## Summary

Add pipeline flow scaffolding with the standard structure used across pixecog. This was evaluated for codio but rejected — codio is about code reuse discovery, not workflow bootstrapping.

## Architectural Decision: `projio init-flow` vs `pipeio` as a Sibling Package

There are two viable homes for this capability:

### Option A: `projio init-flow` subcommand
Add directly to projio's CLI. Quick to ship, no new package.

### Option B: `projio/packages/pipeio` (recommended long-term)
Pipeline management is a distinct, substantial concern — not just scaffolding, but also:
- Flow scaffolding (`pipeio init-flow`)
- Pipe/flow registry management (the `pipe_flow_mod_registry.yml` lifecycle)
- Pipeline context and session runtime API (currently in `pixecog/code/utils/io/`)
- Snakemake execution wrappers / dry-run / status
- Cross-flow dependency tracking
- Notebook lifecycle (the Makefile-driven jupytext workflow)
- Report generation coordination

This scope is comparable to codio, indexio, or biblio — each of which is its own package. Cramming it into projio risks bloating the orchestrator with domain logic that belongs in a dedicated tool.

**Recommended path**: Create `projio/packages/pipeio` as a sibling package following the same patterns (src-layout, argparse CLI, YAML configs, projio MCP integration). projio delegates pipeline concerns to pipeio the same way it delegates code-reuse concerns to codio and indexing concerns to indexio.

| Concern | projio | pipeio |
|---------|--------|--------|
| `.projio/` namespace | owns | consumes (reads project config) |
| Flow scaffolding | — | `pipeio init-flow --pipe X --flow Y` |
| Pipe/flow registry | — | `pipeio register`, `pipeio list` |
| Pipeline context API | — | `pipeio.context.PipelineContext` |
| Notebook lifecycle | — | `pipeio nb-sync`, `pipeio nb-publish` |
| MCP tools | hosts | `pipeio_list`, `pipeio_status`, etc. |

Either option works for the initial scaffold; the rest of this document describes the requirements regardless of where it lands.

## The Pattern

Every pipeline flow in `pixecog/code/pipelines/` follows this structure:

```
code/pipelines/<pipe>/<flow>/
├── Snakefile              # Snakemake DAG (snakebids + BidsPaths wiring)
├── config.yml             # pybids_inputs, input/output dirs, registry, params
├── Makefile               # Notebook lifecycle (jupytext pair/sync/exec/publish)
├── scripts/               # Rule implementations (snakemake script nodes)
│   └── example_step.py
├── notebooks/             # Exploratory/investigative notebooks
│   └── notebook.yml       # Jupytext pairing + publishing config
├── report/                # RST captions for snakemake report() output wrappers
│   └── workflow.rst
└── _docs/                 # Flow-local documentation
    └── README.md
```

### Reference examples

| Example | Path | Notes |
|---------|------|-------|
| **Complete** | `pixecog/code/pipelines/preprocess/ieeg/` | ~30 rules, 16+ notebooks, full report/ |
| **Template** | `pixecog/code/pipelines/_template/flow/` | Minimal skeleton with placeholders |

## What Each Component Does

### Snakefile
- Imports: `snakemake.utils.min_version`, `snakebids.generate_inputs`, `sutil.repo_root.repo_abs`, `sutil.bids.paths.BidsPaths`
- Loads `config.yml` via `safe_load`
- Sets up `inputs`, `in_paths`, `out_paths` from registry + pybids
- Standard rules: `all`, `registry` (writes output registry YAML), `touch_all`
- Template uses `__PIPE__` / `__FLOW__` placeholders

### config.yml
- `input_dir`, `input_registry` — where BIDS data comes from
- `pybids_inputs` — snakebids filter/wildcard definitions
- `output_dir: "derivatives/__PIPE__"`
- `output_registry: "derivatives/__PIPE__/pipe-__PIPE___flow-__FLOW___registry.yml"`
- `registry:` — nested dict defining output path families and their members (root, datatype, suffix, extension)
- Pipeline-specific params section at the bottom

### Notebook System: The Validation Layer

Notebooks are not an afterthought — they are the **primary mechanism for prototyping and validating analysis approaches** before wiring them into the Snakemake DAG. The workflow is:

1. **Investigate** in a notebook (interactive, exploratory, read-only)
2. **Validate** the approach produces correct results on representative data
3. **Extract** the validated logic into a `scripts/` node
4. **Wire** the script into a Snakemake rule

This means the notebook system must be first-class: properly managed, reproducible, and publishable. It consists of three tightly coupled pieces:

#### `notebooks/` directory structure

Each notebook lives in its **own subdirectory** (avoids sibling file collisions when jupytext generates paired formats):

```
notebooks/
├── notebook.yml                           # config: what to pair, sync, publish
├── explore_registry_bootstrap/            # starter: verify config + paths work
│   ├── explore_registry_bootstrap.py      # source of truth (percent format)
│   ├── explore_registry_bootstrap.ipynb   # paired: for interactive execution
│   └── explore_registry_bootstrap.md      # paired: myst markdown for docs
├── investigate_noise_tfspace_demo/        # prototype: becomes scripts/noise_tfspace/
│   ├── investigate_noise_tfspace_demo.py
│   ├── investigate_noise_tfspace_demo.ipynb
│   └── investigate_noise_tfspace_demo.md
└── review_channel_features/              # review: QC after pipeline runs
    └── review_channel_features.py
```

**Naming conventions** signal intent:
- `explore_*` — lightweight bootstrap / registry exploration
- `investigate_*` — deep prototyping of an approach (the validation step before pipeline wiring)
- `review_*` — post-hoc QC of pipeline outputs

**Jupytext triplet**: `.py` is the source of truth (version-controlled, diff-friendly, percent-format cells). `.ipynb` is generated for interactive execution. `.md` (myst) is generated for documentation publishing. The `.py` header declares the pairing:

```python
# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: title,-all
#     formats: ipynb,py:percent,md:myst
# ---
```

**Bootstrap pattern**: Every investigation notebook starts by loading the flow's context — either directly from `config.yml` or via `PipelineContext`:

```python
# Direct (mirrors Snakefile setup):
flow_dir = Path(__file__).resolve().parents[2]
cfg = safe_load((flow_dir / "config.yml").read_text())
inputs = generate_inputs(repo_abs(cfg["input_dir"]), cfg["pybids_inputs"])
out_paths = BidsPaths(cfg["registry"], repo_abs(cfg["output_dir"]), inputs)

# Or via PipelineContext:
from utils.io import notebook_bootstrap, PipelineContext
repo_root = notebook_bootstrap()
ctx = PipelineContext.from_registry("preprocess", flow="ieeg")
```

**Investigation notebooks document their purpose** with a structured docstring:

```python
"""
Title: investigate_noise_tfspace_demo.py
Status: INVESTIGATION
Objective: Prototype a TF-space noise-characterization workflow ...
Focus: [bullet list of specific questions to answer]
Guardrails: [constraints: read-only, in-memory, etc.]
"""
```

This metadata makes it clear what each notebook validates and whether the approach was accepted or abandoned.

#### `notebook.yml` — Pairing and Publishing Config

Declares which notebooks to manage and where to publish them:

```yaml
publish:
  docs_dir: docs/reports/pipelines/pipe-__PIPE__/flow-__FLOW__/notebooks
  prefix: nb-

entries:
  - path: notebooks/explore_registry_bootstrap/explore_registry_bootstrap.py
    pair_ipynb: true      # generate/maintain .ipynb
    pair_myst: true       # generate/maintain .md (myst)
    publish_myst: true    # copy myst md to docs_dir
  - path: notebooks/investigate_noise_tfspace_demo/investigate_noise_tfspace_demo.py
    pair_ipynb: true
    pair_myst: true
    publish_myst: true
```

Per-entry flags control granularly:
- `pair_ipynb` — whether to create/maintain an `.ipynb` companion
- `pair_myst` — whether to create/maintain a myst `.md` companion
- `publish_ipynb` — copy executed `.ipynb` to `docs_dir`
- `publish_html` — render `.ipynb` → `.html` and copy to `docs_dir`
- `publish_myst` — copy myst `.md` to `docs_dir`

The `prefix` field prepends to published filenames (e.g., `nb-investigate_noise_tfspace_demo.md`).

**Publish destination and pipeio config**: Currently `publish.docs_dir` is hardcoded per `notebook.yml` (an absolute or repo-relative path). In a pipeio-managed world, the publish destination should instead be recorded in the **pipeio config for that workflow** — e.g., in `.projio/pipeio/<pipe>/<flow>.yml` or a `pipeio` section within the flow's `config.yml`:

```yaml
# .projio/pipeio/preprocess/ieeg.yml (or equivalent)
pipe: preprocess
flow: ieeg
publish:
  notebooks_dir: docs/reports/pipelines/pipe-preprocess/flow-ieeg/notebooks
  reports_dir: docs/reports/pipelines/pipe-preprocess/flow-ieeg/reports
  prefix: nb-
```

The Makefile (or a future `pipeio nb-publish` command) would read this config to resolve the destination, rather than each `notebook.yml` embedding its own path. This centralizes publish routing in pipeio's domain — the notebook config declares *what* to publish (entries + format flags), while pipeio config declares *where* it goes. This separation also makes it possible to change publish destinations project-wide without editing every `notebook.yml`.

#### `Makefile` — Notebook Lifecycle Engine

The Makefile is the automation layer that operates on `notebook.yml`. It is **config-driven** — all decisions about what to pair/sync/publish come from `notebook.yml`, not from the Makefile itself.

**Configuration variables** (overridable per-flow):
```makefile
CONDA        ?= /storage/share/python/environments/Anaconda3/condabin/conda
ENV          ?= cogpy
NOTEBOOK_CFG ?= notebooks/notebook.yml
```

**Lifecycle targets** (in intended execution order):

| Target | What it does |
|--------|-------------|
| `nb-list` | Print resolved entry paths from `notebook.yml` |
| `nb-pair` | Create missing `.ipynb` / `.md` files and set jupytext formats. Idempotent — skips existing pairs |
| `nb-status` | Dry-run: show what `nb-sync` would do (which direction each file would sync) |
| `nb-sync` | **SAFE directional sync** — newer file wins. If `.ipynb` newer → update `.py` from it. If `.py` newer → update `.ipynb` (preserving outputs/metadata via `--update`). Never uses `jupytext --sync` which can have surprising bidirectional effects |
| `nb-exec-all` | Execute all `.ipynb` files in-place via `jupyter nbconvert --execute --inplace` |
| `nb-publish-ipynb` | Copy executed `.ipynb` to `docs_dir` with prefix |
| `nb-publish-html` | Render `.ipynb` → `.html` via `nbconvert` and copy to `docs_dir` |
| `nb-publish-myst` | Copy/generate myst `.md` to `docs_dir` |
| `nb-publish` | All-in-one: pair → sync → exec → publish (ipynb + html + myst) |
| `smk-touchall` | Touch all snakemake outputs (force rebuild during development) |

**Sync safety model**: The sync logic is intentionally conservative:
- `.ipynb` newer than `.py` → `jupytext --to py <ipynb>` (overwrite `.py` from notebook)
- `.py` newer than `.ipynb` → `jupytext --update --to notebook <py>` (`--update` preserves cell outputs and metadata)
- Same timestamp → skip (already in sync)
- Only one file exists → create the other

**Evolution note**: The ieeg Makefile has grown beyond the template with:
- `NB=<path>` filter — sync/pair only specific notebooks
- `TOUCHED=true` — use `git diff` to auto-detect which notebooks changed since `GIT_BASE`
- These should be folded back into the canonical template

### scripts/

Each script follows the snakemake mock pattern for standalone debugging:
```python
if "snakemake" not in globals():
    snakemake = SimpleNamespace(
        input=SimpleNamespace(source="..."),
        output=SimpleNamespace(result="..."),
    )
```
Template provides `example_step.py` with this pattern. Scripts are typically extracted from validated investigation notebooks — the notebook proves the approach works, then the core logic is refactored into a script node that Snakemake can orchestrate.

### report/
- One `.rst` file per reportable output (short captions, 1-2 lines)
- Referenced by snakemake's `report()` wrapper in Snakefile rules:
  ```python
  output:
      featuremap=report(
          out_paths("badlabel", "featuremap"),
          caption="report/featuremap.rst",
          category="sub-{subject}",
          subcategory="featuremap",
          labels={"figure": "ses-{session}"}
      )
  ```
- Template should scaffold `report/workflow.rst` as a starter

### _docs/
- Flow-local documentation, suggested structure: `mod-<mod>/..._theory.md`, `..._specification.md`, `..._delta.md`
- Can be published to `docs/explanation/pipelines/pipe-<PIPE>/flow-<FLOW>/`

## Proposed CLI

```bash
projio init-flow --pipe <PIPE> --flow <FLOW> [--root <PROJECT_ROOT>]
```

- Creates `code/pipelines/<PIPE>/<FLOW>/` with all skeleton files
- Substitutes `__PIPE__` → `<PIPE>` and `__FLOW__` → `<FLOW>` in all templates
- Does not overwrite existing files (use `--force` to override)

## Implementation Considerations

1. **Template storage**: Store flow templates alongside codio-style templates in `src/projio/templates/flow/` (or similar). The existing `_template/flow/` in pixecog is the source of truth for the skeleton.

2. **Makefile drift**: The notebook Makefile is nearly identical across flows but has diverged (ieeg has `NB`/`TOUCHED` filtering that the template lacks). Options:
   - (a) **Shared include**: `include ../../_shared/Makefile.notebooks` — flows only override variables
   - (b) **Canonical copy**: scaffold always writes the latest version; accept drift
   - (c) **Symlink**: all flows link to one copy
   - Recommendation: **(a)** shared include, with per-flow variable overrides only

3. **Placeholder substitution**: `__PIPE__` and `__FLOW__` appear in:
   - `config.yml` (`output_dir`, `output_registry`)
   - `_docs/README.md`
   - `scripts/example_step.py` (mock paths)

4. **notebook.yml**: Scaffold with `publish.docs_dir` pointing to `docs/reports/pipelines/pipe-<PIPE>/flow-<FLOW>/notebooks` and an empty `entries: []`

5. **report/**: Scaffold with just `workflow.rst` containing `<FLOW> pipeline report`

6. **Integration with existing pipelines**: The `_template/flow/` directory in pixecog can be deprecated once projio owns the scaffold. Existing flows are untouched.

## Related: Pipeline Runtime API (`utils.io`)

The scaffold creates the static file structure, but there is also a runtime API in `pixecog/code/utils/io/` that notebooks and scripts use to interact with flows programmatically. This is relevant context for projio because the scaffold should produce files that are compatible with this API.

### `PipelineRegistry` (`registry.py`)

A registry of all pipe/flow definitions, loaded from `workflow/pipe_flow_mod_registry.yml`. Resolves `(pipe, flow)` → `config.yml` path. Key classes:

- `PipelineRegistry` — wrapper around the registry YAML payload
  - `.load_default()` — loads the default registry file
  - `.get(pipe=, flow=)` → `PipelineEntry`
- `PipelineEntry` — frozen dataclass: `pipe`, `flow`, `meta`, `config_path`
  - `.load_config()` → parsed config dict

The registry locates config files via `flow_meta.code.config_path` or by scanning `flow_meta.code.entrypoints[].flow_root + "/config.yml"`.

**Implication for `init-flow`**: When scaffolding a new flow, projio should also offer to register it in the pipe/flow registry (or at least print instructions).

### `PipelineContext` (`context.py`)

The central runtime object for notebooks and scripts. Wraps a flow's `config.yml` and provides:

- **Construction**: `PipelineContext.from_registry(pipe, flow=)` or `PipelineContext.from_config(pipe, flow, cfg, cfg_path)`
- **Path API**: `ctx.pattern(group, product)` → BIDS path pattern string; `ctx.path(group, product, **entities)` → resolved `Path`; `ctx.have(group, product, **entities)` → bool
- **Registry introspection**: `ctx.groups()` → list of output registry families; `ctx.products(group)` → list of member names
- **Session iteration**: `ctx.iter_sessions(base_input=, entities=)` → list of `Session` objects
- **Stage handles**: `ctx.stage(name)` → `Stage` object (supports aliases via `cfg['stage_aliases']`)
- **Expansion**: `ctx.expand(group, product, filter=, max_n=)` → list of all matching paths across sessions

Internally it uses `snakebids.generate_inputs` + `sutil.bids.paths.BidsPaths` to wire up path resolution from the config's `pybids_inputs`, `input_registry`, and `registry` sections. It also auto-discovers extra input sources via the `input_dir_<name>` / `input_registry_<name>` naming convention.

### `Session` (`session.py`)

Frozen entity container delegating to `PipelineContext`:
- `.get(group, product, **overrides)` → Path
- `.have(group, product)` → bool
- `.bundle(group, bundle)` → `{member: Path}` dict

### `Stage` (`stage.py`)

Handle to a single output-registry group:
- `.paths(sess, members=)` → `{member: Path}` dict
- `.have(sess, members=)` → bool (all members exist)
- `.resolve(sess, prefer=[...])` → first stage name in preference list that exists on disk

### `notebook_bootstrap` (`bootstrap.py`)

Adds `<repo>/code` and `<repo>/code/lib/*/src` to `sys.path` so notebooks can `import utils` and editable in-repo libraries. Every notebook starts with:
```python
from utils.io import notebook_bootstrap, PipelineContext
repo_root = notebook_bootstrap()
ctx = PipelineContext.from_registry("preprocess", flow="ieeg")
```

### Design implications for projio scaffolding

1. **`config.yml` must be compatible** with `PipelineContext.from_config()` — it expects `input_dir` (or `bids_dir`), `pybids_inputs`, `output_dir`, `registry`, and optionally `input_registry`.

2. **The output `registry:` section in `config.yml`** defines the path families. Each family has `base_input`, `bids.root`, `bids.datatype`, and `members: {name: {suffix, extension}}`. The scaffold template already has this structure.

3. **`notebook.yml` + bootstrap pattern**: The scaffold should include a starter notebook that uses `notebook_bootstrap()` + `PipelineContext.from_registry()` to demonstrate the standard entry point.

4. **Pipe/flow registry entry**: `init-flow` should optionally append to `workflow/pipe_flow_mod_registry.yml` with:
   ```yaml
   pipes:
     <PIPE>:
       flows:
         <FLOW>:
           code:
             config_path: "code/pipelines/<PIPE>/<FLOW>/config.yml"
             entrypoints:
               - flow_root: "code/pipelines/<PIPE>/<FLOW>"
                 snakefile: "Snakefile"
   ```
