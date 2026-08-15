"""BuildGallery: the lazy build (`baffin build`; see :doc:`/lazy-build`).

Discover → assemble → group → plan → diff,
generate only the MISSes, then always render (HTML is cheap).
Generation is per-asset skip-and-report;
the manifest records every derivative produced.

Video poster/clip generation branches by kind
in the Phase-5 ``AssetProcessor`` composite;
this use case drives the photo-tier path via the ``Thumbnailer``.
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
    SidecarStore,
    SiteRenderer,
    Thumbnailer,
)
from baffin.application.reporting import BuildReport, per_asset
from baffin.domain import Site


@dataclass(frozen=True)
class BuildResult:
    plan: BuildPlan
    generated: tuple[str, ...]
    report: BuildReport
    site: Site


@dataclass(frozen=True)
class BuildGallery:
    repo: AssetRepository
    hasher: Hasher
    reader: MetadataReader
    sidecars: SidecarStore
    thumbnailer: Thumbnailer
    store: DerivativeStore
    renderer: SiteRenderer

    def execute(self, config: GalleryConfig) -> BuildResult:
        report = BuildReport()
        refs = self.repo.discover(config.source)
        assets = assemble_assets(
            refs, self.hasher, self.reader, report=report, strict=config.strict
        )
        groups = group_timeline(assets, config.grouping)
        plan = plan_derivatives(assets, config.specs, include_full=config.include_full)
        build = diff_plan(plan, self.store.snapshot())

        generated: list[str] = []
        for miss in build.misses:
            with per_asset(report, str(miss.asset.ref.path), strict=config.strict):
                embed = self.sidecars.read(miss.asset.ref)
                dst = config.output / miss.rel_path
                deriv = self.thumbnailer.render(
                    miss.asset.ref,
                    miss.spec,
                    dst,
                    strip_gps=config.strip_gps,
                    embed=embed,
                )
                self.store.record(miss.cache_key, deriv)
                generated.append(miss.cache_key)

        site = Site(
            title=config.title,
            base_url=config.base_url,
            peers=(),
            groups=groups,
            photo_tiers=config.active_photo_specs,
            show_filenames=config.show_filenames,
        )
        self.renderer.render(site, config.output)  # always: HTML is cheap
        return BuildResult(
            plan=build, generated=tuple(generated), report=report, site=site
        )
