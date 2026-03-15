# Codio Design Roadmap

## M1

Current-state analysis and prompt/spec scaffold.

Deliverables:

- `docs/specs/codio/codio-current-state.md`
- `docs/specs/codio/codio-design-review.md`
- `docs/prompts/m7/`
- initial design placeholders in `docs/explanation/` and `docs/reference/`

## M2

Codio vision, scope boundaries, and entity model.

Focus:

- define what codio owns
- define managed vs attached repository modes
- define canonical identifiers such as `repo_id`

## M3

Library workspace layout and ingestion specification.

Focus:

- managed library storage layout
- attached repository metadata
- ingestion/update/provenance rules

## M4

Code intelligence and indexing design.

Focus:

- what codio indexes directly
- what codio delegates to external retrieval systems
- how retrieval evidence maps back to codio entities

## M5

Ecosystem integration and cross-project sharing.

Focus:

- registry portability
- shared library catalogs and notes
- integration boundaries with `indexio`, `projio`, and sibling repos

## M6

Implementation planning.

Focus:

- sequence concrete runtime changes
- identify low-risk migrations from the current library-centric model
- define test and rollout strategy before feature implementation
