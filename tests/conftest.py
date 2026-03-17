from __future__ import annotations
import pytest
from pathlib import Path
import tempfile
import yaml


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory with sample registry files."""
    codio_dir = tmp_path / ".projio" / "codio"
    codio_dir.mkdir(parents=True)

    catalog_data = {
        "libraries": {
            "internal-utils": {
                "kind": "internal",
                "language": "python",
                "path": "src/utils",
                "summary": "Internal utility functions",
            },
            "numpy-mirror": {
                "kind": "external_mirror",
                "language": "python",
                "repo_url": "https://github.com/numpy/numpy",
                "pip_name": "numpy",
                "license": "BSD-3-Clause",
                "summary": "Numerical computing library",
            },
            "no-profile-lib": {
                "kind": "utility",
                "language": "python",
                "summary": "A library without a profile",
            },
        }
    }

    profiles_data = {
        "profiles": {
            "internal-utils": {
                "priority": "tier1",
                "runtime_import": "internal",
                "decision_default": "existing",
                "capabilities": ["utilities", "helpers"],
                "status": "active",
            },
            "numpy-mirror": {
                "priority": "tier2",
                "runtime_import": "pip_only",
                "decision_default": "wrap",
                "capabilities": ["numerical-computing", "arrays"],
                "curated_note": "docs/reference/numpy.md",
                "status": "active",
            },
        }
    }

    with open(codio_dir / "catalog.yml", "w") as f:
        yaml.dump(catalog_data, f)
    with open(codio_dir / "profiles.yml", "w") as f:
        yaml.dump(profiles_data, f)

    return tmp_path


@pytest.fixture
def registry(tmp_project):
    """Create a Registry from the tmp_project fixture."""
    from codio.config import CodioConfig
    from codio.registry import Registry

    config = CodioConfig(
        catalog_path=tmp_project / ".projio" / "codio" / "catalog.yml",
        profiles_path=tmp_project / ".projio" / "codio" / "profiles.yml",
        project_root=tmp_project,
    )
    return Registry(config=config)
