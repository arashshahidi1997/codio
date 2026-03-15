# Prompt: Codio Entity Model

You are working inside the `codio` repository.

Your task is to draft the codio entity model for the post-M1 design phase.

## Read first

- `docs/specs/codio/codio-current-state.md`
- `docs/specs/codio/codio-design-review.md`
- `docs/reference/entity-model.md`
- `src/codio/models.py`
- `src/codio/registry.py`
- `docs/specs/codio/codio-concepts.md`
- `docs/specs/codio/codio-registry-schema.md`

## Task

Write or revise:

- `docs/reference/entity-model.md`

## Requirements

- Start from the entities actually implemented today.
- Propose new entities only when they solve a concrete gap already identified in M1.
- Address the relation between:
  - repository
  - code source
  - library
  - managed repository
  - attached repository
  - index source
- Make clear which identifiers are canonical.
- Evaluate whether `repo_id` should be primary and whether `repo_url` and citekeys are metadata.

## Deliverables

Produce a reference-style document that includes:

- entity definitions
- canonical identifiers
- ownership rules
- likely derived views
- open questions that still need M3 or M4
