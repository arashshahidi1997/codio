# Prompt: Add Code-Aware Backends to indexio

> Run this prompt inside the **indexio** repo with Claude Code.

---

## Context

indexio is a config-driven RAG indexing tool. It currently has hard-coded backends:

- **Chunking**: `langchain_text_splitters.RecursiveCharacterTextSplitter` (naive character splitting)
- **Embedding**: `langchain_huggingface.HuggingFaceEmbeddings` (single backend)
- **Vector store**: ChromaDB only
- **LLM**: Ollama / OpenAI-compatible (already has string-dispatch pattern in `chat/pipeline.py`)

Ecosystem packages (codio, biblio, etc.) register sources via `sync_owned_sources()`. codio registers **code files** (`**/*.py`) as sources. The problem: naive character chunking destroys code structure. A function split mid-body produces useless chunks.

## Goal

Add a **pluggable chunking backend system** so that code sources get **structure-aware chunking** while document sources keep the existing text splitter. This is the highest-impact change — it directly improves retrieval quality for code.

## Requirements

### 1. Chunking Backend Abstraction

Create a minimal backend interface in `src/indexio/chunkers.py`:

```python
class Chunker(Protocol):
    def chunk(self, text: str, metadata: dict) -> list[Document]: ...
```

Implement three backends:

#### a) `text` (default, existing behavior)
- Wraps `RecursiveCharacterTextSplitter`
- Uses `chunk_size_chars` and `chunk_overlap_chars` from config
- This is what all current sources use — no behavior change

#### b) `code` (tree-sitter based)
- Uses `tree-sitter` + language grammars (`tree-sitter-python`, `tree-sitter-javascript`, etc.)
- Chunks by **semantic code units**: functions, classes, methods
- Falls back to `text` chunker for files where parsing fails or language is unsupported
- Each chunk's metadata includes: `symbol_name`, `symbol_type` (function/class/method), `language`
- Start with Python support only. Other languages can be added later.

#### c) `ast` (Python ast module, no native dependency)
- Uses Python's built-in `ast` module — zero extra dependencies
- Extracts functions and classes as chunks
- Lighter alternative to tree-sitter when only Python is needed
- Falls back to `text` for non-Python files

### 2. Config Schema Changes

Add an optional `chunker` field to `SourceConfig` in `config.py`:

```yaml
sources:
  - id: "docs"
    corpus: "docs"
    glob: "docs/**/*.md"
    # chunker defaults to "text" — no change for existing configs

  - id: "codio-src-mylib"
    corpus: "codelib"
    glob: "src/mylib/**/*.py"
    chunker: "code"  # use tree-sitter chunking
```

Also add a top-level `chunkers` config section for backend-specific settings:

```yaml
chunkers:
  code:
    languages: ["python"]  # which tree-sitter grammars to load
    max_chunk_chars: 2000   # split very large functions
  ast:
    include_docstrings: true
```

**Default**: If `chunker` is omitted, use `"text"`. Existing configs must work unchanged.

### 3. Integration with Build Pipeline

In `build.py`, the `_split_docs()` function currently hard-codes `RecursiveCharacterTextSplitter`. Change it to:

1. Accept a `chunker` parameter (string name from source config)
2. Dispatch to the appropriate backend via a factory function
3. Keep the existing signature compatible — when `chunker` is None or `"text"`, behavior is identical

The factory pattern should match the existing LLM backend dispatch in `chat/pipeline.py` (simple string-based selection, no over-engineered plugin registry).

### 4. Dependencies

- `tree-sitter` and `tree-sitter-python` should be **optional dependencies** (like the chat extras)
- Add a `[code]` extras group in `pyproject.toml`:
  ```toml
  [project.optional-dependencies]
  code = ["tree-sitter>=0.20", "tree-sitter-python>=0.20"]
  ```
- The `ast` chunker has no extra dependencies (stdlib only)
- If tree-sitter is not installed and `chunker: "code"` is requested, raise a clear error with install instructions

### 5. Metadata Enrichment

Code chunkers should add structured metadata to each chunk's `Document.metadata`:

```python
{
    "source_id": "codio-src-mylib",
    "source_path": "src/mylib/utils.py",
    "chunk_index": 3,
    "symbol_name": "parse_config",      # new
    "symbol_type": "function",           # new: function | class | method
    "language": "python",                # new
    "start_line": 45,                    # new
    "end_line": 72,                      # new
}
```

This metadata enables **symbol-level filtering** in `query.py` — e.g., "find functions related to config parsing".

### 6. Query Enhancement (optional, lower priority)

Add an optional `symbol_type` filter to `query_index()`:

```python
def query_index(config, query, corpus=None, symbol_type=None, ...):
```

This lets codio's `discover` command search specifically for functions, classes, etc.

## Design Constraints

- **Config-first**: Backend selection lives in YAML, not auto-detected
- **Lazy imports**: tree-sitter imported inside the code chunker, not at module level
- **No behavior change for existing configs**: `chunker` field is optional, defaults to `"text"`
- **Minimal abstraction**: Use the same pattern as LLM backends (string dispatch + factory function). Do NOT create an abstract base class hierarchy or plugin registry.
- **Test with real code**: Add tests that chunk actual Python files and verify symbol extraction

## Files to Modify

- `src/indexio/config.py` — add `chunker` field to `SourceConfig`, add `ChunkerConfig` dataclass
- `src/indexio/build.py` — modify `_split_docs()` to dispatch to chunker backends
- `src/indexio/query.py` — add optional `symbol_type` filter
- `pyproject.toml` — add `[code]` optional dependencies

## Files to Create

- `src/indexio/chunkers.py` — chunker backends (text, code, ast)

## Files to Update for Tests

- `tests/test_indexio.py` — config parsing tests for new fields
- `tests/test_chunkers.py` (new) — unit tests for each chunker backend

## Out of Scope

- Graph-RAG / knowledge graph construction (future work)
- Non-Python tree-sitter grammars (add later)
- Embedding backend abstraction (separate task)
- Vector store abstraction (separate task)

## Acceptance Criteria

1. `indexio build` with no config changes produces identical output (backward compatible)
2. A source with `chunker: "code"` chunks Python files by function/class
3. A source with `chunker: "ast"` chunks Python files using stdlib ast
4. Chunk metadata includes symbol_name, symbol_type, language, start_line, end_line
5. Missing tree-sitter raises ImportError with install instructions
6. All existing tests pass
7. New tests cover each chunker backend
