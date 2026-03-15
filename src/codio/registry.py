"""Registry loader and manager for Codio."""

from __future__ import annotations

from pathlib import Path

import yaml

from codio.config import CodioConfig, load_config
from codio.models import (
    LibraryCatalogEntry,
    LibraryRecord,
    ProjectProfileEntry,
    RegistrySnapshot,
    RepositoryEntry,
    ValidationResult,
)
from codio.vocab import (
    DecisionDefault,
    Kind,
    Priority,
    RuntimeImport,
    Status,
    get_vocab,
)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_catalog(path: Path) -> dict[str, LibraryCatalogEntry]:
    """Read a YAML catalog file and return entries keyed by library name.

    Returns an empty dict when *path* does not exist.
    """
    if not path.exists():
        return {}

    with open(path) as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, dict) or "libraries" not in raw:
        return {}

    entries: dict[str, LibraryCatalogEntry] = {}
    for name, fields in raw["libraries"].items():
        if not isinstance(fields, dict):
            continue
        entries[name] = LibraryCatalogEntry(name=name, **fields)
    return entries


def load_profiles(path: Path) -> dict[str, ProjectProfileEntry]:
    """Read a YAML profiles file and return entries keyed by library name.

    Returns an empty dict when *path* does not exist.
    """
    if not path.exists():
        return {}

    with open(path) as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, dict) or "profiles" not in raw:
        return {}

    entries: dict[str, ProjectProfileEntry] = {}
    for name, fields in raw["profiles"].items():
        if not isinstance(fields, dict):
            continue
        entries[name] = ProjectProfileEntry(name=name, **fields)
    return entries


def load_repos(path: Path) -> dict[str, RepositoryEntry]:
    """Read a YAML repos file and return entries keyed by repo_id.

    Returns an empty dict when *path* does not exist.
    """
    if not path.exists():
        return {}

    with open(path) as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, dict) or "repositories" not in raw:
        return {}

    entries: dict[str, RepositoryEntry] = {}
    for repo_id, fields in raw["repositories"].items():
        if not isinstance(fields, dict):
            continue
        entries[repo_id] = RepositoryEntry(repo_id=repo_id, **fields)
    return entries


