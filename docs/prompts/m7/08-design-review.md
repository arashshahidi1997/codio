# Prompt: Design Review

You are working inside the `codio` repository.

Your task is to review the current codio design documents for coherence, scope control, and migration realism.

## Read first

- `docs/specs/codio/codio-current-state.md`
- `docs/specs/codio/codio-roadmap.md`
- `docs/specs/codio/codio-design-review.md`
- `docs/explanation/vision.md`
- `docs/explanation/code-intelligence.md`
- `docs/explanation/cross-project-sharing.md`
- `docs/reference/entity-model.md`
- `docs/reference/library-layout.md`
- `docs/reference/ingestion.md`

## Task

Update:

- `docs/specs/codio/codio-design-review.md`

Optional edits:

- any of the design documents above, if the review finds contradictions

## Review criteria

- Are the documents aligned on the primary entity model?
- Are implemented features clearly separated from target design?
- Are managed and attached repositories described consistently?
- Is the codio/indexio boundary clear?
- Is the codio/projio boundary clear?
- Are migration steps from the current registry model plausible?
- Are any documents quietly assuming unsupported capabilities?

## Deliverables

1. Update `docs/specs/codio/codio-design-review.md` with findings and unresolved questions.
2. Tighten any contradictory wording in the design docs.
3. Provide a short review summary listing:
   - the strongest parts of the design
   - the main contradictions
   - the blockers for implementation planning
