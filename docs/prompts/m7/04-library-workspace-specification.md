# Prompt: Library Workspace Specification

You are working inside the `codio` repository.

Your task is to draft the specification for a codio-managed library workspace without implementing it.

## Read first

- `docs/specs/codio/codio-current-state.md`
- `docs/reference/library-layout.md`
- `docs/reference/entity-model.md`
- `docs/explanation/cross-project-sharing.md`
- `docs/specs/codio/codio-architecture.md`

## Task

Write or revise:

- `docs/reference/library-layout.md`

## Requirements

- Define the managed-workspace layout separately from attached repositories.
- Keep the spec compatible with the current `.codio/` registry model.
- Prefer repo slugs or `repo_id` as canonical path identifiers.
- Be concrete about which directories are codio-owned.
- Call out any assumptions about shared workspace roots as assumptions, not facts.

## Deliverables

Document:

- candidate on-disk layout
- naming and identity rules
- required metadata beside managed repos
- how the layout relates to current catalog/profile files
- unresolved questions about storage ownership and durability
