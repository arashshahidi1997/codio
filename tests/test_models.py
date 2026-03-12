from __future__ import annotations
import pytest
from codio.models import LibraryCatalogEntry, ProjectProfileEntry, LibraryRecord, ValidationResult, RegistrySnapshot
from codio.vocab import Kind, RuntimeImport, DecisionDefault, Priority, Status


def test_catalog_entry_required_fields():
    entry = LibraryCatalogEntry(name="foo", kind=Kind.internal)
    assert entry.name == "foo"
    assert entry.kind == "internal"
    assert entry.language == ""


def test_catalog_entry_all_fields():
    entry = LibraryCatalogEntry(
        name="numpy", kind=Kind.external_mirror,
        language="python", repo_url="https://github.com/numpy/numpy",
        pip_name="numpy", license="BSD-3-Clause", path="mirrors/numpy",
        summary="Numerical computing",
    )
    assert entry.pip_name == "numpy"
    assert entry.license == "BSD-3-Clause"


def test_profile_entry_defaults():
    entry = ProjectProfileEntry(name="foo")
    assert entry.priority == "tier2"
    assert entry.runtime_import == "reference_only"
    assert entry.decision_default == "new"
    assert entry.capabilities == []
    assert entry.status == "active"


def test_profile_entry_custom():
    entry = ProjectProfileEntry(
        name="numpy", priority=Priority.tier1,
        runtime_import=RuntimeImport.pip_only,
        decision_default=DecisionDefault.wrap,
        capabilities=["arrays", "math"],
    )
    assert entry.priority == "tier1"
    assert entry.capabilities == ["arrays", "math"]


def test_library_record_from_catalog_only():
    catalog = LibraryCatalogEntry(name="foo", kind=Kind.internal, summary="test")
    record = LibraryRecord.from_entries(catalog)
    assert record.name == "foo"
    assert record.kind == "internal"
    assert record.has_profile is False
    assert record.priority == "tier2"  # default


def test_library_record_from_entries():
    catalog = LibraryCatalogEntry(name="bar", kind=Kind.external_mirror, language="python")
    profile = ProjectProfileEntry(name="bar", priority=Priority.tier1, decision_default=DecisionDefault.wrap, capabilities=["graphs"])
    record = LibraryRecord.from_entries(catalog, profile)
    assert record.name == "bar"
    assert record.kind == "external_mirror"
    assert record.priority == "tier1"
    assert record.decision_default == "wrap"
    assert record.capabilities == ["graphs"]
    assert record.has_profile is True


def test_library_record_serialization():
    catalog = LibraryCatalogEntry(name="x", kind=Kind.utility)
    record = LibraryRecord.from_entries(catalog)
    d = record.model_dump()
    assert d["name"] == "x"
    assert d["kind"] == "utility"
    assert isinstance(d, dict)


def test_validation_result():
    v = ValidationResult(valid=True)
    assert v.valid is True
    assert v.errors == []
    assert v.warnings == []

    v2 = ValidationResult(valid=False, errors=["bad"], warnings=["warn"])
    assert v2.valid is False
    assert len(v2.errors) == 1


def test_registry_snapshot():
    cat = LibraryCatalogEntry(name="a", kind=Kind.internal)
    prof = ProjectProfileEntry(name="a")
    snap = RegistrySnapshot(libraries={"a": cat}, profiles={"a": prof})
    assert "a" in snap.libraries
    assert snap.version == "0.1.0"
