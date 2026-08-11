"""Domain layer: pure frozen dataclasses and the cache-key logic (SPEC §4)."""

from baffin.domain.models import (
    AssetKind,
    AssetMeta,
    CameraInfo,
    Derivative,
    GpsFix,
    Peer,
    RawMetadata,
    SourceRef,
    StoreState,
)

__all__ = [
    "AssetKind",
    "AssetMeta",
    "CameraInfo",
    "Derivative",
    "GpsFix",
    "Peer",
    "RawMetadata",
    "SourceRef",
    "StoreState",
]
