# Discovery-first engineering

Codio is built around a single workflow principle: **search before you implement**.

## The problem

Research and engineering projects accumulate reusable logic across internal packages, copied experiments, mirrored libraries, and notebooks. Without a discovery layer, that prior art is hard to find, easy to duplicate, and rarely turned into explicit decisions.

The cost of reimplementing existing code is real: maintenance burden, inconsistency, and wasted effort. The cost of importing an external library without understanding project policy is also real: integration debt, license surprises, and broken abstractions.

## The codio workflow

Codio inserts a discovery step between problem definition and implementation:

```
idea
  |
codio discover
  |
inspect candidates + notes
  |
choose: existing / wrap / direct / new
  |
implement
```

The goal is not to prevent new code from being written. It is to make sure the decision to write new code is informed.

## Why discovery must be cheap

If discovery takes longer than implementation, people skip it. Codio keeps the cost low:

- Capability search is a keyword match against structured metadata, not a full code analysis.
- Results include priority and policy context, so you can make a decision without deep inspection.
- Curated notes capture the expensive analysis once so it doesn't need to be repeated.

## Agents and discovery

For AI agents, discovery-first engineering is especially important. Agents default to implementation — they will write new code unless explicitly told to search first. Codio provides the structured interface (MCP tools and agent skills) that makes "search before implement" a reliable agent behavior.

## What codio doesn't do

Codio does not analyze source code for you. It does not automatically detect that two modules overlap. It is a metadata registry and discovery tool, not a static analysis engine.

The quality of discovery depends on the quality of the registry. Libraries that aren't registered can't be found. Capabilities that aren't tagged won't match queries. This is a deliberate trade-off: curated metadata is more reliable than automated inference for engineering decisions.
