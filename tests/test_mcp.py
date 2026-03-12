from __future__ import annotations
from codio.mcp import mcp_list, mcp_get, mcp_registry, mcp_vocab, mcp_validate


def test_mcp_list(registry):
    result = mcp_list(registry)
    assert isinstance(result, list)
    assert len(result) == 3
    assert all(isinstance(r, dict) for r in result)
    names = {r["name"] for r in result}
    assert "internal-utils" in names


def test_mcp_list_filtered(registry):
    result = mcp_list(registry, kind="internal")
    assert len(result) == 1
    assert result[0]["name"] == "internal-utils"


def test_mcp_get(registry):
    result = mcp_get(registry, "numpy-mirror")
    assert result is not None
    assert result["name"] == "numpy-mirror"
    assert result["kind"] == "external_mirror"
    assert result["has_profile"] is True


def test_mcp_get_missing(registry):
    assert mcp_get(registry, "nonexistent") is None


def test_mcp_registry(registry):
    result = mcp_registry(registry)
    assert "libraries" in result
    assert "profiles" in result
    assert "version" in result


def test_mcp_vocab():
    result = mcp_vocab()
    assert "kind" in result
    assert "runtime_import" in result
    assert "internal" in result["kind"]["values"]


def test_mcp_validate(registry):
    result = mcp_validate(registry)
    assert isinstance(result, dict)
    assert "valid" in result
    assert "errors" in result
    assert "warnings" in result
