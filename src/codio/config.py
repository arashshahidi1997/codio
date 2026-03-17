from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CATALOG_PATH = ".projio/codio/catalog.yml"
DEFAULT_PROFILES_PATH = ".projio/codio/profiles.yml"
DEFAULT_REPOS_PATH = ".projio/codio/repos.yml"
DEFAULT_NOTES_DIR = "docs/reference/codelib/libraries/"
DEFAULT_MIRRORS_DIR = ".projio/codio/mirrors/"


def _default_path(value: str) -> Path:
    return field(default_factory=lambda v=value: Path(v))


@dataclass
class CodioConfig:
    catalog_path: Path = _default_path(DEFAULT_CATALOG_PATH)
    profiles_path: Path = _default_path(DEFAULT_PROFILES_PATH)
    repos_path: Path = _default_path(DEFAULT_REPOS_PATH)
    notes_dir: Path = _default_path(DEFAULT_NOTES_DIR)
    mirrors_dir: Path = _default_path(DEFAULT_MIRRORS_DIR)
    project_root: Path = field(default_factory=lambda: Path("."))


def load_config(project_root: Path | None = None) -> CodioConfig:
    """Load Codio configuration, optionally from a .projio/config.yml file.

    If *project_root* is ``None`` the current working directory is used.
    When a ``.projio/config.yml`` file exists under the project root its
    ``codio`` section is read and merged with the defaults.  All paths are
    resolved relative to *project_root*.
    """
    if project_root is None:
        project_root = Path.cwd()
    project_root = Path(project_root)

    config_file = project_root / ".projio" / "config.yml"

    overrides: dict[str, str] = {}
    if config_file.exists():
        import yaml

        with open(config_file) as fh:
            raw = yaml.safe_load(fh)
        if isinstance(raw, dict) and "codio" in raw:
            section = raw["codio"]
            if isinstance(section, dict):
                overrides = section

    catalog_path = project_root / overrides.get("catalog_path", DEFAULT_CATALOG_PATH)
    profiles_path = project_root / overrides.get("profiles_path", DEFAULT_PROFILES_PATH)
    repos_path = project_root / overrides.get("repos_path", DEFAULT_REPOS_PATH)
    notes_dir = project_root / overrides.get("notes_dir", DEFAULT_NOTES_DIR)
    mirrors_dir = project_root / overrides.get("mirrors_dir", DEFAULT_MIRRORS_DIR)

    return CodioConfig(
        catalog_path=catalog_path,
        profiles_path=profiles_path,
        repos_path=repos_path,
        notes_dir=notes_dir,
        mirrors_dir=mirrors_dir,
        project_root=project_root,
    )
