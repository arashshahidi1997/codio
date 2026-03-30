from __future__ import annotations
from pathlib import Path
import yaml
from codio.registry import Registry, load_catalog, load_profiles
from codio.config import CodioConfig


def test_load_catalog(tmp_project):
    entries = load_catalog(tmp_project / ".projio" / "codio" / "catalog.yml")
    assert "internal-utils" in entries
    assert "numpy-mirror" in entries
    assert entries["internal-utils"].kind == "internal"


def test_load_catalog_missing_file(tmp_path):
    entries = load_catalog(tmp_path / "nonexistent.yml")
    assert entries == {}


def test_load_profiles(tmp_project):
    entries = load_profiles(tmp_project / ".projio" / "codio" / "profiles.yml")
    assert "internal-utils" in entries
    assert entries["internal-utils"].priority == "tier1"


def test_registry_list_all(registry):
    records = registry.list()
    assert len(records) == 3
    names = {r.name for r in records}
    assert names == {"internal-utils", "numpy-mirror", "no-profile-lib"}


def test_registry_list_filter_kind(registry):
    records = registry.list(kind="internal")
    assert len(records) == 1
    assert records[0].name == "internal-utils"


def test_registry_list_filter_capability(registry):
    records = registry.list(capability="arrays")
    assert len(records) == 1
    assert records[0].name == "numpy-mirror"


def test_registry_list_filter_language(registry):
    records = registry.list(language="python")
    assert len(records) == 3


def test_registry_list_filter_no_match(registry):
    records = registry.list(kind="external_mirror", capability="nonexistent")
    assert len(records) == 0


def test_registry_get(registry):
    record = registry.get("internal-utils")
    assert record is not None
    assert record.kind == "internal"
    assert record.priority == "tier1"
    assert record.has_profile is True


def test_registry_get_no_profile(registry):
    record = registry.get("no-profile-lib")
    assert record is not None
    assert record.has_profile is False
    assert record.priority == "tier2"  # default


def test_registry_get_missing(registry):
    assert registry.get("nonexistent") is None


def test_registry_snapshot(registry):
    snap = registry.snapshot()
    assert len(snap.libraries) == 3
    assert len(snap.profiles) == 2


def test_registry_validate(registry):
    result = registry.validate()
    assert result.valid is True
    # no-profile-lib should generate a warning
    assert any("no-profile-lib" in w for w in result.warnings)
    # numpy curated_note doesn't exist -> warning
    assert any("curated_note" in w for w in result.warnings)


def test_registry_catalog_property(registry):
    """registry.catalog is a public property, not a private attribute."""
    cat = registry.catalog
    assert isinstance(cat, dict)
    assert "internal-utils" in cat
    assert "numpy-mirror" in cat


def test_registry_validate_orphan_profile(tmp_path):
    """Profile referencing non-existent catalog entry should be an error."""
    codio_dir = tmp_path / ".projio" / "codio"
    codio_dir.mkdir(parents=True)
    with open(codio_dir / "catalog.yml", "w") as f:
        yaml.dump({"libraries": {"real": {"kind": "internal"}}}, f)
    with open(codio_dir / "profiles.yml", "w") as f:
        yaml.dump({"profiles": {"ghost": {"priority": "tier1"}}}, f)

    config = CodioConfig(
        catalog_path=codio_dir / "catalog.yml",
        profiles_path=codio_dir / "profiles.yml",
        project_root=tmp_path,
    )
    reg = Registry(config=config)
    result = reg.validate()
    assert result.valid is False
    assert any("ghost" in e for e in result.errors)
