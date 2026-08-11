"""BuildGallery: only misses generated, render always runs, strict vs skip."""

from pathlib import Path

import pytest

from baffin.application.assembly import assemble_assets
from baffin.application.build import BuildGallery
from baffin.application.config import GalleryConfig
from baffin.application.errors import DerivativeFailed
from baffin.application.planning import plan_derivatives
from baffin.application.reporting import BuildReport
from baffin.domain import AssetMeta, Derivative, DerivativeSpec, SourceRef
from baffin.testing.fakes import (
    FakeAssetRepository,
    FakeDerivativeStore,
    FakeHasher,
    FakeMetadataReader,
    FakeSidecarStore,
    FakeSiteRenderer,
    FakeThumbnailer,
)

REFS = [
    SourceRef(path=Path("photos/a.jpg"), size=1, mtime_ns=1),
    SourceRef(path=Path("photos/b.jpg"), size=2, mtime_ns=2),
]


def _config(**kw: object) -> GalleryConfig:
    return GalleryConfig(source=Path("photos"), output=Path("site"), **kw)  # type: ignore[arg-type]


def _build(thumbnailer: object = None, store: object = None) -> BuildGallery:
    return BuildGallery(
        repo=FakeAssetRepository(REFS),
        hasher=FakeHasher(),
        reader=FakeMetadataReader(),
        sidecars=FakeSidecarStore(),
        thumbnailer=thumbnailer or FakeThumbnailer(),  # type: ignore[arg-type]
        store=store or FakeDerivativeStore(),  # type: ignore[arg-type]
        renderer=FakeSiteRenderer(),
    )


def test_generates_only_missing_tiers() -> None:
    # Pre-seed the cache with every tier for asset "a" so only "b" misses.
    assets = assemble_assets(
        [REFS[0]],
        FakeHasher(),
        FakeMetadataReader(),
        report=BuildReport(),
        strict=False,
    )
    present = {p.cache_key for p in plan_derivatives(assets, _config().specs)}
    store = FakeDerivativeStore(present=present)
    thumb = FakeThumbnailer()

    build = _build(thumbnailer=thumb, store=store)
    result = build.execute(_config())

    assert set(thumb.rendered) == {"hash-b"}  # only the uncached asset
    assert all(k in store.recorded for k in result.generated)


def test_render_always_runs_even_with_no_misses() -> None:
    assets = assemble_assets(
        REFS, FakeHasher(), FakeMetadataReader(), report=BuildReport(), strict=False
    )
    present = {p.cache_key for p in plan_derivatives(assets, _config().specs)}
    renderer = FakeSiteRenderer()
    build = BuildGallery(
        repo=FakeAssetRepository(REFS),
        hasher=FakeHasher(),
        reader=FakeMetadataReader(),
        sidecars=FakeSidecarStore(),
        thumbnailer=FakeThumbnailer(),
        store=FakeDerivativeStore(present=present),
        renderer=renderer,
    )
    result = build.execute(_config())
    assert result.generated == ()
    assert len(renderer.rendered) == 1


class _RaisingThumbnailer:
    def render(
        self,
        src: SourceRef,
        spec: DerivativeSpec,
        dst: Path,
        *,
        strip_gps: bool,
        embed: AssetMeta | None,
    ) -> Derivative:
        raise DerivativeFailed(f"cannot render {dst}")


def test_skip_and_report_survives_a_failing_asset() -> None:
    build = _build(thumbnailer=_RaisingThumbnailer())
    result = build.execute(_config())
    assert result.generated == ()
    assert len(result.report.skipped) > 0  # failures recorded, run completed


def test_strict_makes_a_failing_asset_fatal() -> None:
    build = _build(thumbnailer=_RaisingThumbnailer())
    with pytest.raises(DerivativeFailed):
        build.execute(_config(strict=True))
