# Codio

**Code reuse discovery for project-centric engineering.**

Codio answers a practical question before implementation begins:
*What code already exists in this project that solves this problem?*

It treats internal packages, utilities, mirrored libraries, and curated notes as searchable engineering knowledge. Codio is a standalone CLI tool installed once and invoked inside any project.

## Start here

- **New to codio?** Follow the [Quickstart tutorial](tutorials/quickstart.md) to set up a registry and run your first discovery query.
- **Already using codio?** Jump to [How-to guides](how-to/index.md) for task-focused recipes.
- **Want to understand the design?** Read the [Explanation](explanation/index.md) pages.
- **Need exact syntax?** See the [Reference](reference/index.md).

## How it works

```
codio init          # scaffold .codio/ in your project
codio list          # see what libraries are registered
codio discover X    # search for libraries matching capability X
codio study lib     # structured analysis of a library
codio validate      # check registry consistency
```

## Part of the ecosystem

Codio follows the same patterns as its sibling tools:

| Tool | Purpose | Scaffolds | CLI entry |
|------|---------|-----------|-----------|
| **projio** | Project orchestration | `.projio/` | `projio init` |
| **biblio** | Bibliography/papers | `bib/` | `biblio init` |
| **notio** | Notes and project memory | `notes/` | `notio init` |
| **codio** | Code reuse discovery | `.codio/` | `codio init` |
