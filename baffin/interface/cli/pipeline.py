"""Shell build pipeline: plan in the core, fan generation out in the shell.

Assembles assets, plans and diffs against the cache (pure), then generates only
the misses via the AssetProcessor (serial or pooled) and renders. Videos branch
by kind inside the processor.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from baffin.adapters.generation import generate
from baffin.adapters.processor import AssetJob, AssetProcessor
from baffin.adapters.render.renderer import Jinja2Renderer
from baffin.adapters.repository import FsAssetRepository
from baffin.adapters.store import FileDerivativeStore
from baffin.application.assembly import assemble_assets
from baffin.application.config import GalleryConfig
from baffin.application.grouping import group_timeline
from baffin.application.planning import diff_plan, plan_derivatives
from baffin.application.reporting import BuildReport
from baffin.domain import DerivativeSpec, Site, SourceRef


def _model(config: GalleryConfig) -> Site:
    processor = AssetProcessor.from_config(config)
    refs = FsAssetRepository().discover(config.source)
    assets = assemble_assets(
        refs,
        processor.hasher,
        processor.reader,
        report=BuildReport(),
        strict=config.strict,
    )
    groups = group_timeline(assets, config.grouping)
    return Site(title=config.title, base_url=config.base_url, peers=(), groups=groups)


@dataclass(frozen=True)
class BuildSummary:
    generated: int
    groups: int
    skipped: tuple[tuple[str, str], ...]


def run_build(config: GalleryConfig, *, jobs: int = 1) -> BuildSummary:
    repo = FsAssetRepository()
    store = FileDerivativeStore(config.output)
    processor = AssetProcessor.from_config(config)
    report = BuildReport()

    refs = repo.discover(config.source)
    assets = assemble_assets(
        refs, processor.hasher, processor.reader, report=report, strict=config.strict
    )
    groups = group_timeline(assets, config.grouping)
    plan = plan_derivatives(assets, config.specs, include_full=config.include_full)
    diff = diff_plan(plan, store.snapshot())

    grouped: dict[SourceRef, list[DerivativeSpec]] = {}
    for miss in diff.misses:
        grouped.setdefault(miss.asset.ref, []).append(miss.spec)
    job_list = [AssetJob(ref=ref, specs=tuple(specs)) for ref, specs in grouped.items()]

    generated = 0
    for result in generate(processor, job_list, workers=jobs):
        for gen in result.generated:
            store.record(gen.cache_key, gen.derivative)
            generated += 1

    site = Site(title=config.title, base_url=config.base_url, peers=(), groups=groups)
    Jinja2Renderer().render(site, config.output)
    return BuildSummary(
        generated=generated,
        groups=len(groups),
        skipped=tuple((label, str(error)) for label, error in report.skipped),
    )


def render_only(config: GalleryConfig) -> None:
    """Re-render templates over the existing model; no derivatives generated."""
    Jinja2Renderer().render(_model(config), config.output)


def watch_templates(config: GalleryConfig, template_dir: Path) -> None:
    """Block, re-rendering the site whenever a template changes (never regen)."""
    from watchfiles import watch

    for _ in watch(template_dir):
        render_only(config)
