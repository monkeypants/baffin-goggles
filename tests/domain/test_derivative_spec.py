"""DerivativeSpec.cache_key: deterministic, content- and spec-sensitive (SPEC §8)."""

from datetime import datetime
from pathlib import Path

from baffin.domain import Asset, DerivativeSpec, SourceRef


def _asset(content_hash: str) -> Asset:
    return Asset(
        ref=SourceRef(path=Path("photos/a.jpg"), size=10, mtime_ns=20),
        content_hash=content_hash,
        kind="photo",
        captured_at=datetime(2025, 7, 14, 9, 30),
        width=6000,
        height=4000,
        orientation=1,
    )


THUMB = DerivativeSpec(name="thumb", max_edge=300, quality=80)


def test_cache_key_is_stable_across_runs() -> None:
    """Pinned digest: proves SHA-256 over a canonical string, not the builtin
    per-process-salted hash() — the key must be identical run to run."""
    key = THUMB.cache_key(_asset("hash-a"))
    assert key == "7a5d20c407dee678a9a382d24afdad08628ae95363d9433ee8b922ea3bd2b6f9"
    assert key == THUMB.cache_key(_asset("hash-a"))  # repeatable within a run


def test_cache_key_distinct_per_content_hash() -> None:
    assert THUMB.cache_key(_asset("hash-a")) != THUMB.cache_key(_asset("hash-b"))


def test_cache_key_changes_when_any_spec_field_changes() -> None:
    asset = _asset("hash-a")
    base = THUMB.cache_key(asset)
    assert DerivativeSpec("thumb", 320, 80).cache_key(asset) != base  # max_edge
    assert DerivativeSpec("thumb", 300, 82).cache_key(asset) != base  # quality
    assert DerivativeSpec("low", 300, 80).cache_key(asset) != base  # name


def test_cache_key_handles_full_tier_none_max_edge() -> None:
    full = DerivativeSpec(name="full", max_edge=None, quality=95)
    key = full.cache_key(_asset("hash-a"))
    assert len(key) == 64  # sha256 hexdigest
    assert key != THUMB.cache_key(_asset("hash-a"))
