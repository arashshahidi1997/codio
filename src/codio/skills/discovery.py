from __future__ import annotations

from dataclasses import dataclass, field
from codio.registry import Registry
from codio.models import LibraryRecord


@dataclass
class DiscoveryCandidate:
    """A candidate library returned from discovery."""

    name: str
    kind: str
    summary: str
    capabilities: list[str]
    decision_default: str
    runtime_import: str
    priority: str
    relevance_reason: str  # why this candidate matched
    curated_note: str = ""


@dataclass
class DiscoveryResult:
    """Result of a discovery query."""

    query: str
    candidates: list[DiscoveryCandidate]
    recommended_decision: str  # one of: existing, wrap, direct, new
    reasoning: str


def discover(
    query: str,
    registry: Registry,
    *,
    language: str | None = None,
) -> DiscoveryResult:
    """Search registry for libraries matching a capability query.

    The query is matched against:
    1. Capability tags (exact match)
    2. Library names (substring match)
    3. Summaries (substring match)

    Returns ranked candidates with a recommended decision.
    """
    query_lower = query.lower()
    candidates: list[DiscoveryCandidate] = []

    # Get all libraries, optionally filtered by language
    all_records = registry.list(language=language) if language else registry.list()

    for record in all_records:
        reason = _match_reason(query_lower, record)
        if reason:
            candidates.append(
                DiscoveryCandidate(
                    name=record.name,
                    kind=record.kind,
                    summary=record.summary,
                    capabilities=record.capabilities,
                    decision_default=record.decision_default,
                    runtime_import=record.runtime_import,
                    priority=record.priority,
                    relevance_reason=reason,
                    curated_note=record.curated_note,
                )
            )

    # Sort: tier1 first, then by match quality (capability > name > summary)
    candidates.sort(key=_candidate_sort_key)

    # Determine recommended decision
    recommended, reasoning = _recommend(candidates)

    return DiscoveryResult(
        query=query,
        candidates=candidates,
        recommended_decision=recommended,
        reasoning=reasoning,
    )


def _match_reason(query: str, record: LibraryRecord) -> str:
    """Return a relevance reason if the record matches the query, else empty string."""
    # Check capability tags first (highest signal)
    for cap in record.capabilities:
        if query in cap.lower():
            return f"Capability match: {cap}"
    # Check name
    if query in record.name.lower():
        return f"Name match: {record.name}"
    # Check summary
    if query in record.summary.lower():
        return "Summary match"
    return ""


def _candidate_sort_key(c: DiscoveryCandidate) -> tuple:
    """Sort key: priority tier (ascending), then match type (capability > name > summary)."""
    priority_order = {"tier1": 0, "tier2": 1, "tier3": 2}
    match_order = 2  # summary
    if "Capability match" in c.relevance_reason:
        match_order = 0
    elif "Name match" in c.relevance_reason:
        match_order = 1
    return (priority_order.get(c.priority, 9), match_order)


def _recommend(candidates: list[DiscoveryCandidate]) -> tuple[str, str]:
    """Recommend a decision based on candidates found."""
    if not candidates:
        return "new", "No existing libraries found matching the query."

    top = candidates[0]
    if top.kind == "internal" and top.decision_default == "existing":
        return (
            "existing",
            f"Internal library '{top.name}' already provides this capability.",
        )
    if top.decision_default in ("wrap", "direct"):
        return (
            top.decision_default,
            f"Library '{top.name}' is available with policy '{top.decision_default}'.",
        )
    if top.kind == "external_mirror":
        return "wrap", f"External mirror '{top.name}' found; wrapping is recommended."
    return (
        top.decision_default,
        f"Based on top candidate '{top.name}' with default decision '{top.decision_default}'.",
    )
