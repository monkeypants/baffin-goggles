"""ExifMetadataReader: EXIF read, mtime fallback, gps, and video handling."""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import pytest

from baffin.adapters.metadata import ExifMetadataReader
from baffin.application.errors import MetadataUnreadable
from baffin.domain import SourceRef

JpegFactory = Callable[..., Path]


def _ref(path: Path, *, mtime_ns: int = 1_600_000_000_000_000_000) -> SourceRef:
    return SourceRef(path=path, size=path.stat().st_size, mtime_ns=mtime_ns)


def test_reads_exif_datetime_dims_orientation_and_camera(
    make_jpeg: JpegFactory,
) -> None:
    path = make_jpeg(
        size=(800, 600),
        exif={
            "Exif.Photo.DateTimeOriginal": "2025:07:14 09:30:00",
            "Exif.Image.Orientation": "6",
            "Exif.Image.Model": "ILCE-7M4",
            "Exif.Photo.ISOSpeedRatings": "200",
            "Exif.Photo.FNumber": "56/10",
            "Exif.Photo.FocalLength": "35/1",
        },
    )
    meta = ExifMetadataReader().read(_ref(path))

    assert meta.kind == "photo"
    assert meta.captured_at == datetime(2025, 7, 14, 9, 30, 0)
    assert (meta.width, meta.height) == (800, 600)
    assert meta.orientation == 6
    assert meta.camera is not None
    assert meta.camera.model == "ILCE-7M4"
    assert meta.camera.iso == 200
    assert meta.camera.aperture == pytest.approx(5.6)
    assert meta.camera.focal_len == pytest.approx(35.0)


def test_captured_at_falls_back_to_mtime(make_jpeg: JpegFactory) -> None:
    path = make_jpeg()  # no DateTimeOriginal
    mtime_ns = 1_700_000_000_000_000_000
    meta = ExifMetadataReader().read(_ref(path, mtime_ns=mtime_ns))
    assert meta.captured_at == datetime.fromtimestamp(mtime_ns / 1_000_000_000)


def test_gps_is_read_when_present_and_none_when_absent(
    make_jpeg: JpegFactory,
) -> None:
    plain = make_jpeg(name="plain.jpg")
    assert ExifMetadataReader().read(_ref(plain)).gps is None

    tagged = make_jpeg(
        name="tagged.jpg",
        exif={
            "Exif.GPSInfo.GPSLatitude": "66/1 30/1 0/1",
            "Exif.GPSInfo.GPSLatitudeRef": "N",
            "Exif.GPSInfo.GPSLongitude": "65/1 42/1 0/1",
            "Exif.GPSInfo.GPSLongitudeRef": "W",
        },
    )
    gps = ExifMetadataReader().read(_ref(tagged)).gps
    assert gps is not None
    assert gps.lat == pytest.approx(66.5)
    assert gps.lon == pytest.approx(-65.7)


def test_video_gets_a_minimal_record(tmp_path: Path) -> None:
    clip = tmp_path / "c.mp4"
    clip.write_bytes(b"not really a video")
    meta = ExifMetadataReader().read(_ref(clip))
    assert meta.kind == "video"
    assert (meta.width, meta.height) == (0, 0)


def test_unreadable_image_raises(tmp_path: Path) -> None:
    fake = tmp_path / "broken.jpg"
    fake.write_bytes(b"this is not a jpeg")
    with pytest.raises(MetadataUnreadable):
        ExifMetadataReader().read(_ref(fake))
