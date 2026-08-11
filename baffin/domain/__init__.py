"""Domain layer: pure frozen dataclasses and the cache-key logic (SPEC §4)."""

from baffin.domain.models import (
    Asset,
    AssetKind,
    AssetMeta,
    CameraInfo,
    Derivative,
    GpsFix,
    Group,
    Peer,
    RawMetadata,
    Site,
    SourceRef,
    StoreState,
)

__all__ = [
    "Asset",
    "AssetKind",
    "AssetMeta",
    "CameraInfo",
    "Derivative",
    "GpsFix",
    "Group",
    "Peer",
    "RawMetadata",
    "Site",
    "SourceRef",
    "StoreState",
]
