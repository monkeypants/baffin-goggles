"""diff_plan: HIT/MISS partitioning over an immutable cache snapshot."""

from datetime import datetime
from pathlib import Path

from baffin.application.planning import diff_plan, plan_derivatives
from baffin.domain import Asset, DerivativeSpec, SourceRef, StoreState

THUMB = DerivativeSpec("thumb", 300, 80)
MED = DerivativeSpec("med", 1600, 82)


def _asset(tag: str, path: str = "photos/a.jpg") -> Asset:
    return Asset(
        ref=SourceRef(path=Path(path), size=1, mtime_ns=1),
        content_hash=tag,
        kind="photo",
        captured_at=datetime(2025, 7, 14, 9),
        width=100,
        height=100,
        orientation=1,
    )


def test_fully_cached_plan_is_all_hits() -> None:
    plan = plan_derivatives([_asset("a")], [THUMB, MED])
    snapshot = StoreState(present=frozenset(p.cache_key for p in plan))
    result = diff_plan(plan, snapshot)
    assert result.misses == ()
    assert len(result.hits) == 2


def test_empty_snapshot_is_all_misses() -> None:
    plan = plan_derivatives([_asset("a")], [THUMB, MED])
    result = diff_plan(plan, StoreState())
    assert result.hits == ()
    assert len(result.misses) == 2


def test_changed_spec_misses_only_that_tier() -> None:
    asset = _asset("a")
    old = plan_derivatives([asset], [THUMB, MED])
    snapshot = StoreState(present=frozenset(p.cache_key for p in old))

    # thumb re-tuned 300 -> 320; med unchanged.
    new_thumb = DerivativeSpec("thumb", 320, 80)
    new = plan_derivatives([asset], [new_thumb, MED])
    result = diff_plan(new, snapshot)

    assert [p.spec.name for p in result.misses] == ["thumb"]
    assert [p.spec.name for p in result.hits] == ["med"]


def test_moved_source_with_same_bytes_is_a_hit() -> None:
    # Same content_hash, different source path (a rename/move) -> same key.
    original = _asset("samebytes", path="photos/2025/a.jpg")
    moved = _asset("samebytes", path="archive/renamed.jpg")
    snapshot = StoreState(
        present=frozenset(p.cache_key for p in plan_derivatives([original], [THUMB]))
    )
    result = diff_plan(plan_derivatives([moved], [THUMB]), snapshot)
    assert result.misses == ()
    assert len(result.hits) == 1
