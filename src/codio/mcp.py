from __future__ import annotations

from codio.registry import Registry
from codio.vocab import get_vocab


def mcp_list(
    registry: Registry,
    *,
    kind: str | None = None,
    language: str | None = None,
    capability: str | None = None,
    priority: str | None = None,
    runtime_import: str | None = None,
) -> list[dict]:
    """Return filtered library listing as list of dicts."""
    records = registry.list(
        kind=kind,
        language=language,
        capability=capability,
        priority=priority,
        runtime_import=runtime_import,
    )
    return [r.model_dump() for r in records]


def mcp_get(registry: Registry, name: str) -> dict | None:
    """Return full merged record for one library as a dict, or None."""
    record = registry.get(name)
    if record is None:
        return None
    return record.model_dump()


def mcp_registry(registry: Registry) -> dict:
    """Return full registry snapshot as a dict."""
    return registry.snapshot().model_dump()


def mcp_vocab() -> dict:
    """Return controlled vocabulary."""
    return get_vocab()


def mcp_validate(registry: Registry) -> dict:
    """Return registry validation result as a dict."""
    return registry.validate().model_dump()
