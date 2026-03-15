from __future__ import annotations
from codio.vocab import Kind, RuntimeImport, DecisionDefault, Priority, Status, get_vocab


def test_kind_values():
    assert set(Kind) == {Kind.internal, Kind.external_mirror, Kind.utility}


def test_runtime_import_values():
    assert set(RuntimeImport) == {RuntimeImport.internal, RuntimeImport.pip_only, RuntimeImport.reference_only}


def test_decision_default_values():
    assert set(DecisionDefault) == {DecisionDefault.existing, DecisionDefault.wrap, DecisionDefault.direct, DecisionDefault.new}


def test_priority_values():
    assert set(Priority) == {Priority.tier1, Priority.tier2, Priority.tier3}


def test_status_values():
    assert set(Status) == {Status.active, Status.candidate, Status.deprecated}


def test_enum_descriptions():
    assert Kind.internal.description != ""
    assert RuntimeImport.pip_only.description != ""


def test_get_vocab_structure():
    vocab = get_vocab()
    assert set(vocab.keys()) == {
        "kind", "runtime_import", "decision_default", "priority", "status",
        "storage", "hosting", "source_type", "added_by",
    }
    for field_name, field_data in vocab.items():
        assert "values" in field_data
        assert "description" in field_data
        assert isinstance(field_data["values"], dict)
        assert all(isinstance(v, str) for v in field_data["values"].values())


def test_get_vocab_kind_values():
    vocab = get_vocab()
    assert "internal" in vocab["kind"]["values"]
    assert "external_mirror" in vocab["kind"]["values"]
    assert "utility" in vocab["kind"]["values"]
