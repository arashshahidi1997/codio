"""Controlled vocabulary for the Codio system."""

from __future__ import annotations

from enum import StrEnum
from typing import Any


# ---------------------------------------------------------------------------
# Base helper
# ---------------------------------------------------------------------------

class _DescribedEnum(StrEnum):
    """StrEnum whose members carry a human-readable description."""

    def __new__(cls, value: str, description: str = "") -> _DescribedEnum:
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._description = description
        return obj

    @property
    def description(self) -> str:
        return self._description


# ---------------------------------------------------------------------------
# Vocabularies
# ---------------------------------------------------------------------------

class Kind(_DescribedEnum):
    """Library identity class."""

    internal = ("internal", "Internal package or module")
    external_mirror = ("external_mirror", "Mirrored external dependency")
    utility = ("utility", "Shared utility library")


class RuntimeImport(_DescribedEnum):
    """How a library participates in runtime."""

    internal = ("internal", "Imported directly at runtime")
    pip_only = ("pip_only", "Installed via pip but not imported directly")
    reference_only = ("reference_only", "Referenced in docs or config only")


class DecisionDefault(_DescribedEnum):
    """Default engineering decision."""

    existing = ("existing", "Use the existing implementation as-is")
    wrap = ("wrap", "Wrap the external library with a thin adapter")
    direct = ("direct", "Use the external library directly")
    new = ("new", "Write a new implementation from scratch")


class Priority(_DescribedEnum):
    """Project priority tier."""

    tier1 = ("tier1", "Highest priority")
    tier2 = ("tier2", "Medium priority")
    tier3 = ("tier3", "Lower priority")


class Status(_DescribedEnum):
    """Lifecycle state."""

    active = ("active", "Currently in active use")
    candidate = ("candidate", "Under consideration for adoption")
    deprecated = ("deprecated", "Scheduled for removal")


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_VOCABS: dict[str, type[_DescribedEnum]] = {
    "kind": Kind,
    "runtime_import": RuntimeImport,
    "decision_default": DecisionDefault,
    "priority": Priority,
    "status": Status,
}


def get_vocab() -> dict[str, dict[str, Any]]:
    """Return a dict mapping field names to allowed values and descriptions.

    Structure::

        {
            "kind": {
                "values": {"internal": "Internal package or module", ...},
                "description": "Library identity class",
            },
            ...
        }
    """
    result: dict[str, dict[str, Any]] = {}
    for field, enum_cls in _VOCABS.items():
        result[field] = {
            "values": {m.value: m.description for m in enum_cls},
            "description": enum_cls.__doc__ or "",
        }
    return result
