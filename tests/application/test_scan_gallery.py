"""ScanGallery: correct plan/counts and zero side effects, against fakes."""

from pathlib import Path

from baffin.application.assembly import assemble_assets
from baffin.application.config import GalleryConfig
from baffin.application.planning import plan_derivatives
from baffin.application.reporting import BuildReport
from baffin.application.scan import ScanGallery
from baffin.domain import SourceRef
from baffin.testing.fakes import (
    FakeAssetRepository,
    FakeDerivativeStore,
    FakeHasher,
    FakeMetadataReader,
)

REFS = [
    SourceRef(path=Path("photos/a.jpg"), size=1, mtime_ns=1),
    SourceRef(path=Path("photos/b.jpg"), size=2, mtime_ns=2),
]


def _config() -> GalleryConfig:
    return GalleryConfig(source=Path("photos"), output=Path("site"))


def test_empty_cache_reports_all_misses_and_no_full_tier() -> None:
    store = FakeDerivativeStore()
    scan = ScanGallery(
        repo=FakeAssetRepository(REFS),
        hasher=FakeHasher(),
        reader=FakeMetadataReader(),
        store=store,
    )
    result = scan.execute(_config())

    # 2 assets x 3 tiers (thumb/low/med; full is opt-in and off).
    assert result.hits == 0
    assert result.misses == 6
    assert len(result.assets) == 2


def test_scan_has_no_side_effects() -> None:
    store = FakeDerivativeStore()
    scan = ScanGallery(
        repo=FakeAssetRepository(REFS),
        hasher=FakeHasher(),
        reader=FakeMetadataReader(),
        store=store,
    )
    scan.execute(_config())
    assert store.recorded == []
    assert store.deleted == []


def test_fully_cached_scan_is_all_hits() -> None:
    assets = assemble_assets(
        REFS, FakeHasher(), FakeMetadataReader(), report=BuildReport(), strict=False
    )
    keys = {p.cache_key for p in plan_derivatives(assets, _config().specs)}

    scan = ScanGallery(
        repo=FakeAssetRepository(REFS),
        hasher=FakeHasher(),
        reader=FakeMetadataReader(),
        store=FakeDerivativeStore(present=keys),
    )
    result = scan.execute(_config())
    assert result.misses == 0
    assert result.hits == 6
