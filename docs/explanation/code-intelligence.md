# Code Intelligence in Codio

## What codio does today

Codio provides metadata-based search over a curated registry of libraries.
The `discover()` function matches a query string against three fields in the
registry: capability tags (exact match), library names (substring), and
summaries (substring).  Results are ranked by priority tier and match type,
and the top candidate drives a recommended engineering decision (`existing`,
`wrap`, `direct`, or `new`).

The `study_library()` and `compare_libraries()` functions produce structured
analyses — strengths, caveats, entry points, integration notes — but these
are derived entirely from registry metadata (kind, priority, runtime import
policy, license, declared capabilities).  No source code is read.

The MCP tools (`codio_list`, `codio_get`, `codio_registry`, `codio_vocab`,
`codio_validate`) expose the same metadata through a machine interface.
They query catalog and profile entries; they do not inspect code.

The `codio rag sync` command registers two source types with indexio:

- `codio-notes` — a glob over curated Markdown notes
  (`docs/reference/codelib/libraries/**/*.md`)
- `codio-catalog` — the catalog YAML file itself

This is the extent of codio's integration with retrieval infrastructure.
No source trees, test files, docstrings, or example code are registered.
No retrieval queries are issued from within codio.


## What code intelligence means for codio

There is a gap between what codio provides today and what an agent needs to
answer "what code already exists that solves this problem?"

Metadata search tells you a library exists and what its declared capabilities
are.  Code intelligence means being able to answer deeper questions:

- What functions or classes implement a specific capability?
- What are the actual call signatures and return types?
- How is this library used elsewhere in the project?
- Are there examples or tests that demonstrate the intended usage?
- What patterns does this code follow, and are they compatible with mine?

Codio should not try to answer all of these questions itself.  But it should
make the right source material available so that retrieval systems can answer
them.  The distinction is between *defining what is indexable* and *performing
the indexing*.


## Indexable source types

A library known to codio may have several kinds of source material that are
relevant for code intelligence.  Not all libraries have all types.

**Curated notes** (already registered).  Hand-written Markdown documents that
explain when and how to use a library.  These are high-signal, low-volume
sources that work well for retrieval.

**Catalog metadata** (already registered).  The YAML catalog provides
structured identity information.  Useful as context alongside retrieved
content, less useful as a retrieval target on its own.

**Source trees**.  Internal libraries and external mirrors have a `path` field
pointing to their local source code.  These source trees contain the actual
implementations — modules, functions, classes — that agents need to
understand.  This is the highest-value unregistered source type.

**Tests and examples**.  Test files demonstrate intended usage patterns and
edge cases.  Example directories, when they exist, show integration
approaches.  Both are strong signals for "how do I use this?"

**Docstrings and inline documentation**.  Extracted from source files, these
provide function-level guidance without requiring full code understanding.
However, extracting them requires language-specific parsing, which raises
questions about where the extraction boundary belongs.

**Attached repositories**.  External libraries that are not mirrored locally
but have a `repo_url` may be cloned or fetched for indexing.  This is a
more complex scenario that involves network access and storage.


## Indexing boundaries

The core question is: what does codio own versus what does indexio own?

### Codio owns

- **Source definitions**: codio knows which libraries exist, where their code
  lives (`path`), where their curated notes are, and what metadata describes
  them.  Codio is the authority on the *manifest* of indexable sources.

- **Source registration**: codio generates source descriptors (id, corpus,
  glob or path) and registers them with indexio via `sync_owned_sources()`.
  This is the integration contract.

- **Entity mapping**: codio defines the relationship between a source
  descriptor and a library entity.  When retrieval returns a chunk from a
  source, the source id should map back to a codio library name, kind,
  priority, and decision policy.

- **Registry queries**: codio answers "what libraries exist?", "what is the
  policy for this library?", and "what capabilities are declared?"

### Indexio owns

- **Chunking**: splitting source files into retrieval-appropriate segments.
  This involves decisions about chunk size, overlap, and boundary detection
  that are general to all text, not specific to code libraries.

- **Embedding and indexing**: converting chunks to vectors and storing them
  in a searchable index.

- **Retrieval**: executing similarity search against the index and returning
  ranked results with source attribution.

- **Index lifecycle**: building, updating, and invalidating indexes as
  source material changes.

### The boundary in practice

Codio should not embed, chunk, or search.  Codio should produce a complete
manifest of sources — with enough metadata for indexio to attribute results
back to codio entities.  The `sync_owned_sources()` contract already
supports this pattern; codio just needs to register more source types.

The source descriptors that codio produces should include:

- A stable source id that codio can map back to a library name
- The corpus name (e.g., `codelib`)
- A path or glob pointing to the source material
- Optional metadata (library name, kind, language) to support filtering


## Retrieval outputs needed by agents

When an agent runs the `codelib-discovery` skill and finds candidates via
metadata search, it often needs to go deeper.  The following retrieval
outputs support that deeper investigation:

**Capability evidence**.  Concrete code snippets or documentation passages
that demonstrate a library provides a specific capability.  This moves
beyond the declared capability tag to actual proof.

**Entry points**.  The main modules, classes, or functions an integrator
should start with.  Today `study_library()` derives these from the `path`
and `pip_name` fields.  Retrieval over source code can surface the actual
public API surface.

**Usage patterns**.  Examples of how the library is imported and called
within the project.  These come from test files, example directories, or
other project code that depends on the library.

