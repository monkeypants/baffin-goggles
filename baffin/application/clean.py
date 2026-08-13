"""CleanGallery: prune orphaned derivatives (`baffin clean`; see
:doc:`/use-cases`).

An orphan is a stored derivative whose key is no longer in the live plan — e.g.
a tier turned off, or a source that's gone. ``--all`` treats *everything* as an
orphan by passing an empty live set, wiping the cache.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from baffin.application.assembly import assemble_assets
from baffin.application.config import GalleryConfig
from baffin.application.planning import plan_derivatives
from baffin.application.ports import (
    AssetRepository,
    DerivativeStore,
    Hasher,
    MetadataReader,
)
from baffin.application.reporting import BuildReport


@dataclass(frozen=True)
class CleanResult:
    removed: tuple[Path, ...]


@dataclass(frozen=True)
class CleanGallery:
    repo: AssetRepository
    hasher: Hasher
    reader: MetadataReader
    store: DerivativeStore

    def execute(self, config: GalleryConfig, *, wipe: bool = False) -> CleanResult:
        live_keys: set[str] = set()
        if not wipe:
            refs = self.repo.discover(config.source)
            assets = assemble_assets(
                refs,
                self.hasher,
                self.reader,
                report=BuildReport(),
                strict=config.strict,
            )
            plan = plan_derivatives(
                assets, config.specs, include_full=config.include_full
            )
            live_keys = {p.cache_key for p in plan}

        orphans = list(self.store.orphans(live_keys))
        for path in orphans:
            self.store.delete(path)
        return CleanResult(removed=tuple(orphans))
