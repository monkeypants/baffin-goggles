"""Builders for test fixtures.

``an_asset`` returns a photo captured 14 Jul 2025 whose content hash is its tag.
Tests override only the fields they care about.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from baffin.domain import Asset, AssetKind, CameraInfo, GpsFix, SourceRef

_DEFAULT_CAPTURED = datetime(2025, 7, 14, 9, 30)


def a_source_ref(
    name: str = "a.jpg", *, size: int = 10, mtime_ns: int = 20
) -> SourceRef:
    """A source ref under ``photos/``: the read-only original's handle."""
    return SourceRef(path=Path("photos") / name, size=size, mtime_ns=mtime_ns)


def an_asset(
    tag: str = "a",
    *,
    captured_at: datetime = _DEFAULT_CAPTURED,
    kind: AssetKind = "photo",
    width: int = 6000,
    height: int = 4000,
    orientation: int = 1,
    camera: CameraInfo | None = None,
    gps: GpsFix | None = None,
    content_hash: str | None = None,
    at_path: str | None = None,
) -> Asset:
    """Build an Asset.
    ``content_hash`` defaults to ``tag``;
    ``at_path`` moves the source without changing identity
    (to demonstrate move == cache hit)."""
    ref = (
        SourceRef(path=Path(at_path), size=10, mtime_ns=20)
        if at_path is not None
        else a_source_ref(f"{tag}.jpg")
    )
    return Asset(
        ref=ref,
        content_hash=content_hash if content_hash is not None else tag,
        kind=kind,
        captured_at=captured_at,
        width=width,
        height=height,
        orientation=orientation,
        camera=camera,
        gps=gps,
    )
