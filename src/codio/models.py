"""Pydantic data models for the Codio system."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from codio.vocab import (
    AddedBy,
    DecisionDefault,
    Hosting,
    Kind,
    Priority,
    Role,
    RuntimeImport,
    SourceType,
    Status,
    Storage,
)


# ---------------------------------------------------------------------------
# Catalog entry — shared identity-level metadata
# ---------------------------------------------------------------------------


class LibraryCatalogEntry(BaseModel):
    """Shared identity-level metadata for a library."""

    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(..., description="Library slug key")
    kind: Kind = Field(..., description="Identity class")
    role: str = Field(default="", description="Project role: core, shared, or external")
    language: str = Field(default="", description="Dominant language")
    repo_url: str = Field(default="", description="Upstream repo URL")
    pip_name: str = Field(default="", description="Package manager name")
    license: str = Field(default="", description="Software license")
    path: str = Field(default="", description="Local path for internal code or mirrors")
    summary: str = Field(default="", description="Short description")

    # optional FK to Repository
    repo_id: str = Field(default="", description="FK to Repository entry in repos.yml")

    # provenance (optional, recorded at ingestion time)
    added_by: str = Field(default="", description="How the entry was added: manual, discovery, import")
    added_date: str = Field(default="", description="ISO date when entry was added")


# ---------------------------------------------------------------------------
# Profile entry — project-specific interpretation
# ---------------------------------------------------------------------------


class ProjectProfileEntry(BaseModel):
    """Project-specific interpretation of a library."""

    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(..., description="Must match a catalog key")
    priority: Priority = Field(default=Priority.tier2, description="Priority tier")
    runtime_import: RuntimeImport = Field(
        default=RuntimeImport.reference_only,
        description="How the library participates in runtime",
    )
    decision_default: DecisionDefault = Field(
        default=DecisionDefault.new,
        description="Default engineering decision",
    )
    curated_note: str = Field(default="", description="Path to curated note")
    capabilities: list[str] = Field(default_factory=list, description="Capability tags")
    status: Status = Field(default=Status.active, description="Lifecycle state")
    notes: str = Field(default="", description="Short local comment")


# ---------------------------------------------------------------------------
# Merged record — catalog + profile for a single library
# ---------------------------------------------------------------------------


class LibraryRecord(BaseModel):
    """Merged view combining catalog and profile for a single library."""

    model_config = ConfigDict(use_enum_values=True)

    # identity
    name: str = Field(..., description="Library slug key")

    # catalog fields
    kind: Kind = Field(..., description="Identity class")
    role: str = Field(default="", description="Project role: core, shared, or external")
    language: str = Field(default="", description="Dominant language")
    repo_url: str = Field(default="", description="Upstream repo URL")
    pip_name: str = Field(default="", description="Package manager name")
    license: str = Field(default="", description="Software license")
    path: str = Field(default="", description="Local path for internal code or mirrors")
    summary: str = Field(default="", description="Short description")
    repo_id: str = Field(default="", description="FK to Repository entry in repos.yml")
    added_by: str = Field(default="", description="How the entry was added")
    added_date: str = Field(default="", description="ISO date when entry was added")

    # profile fields
    priority: Priority = Field(default=Priority.tier2, description="Priority tier")
    runtime_import: RuntimeImport = Field(
        default=RuntimeImport.reference_only,
        description="How the library participates in runtime",
    )
    decision_default: DecisionDefault = Field(
        default=DecisionDefault.new,
        description="Default engineering decision",
    )
    curated_note: str = Field(default="", description="Path to curated note")
    capabilities: list[str] = Field(default_factory=list, description="Capability tags")
    status: Status = Field(default=Status.active, description="Lifecycle state")
    notes: str = Field(default="", description="Short local comment")

    # merge metadata
    has_profile: bool = Field(
        default=False,
        description="Whether a project profile was found for this library",
    )

    @classmethod
    def from_entries(
        cls,
        catalog: LibraryCatalogEntry,
        profile: ProjectProfileEntry | None = None,
    ) -> LibraryRecord:
        """Merge a catalog entry and an optional profile into a single record."""
        data = catalog.model_dump()
        if profile is not None:
            # Overlay profile fields (skip 'name' — already present from catalog)
            profile_data = profile.model_dump(exclude={"name"})
            data.update(profile_data)
            data["has_profile"] = True
        return cls(**data)


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------


class ValidationResult(BaseModel):
    """Result of a registry validation pass."""

    valid: bool = Field(..., description="Whether the registry passed validation")
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")


# ---------------------------------------------------------------------------
# Repository entity — first-class repo identity
# ---------------------------------------------------------------------------


class RepositoryEntry(BaseModel):
    """A version-controlled repository tracked by codio."""

    model_config = ConfigDict(use_enum_values=True)

    repo_id: str = Field(..., description="Canonical slug (e.g. scipy--scipy)")
    url: str = Field(default="", description="Clone URL")
    hosting: Hosting = Field(default=Hosting.other, description="Hosting provider")
    storage: Storage = Field(default=Storage.external, description="Storage mode")
    local_path: str = Field(default="", description="Filesystem path when cloned locally")
    default_branch: str = Field(default="main", description="Default branch name")


# ---------------------------------------------------------------------------
# Code source — indexable unit within a repository
# ---------------------------------------------------------------------------


class CodeSourceEntry(BaseModel):
    """A unit of code within a repository that codio tracks."""

    model_config = ConfigDict(use_enum_values=True)

    source_id: str = Field(..., description="Unique slug within the registry")
    repo_id: str = Field(default="", description="FK to RepositoryEntry")
    subpath: str = Field(default="", description="Path within the repository")
    source_type: SourceType = Field(default=SourceType.tree, description="Source unit type")
    indexable: bool = Field(default=True, description="Whether to register in indexio")


# ---------------------------------------------------------------------------
# Registry snapshot
# ---------------------------------------------------------------------------


class RegistrySnapshot(BaseModel):
    """Full registry payload containing all catalog entries and profiles."""

    libraries: dict[str, LibraryCatalogEntry] = Field(
        ..., description="Catalog entries keyed by library name"
    )
    profiles: dict[str, ProjectProfileEntry] = Field(
        ..., description="Profile entries keyed by library name"
    )
    repositories: dict[str, RepositoryEntry] = Field(
        default_factory=dict, description="Repository entries keyed by repo_id"
    )
    version: str = Field(default="0.2.0", description="Registry schema version")
