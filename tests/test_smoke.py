"""Smoke test: the package imports cleanly."""


def test_import_baffin() -> None:
    import baffin

    assert baffin is not None
