# Prompt: Cross-Project Sharing

You are working inside the `codio` repository.

Your task is to design how codio should support cross-project sharing of code intelligence metadata without losing project-local flexibility.

## Read first

- `docs/specs/codio/codio-current-state.md`
- `docs/explanation/cross-project-sharing.md`
- `docs/reference/entity-model.md`
- `docs/reference/library-layout.md`
- `src/codio/config.py`
- `src/codio/registry.py`

## Task

Write or revise:

- `docs/explanation/cross-project-sharing.md`

## Requirements

- Start from current portability features that already exist.
- Define what metadata can be shared across repos and what should remain local.
- Avoid making codio depend on one workspace manager or orchestrator.
- Address how managed and attached repositories affect sharing.
- Call out migration concerns from the current `.codio/catalog.yml` and `.codio/profiles.yml` model.

## Deliverables

Produce a concise explanation page covering:

- shareable vs local metadata
- likely sharing mechanisms
- risks of over-centralization
- compatibility with current codio usage
