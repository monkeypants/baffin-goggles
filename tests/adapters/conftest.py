"""Shared adapter fixtures: generate tiny media on disk (no committed binaries)."""

from collections.abc import Callable, Mapping
from pathlib import Path

import pyexiv2
import pytest
from PIL import Image

JpegFactory = Callable[..., Path]


@pytest.fixture
def make_jpeg(tmp_path: Path) -> JpegFactory:
    """Return a factory that writes a JPEG (optionally with EXIF tags)."""

    def _make(
        name: str = "a.jpg",
        size: tuple[int, int] = (640, 480),
        exif: Mapping[str, str] | None = None,
        color: tuple[int, int, int] = (30, 80, 160),
    ) -> Path:
        path = tmp_path / name
        Image.new("RGB", size, color).save(path, "JPEG", quality=90)
        if exif:
            with pyexiv2.Image(str(path)) as img:
                img.modify_exif(dict(exif))
        return path

    return _make
