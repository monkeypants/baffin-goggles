"""Tracing a gallery image back to its original (see :doc:`/use-cases`).

``content_hash_of`` recovers the content hash from a hash, derivative path, or
image URL; ``ResolveOrigins`` inverts the build into a hash → source-path index.
"""

from pathlib import Path

from baffin.application.origin import ResolveOrigins, content_hash_of
from baffin.domain import SourceRef
from baffin.testing.fakes import FakeAssetRepository, FakeHasher


def _ref(name: str) -> SourceRef:
    return SourceRef(path=Path("photos") / name, size=1, mtime_ns=1)


def test_content_hash_of_reads_hash_path_and_url() -> None:
    assert content_hash_of("069f10b0a11b9961") == "069f10b0a11b9961"
    assert content_hash_of("full/069f10b0a11b9961.jpg") == "069f10b0a11b9961"
    assert content_hash_of("http://h/med/069f10b0a11b9961.jpg") == "069f10b0a11b9961"


def test_content_hash_of_rejects_non_hashes() -> None:
    assert content_hash_of("DSC00003.JPG") is None
    # A 64-hex SHA-256 cache key is not a 16-hex content hash.
    assert content_hash_of("a" * 64) is None


def test_resolve_origins_maps_hash_to_source_path() -> None:
    refs = [_ref("DSC1.JPG"), _ref("DSC2.JPG")]
    hasher = FakeHasher(
        by_path={
            refs[0].path: "aaaa000000000000",
            refs[1].path: "bbbb000000000000",
        }
    )
    resolver = ResolveOrigins(repo=FakeAssetRepository(refs), hasher=hasher)

    index = resolver.index(Path("photos"))

    assert index["aaaa000000000000"] == Path("photos/DSC1.JPG")
    assert index["bbbb000000000000"] == Path("photos/DSC2.JPG")