**Integration constraints**.  Information about thread safety, async
compatibility, required initialization, or configuration that affects how
the library can be used.  Often found in docstrings and README files.

**Version and compatibility notes**.  Which versions are in use, known
incompatibilities, deprecation warnings.  Some of this lives in curated
notes, some in requirements files or lock files.

The key requirement is that retrieval results carry enough provenance to
link back to a codio entity.  An agent receiving a code chunk needs to know:
this chunk came from library X, which has priority tier1, decision policy
"existing", and runtime import "internal".  Without that link, the retrieval
result is just text without actionable context.


## Integration boundary with indexio

The current integration works through a single function: `sync_codio_rag_sources()`
in `src/codio/rag.py`.  It produces source descriptors and passes them to
`indexio.sync_owned_sources()`.

### Current source registration

```python
# From src/codio/rag.py — owned_codio_sources()
[
    {"id": "codio-notes",   "corpus": "codelib", "glob": ".../**/*.md"},
    {"id": "codio-catalog", "corpus": "codelib", "path": "...catalog.yml"},
]
```

Two sources, both in the `codelib` corpus.  The source ids are constants
defined in `rag.py`.

### Expanded source registration

To support code intelligence, codio should register additional sources
derived from the catalog.  For each library that has a `path` field pointing
to a local directory:

```python
{
    "id": f"codio-src-{library_name}",
    "corpus": "codelib",
    "glob": f"{library_path}/**/*.py",
    "metadata": {"library": library_name, "kind": kind},
}
```

This would let indexio index the actual source trees of known libraries
while preserving the link back to the codio entity.

The same pattern extends to test files, example directories, or any other
path-based source material that codio can identify from its registry.

### Mapping retrieval results back to codio entities

When an agent retrieves chunks from the `codelib` corpus, it needs to
resolve the source id back to a codio library.  This requires a convention:

- Source ids use a prefix scheme: `codio-src-{name}`, `codio-notes`,
  `codio-catalog`
- Codio provides a lookup function that maps a source id to a library
  record, or `None` for corpus-level sources like the catalog
- Agents call `codio get {name}` after retrieval to get the full policy
  context for a matched library

This keeps the retrieval loop clean: search via indexio, contextualize via
codio.


## Staged implementation path

### Phase 1: Expand source registration

Register source trees for libraries that have a local `path`.  This is a
change to `owned_codio_sources()` in `rag.py` — iterate the catalog,
produce a source descriptor for each library with a non-empty `path` field,
and include the library name in the source id.

This requires no new dependencies, no new CLI commands, and no changes to
indexio.  It uses the existing `sync_owned_sources()` contract.

Outcome: indexio can now index the actual code of known libraries.  Agents
can retrieve code chunks and link them back to codio entities via source id
conventions.

### Phase 2: Source id resolution

Add a function to map source ids back to library records.  Expose this
through a CLI subcommand (`codio resolve-source <source-id>`) and an MCP
tool.  This closes the loop: retrieval returns a source id, codio resolves
it to a library with full metadata and policy.

### Phase 3: Richer source manifests

Extend source registration to include:

- Test directories associated with libraries (requires a convention or a
  new catalog field for test paths)
- Example directories
- README and documentation files within source trees

Each gets its own source id pattern so agents can distinguish between
implementation code, tests, and documentation in retrieval results.

### Phase 4: Retrieval-augmented discovery

Extend `discover()` to optionally call indexio for retrieval when metadata
search returns no candidates or low-confidence results.  This is the point
where codio begins to issue retrieval queries rather than just registering
sources.  It should be opt-in and require indexio to be installed and
configured.

### Future considerations

- Registering attached repositories (libraries with `repo_url` but no local
  `path`) would require a fetch or clone step, adding complexity around
  network access and storage
- Language-specific source analysis (AST parsing, type extraction) could
  improve the quality of source descriptors but would add per-language
  dependencies
- Cross-project source sharing (the same library indexed in multiple
  projects) needs coordination at the indexio level, not within codio


## What codio should NOT do

**General-purpose code search**.  Codio is scoped to libraries known to its
registry.  Searching arbitrary code across a project is a different tool's
job.  Codio's value is that it searches within a curated, policy-annotated
set of libraries.

**IDE integration**.  Codio operates through CLI, MCP tools, and agent
skills.  It does not provide editor plugins, LSP servers, or real-time
code completion.  These concerns belong to tools that operate at the
keystroke level, not the decision level.

**Language-specific parsing**.  Codio should not contain Python AST parsers,
JavaScript analyzers, or any language-specific code understanding.  If
source-level analysis is needed, it should be handled by indexio's chunking
layer or by a separate tool that produces language-neutral summaries.
Codio's role is to know *what* to index, not *how* to parse it.

**Embedding or vector storage**.  Codio defines sources; indexio builds
indexes.  Introducing vector storage into codio would duplicate indexio's
responsibility and create a maintenance burden for a concern that is
already handled elsewhere in the ecosystem.

**Dependency resolution**.  Codio records what libraries exist and what
their packages are called.  It does not resolve dependency trees, check
version compatibility, or manage installations.  Package managers and lock
files handle this.

**Runtime code instrumentation**.  Codio is a pre-implementation tool.  It
answers questions before code is written.  It does not trace execution,
profile performance, or monitor runtime behavior.
