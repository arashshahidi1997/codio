# Codio Agent Skills

## Purpose

Codio is designed for agent use as much as for human use. This document defines the expected workflows that operate on Codio data and retrieval surfaces.

## codelib-discovery

### Role

`codelib-discovery` searches internal libraries, utilities, examples, mirrors, and curated notes before implementation begins.

### Responsibilities

- translate a user problem into capability-oriented search queries
- retrieve candidate libraries and supporting evidence
- inspect project profile metadata
- summarize likely implementation paths
- recommend one of `existing`, `wrap`, `direct`, or `new`

### Expected Output

The workflow should return a small set of candidate libraries with enough evidence to support a decision rather than a long undifferentiated search dump.

## codelib-update

### Role

`codelib-update` maintains Codio’s registry and curated reference layer.

### Responsibilities

- add or update library catalog entries
- add or update project profiles
- create or refresh curated library notes
- validate vocabulary and references
- trigger or coordinate index refresh where needed

### Expected Output

The workflow should leave the registry internally consistent and the affected library easier to discover in future sessions.

## library-study

### Role

`library-study` performs deeper structured analysis of one or more external libraries. It is intended for cases where a quick discovery pass is insufficient.

### Parallel Analysis Pattern

```text
agent orchestrator
   ↓
spawn parallel analysis agents
   ↓
each agent studies a library
   ↓
results aggregated into notes
```

### Typical Inputs

- local mirrors
- GitHub repositories
- package documentation
- documentation fetched through web retrieval tools

### Typical Outputs

- comparative capability summaries
- recommended entry points
- caveats and integration risks
- curated notes suitable for the Codio reference layer

## Agent Design Principles

- Agents should search before proposing new implementation.
- Agents should prefer structured registry and MCP outputs over ad hoc file scraping.
- Agents should separate evidence collection from implementation recommendation.
- Deep study should be parallelizable because library analysis is naturally decomposable.
