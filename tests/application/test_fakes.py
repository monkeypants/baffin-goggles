"""The fakes behave as advertised (their Protocol conformance is a mypy concern)."""

from pathlib import Path

from baffin.domain import Derivative, DerivativeSpec, SourceRef
from baffin.testing.fakes import (
    FakeAssetRepository,
    FakeDerivativeStore,
    FakeHasher,
    FakeMetadataReader,
)

REF = SourceRef(path=Path("photos/a.jpg"), size=1, mtime_ns=1)


def test_repo_discovers_seeded_refs() -> None:
    repo = FakeAssetRepository([REF])
    assert list(repo.discover(Path("photos"))) == [REF]


def test_hasher_is_deterministic_and_records_calls() -> None:
    hasher = FakeHasher()
    assert hasher.hash_file(REF) == "hash-a"
    assert hasher.calls == [Path("photos/a.jpg")]


def test_metadata_reader_falls_back_to_default() -> None:
    reader = FakeMetadataReader()
    assert reader.read(REF).kind == "photo"


def test_store_records_snapshots_and_prunes() -> None:
    store = FakeDerivativeStore()
    deriv = Derivative(
        asset_hash="a",
        spec_name="thumb",
        rel_path=Path("thumb/a.jpg"),
        width=300,
        height=200,
    )
    store.record("key-a", deriv)
    assert "key-a" in store.snapshot().present

    # key-a is now an orphan if it isn't in the live set.
    orphans = list(store.orphans(live_keys=set()))
    assert orphans == [Path("thumb/a.jpg")]
    store.delete(Path("thumb/a.jpg"))
    assert "key-a" not in store.snapshot().present


def test_spec_used_by_fakes_is_the_real_domain_type() -> None:
    assert DerivativeSpec("thumb", 300, 80).cache_key
