"""Asset assembly (see :doc:`/lazy-build`):
source refs become domain Assets by hash + read.
The two fallible steps run under skip-and-report,
so one unreadable file is skipped and recorded while the run continues;
--strict makes it fatal.
"""

from pathlib import Path

import pytest

from baffin.application.assembly import assemble_assets
from baffin.application.errors import MetadataUnreadable
from baffin.application.reporting import BuildReport
from baffin.domain import RawMetadata, SourceRef
from baffin.testing.fakes import FakeHasher, FakeMetadataReader


def _ref(name: str) -> SourceRef:
    return SourceRef(path=Path("photos") / name, size=1, mtime_ns=1)


class _BrokenReader:
    def read(self, ref: SourceRef) -> RawMetadata:
        raise MetadataUnreadable(str(ref.path))


def test_a_readable_ref_becomes_an_asset() -> None:
    report = BuildReport()
    [asset] = assemble_assets(
        [_ref("a.jpg")],
        FakeHasher(),
        FakeMetadataReader(),
        report=report,
        strict=False,
    )
    assert asset.content_hash == "hash-a"
    assert asset.kind == "photo"
    assert report.ok


def test_an_unreadable_asset_is_skipped_and_reported() -> None:
    report = BuildReport()
    assets = assemble_assets(
        [_ref("bad.jpg")],
        FakeHasher(),
        _BrokenReader(),
        report=report,
        strict=False,
    )
    assert assets == []
    assert [label for label, _ in report.skipped] == ["photos/bad.jpg"]


def test_strict_makes_an_unreadable_asset_fatal() -> None:
    with pytest.raises(MetadataUnreadable):
        assemble_assets(
            [_ref("bad.jpg")],
            FakeHasher(),
            _BrokenReader(),
            report=BuildReport(),
            strict=True,
        )
