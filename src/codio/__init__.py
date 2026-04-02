"""Top-level package for codio."""

from codio.config import CodioConfig, load_config
from codio.models import (
    CodeSourceEntry,
    LibraryCatalogEntry,
    LibraryRecord,
    ProjectProfileEntry,
    RegistrySnapshot,
    RepositoryEntry,
    ValidationResult,
)
from codio.paths import find_project_root
from codio.registry import Registry, load_catalog, load_profiles, load_repos
from codio.scaffold import ScaffoldResult, init_codio_scaffold
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
    get_vocab,
)

__all__ = [
    "AddedBy",
    "CodeSourceEntry",
    "CodioConfig",
    "DecisionDefault",
    "Hosting",
    "Kind",
    "LibraryCatalogEntry",
    "LibraryRecord",
    "Priority",
    "ProjectProfileEntry",
    "Role",
    "Registry",
    "RegistrySnapshot",
    "RepositoryEntry",
    "RuntimeImport",
    "ScaffoldResult",
    "SourceType",
    "Status",
    "Storage",
    "ValidationResult",
    "find_project_root",
    "get_vocab",
    "init_codio_scaffold",
    "load_catalog",
    "load_config",
    "load_profiles",
    "load_repos",
]
