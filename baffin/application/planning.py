"""Derivative planning and cache diffing (SPEC §8): pure functional core.

``plan_derivatives`` expands assets x specs into content-addressed planned
derivatives; ``diff_plan`` splits that plan into cache HITs and MISSes against a
:class:`~baffin.domain.StoreState` snapshot. No I/O — the shell pre-checks file
existence into the snapshot so this stays pure.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from baffin.domain import Asset, DerivativeSpec, StoreState


@dataclass(frozen=True)
class PlannedDerivative:
    """One intended output tier for one asset, with its cache key and path."""

    asset: Asset
    spec: DerivativeSpec
    cache_key: str
    rel_path: Path


def plan_derivatives(
    assets: list[Asset] | tuple[Asset, ...],
    specs: list[DerivativeSpec] | tuple[DerivativeSpec, ...],
    *,
    include_full: bool = False,
) -> tuple[PlannedDerivative, ...]:
    """Expand ``(asset x specs)`` into planned JPEG tiers (SPEC §7).

    The ``full`` tier is opt-in: with ``include_full=False`` any spec named
    ``full`` is dropped, so toggling it changes only that tier.

    >>> from baffin.application.planning import plan_derivatives
    >>> from baffin.domain import DerivativeSpec
    >>> from baffin.testing.builders import an_asset
    >>> specs = [DerivativeSpec("thumb", 300, 80), DerivativeSpec("full", None, 95)]
    >>> [p.rel_path.as_posix() for p in plan_derivatives([an_asset("x")], specs)]
    ['thumb/x.jpg']
    >>> plan = plan_derivatives([an_asset("x")], specs, include_full=True)
    >>> [p.rel_path.as_posix() for p in plan]
    ['thumb/x.jpg', 'full/x.jpg']
    """
    active = [s for s in specs if s.name != "full" or include_full]
    planned: list[PlannedDerivative] = []
    for asset in assets:
        for spec in active:
            planned.append(
                PlannedDerivative(
                    asset=asset,
                    spec=spec,
                    cache_key=spec.cache_key(asset),
                    rel_path=Path(spec.name) / f"{asset.content_hash}.jpg",
                )
            )
    return tuple(planned)


@dataclass(frozen=True)
class BuildPlan:
    """The plan split against the cache: what to skip vs what to generate."""

    hits: tuple[PlannedDerivative, ...]
    misses: tuple[PlannedDerivative, ...]


def diff_plan(
    plan: tuple[PlannedDerivative, ...], store_state: StoreState
) -> BuildPlan:
    """Split a plan into cache HITs and MISSes over an immutable snapshot.

    Pure: a key is a HIT iff it is ``present`` in the snapshot (manifest-recorded
    AND file-on-disk, pre-checked by the shell). Identical bytes yield an
    identical key, so a moved or duplicated source is a hit; changing a spec
    changes only that tier's key, so only that tier misses.

    >>> from baffin.application.planning import diff_plan, plan_derivatives
    >>> from baffin.domain import DerivativeSpec, StoreState
    >>> from baffin.testing.builders import an_asset
    >>> plan = plan_derivatives([an_asset("x")], [DerivativeSpec("thumb", 300, 80)])
    >>> warm = StoreState(present=frozenset(p.cache_key for p in plan))
    >>> diff_plan(plan, warm).misses
    ()
    >>> len(diff_plan(plan, StoreState()).misses)
    1
    """
    hits = tuple(p for p in plan if p.cache_key in store_state.present)
    misses = tuple(p for p in plan if p.cache_key not in store_state.present)
    return BuildPlan(hits=hits, misses=misses)
