# Codio Design Review

## Purpose

This document reviews the M7 design documents for coherence, scope control, and migration realism. It replaces the earlier M1 review checklist with findings from the completed design phase.

## Documents reviewed

| Document | Location | Scope |
|----------|----------|-------|
| Vision | `docs/explanation/vision.md` | Role, ownership, design goals |
| Entity model | `docs/reference/entity-model.md` | Entities, identifiers, relationships |
| Library layout | `docs/reference/library-layout.md` | On-disk workspace specification |
| Ingestion | `docs/reference/ingestion.md` | Workflow stages, provenance, sync |
| Code intelligence | `docs/explanation/code-intelligence.md` | Indexing boundaries, retrieval |
| Cross-project sharing | `docs/explanation/cross-project-sharing.md` | Shareable vs local metadata |
| Current state | `docs/specs/codio/codio-current-state.md` | M1 baseline (refreshed) |

## Review criteria

1. Are the documents aligned on the primary entity model?
2. Are implemented features clearly separated from target design?
3. Are managed and attached repositories described consistently?
4. Is the codio/indexio boundary clear?
5. Is the codio/projio boundary clear?
6. Are migration steps from the current registry model plausible?
7. Are any documents quietly assuming unsupported capabilities?

---

## Findings

### Strongest parts of the design

**Consistent entity model.** All six documents use the same proposed entities (Repository, CodeSource, IndexSource) and the same vocabulary. The `repo_id` slug is treated consistently as an optional FK on catalog entries, not a replacement for the library `name` primary key. The entity-model document is the single reference, and other documents cite it rather than redefining entities.

**Clear implemented/proposed separation.** Every document marks what exists in code today versus what is proposed. The vision document has an explicit present-vs-target table. The library layout and ingestion documents open with "Current State (Implemented)" sections before introducing proposed designs.

**Consistent storage modes.** Managed, attached, and external are described identically across entity model, library layout, ingestion, and cross-project sharing. The three-mode taxonomy is used without variation.

**Clean codio/indexio boundary.** The code-intelligence document clearly states: codio defines sources and manifests, indexio handles chunking, embedding, retrieval, and index lifecycle. The ingestion document aligns: stage 5 (indexio registration) is optional and uses the existing `sync_owned_sources()` contract. Neither document introduces indexing logic inside codio.

**Clean codio/projio boundary.** The vision document explicitly states codio must remain functional without projio. Config integration is read-only. No document assumes projio is a prerequisite.

**Pragmatic migration path.** All proposed changes are additive: new optional fields on existing models, new files (`repos.yml`), new directories (`.codio/mirrors/`). No existing schema is modified. Existing registries without new fields remain valid.

### Contradictions found

**Workspace directory name.** The vision document refers to a future workspace as `.codio/libs/<slug>/` in one passage, while the library-layout document specifies `.codio/mirrors/<repo_id>/`. The ingestion document uses `.codio/mirrors/<repo_id>/`, aligning with library-layout. The vision document should be updated to match.

**`kind` field ownership.** The cross-project-sharing document notes that `kind` may differ across projects (a library is `internal` in its authoring project, `external_mirror` in a consuming project) and suggests it arguably belongs in the profile, not the catalog. However, the entity model and registry schema documents treat `kind` as a catalog field without flagging this tension. This is not a blocking contradiction — `kind` works as a catalog field for single-project use — but it becomes a problem if catalog entries are shared across projects.

### Open questions resolved by the design

| Question (from M1) | Resolution |
|---------------------|------------|
| Primary object: repository, code source, or broader wrapper? | Library remains primary. Repository is a parallel entity with an optional FK relationship. Libraries without repositories are valid. |
| Is a library a first-class entity or a derived view? | First-class. Libraries are not derived from repositories. They are independently authored and may reference zero or one repositories. |
| Which fields move to new entities? | No existing fields move. `repo_id` is added as a new optional field on catalog entries. `path` semantics are preserved but clarified by CodeSource. |
| Codio-owned vs delegated storage? | Managed mirrors are codio-owned (`.codio/mirrors/`). DataLad is not required. Plain git clone is the default. |
| Index source trees or define manifests? | Define manifests. Codio registers source descriptors with indexio. Codio does not index. |

