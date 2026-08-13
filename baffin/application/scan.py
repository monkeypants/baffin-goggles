"""ScanGallery: the dry run (`baffin scan`; see :doc:`/use-cases`).

Discover → assemble → group → plan → diff, and report the HIT/MISS plan.
Generates nothing and records nothing; read-only.
"""

from __future__ import annotations

from dataclasses import dataclass

from baffin.application.assembly import assemble_assets
from baffin.application.config import GalleryConfig
from baffin.application.grouping import group_timeline
from baffin.application.planning import BuildPlan, diff_plan, plan_derivatives
from baffin.application.ports import (
    AssetRepository,
    DerivativeStore,
    Hasher,
    MetadataReader,
)
from baffin.application.reporting import BuildReport
from baffin.domain import Asset, Group


@dataclass(frozen=True)
class ScanReport:
    assets: tuple[Asset, ...]
    groups: tuple[Group, ...]
    plan: BuildPlan
    report: BuildReport

    @property
    def hits(self) -> int:
        return len(self.plan.hits)

    @property
    def misses(self) -> int:
        return len(self.plan.misses)


@dataclass(frozen=True)
class ScanGallery:
    repo: AssetRepository
    hasher: Hasher
    reader: MetadataReader
    store: DerivativeStore

    def execute(self, config: GalleryConfig) -> ScanReport:
        report = BuildReport()
        refs = self.repo.discover(config.source)
        assets = assemble_assets(
            refs, self.hasher, self.reader, report=report, strict=config.strict
        )
        groups = group_timeline(assets, config.grouping)
        plan = plan_derivatives(assets, config.specs, include_full=config.include_full)
        build = diff_plan(plan, self.store.snapshot())
        return ScanReport(
            assets=tuple(assets), groups=groups, plan=build, report=report
        )
