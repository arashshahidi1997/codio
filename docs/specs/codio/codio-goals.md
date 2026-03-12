# Codio Goals

## Purpose of the Goals

This document defines the design goals for Codio. These goals constrain implementation choices and explain what the subsystem must optimize for.

## Discovery-First Engineering

Codio must make discovery the default step before implementation. A user or agent should be able to inspect relevant prior art quickly enough that searching existing code is cheaper than writing a new version from memory.

This goal implies:

- searchable code and notes must be available early in the workflow
- query results must support engineering decisions, not only retrieval
- the system must prioritize evidence of reuse over novelty

## Agent Usability

Codio must expose an agent-first query surface. Agents should be able to ask for catalogs, single-library metadata, vocabulary, validation status, and retrieval results without relying on ad hoc file parsing.

This goal implies:

- a stable MCP tool interface
- structured outputs rather than prose-only responses
- deterministic fields for downstream planning and validation

## Reusable Registry Schema

Codio must define a registry format that separates library identity from project policy. The same catalog entry should be reusable across projects, while each project can declare its own interpretation, priority, and runtime decision.

This goal implies:

- shared metadata belongs in a library catalog
- local policy belongs in a project profile
- registry semantics must remain understandable without repository-specific assumptions

## Project Portability

Codio should be portable across repositories with different domains, language mixes, and mirror strategies. It must not assume a single programming language, a single packaging system, or a single kind of codebase.

This goal implies:

- language and runtime metadata must be explicit
- mirrors must be treated as optional reference assets
- concept names should generalize beyond one project

## Minimal Maintenance Burden

Codio must improve discovery without creating heavy documentation debt. Registry updates and curated notes should be simple enough that teams can keep them current.

This goal implies:

- only high-value metadata should be mandatory
- validation tooling should detect stale or broken references
- curated notes should be reserved for important libraries, not every artifact

## Reproducible Knowledge

Codio should turn informal implementation memory into reproducible project knowledge. A future user or agent should be able to reconstruct why a library was preferred, wrapped, or rejected.

This goal implies:

- registry state should be versioned with the project
- curated notes should record scope, caveats, and intended usage
- discovery outputs should support auditable engineering decisions