def save_repos(path: Path, repos: dict[str, RepositoryEntry]) -> None:
    """Write repository entries to a YAML file."""
    data: dict[str, dict] = {}
    for repo_id, entry in repos.items():
        d = entry.model_dump(mode="json", exclude={"repo_id"})
        # Drop empty defaults to keep file clean
        data[repo_id] = {k: v for k, v in d.items() if v}
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        yaml.dump({"repositories": data}, fh, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_VOCAB_FIELDS: dict[str, type] = {
    "kind": Kind,
    "runtime_import": RuntimeImport,
    "decision_default": DecisionDefault,
    "priority": Priority,
    "status": Status,
}


class Registry:
    """Central registry that merges a library catalog with project profiles."""

    def __init__(self, config: CodioConfig | None = None) -> None:
        if config is None:
            config = load_config()
        self._config = config
        self._catalog = load_catalog(config.catalog_path)
        self._profiles = load_profiles(config.profiles_path)
        self._repos = load_repos(config.repos_path)

    @classmethod
    def from_paths(
        cls,
        catalog_path: Path,
        profiles_path: Path,
        project_root: Path | None = None,
    ) -> Registry:
        """Convenience constructor that builds a config from explicit paths."""
        config = CodioConfig(
            catalog_path=catalog_path,
            profiles_path=profiles_path,
            project_root=project_root or Path("."),
        )
        return cls(config=config)

    # -- queries -------------------------------------------------------------

    def list(
        self,
        *,
        kind: str | None = None,
        language: str | None = None,
        capability: str | None = None,
        priority: str | None = None,
        runtime_import: str | None = None,
    ) -> list[LibraryRecord]:
        """Return a filtered list of merged :class:`LibraryRecord` objects."""
        records: list[LibraryRecord] = []
        for name in self._catalog:
            record = self._merge(name)
            if kind is not None and record.kind != kind:
                continue
            if language is not None and record.language != language:
                continue
            if capability is not None and capability not in record.capabilities:
                continue
            if priority is not None and record.priority != priority:
                continue
            if runtime_import is not None and record.runtime_import != runtime_import:
                continue
            records.append(record)
        return records

    def get(self, name: str) -> LibraryRecord | None:
        """Return the merged record for *name*, or ``None`` if not found."""
        if name not in self._catalog:
            return None
        return self._merge(name)

    def snapshot(self) -> RegistrySnapshot:
        """Return the full registry payload."""
        return RegistrySnapshot(
            libraries=dict(self._catalog),
            profiles=dict(self._profiles),
            repositories=dict(self._repos),
        )

    # -- repo queries --------------------------------------------------------

    def list_repos(self, *, storage: str | None = None) -> list[RepositoryEntry]:
        """Return repository entries, optionally filtered by storage mode."""
        repos = list(self._repos.values())
        if storage is not None:
            repos = [r for r in repos if r.storage == storage]
        return repos

    def get_repo(self, repo_id: str) -> RepositoryEntry | None:
        """Return a single repository entry or ``None``."""
        return self._repos.get(repo_id)

    # -- validation ----------------------------------------------------------

    def validate(self) -> ValidationResult:
        """Validate the registry, returning errors and warnings."""
        errors: list[str] = []
        warnings: list[str] = []
        vocab = get_vocab()

        # 1. Profile entries referencing non-existent catalog keys
        for name in self._profiles:
            if name not in self._catalog:
                errors.append(
                    f"Profile '{name}' references a library not in the catalog."
                )

        # 2. Invalid vocab values in catalog entries
        for name, entry in self._catalog.items():
            value = entry.kind
            allowed = set(vocab["kind"]["values"])
            if value not in allowed:
                errors.append(
                    f"Catalog '{name}': invalid kind '{value}' "
                    f"(allowed: {sorted(allowed)})."
                )

        # 2b. Invalid vocab values in profile entries
        profile_vocab_fields = {
            "runtime_import": "runtime_import",
            "decision_default": "decision_default",
            "priority": "priority",
            "status": "status",
        }
        for name, entry in self._profiles.items():
            for field_name, vocab_key in profile_vocab_fields.items():
                value = getattr(entry, field_name)
                allowed = set(vocab[vocab_key]["values"])
                if value not in allowed:
                    errors.append(
                        f"Profile '{name}': invalid {field_name} '{value}' "
                        f"(allowed: {sorted(allowed)})."
                    )

        # 3. Curated note paths that don't exist on disk
        for name, entry in self._profiles.items():
            if entry.curated_note:
                note_path = self._config.project_root / entry.curated_note
                if not note_path.exists():
                    warnings.append(
                        f"Profile '{name}': curated_note path "
                        f"'{entry.curated_note}' does not exist."
                    )

        # 4. Catalog entries without profiles
        for name in self._catalog:
            if name not in self._profiles:
                warnings.append(
                    f"Catalog entry '{name}' has no corresponding profile."
                )

        # 5. Catalog repo_id references non-existent repo
        for name, entry in self._catalog.items():
            if entry.repo_id and entry.repo_id not in self._repos:
                warnings.append(
                    f"Catalog '{name}': repo_id '{entry.repo_id}' "
                    f"not found in repos.yml."
                )

        # 6. Managed repos with missing local_path on disk
        for repo_id, repo in self._repos.items():
            if repo.storage == "managed" and repo.local_path:
                repo_path = self._config.project_root / repo.local_path
                if not repo_path.exists():
                    warnings.append(
                        f"Repository '{repo_id}': managed local_path "
                        f"'{repo.local_path}' does not exist."
                    )
            if repo.storage == "attached" and repo.local_path:
                repo_path = self._config.project_root / repo.local_path
                if not repo_path.exists():
                    warnings.append(
                        f"Repository '{repo_id}': attached local_path "
                        f"'{repo.local_path}' does not exist."
                    )

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    # -- internals -----------------------------------------------------------

    def _merge(self, name: str) -> LibraryRecord:
        """Merge a catalog entry with its optional profile."""
        catalog_entry = self._catalog[name]
        profile_entry = self._profiles.get(name)
        return LibraryRecord.from_entries(catalog_entry, profile_entry)
