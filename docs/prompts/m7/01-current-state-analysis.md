# Prompt: Current-State Analysis

You are working inside the `codio` repository.

Your task is to refresh and tighten the current-state analysis for codio without implementing runtime features.

## Scope

Study the repository as it exists now and validate or update:

- `docs/specs/codio/codio-current-state.md`
- `docs/specs/codio/codio-design-review.md`

## Requirements

- Ground every claim in repository evidence.
- Distinguish clearly between implemented behavior and aspirational design docs.
- Inspect `src/codio/`, `tests/`, `docs/reference/`, `docs/explanation/`, `docs/specs/codio/`, and `docs/prompts/`.
- Call out mismatches between code, tests, and docs.
- Do not invent ingestion, indexing, or repository-management features that are not present.

## Deliverables

1. Update `docs/specs/codio/codio-current-state.md` if needed.
2. Update `docs/specs/codio/codio-design-review.md` with any new ambiguities or tensions.
3. Provide a concise summary of:
   - current strengths
   - current limitations
   - main design risks if M2 starts from the wrong assumptions
