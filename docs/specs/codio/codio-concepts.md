# Codio Concepts

## Conceptual Model

Codio models a project as a searchable catalog of implementation knowledge. The core concepts below define the vocabulary used by the registry, MCP tools, and agent workflows.

## Definitions

### Library

A **library** is a named implementation unit known to Codio. A library may be:

- an internal package
- a project utility module
- a local code collection
- an external mirrored repository

The library is the primary identity object in Codio.

### Mirror

A **mirror** is a local copy of an external codebase retained for reference, study, or selective reuse. A mirror is not automatically a runtime dependency. Its purpose is to preserve implementation knowledge close to the project.

### Curated Library Note

A **curated library note** is a human-maintained reference document that explains how a library should be interpreted within a project. It records scope, strengths, caveats, recommended entry points, and policy decisions.

Curated notes are interpretive documents, not raw registry records.

### Capability

A **capability** is a named problem area or engineering function that a library can address, such as signal filtering, plotting, graph traversal, schema validation, or retrieval.

Capabilities are the bridge between user problems and library discovery.

### Runtime Policy

A **runtime policy** states how a library may participate in execution. Typical policies include:

- internal runtime dependency
- wrapped external dependency
- direct external dependency
- reference only
- optional tooling dependency

Runtime policy makes the difference between searchable knowledge and approved runtime usage explicit.

### Project Profile

A **project profile** is the project-specific interpretation of a library. It expresses priority, default decision, runtime policy, and local references such as curated notes.

The project profile answers: how should this project treat this library?

### Library Catalog

A **library catalog** is the shared metadata layer for all known libraries. It records stable identity-level attributes such as name, language, repository URL, package name, and license.

The library catalog answers: what is this library?

### Capability Evidence

A **capability evidence** record is any concrete support for the claim that a library provides a capability. Evidence may include:

- source file locations
- API entry points
- examples or notebooks
- test cases
- curated notes
- indexed retrieval hits

Capability evidence is how Codio supports decisions with inspectable artifacts rather than unsupported claims.

## Interaction of Concepts

The concepts interact as a layered model:

1. A **library catalog** defines a library’s shared identity.
2. A **project profile** defines local policy for that library.
3. A **capability** links a user need to candidate libraries.
4. **Capability evidence** supports the match between capability and library.
5. A **curated library note** explains project-specific interpretation.
6. A **runtime policy** constrains whether the library is reused, wrapped, imported directly, or treated as reference-only.
7. A **mirror** provides local access when the library is external.

This separation keeps discovery, policy, and implementation evidence distinct.
