"""EXIF metadata reader: pyexiv2 for tags, Pillow for dimensions.

The :class:`MetadataReader` port (see :doc:`/use-cases`). Yields a
:class:`RawMetadata` — the raw technical read, distinct from the authored
sidecar. ``captured_at`` comes from EXIF ``DateTimeOriginal`` and falls back to
the file's mtime. Videos get a minimal record (a real probe is a future
extension); GPS is read here and stripped from outputs later (see
:ref:`rationale-privacy`).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pyexiv2
from PIL import Image, UnidentifiedImageError

from baffin.application.errors import MetadataUnreadable
from baffin.domain import CameraInfo, GpsFix, RawMetadata, SourceRef

_VIDEO_SUFFIXES = frozenset({".mp4", ".mov"})


class ExifMetadataReader:
    def read(self, ref: SourceRef) -> RawMetadata:
        mtime = datetime.fromtimestamp(ref.mtime_ns / 1_000_000_000)
        if ref.path.suffix.lower() in _VIDEO_SUFFIXES:
            return RawMetadata(
                kind="video",
                captured_at=mtime,
                width=0,
                height=0,
                orientation=1,
            )

        try:
            with Image.open(ref.path) as image:
                width, height = image.size
        except (OSError, UnidentifiedImageError) as exc:
            raise MetadataUnreadable(str(ref.path)) from exc

        try:
            with pyexiv2.Image(str(ref.path)) as handle:
                exif: dict[str, str] = handle.read_exif()
        except Exception as exc:  # pyexiv2 raises bare RuntimeError on bad files
            raise MetadataUnreadable(str(ref.path)) from exc

        return RawMetadata(
            kind="photo",
            captured_at=_parse_datetime(exif.get("Exif.Photo.DateTimeOriginal"))
            or mtime,
            width=width,
            height=height,
            orientation=_int(exif.get("Exif.Image.Orientation"), default=1),
            camera=_camera(exif),
            gps=_gps(exif),
        )


def _parse_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def _int(raw: str | None, *, default: int) -> int:
    try:
        return int(raw) if raw is not None else default
    except ValueError:
        return default


def _rational(raw: str | None) -> float | None:
    if not raw:
        return None
    try:
        if "/" in raw:
            num, den = raw.split("/", 1)
            return float(num) / float(den) if float(den) else None
        return float(raw)
    except (ValueError, ZeroDivisionError):
        return None


def _camera(exif: dict[str, str]) -> CameraInfo | None:
    info = CameraInfo(
        iso=_int(exif.get("Exif.Photo.ISOSpeedRatings"), default=0) or None,
        shutter=exif.get("Exif.Photo.ExposureTime"),
        aperture=_rational(exif.get("Exif.Photo.FNumber")),
        focal_len=_rational(exif.get("Exif.Photo.FocalLength")),
        lens=exif.get("Exif.Photo.LensModel"),
        model=exif.get("Exif.Image.Model"),
    )
    return info if info != CameraInfo() else None


def _gps(exif: dict[str, str]) -> GpsFix | None:
    lat = _dms(
        exif.get("Exif.GPSInfo.GPSLatitude"), exif.get("Exif.GPSInfo.GPSLatitudeRef")
    )
    lon = _dms(
        exif.get("Exif.GPSInfo.GPSLongitude"), exif.get("Exif.GPSInfo.GPSLongitudeRef")
    )
    if lat is None or lon is None:
        return None
    return GpsFix(lat=lat, lon=lon)


def _dms(raw: str | None, ref: str | None) -> float | None:
    if not raw:
        return None
    parts = [_rational(p) for p in raw.split()]
    if len(parts) != 3 or any(p is None for p in parts):
        return None
    degrees, minutes, seconds = (p or 0.0 for p in parts)
    value = degrees + minutes / 60 + seconds / 3600
    return -value if ref in {"S", "W"} else value


if TYPE_CHECKING:
    from baffin.application.ports import MetadataReader

    _conforms: MetadataReader = ExifMetadataReader()
