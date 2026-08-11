"""Asset aggregate and the Group/Site timeline model: construction + immutability."""

from dataclasses import FrozenInstanceError
from datetime import datetime
from pathlib import Path

import pytest

from baffin.domain import Asset, CameraInfo, GpsFix, Group, Peer, Site, SourceRef


def _asset(content_hash: str = "hash-a") -> Asset:
    return Asset(
        ref=SourceRef(path=Path("photos/a.jpg"), size=10, mtime_ns=20),
        content_hash=content_hash,
        kind="photo",
        captured_at=datetime(2025, 7, 14, 9, 30),
        width=6000,
        height=4000,
        orientation=1,
    )


def test_asset_construction_and_optional_defaults() -> None:
    asset = _asset()
    assert asset.content_hash == "hash-a"
    assert asset.kind == "photo"
    assert asset.camera is None
    assert asset.gps is None


def test_asset_accepts_camera_and_gps() -> None:
    asset = Asset(
        ref=SourceRef(path=Path("photos/b.jpg"), size=1, mtime_ns=2),
        content_hash="hash-b",
        kind="photo",
        captured_at=datetime(2025, 7, 15, 12, 0),
        width=100,
        height=100,
        orientation=6,
        camera=CameraInfo(iso=200, model="ILCE-7M4"),
        gps=GpsFix(lat=66.5, lon=-65.7),
    )
    assert asset.camera is not None
    assert asset.camera.iso == 200
    assert asset.gps is not None


def test_asset_is_frozen() -> None:
    asset = _asset()
    with pytest.raises(FrozenInstanceError):
        asset.content_hash = "changed"  # type: ignore[misc]


def test_group_holds_assets_and_is_frozen() -> None:
    a = _asset()
    span = (datetime(2025, 7, 14, 0, 0), datetime(2025, 7, 14, 23, 59))
    group = Group(key="day-01", label="Day 1 — 14 Jul", span=span, assets=(a,))
    assert group.assets == (a,)
    with pytest.raises(FrozenInstanceError):
        group.label = "x"  # type: ignore[misc]


def test_site_composes_groups_and_peers_and_is_frozen() -> None:
    a = _asset()
    span = (datetime(2025, 7, 14, 0, 0), datetime(2025, 7, 14, 23, 59))
    group = Group(key="day-01", label="Day 1", span=span, assets=(a,))
    site = Site(
        title="Akshayuk Pass",
        base_url="https://example.com/baffin/",
        peers=(Peer(name="Dana", url="https://dana.example.com/"),),
        groups=(group,),
    )
    assert site.groups == (group,)
    assert site.peers[0].name == "Dana"
    with pytest.raises(FrozenInstanceError):
        site.title = "x"  # type: ignore[misc]
