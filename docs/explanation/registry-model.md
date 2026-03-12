# Two-layer registry model

Codio separates library metadata into two files: a **catalog** and a **profile**. This separation is deliberate and solves a specific problem.

## The catalog answers: what is this library?

The catalog (`.codio/catalog.yml`) stores identity-level metadata that is stable across projects: name, kind, language, repository URL, package name, license, local path.

This information doesn't change depending on who is using the library or why.

## The profile answers: how should this project use it?

The profile (`.codio/profiles.yml`) stores project-specific policy: priority tier, runtime import policy, default engineering decision, capability tags, curated note reference.

Two projects can share a catalog entry for the same library but assign different priorities, runtime policies, or default decisions.

## Why not merge them?

If identity and policy live in the same record:

- Shared metadata becomes hard to reuse across projects.
- Policy changes pollute the identity layer.
- Comparing how different projects treat the same library becomes difficult.

Separation keeps the catalog portable and the profile local.

## Profile entries must reference catalog keys

A profile entry without a corresponding catalog entry is an error. The catalog defines the namespace; the profile interprets it. This constraint is enforced by `codio validate`.

## Catalog entries without profiles are allowed

Low-priority or newly added libraries may exist in the catalog without a profile. Codio treats these as known but unprioritized. Validation reports them as warnings, not errors.
