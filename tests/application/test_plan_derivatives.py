"""Derivative planning (SPEC §7): a pure expansion of every asset by every
active spec into content-addressed tiers. The full tier is opt-in, so toggling
``include_full`` adds or drops only that one tier.
"""

from pathlib import Path

from baffin.application.planning import plan_derivatives
from baffin.domain import DerivativeSpec
from baffin.testing.builders import an_asset

THUMB = DerivativeSpec("thumb", 300, 80)
MED = DerivativeSpec("med", 1600, 82)
FULL = DerivativeSpec("full", None, 95)
SPECS = [THUMB, MED, FULL]


def test_expands_every_asset_by_every_active_spec() -> None:
    assets = [an_asset("a"), an_asset("b")]
    plan = plan_derivatives(assets, [THUMB, MED])  # full absent entirely
    assert len(plan) == 4  # 2 assets, 2 specs
    assert {p.rel_path for p in plan} == {
        Path("thumb/a.jpg"),
        Path("med/a.jpg"),
        Path("thumb/b.jpg"),
        Path("med/b.jpg"),
    }
    assert all(p.cache_key == p.spec.cache_key(p.asset) for p in plan)


def test_include_full_toggle_touches_only_the_full_tier() -> None:
    assets = [an_asset("a")]
    without = plan_derivatives(assets, SPECS, include_full=False)
    with_full = plan_derivatives(assets, SPECS, include_full=True)

    without_names = {p.spec.name for p in without}
    with_names = sorted(p.spec.name for p in with_full)
    assert without_names == {"thumb", "med"}
    assert with_names == ["full", "med", "thumb"]
    # Non-full entries are identical whether or not full is included.
    assert {p.cache_key for p in without} == {
        p.cache_key for p in with_full if p.spec.name != "full"
    }
