# Codio Workflow

## Role in Engineering Workflow

Codio is used between problem definition and implementation. Its purpose is to force an explicit discovery step before a new solution is written.

Typical process:

```text
idea
 ↓
codio search
 ↓
inspect code + notes
 ↓
choose implementation strategy
 ↓
implement
```

## Workflow Stages

### 1. Idea

An engineer or agent starts with a problem statement, desired capability, or implementation gap.

### 2. Codio Search

Codio is queried for candidate libraries, mirrors, notes, and retrieval hits relevant to that capability.

### 3. Inspect Code and Notes

The candidate implementations are inspected. The project profile, curated note, and capability evidence are used to determine whether a result is appropriate.

### 4. Choose Implementation Strategy

Codio does not end with retrieval. It supports a concrete engineering decision.

| Decision | Meaning |
|---|---|
| `existing` | internal code already solves it |
| `wrap` | external library wrapped into project API |
| `direct` | direct dependency |
| `new` | implement new code |

### 5. Implement

The chosen decision determines the implementation path. Codio has already reduced ambiguity by showing the relevant prior art and project policy.

## Decision Model

### Existing

Choose `existing` when stable internal code already satisfies the need with acceptable quality and fit.

### Wrap

Choose `wrap` when an external library provides the capability but should be mediated through project APIs, adapters, or schema normalization.

### Direct

Choose `direct` when the external dependency is appropriate to call directly and the project does not benefit from an additional abstraction layer.

### New

Choose `new` only when the prior art is inadequate, incompatible, too unstable, or absent.

## Workflow Integration Principles

- Discovery should happen before literature review when the problem is implementation-oriented.
- Curated notes should be consulted before adding a new dependency.
- The final decision should be recordable in notes, plans, or code review context.
- Codio search may be repeated during implementation when the first candidate proves insufficient.
