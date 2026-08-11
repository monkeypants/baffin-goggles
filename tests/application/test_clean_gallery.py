"""CleanGallery: orphans removed, live derivatives retained, --all wipes."""

from pathlib import Path

from baffin.application.assembly import assemble_assets
from baffin.application.clean import CleanGallery
from baffin.application.config import GalleryConfig
from baffin.application.planning import plan_derivatives
from baffin.application.reporting import BuildReport
from baffin.domain import Derivative, SourceRef
from baffin.testing.fakes import (
    FakeAssetRepository,
    FakeDerivativeStore,
    FakeHasher,
    FakeMetadataReader,
)

REFS = [SourceRef(path=Path("photos/a.jpg"), size=1, mtime_ns=1)]


def _config(**kw: object) -> GalleryConfig:
    return GalleryConfig(source=Path("photos"), output=Path("site"), **kw)  # type: ignore[arg-type]


def _store_with_all_tiers() -> FakeDerivativeStore:
    """A store that recorded every tier including full (as if a prior --full run)."""
    store = FakeDerivativeStore()
    assets = assemble_assets(
        REFS, FakeHasher(), FakeMetadataReader(), report=BuildReport(), strict=False
    )
    for planned in plan_derivatives(assets, _config().specs, include_full=True):
        store.record(
            planned.cache_key,
            Derivative(
                asset_hash=planned.asset.content_hash,
                spec_name=planned.spec.name,
                rel_path=planned.rel_path,
                width=1,
                height=1,
            ),
        )
    return store


def _cleaner(store: FakeDerivativeStore) -> CleanGallery:
    return CleanGallery(
        repo=FakeAssetRepository(REFS),
        hasher=FakeHasher(),
        reader=FakeMetadataReader(),
        store=store,
    )


def test_turning_full_off_makes_full_tier_an_orphan() -> None:
    store = _store_with_all_tiers()
    result = _cleaner(store).execute(_config(include_full=False))

    assert result.removed == (Path("full/hash-a.jpg"),)
    # The three live tiers survive.
    surviving = store.snapshot().present
    assert len(surviving) == 3


def test_all_wipes_the_whole_cache() -> None:
    store = _store_with_all_tiers()
    result = _cleaner(store).execute(_config(), wipe=True)

    assert len(result.removed) == 4
    assert store.snapshot().present == frozenset()
