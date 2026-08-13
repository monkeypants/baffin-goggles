"""Cache diffing (see :doc:`/functional-core`):
a plan is split into HITs to skip and MISSes to generate,
purely against an immutable snapshot.
Because the key is the content hash,
identical bytes are one cache entry even after a move;
changing a spec misses only that tier.
"""

from baffin.application.planning import diff_plan, plan_derivatives
from baffin.domain import DerivativeSpec, StoreState
from baffin.testing.builders import an_asset

THUMB = DerivativeSpec("thumb", 300, 80)
MED = DerivativeSpec("med", 1600, 82)


def test_fully_cached_plan_is_all_hits() -> None:
    plan = plan_derivatives([an_asset("a")], [THUMB, MED])
    snapshot = StoreState(present=frozenset(p.cache_key for p in plan))
    result = diff_plan(plan, snapshot)
    assert result.misses == ()
    assert len(result.hits) == 2


def test_empty_snapshot_is_all_misses() -> None:
    plan = plan_derivatives([an_asset("a")], [THUMB, MED])
    result = diff_plan(plan, StoreState())
    assert result.hits == ()
    assert len(result.misses) == 2


def test_changed_spec_misses_only_that_tier() -> None:
    asset = an_asset("a")
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
    original = an_asset("samebytes", at_path="photos/2025/a.jpg")
    moved = an_asset("samebytes", at_path="archive/renamed.jpg")
    snapshot = StoreState(
        present=frozenset(p.cache_key for p in plan_derivatives([original], [THUMB]))
    )
    result = diff_plan(plan_derivatives([moved], [THUMB]), snapshot)
    assert result.misses == ()
    assert len(result.hits) == 1
