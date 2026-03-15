# Prompt: Code Intelligence and Indexing Design

You are working inside the `codio` repository.

Your task is to design codio's future code-intelligence and indexing boundary, based on the current lightweight `indexio` integration.

## Read first

- `docs/specs/codio/codio-current-state.md`
- `docs/explanation/code-intelligence.md`
- `src/codio/rag.py`
- `docs/specs/codio/codio-mcp-tools.md`
- `docs/specs/codio/codio-architecture.md`

## Task

Write or revise:

- `docs/explanation/code-intelligence.md`

Optional supporting edit:

- `docs/specs/codio/codio-design-review.md`

## Requirements

- Distinguish metadata search from code intelligence.
- Define what codio should expose to external indexers versus what it should own itself.
- Explain how retrieval evidence should connect back to codio entities.
- Do not claim semantic retrieval is already implemented in codio.
- Keep the design compatible with both managed and attached repositories.

## Deliverables

Produce a design page that covers:

- indexable source types
- indexing boundaries
- retrieval outputs needed by agents
- integration boundary with `indexio`
- staged implementation implications for M4 and M6
