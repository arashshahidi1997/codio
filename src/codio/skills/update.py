from __future__ import annotations

import yaml
from pathlib import Path

from codio.models import LibraryCatalogEntry, ProjectProfileEntry, ValidationResult
from codio.registry import Registry


def add_library(
    registry: Registry,
    catalog_entry: LibraryCatalogEntry,
    profile_entry: ProjectProfileEntry | None = None,
) -> None:
    """Add or update a library in the registry (in-memory and on disk).

    Updates the YAML files on disk to persist changes.
    """
    registry._catalog[catalog_entry.name] = catalog_entry
    if profile_entry is not None:
        registry._profiles[profile_entry.name] = profile_entry
    _write_catalog(registry._config.catalog_path, registry._catalog)
    if profile_entry is not None:
        _write_profiles(registry._config.profiles_path, registry._profiles)


def remove_library(registry: Registry, name: str) -> bool:
    """Remove a library from catalog and profile. Returns True if found."""
    found = name in registry._catalog
    registry._catalog.pop(name, None)
    registry._profiles.pop(name, None)
    _write_catalog(registry._config.catalog_path, registry._catalog)
    _write_profiles(registry._config.profiles_path, registry._profiles)
    return found


def update_profile(
    registry: Registry,
    profile_entry: ProjectProfileEntry,
) -> bool:
    """Update a project profile. Returns False if library not in catalog."""
    if profile_entry.name not in registry._catalog:
        return False
    registry._profiles[profile_entry.name] = profile_entry
    _write_profiles(registry._config.profiles_path, registry._profiles)
    return True


def validate_registry(registry: Registry) -> ValidationResult:
    """Run validation on the registry."""
    return registry.validate()


def _write_catalog(path: Path, catalog: dict[str, LibraryCatalogEntry]) -> None:
    """Write catalog entries to YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"libraries": {}}
    for name, entry in catalog.items():
        d = entry.model_dump(mode="json", exclude={"name"}, exclude_defaults=False)
        data["libraries"][name] = {k: v for k, v in d.items() if v != "" and v != []}
    with open(path, "w") as fh:
        yaml.dump(data, fh, default_flow_style=False, sort_keys=False)


def _write_profiles(path: Path, profiles: dict[str, ProjectProfileEntry]) -> None:
    """Write profile entries to YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"profiles": {}}
    for name, entry in profiles.items():
        d = entry.model_dump(mode="json", exclude={"name"}, exclude_defaults=False)
        data["profiles"][name] = {k: v for k, v in d.items() if v != "" and v != []}
    with open(path, "w") as fh:
        yaml.dump(data, fh, default_flow_style=False, sort_keys=False)
