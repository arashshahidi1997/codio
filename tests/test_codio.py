from __future__ import annotations


def test_import() -> None:
    import codio

    assert codio.__name__ == "codio"
