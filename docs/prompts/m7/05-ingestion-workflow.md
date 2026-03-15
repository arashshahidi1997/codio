# Prompt: Ingestion Workflow

You are working inside the `codio` repository.

Your task is to design codio's ingestion workflow for managed and attached repositories, without implementing runtime code.

## Read first

- `docs/specs/codio/codio-current-state.md`
- `docs/reference/ingestion.md`
- `docs/reference/library-layout.md`
- `docs/reference/entity-model.md`
- `docs/explanation/code-intelligence.md`

## Task

Write or revise:

- `docs/reference/ingestion.md`

## Requirements

- Separate:
  - managed repository ingestion
  - attached repository registration
- State what codio records, what codio owns, and what codio only references.
- Avoid assuming DataLad is mandatory unless the repo evidence supports that as a design decision.
- Explain provenance, sync/update semantics, and failure cases.
- Keep the design modular so `projio` or other tools can call into codio without owning its concepts.

## Deliverables

Produce a practical ingestion spec with:

- workflow stages
- metadata artifacts
- provenance rules
- update/sync expectations
- explicit non-goals for the first implementation phase
