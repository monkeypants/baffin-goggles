"""Derivative planning and cache diffing (SPEC §8): pure functional core.

``plan_derivatives`` expands assets x specs into content-addressed planned
derivatives; ``diff_plan`` splits that plan into cache HITs and MISSes against a
:class:`~baffin.domain.StoreState` snapshot. No I/O — the shell pre-checks file
existence into the snapshot so this stays pure.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from baffin.domain import Asset, DerivativeSpec


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
