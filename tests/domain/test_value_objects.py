"""Domain value objects: immutability, field shapes, and type distinctions."""

from dataclasses import FrozenInstanceError, fields
from datetime import datetime
from pathlib import Path

import pytest

from baffin.domain import (
    AssetMeta,
    CameraInfo,
    Derivative,
    GpsFix,
    Peer,
    RawMetadata,
    SourceRef,
    StoreState,
)


def test_source_ref_is_frozen() -> None:
    ref = SourceRef(path=Path("photos/a.jpg"), size=123, mtime_ns=456)
    with pytest.raises(FrozenInstanceError):
        ref.size = 999  # type: ignore[misc]


def test_source_ref_field_shapes() -> None:
    ref = SourceRef(path=Path("photos/a.jpg"), size=123, mtime_ns=456)
    assert ref.path == Path("photos/a.jpg")
    assert ref.size == 123
    assert ref.mtime_ns == 456


def test_optional_value_objects_default_to_none() -> None:
    assert CameraInfo() == CameraInfo(
        iso=None, shutter=None, aperture=None, focal_len=None, lens=None, model=None
    )
    assert AssetMeta() == AssetMeta(title=None, caption=None, credit=None, alt=None)


def test_gps_fix_altitude_is_optional() -> None:
    fix = GpsFix(lat=66.5, lon=-65.7)
    assert fix.altitude is None
    with pytest.raises(FrozenInstanceError):
        fix.lat = 0.0  # type: ignore[misc]


def test_store_state_defaults_to_empty_snapshot() -> None:
    assert StoreState().present == frozenset()
    populated = StoreState(present=frozenset({"k1", "k2"}))
    assert "k1" in populated.present


def test_derivative_and_peer_field_shapes() -> None:
    deriv = Derivative(
        asset_hash="abc",
        spec_name="thumb",
        rel_path=Path("thumb/abc.jpg"),
        width=300,
        height=200,
    )
    assert deriv.spec_name == "thumb"
    peer = Peer(name="Dana", url="https://dana.example.com/baffin/")
    assert peer.name == "Dana"


def test_raw_metadata_and_asset_meta_are_distinct() -> None:
    """RawMetadata (technical read) and AssetMeta (authored text) must not be
    conflated — they are different types with different fields (§4, §5)."""
    raw = RawMetadata(
        kind="photo",
        captured_at=datetime(2025, 7, 14, 9, 30),
        width=6000,
        height=4000,
        orientation=1,
    )
    meta = AssetMeta(title="River crossing")

    assert type(raw) is not type(meta)
    raw_fields = {f.name for f in fields(raw)}
    meta_fields = {f.name for f in fields(meta)}
    assert raw_fields == {
        "kind",
        "captured_at",
        "width",
        "height",
        "orientation",
        "camera",
        "gps",
    }
    assert meta_fields == {"title", "caption", "credit", "alt"}
    assert raw_fields.isdisjoint(meta_fields)
