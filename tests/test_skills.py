from __future__ import annotations
from codio.skills.discovery import discover
from codio.skills.update import add_library, remove_library, update_profile, validate_registry
from codio.skills.study import study_library, compare_libraries
from codio.models import LibraryCatalogEntry, ProjectProfileEntry
from codio.vocab import Kind, Priority, RuntimeImport, DecisionDefault


# --- Discovery ---

def test_discover_by_capability(registry):
    result = discover("arrays", registry)
    assert len(result.candidates) > 0
    assert result.candidates[0].name == "numpy-mirror"
    assert "Capability match" in result.candidates[0].relevance_reason


def test_discover_by_name(registry):
    result = discover("numpy", registry)
    assert any(c.name == "numpy-mirror" for c in result.candidates)


def test_discover_by_summary(registry):
    result = discover("utility", registry)
    assert any(c.name == "internal-utils" for c in result.candidates)


def test_discover_no_match(registry):
    result = discover("nonexistent-capability-xyz", registry)
    assert len(result.candidates) == 0
    assert result.recommended_decision == "new"


def test_discover_with_language_filter(registry):
    result = discover("arrays", registry, language="python")
    assert len(result.candidates) > 0
    result2 = discover("arrays", registry, language="rust")
    assert len(result2.candidates) == 0


# --- Update ---

def test_add_library(registry):
    new_cat = LibraryCatalogEntry(name="newlib", kind=Kind.utility, language="python", summary="New library")
    new_prof = ProjectProfileEntry(name="newlib", priority=Priority.tier1)
    add_library(registry, new_cat, new_prof)
    record = registry.get("newlib")
    assert record is not None
    assert record.kind == "utility"
    assert record.priority == "tier1"


def test_add_library_catalog_only(registry):
    new_cat = LibraryCatalogEntry(name="catonly", kind=Kind.internal, summary="Catalog only")
    add_library(registry, new_cat)
    record = registry.get("catonly")
    assert record is not None
    assert record.has_profile is False


def test_remove_library(registry):
    assert registry.get("internal-utils") is not None
    result = remove_library(registry, "internal-utils")
    assert result is True
    assert registry.get("internal-utils") is None


def test_remove_nonexistent(registry):
    result = remove_library(registry, "nonexistent")
    assert result is False


def test_update_profile(registry):
    new_prof = ProjectProfileEntry(name="internal-utils", priority=Priority.tier2, decision_default=DecisionDefault.wrap)
    result = update_profile(registry, new_prof)
    assert result is True
    record = registry.get("internal-utils")
    assert record.priority == "tier2"
    assert record.decision_default == "wrap"


def test_update_profile_missing_catalog(registry):
    new_prof = ProjectProfileEntry(name="nonexistent")
    result = update_profile(registry, new_prof)
    assert result is False


def test_validate_registry(registry):
    result = validate_registry(registry)
    assert result.valid is True


# --- Study ---

def test_study_library(registry):
    analysis = study_library("numpy-mirror", registry)
    assert analysis is not None
    assert analysis.name == "numpy-mirror"
    assert analysis.kind == "external_mirror"
    assert len(analysis.strengths) > 0
    assert analysis.has_curated_note is True


def test_study_internal_library(registry):
    analysis = study_library("internal-utils", registry)
    assert analysis is not None
    assert analysis.kind == "internal"
    assert any("internal" in s.lower() or "Internal" in s for s in analysis.strengths)


def test_study_missing_library(registry):
    assert study_library("nonexistent", registry) is None


def test_compare_libraries(registry):
    result = compare_libraries(["internal-utils", "numpy-mirror"], registry, query="computing")
    assert len(result.libraries) == 2
    assert result.recommendation != ""
    assert isinstance(result.shared_capabilities, list)
    assert isinstance(result.distinguishing_factors, list)


def test_compare_single_library(registry):
    result = compare_libraries(["numpy-mirror"], registry)
    assert len(result.libraries) == 1
    assert "numpy-mirror" in result.recommendation


def test_compare_no_libraries(registry):
    result = compare_libraries(["nonexistent"], registry)
    assert len(result.libraries) == 0
