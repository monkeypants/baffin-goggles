"""Shared thumbnailer suite: Vips and Pillow must agree on dims + GPS strip."""

import hashlib
import os
from collections.abc import Callable
from pathlib import Path

import pyexiv2
import pytest
from PIL import Image

from baffin.adapters.thumbnails import PillowThumbnailer, VipsThumbnailer
from baffin.application.ports import Thumbnailer
from baffin.domain import AssetMeta, DerivativeSpec, SourceRef

JpegFactory = Callable[..., Path]

THUMB = DerivativeSpec("thumb", 300, 80)
FULL = DerivativeSpec("full", None, 95)


@pytest.fixture(params=["vips", "pillow"])
def thumbnailer(request: pytest.FixtureRequest) -> Thumbnailer:
    return {"vips": VipsThumbnailer(), "pillow": PillowThumbnailer()}[request.param]


def _ref(path: Path) -> SourceRef:
    stat = path.stat()
    return SourceRef(path=path, size=stat.st_size, mtime_ns=stat.st_mtime_ns)


def test_downscales_to_longest_edge(
    thumbnailer: Thumbnailer, make_jpeg: JpegFactory, tmp_path: Path
) -> None:
    src = make_jpeg(size=(800, 600))
    dst = tmp_path / "thumb" / "hash.jpg"
    deriv = thumbnailer.render(_ref(src), THUMB, dst, strip_gps=True, embed=None)
    assert (deriv.width, deriv.height) == (300, 225)
    assert Image.open(dst).size == (300, 225)


def test_full_tier_keeps_original_dimensions(
    thumbnailer: Thumbnailer, make_jpeg: JpegFactory, tmp_path: Path
) -> None:
    src = make_jpeg(size=(640, 480))
    dst = tmp_path / "full" / "hash.jpg"
    deriv = thumbnailer.render(_ref(src), FULL, dst, strip_gps=True, embed=None)
    assert (deriv.width, deriv.height) == (640, 480)


def test_full_tier_handles_a_rotated_original(
    thumbnailer: Thumbnailer, tmp_path: Path
) -> None:
    # Regression: the full tier read with sequential access, which autorot()
    # + sharpen() break with "out of order read" on a rotated JPEG. A tall,
    # detailed original tagged Orientation=6 (display-rotated 90°) exercises it.
    src = tmp_path / "portrait.jpg"
    Image.frombytes("RGB", (1200, 1800), os.urandom(1200 * 1800 * 3)).save(
        src, "JPEG", quality=92
    )
    with pyexiv2.Image(str(src)) as handle:
        handle.modify_exif({"Exif.Image.Orientation": "6"})

    dst = tmp_path / "full" / "hash.jpg"
    deriv = thumbnailer.render(_ref(src), FULL, dst, strip_gps=True, embed=None)

    # Orientation 6 swaps the displayed dimensions; the full tier must not crash.
    assert (deriv.width, deriv.height) == (1800, 1200)
    assert Image.open(dst).size == (1800, 1200)


def test_gps_is_stripped_from_output(
    thumbnailer: Thumbnailer, make_jpeg: JpegFactory, tmp_path: Path
) -> None:
    src = make_jpeg(
        exif={
            "Exif.GPSInfo.GPSLatitude": "66/1 30/1 0/1",
            "Exif.GPSInfo.GPSLatitudeRef": "N",
            "Exif.GPSInfo.GPSLongitude": "65/1 42/1 0/1",
            "Exif.GPSInfo.GPSLongitudeRef": "W",
        }
    )
    dst = tmp_path / "thumb" / "hash.jpg"
    thumbnailer.render(_ref(src), THUMB, dst, strip_gps=True, embed=None)

    with pyexiv2.Image(str(dst)) as handle:
        exif = handle.read_exif()
    assert not any(key.startswith("Exif.GPSInfo") for key in exif)


def test_original_is_untouched(
    thumbnailer: Thumbnailer, make_jpeg: JpegFactory, tmp_path: Path
) -> None:
    src = make_jpeg()
    before = hashlib.sha256(src.read_bytes()).hexdigest()
    thumbnailer.render(
        _ref(src), THUMB, tmp_path / "t" / "h.jpg", strip_gps=True, embed=None
    )
    assert hashlib.sha256(src.read_bytes()).hexdigest() == before


def test_embeds_authored_caption(
    thumbnailer: Thumbnailer, make_jpeg: JpegFactory, tmp_path: Path
) -> None:
    src = make_jpeg()
    dst = tmp_path / "thumb" / "hash.jpg"
    thumbnailer.render(
        _ref(src),
        THUMB,
        dst,
        strip_gps=True,
        embed=AssetMeta(caption="River crossing", credit="Chris"),
    )
    with pyexiv2.Image(str(dst)) as handle:
        iptc = handle.read_iptc()
    assert iptc.get("Iptc.Application2.Caption") == "River crossing"
    assert iptc.get("Iptc.Application2.Credit") == "Chris"
