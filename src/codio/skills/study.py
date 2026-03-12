from __future__ import annotations
from dataclasses import dataclass, field
from codio.registry import Registry


@dataclass
class LibraryAnalysis:
    """Structured analysis of a single library."""
    name: str
    kind: str
    language: str
    summary: str
    capabilities: list[str]
    entry_points: list[str]  # suggested entry points (e.g. key modules/files)
    strengths: list[str]
    caveats: list[str]
    integration_notes: str
    has_curated_note: bool
    curated_note_path: str = ""


@dataclass
class ComparisonResult:
    """Comparative analysis across multiple libraries."""
    query: str
    libraries: list[LibraryAnalysis]
    recommendation: str  # which library to prefer and why
    shared_capabilities: list[str]
    distinguishing_factors: list[str]


def study_library(name: str, registry: Registry) -> LibraryAnalysis | None:
    """Perform structured analysis of a single library from the registry.

    Returns None if the library is not found in the registry.
    This generates a structured analysis based on registry metadata.
    For deeper analysis, agents should supplement this with source code inspection.
    """
    record = registry.get(name)
    if record is None:
        return None

    strengths = []
    caveats = []
    entry_points = []

    # Derive insights from metadata
    if record.kind == "internal":
        strengths.append("Internal library — no external dependency risk")
        if record.path:
            entry_points.append(record.path)
    elif record.kind == "external_mirror":
        strengths.append("Source available locally as mirror")
        caveats.append("Mirror may be out of date with upstream")
        if record.path:
            entry_points.append(record.path)
        if record.repo_url:
            entry_points.append(record.repo_url)

    if record.pip_name:
        entry_points.append(f"pip install {record.pip_name}")

    if record.priority == "tier1":
        strengths.append("Tier 1 priority — well-established in project")
    elif record.priority == "tier3":
        caveats.append("Tier 3 priority — lower project investment")

    if record.runtime_import == "reference_only":
        caveats.append("Reference only — not approved for runtime import")

    if record.capabilities:
        strengths.append(f"Declared capabilities: {', '.join(record.capabilities)}")

    integration_notes = _integration_notes(record)

    return LibraryAnalysis(
        name=record.name,
        kind=record.kind,
        language=record.language,
        summary=record.summary,
        capabilities=record.capabilities,
        entry_points=entry_points,
        strengths=strengths,
        caveats=caveats,
        integration_notes=integration_notes,
        has_curated_note=bool(record.curated_note),
        curated_note_path=record.curated_note,
    )


def compare_libraries(names: list[str], registry: Registry, query: str = "") -> ComparisonResult:
    """Compare multiple libraries and produce a recommendation.

    Libraries not found in the registry are silently skipped.
    """
    analyses = []
    for name in names:
        analysis = study_library(name, registry)
        if analysis is not None:
            analyses.append(analysis)

    # Find shared and distinguishing capabilities
    if len(analyses) >= 2:
        cap_sets = [set(a.capabilities) for a in analyses]
        shared = sorted(set.intersection(*cap_sets)) if cap_sets else []
        all_caps = set.union(*cap_sets) if cap_sets else set()
        distinguishing = sorted(all_caps - set(shared))
    else:
        shared = []
        distinguishing = []

    recommendation = _build_recommendation(analyses)

    return ComparisonResult(
        query=query,
        libraries=analyses,
        recommendation=recommendation,
        shared_capabilities=shared,
        distinguishing_factors=distinguishing,
    )


def _integration_notes(record) -> str:
    """Generate integration notes based on record metadata."""
    parts = []
    if record.decision_default == "wrap":
        parts.append(f"Wrap {record.name} behind a project API before use.")
    elif record.decision_default == "direct":
        parts.append(f"Can be used directly as a dependency.")
    elif record.decision_default == "existing":
        parts.append(f"Use the existing internal implementation.")

    if record.license:
        parts.append(f"License: {record.license}.")

    return " ".join(parts) if parts else "No specific integration guidance available."


def _build_recommendation(analyses: list[LibraryAnalysis]) -> str:
    """Build a recommendation string from analyses."""
    if not analyses:
        return "No libraries found for comparison."
    if len(analyses) == 1:
        return f"Only '{analyses[0].name}' was found. Evaluate based on its analysis."

    # Prefer internal over external, tier1 over tier2/3
    internals = [a for a in analyses if a.kind == "internal"]
    if internals:
        return f"Prefer internal library '{internals[0].name}' to avoid external dependencies."

    # Among externals, prefer the one with more capabilities
    by_caps = sorted(analyses, key=lambda a: len(a.capabilities), reverse=True)
    return f"Consider '{by_caps[0].name}' which has the broadest declared capabilities."
