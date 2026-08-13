"""Parallel generation matches serial byte-for-byte (see :doc:`/lazy-build`)."""

import hashlib
from pathlib import Path

from PIL import Image

from baffin.application.config import GalleryConfig
from baffin.interface.cli.pipeline import run_build


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


def test_parallel_output_is_identical_to_serial(tmp_path: Path) -> None:
    photos = tmp_path / "photos"
    _photos(photos, 3)

    serial = tmp_path / "serial"
    parallel = tmp_path / "parallel"
    s = run_build(GalleryConfig(source=photos, output=serial), jobs=1)
    p = run_build(GalleryConfig(source=photos, output=parallel), jobs=3)

    assert s.generated == p.generated == 9  # 3 photos, 3 tiers
    assert _tier_hashes(serial) == _tier_hashes(parallel)
