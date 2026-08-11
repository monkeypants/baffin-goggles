"""Application ports (SPEC §5): the seams between core and shell.

Every port is a :class:`typing.Protocol` — structural, so adapters and fakes
conform without inheritance. The identity currency is :class:`SourceRef` on the
source side and :class:`~pathlib.Path` on the output side.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

from baffin.domain import (
    AssetMeta,
    Derivative,
    DerivativeSpec,
    RawMetadata,
    Site,
    SourceRef,
    StoreState,
)


class AssetRepository(Protocol):
    """Where photos come from. v1: a local read-only folder. v2: an uploaded set
    landed to a local staging path before discovery — ``SourceRef.path`` is
    always a readable local handle either way."""

    def discover(self, root: Path) -> Iterable[SourceRef]: ...


class MetadataReader(Protocol):
    """Raw EXIF/probe read: dims, kind, orientation, camera, gps, captured_at."""

    def read(self, ref: SourceRef) -> RawMetadata: ...


class SidecarStore(Protocol):
    """Optional per-image metadata beside the original — the ONLY place baffin
    writes into the source tree, and only sidecar files, never the photo bytes."""

    def read(self, ref: SourceRef) -> AssetMeta | None: ...
    def write(self, ref: SourceRef, meta: AssetMeta) -> None: ...


class Hasher(Protocol):
    """xxhash of bytes. Owns the stat->hash memo (SPEC §8.1) internally — an
    unchanged ``(path, size, mtime_ns)`` returns the memoised hash, a changed
    stat re-hashes — so the port stays a single call."""

    def hash_file(self, ref: SourceRef) -> str: ...


class Thumbnailer(Protocol):
    """One image derivative. Default adapter: pyvips; fallback: Pillow."""

    def render(
        self,
        src: SourceRef,
        spec: DerivativeSpec,
        dst: Path,
        *,
        strip_gps: bool,
        embed: AssetMeta | None,
    ) -> Derivative: ...


class VideoProcessor(Protocol):
    """Poster frame + copied clip (no transcode). GPS stripped from the copy."""

    def poster(self, src: SourceRef, spec: DerivativeSpec, dst: Path) -> Derivative: ...
    def publish_clip(self, src: SourceRef, dst: Path, *, strip_gps: bool) -> Path: ...


class DerivativeStore(Protocol):
    """Output dir + manifest. ``snapshot`` reads the manifest AND pre-checks file
    existence, returning the immutable :class:`StoreState` the pure diff consumes
    — so HIT/MISS stays a pure function with no per-key I/O in planning."""

    def snapshot(self) -> StoreState: ...
    def record(self, key: str, deriv: Derivative) -> None: ...
    def orphans(self, live_keys: set[str]) -> Iterable[Path]: ...
    def delete(self, path: Path) -> None: ...


class SiteRenderer(Protocol):
    """Jinja2 -> HTML/CSS/JS. Always runs; cheap."""

    def render(self, site: Site, out: Path) -> None: ...
