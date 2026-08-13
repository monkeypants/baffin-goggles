"""Domain layer: pure frozen dataclasses and the cache-key logic (SPEC §4)."""

from baffin.domain.models import (
    Asset,
    AssetKind,
    AssetMeta,
    CameraInfo,
    Derivative,
    DerivativeSpec,
    GpsFix,
    Group,
    Peer,
    RawMetadata,
    Site,
    SourceRef,
    SpecName,
    StoreState,
)

__all__ = [
    "Asset",
    "AssetKind",
    "AssetMeta",
    "CameraInfo",
    "Derivative",
    "DerivativeSpec",
    "GpsFix",
    "Group",
    "Peer",
    "RawMetadata",
    "Site",
    "SourceRef",
    "SpecName",
    "StoreState",
]
