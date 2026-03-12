"""Top-level package for codio."""

from codio.config import CodioConfig, load_config
from codio.models import (
    LibraryCatalogEntry,
    LibraryRecord,
    ProjectProfileEntry,
    RegistrySnapshot,
    ValidationResult,
)
from codio.paths import find_project_root
from codio.registry import Registry, load_catalog, load_profiles
from codio.scaffold import ScaffoldResult, init_codio_scaffold
from codio.vocab import (
    DecisionDefault,
    Kind,
    Priority,
    RuntimeImport,
    Status,
    get_vocab,
)

__all__ = [
    "CodioConfig",
    "DecisionDefault",
    "Kind",
    "LibraryCatalogEntry",
    "LibraryRecord",
    "Priority",
    "ProjectProfileEntry",
    "Registry",
    "RegistrySnapshot",
    "RuntimeImport",
    "ScaffoldResult",
    "Status",
    "ValidationResult",
    "find_project_root",
    "get_vocab",
    "init_codio_scaffold",
    "load_catalog",
    "load_config",
    "load_profiles",
]
