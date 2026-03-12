# Codio Architecture

## Architectural Intent

Codio is a layered discovery system. Each layer adds structure to code assets so they can be searched, interpreted, and used by humans or agents.

## Layers

### 1. Physical Code Library

The physical code layer contains the actual artifacts:

- internal packages
- project utilities
- examples and notebooks
- external mirrors

This is the source material that Codio indexes and describes.

### 2. Library Catalog

The library catalog records stable identity metadata for known libraries. It is project-agnostic where possible and provides the canonical registry namespace.

### 3. Project Profile

The project profile adds local interpretation to catalog entries. It records project-specific priority, runtime policy, default implementation decision, and links to curated notes.

### 4. Curated Notes

Curated notes provide high-signal narrative guidance for important libraries. They explain intended use, important caveats, known capabilities, and recommended integration patterns.

### 5. Corpus Search

Corpus search indexes code and related documentation so users and agents can retrieve candidate implementations by capability, pattern, or problem statement.

### 6. MCP Query Interface

The MCP layer exposes structured access to catalog data, validation, vocabulary, and discovery results. It is the primary machine interface for Codio-aware agents.

### 7. Agent Skills

Agent skills operationalize Codio inside workflows. They coordinate search, interpretation, note maintenance, and implementation decisions.

## Layer Relationships

```text
physical code assets
    ↓
library catalog
    ↓
project profile
    ↓
curated notes + corpus search
    ↓
MCP query interface
    ↓
agent workflows
```

## Data Flow

```text
source code / mirrors / examples
    ↓ index and register
catalog metadata + project policy
    ↓ interpret and retrieve
candidate libraries + capability evidence
    ↓ inspect and decide
reuse / wrap / direct / new
```

## Architectural Constraints

- Mirrors are reference assets unless explicitly approved for runtime use.
- Retrieval alone is insufficient; Codio must also expose policy context.
- Registry metadata must remain useful even if curated notes are missing.
- Agent workflows should compose MCP queries with corpus search rather than bypassing the registry layer.
