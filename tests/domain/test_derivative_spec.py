"""The derivative cache key (see :doc:`/lazy-build`).
It is a SHA-256 over the content hash plus the spec
— deterministic across runs and machines, unlike the salted builtin ``hash`` —
so it can back a cache.
Distinct content or spec yields a distinct key.
"""

from baffin.domain import DerivativeSpec
from baffin.testing.builders import an_asset

THUMB = DerivativeSpec(name="thumb", max_edge=300, quality=80)


def test_cache_key_is_stable_across_runs() -> None:
    key = THUMB.cache_key(an_asset("hash-a"))
    # Pinned digest: proves SHA-256 over a canonical string, not salted hash().
    assert key == "7a5d20c407dee678a9a382d24afdad08628ae95363d9433ee8b922ea3bd2b6f9"
    assert key == THUMB.cache_key(an_asset("hash-a"))  # repeatable within a run


def test_cache_key_distinct_per_content_hash() -> None:
    assert THUMB.cache_key(an_asset("hash-a")) != THUMB.cache_key(an_asset("hash-b"))


def test_cache_key_changes_when_any_spec_field_changes() -> None:
    asset = an_asset("hash-a")
    base = THUMB.cache_key(asset)
    assert DerivativeSpec("thumb", 320, 80).cache_key(asset) != base  # max_edge
    assert DerivativeSpec("thumb", 300, 82).cache_key(asset) != base  # quality
    assert DerivativeSpec("low", 300, 80).cache_key(asset) != base  # name


def test_cache_key_handles_full_tier_none_max_edge() -> None:
    full = DerivativeSpec(name="full", max_edge=None, quality=95)
    key = full.cache_key(an_asset("hash-a"))
    assert len(key) == 64  # sha256 hexdigest
    assert key != THUMB.cache_key(an_asset("hash-a"))
