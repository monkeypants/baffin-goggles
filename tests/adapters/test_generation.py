"""Parallel generation matches serial byte-for-byte (see :doc:`/lazy-build`)."""

import hashlib
from pathlib import Path

import pytest
from PIL import Image

from baffin.adapters import generation
from baffin.adapters.generation import generate
from baffin.adapters.processor import AssetJob, AssetResult
from baffin.application.config import GalleryConfig
from baffin.application.errors import DerivativeFailed
from baffin.application.reporting import BuildReport
from baffin.domain import SourceRef
from baffin.interface.cli.pipeline import run_build


class _FlakyProcessor:
    """A stand-in AssetProcessor that fails on one named source."""

    def __init__(self, bad: str) -> None:
        self.bad = bad

    def process(self, job: AssetJob) -> AssetResult:
        if job.ref.path.name == self.bad:
            raise DerivativeFailed(str(job.ref.path))
        return AssetResult(content_hash=job.ref.path.stem, generated=())


def _job(name: str) -> AssetJob:
    return AssetJob(
        ref=SourceRef(path=Path("photos") / name, size=1, mtime_ns=1), specs=()
    )


def _photos(root: Path, count: int) -> None:
    root.mkdir(parents=True)
    for i in range(count):
        Image.new("RGB", (1000, 750), (20 * i, 90, 160)).save(
            root / f"p{i}.jpg", "JPEG"
        )


def _tier_hashes(out: Path) -> dict[str, str]:
    prints: dict[str, str] = {}
    for tier in ("thumb", "low", "med"):
        for jpg in (out / tier).glob("*.jpg"):
            key = str(jpg.relative_to(out))
            prints[key] = hashlib.sha256(jpg.read_bytes()).hexdigest()
    return prints


def test_workers_are_spawned_never_forked() -> None:
    """The start method is chosen explicitly, not inherited from the platform.

    libvips initialises a thread pool on import, and forking a process holding
    one deadlocks the child. Python's default hid this: macOS spawns, so the
    pooled build worked there, while Linux forks and hung — which nothing
    caught, because the suite only ever ran on macOS. The test below is the one
    that hangs when this regresses; this one names the reason.
    """
    assert generation._SPAWN.get_start_method() == "spawn"


def test_parallel_output_is_identical_to_serial(tmp_path: Path) -> None:
    photos = tmp_path / "photos"
    _photos(photos, 3)

    serial = tmp_path / "serial"
    parallel = tmp_path / "parallel"
    s = run_build(GalleryConfig(source=photos, output=serial), jobs=1)
    p = run_build(GalleryConfig(source=photos, output=parallel), jobs=3)

    assert s.generated == p.generated == 9  # 3 photos, 3 tiers
    assert _tier_hashes(serial) == _tier_hashes(parallel)


def test_generate_skips_and_reports_a_failing_asset() -> None:
    jobs = [_job("good.jpg"), _job("bad.jpg"), _job("good2.jpg")]
    report = BuildReport()
    results = generate(
        _FlakyProcessor("bad.jpg"), jobs, workers=1, report=report, strict=False
    )
    assert len(results) == 2  # the good ones survive
    assert [label for label, _ in report.skipped] == ["photos/bad.jpg"]


def test_generate_skips_in_the_process_pool_too() -> None:
    jobs = [_job(f"p{i}.jpg") for i in range(4)] + [_job("bad.jpg")]
    report = BuildReport()
    results = generate(
        _FlakyProcessor("bad.jpg"), jobs, workers=2, report=report, strict=False
    )
    assert len(results) == 4
    assert [label for label, _ in report.skipped] == ["photos/bad.jpg"]


def test_generate_strict_makes_a_failing_asset_fatal() -> None:
    report = BuildReport()
    with pytest.raises(DerivativeFailed):
        generate(
            _FlakyProcessor("bad.jpg"),
            [_job("bad.jpg")],
            workers=1,
            report=report,
            strict=True,
        )
