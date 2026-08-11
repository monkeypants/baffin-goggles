"""Domain model: plain frozen dataclasses (SPEC §4).

No I/O, no framework imports — stdlib only. Types here are pure value objects;
the only behaviour in the domain is ``DerivativeSpec.cache_key`` (SPEC §3.7).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

AssetKind = Literal["photo", "video"]


@dataclass(frozen=True)
class SourceRef:
    """A location in the read-only source, plus a fast change prefilter."""

    path: Path
    size: int
    mtime_ns: int  # fast prefilter only, never truth


@dataclass(frozen=True)
class CameraInfo:
    """Optional camera settings read from an original's EXIF (all optional)."""

    iso: int | None = None
    shutter: str | None = None  # e.g. "1/250"
    aperture: float | None = None  # f-number
    focal_len: float | None = None  # mm
    lens: str | None = None
    model: str | None = None


@dataclass(frozen=True)
class GpsFix:
    """A GPS reading from an original; stripped from outputs by default (§14)."""

    lat: float
    lon: float
    altitude: float | None = None


@dataclass(frozen=True)
class AssetMeta:
    """Per-image metadata from a sidecar (§13); authored text, all optional.

    Describes a single image — NOT narrative/story data. Distinct from
    :class:`RawMetadata`, which is the raw technical read from an original.
    """

    title: str | None = None
    caption: str | None = None
    credit: str | None = None
    alt: str | None = None


@dataclass(frozen=True)
class RawMetadata:
    """The raw technical read from an original (§5 ``MetadataReader``).

    Everything needed to build an :class:`Asset` except ``ref`` and
    ``content_hash``. Distinct from the authored :class:`AssetMeta` sidecar.
    """

    kind: AssetKind
    captured_at: datetime
    width: int
    height: int
    orientation: int
    camera: CameraInfo | None = None
    gps: GpsFix | None = None


@dataclass(frozen=True)
class Derivative:
    """A generated output tier for one asset (a path within the output site)."""

    asset_hash: str
    spec_name: str
    rel_path: Path
    width: int
    height: int


@dataclass(frozen=True)
class StoreState:
    """Immutable cache snapshot the pure diff consumes (§5, §8).

    ``present`` holds cache keys that are BOTH recorded in the manifest AND
    whose file exists on disk — existence is pre-checked by the shell during
    ``snapshot()`` so ``diff_plan`` stays pure.
    """

    present: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Peer:
    """A fellow traveller's gallery (reserved cross-linking; §15)."""

    name: str
    url: str
