# Codio Overview

## What Codio Is

Codio is a code intelligence and reuse discovery subsystem for project-centric engineering. Its function is to answer a practical question before implementation begins:

> What code already exists in this project or its mirrors that solves this problem?

Codio treats source code, local utilities, mirrors, examples, and curated library notes as searchable engineering knowledge. It is designed for both human use and agent use.

## Why It Exists

Research and engineering projects accumulate reusable logic across internal packages, copied experiments, mirrored upstream libraries, and notebooks. Without a discovery layer, that prior art is difficult to find, easy to duplicate, and rarely turned into explicit implementation decisions.

Codio exists to make reuse discoverable before new code is written. It shifts the default behavior from implementation-first to discovery-first engineering.

## Relationship to Biblio, Notio, and Texio

The broader ecosystem separates knowledge by artifact type.

| Subsystem | Primary Object | Core Question |
|---|---|---|
| `biblio` | papers and citations | What published work defines this method? |
| `notio` | notes and project memory | What has already been decided or observed? |
| `texio` | indexed corpora and retrieval | Where can relevant text be found quickly? |
| `codio` | code libraries and mirrors | What implementation already exists? |

Codio depends on the same general retrieval infrastructure as the other subsystems, but its outputs are implementation-oriented rather than bibliographic or narrative.

## The Repo-Centric Research Model

Codio assumes that a project repository is not only a runtime artifact but also a research environment. The repository contains:

- internal packages that define canonical project APIs
- local utilities that encode conventions
- mirrored external libraries retained as reference material
- notebooks and examples that show real usage patterns
- curated notes that explain how a library should be interpreted inside the project

In this model, code discovery is a form of applied research. The repository is the local corpus of engineering evidence.

## Why Code Reuse Discovery Matters

Code reuse discovery matters because implementation decisions are expensive and sticky. If a project rewrites logic that already exists, it creates avoidable maintenance cost and weakens consistency. If it imports an external library without understanding how it fits the project, it creates integration debt.

Codio reduces those risks by making prior art visible and by structuring the possible outcomes of discovery:

- reuse internal code
- wrap an external library behind project APIs
- use a dependency directly
- implement something new only when justified