### Open questions that remain

1. **`repos.yml` vs catalog section.** The library-layout document recommends a separate `repos.yml` file. The ingestion document assumes this. However, the entity-model document lists this as an open question. A decision should be made before implementation.

2. **`kind` shareability.** If catalog entries are shared across projects, `kind` values may not be correct in the consuming project. Options: move `kind` to profile (breaking change), add a profile-level `kind_override`, or accept that shared catalogs need per-project adjustments to `kind`.

3. **CodeSource granularity.** The entity model asks whether the right unit is a package, directory, module, or glob. The ingestion document sidesteps this by allowing the first implementation to use the catalog `path` field directly, deferring explicit CodeSource entities. This is pragmatic but means the first implementation won't validate whether code sources overlap or are well-scoped.

4. **Provenance tracking scope.** The ingestion document proposes `added_by`, `added_date`, `source_ref` as optional fields. The entity model proposes the same fields as a metadata attachment. Neither specifies where these fields live in the YAML schema (top-level on catalog entries, nested under a `provenance:` key, or in a separate section).

5. **Slug conventions.** The library-layout document specifies `--` as the namespace separator for `repo_id`. This is internally consistent, but no document addresses how `repo_id` relates to library `name` slugs (different namespaces? same conventions? separate registries?).

6. **Cleanup policy.** The library-layout document proposes manual cleanup via `codio mirror prune`. The ingestion document does not reference cleanup at all. The relationship between removing a catalog entry and cleaning up its managed mirror needs explicit design.

7. **Capability taxonomy.** The entity model notes that capabilities are currently free-form strings. As discovery improves, a controlled vocabulary or hierarchical taxonomy may be needed. No document proposes a concrete approach.

### Documents quietly assuming unsupported capabilities

**None found.** All six documents are careful to separate implemented from proposed. No document claims that repository management, code intelligence, or cross-project sharing already works. The ingestion document has an explicit "Non-Goals for First Implementation" section. The code-intelligence document has an explicit "What codio should NOT do" section.

The closest risk is the ingestion document's five-stage pipeline, which reads as a fairly complete specification. Implementers should treat it as a target design, not a guaranteed feature set — the non-goals section is load-bearing.

---

## Recommendations for implementation planning

1. **Fix the workspace directory name inconsistency.** Update the vision document to use `.codio/mirrors/` instead of `.codio/libs/`. This is a one-line fix.

2. **Decide `repos.yml` before coding.** The separate-file recommendation is well-argued. Commit to it or decide against it — either way, the implementation needs a single answer.

3. **Implement ingestion incrementally.** Start with external (metadata-only) registration via a `codio add` command. Add managed cloning second. Add attached registration third. This follows the complexity gradient and delivers value at each step.

4. **Defer CodeSource entities.** The first implementation can use the existing `path` field on catalog entries. Introduce CodeSource only when multiple indexable subtrees per repository become a real need.

5. **Defer provenance to second pass.** Provenance fields are useful for maintenance but not for core functionality. Add them after the basic ingestion pipeline works.

6. **Address `kind` shareability before implementing sharing.** If cross-project sharing is planned soon, resolve whether `kind` stays in the catalog or gains a profile-level override. If sharing is far out, defer.

---

## Review outcome

The M7 design documents form a coherent, well-grounded design layer on top of the M1 implementation. The entity model, workspace layout, ingestion workflow, code-intelligence boundary, and sharing model are internally consistent and externally aligned with the current codebase.

The design is conservative in the right places: it preserves the existing schema, makes all new features additive, and avoids assuming capabilities that don't exist. The remaining open questions are genuine design decisions, not gaps in analysis.

Implementation can proceed from these documents without re-inspecting basic repository facts or re-debating foundational entities.
