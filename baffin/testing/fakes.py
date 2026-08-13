"""In-memory fakes for every application port (see :doc:`/use-cases`).

Each fake is a fast, deterministic, disk-free stand-in that records what it was
asked to do, so use-case tests can assert behaviour and side effects. Structural
conformance to the Protocols is verified by mypy in the ``TYPE_CHECKING`` block
at the bottom.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from baffin.domain import (
    AssetMeta,
    Derivative,
    DerivativeSpec,
    RawMetadata,
    Site,
    SourceRef,
    StoreState,
)


class FakeAssetRepository:
    def __init__(self, refs: list[SourceRef] | None = None) -> None:
        self._refs = list(refs or [])

    def discover(self, root: Path) -> Iterable[SourceRef]:
        return list(self._refs)


class FakeMetadataReader:
    def __init__(
        self,
        default: RawMetadata | None = None,
        by_path: dict[Path, RawMetadata] | None = None,
    ) -> None:
        self._default = default or RawMetadata(
            kind="photo",
            captured_at=datetime(2025, 7, 14, 9),
            width=100,
            height=100,
            orientation=1,
        )
        self._by_path = dict(by_path or {})

    def read(self, ref: SourceRef) -> RawMetadata:
        return self._by_path.get(ref.path, self._default)


class FakeSidecarStore:
    def __init__(self, initial: dict[Path, AssetMeta] | None = None) -> None:
        self._store: dict[Path, AssetMeta] = dict(initial or {})
        self.writes: list[tuple[Path, AssetMeta]] = []

    def read(self, ref: SourceRef) -> AssetMeta | None:
        return self._store.get(ref.path)

    def write(self, ref: SourceRef, meta: AssetMeta) -> None:
        self._store[ref.path] = meta
        self.writes.append((ref.path, meta))


class FakeHasher:
    def __init__(self, by_path: dict[Path, str] | None = None) -> None:
        self._by_path = dict(by_path or {})
        self.calls: list[Path] = []

    def hash_file(self, ref: SourceRef) -> str:
        self.calls.append(ref.path)
        return self._by_path.get(ref.path, f"hash-{ref.path.stem}")


class FakeThumbnailer:
    def __init__(self) -> None:
        self.rendered: list[str] = []  # dst stems, which are the content hash

    def render(
        self,
        src: SourceRef,
        spec: DerivativeSpec,
        dst: Path,
        *,
        strip_gps: bool,
        embed: AssetMeta | None,
    ) -> Derivative:
        self.rendered.append(dst.stem)
        edge = spec.max_edge or 9999
        return Derivative(
            asset_hash=dst.stem,
            spec_name=spec.name,
            rel_path=dst,
            width=edge,
            height=edge,
        )


class FakeVideoProcessor:
    def __init__(self) -> None:
        self.posters: list[str] = []
        self.clips: list[str] = []

    def poster(self, src: SourceRef, spec: DerivativeSpec, dst: Path) -> Derivative:
        self.posters.append(dst.stem)
        return Derivative(
            asset_hash=dst.stem, spec_name=spec.name, rel_path=dst, width=0, height=0
        )

    def publish_clip(self, src: SourceRef, dst: Path, *, strip_gps: bool) -> Path:
        self.clips.append(dst.stem)
        return dst


class FakeDerivativeStore:
    def __init__(self, present: set[str] | None = None) -> None:
        self._present: set[str] = set(present or set())
        self._by_key: dict[str, Derivative] = {}
        self.recorded: list[str] = []
        self.deleted: list[Path] = []

    def snapshot(self) -> StoreState:
        return StoreState(present=frozenset(self._present))

    def record(self, key: str, deriv: Derivative) -> None:
        self._present.add(key)
        self._by_key[key] = deriv
        self.recorded.append(key)

    def orphans(self, live_keys: set[str]) -> Iterable[Path]:
        return [d.rel_path for k, d in self._by_key.items() if k not in live_keys]

    def delete(self, path: Path) -> None:
        self.deleted.append(path)
        for key, deriv in list(self._by_key.items()):
            if deriv.rel_path == path:
                del self._by_key[key]
                self._present.discard(key)


class FakeSiteRenderer:
    def __init__(self) -> None:
        self.rendered: list[Site] = []

    def render(self, site: Site, out: Path) -> None:
        self.rendered.append(site)


if TYPE_CHECKING:
    # mypy verifies each fake conforms structurally to its port.
    from baffin.application.ports import (
        AssetRepository,
        DerivativeStore,
        Hasher,
        MetadataReader,
        SidecarStore,
        SiteRenderer,
        Thumbnailer,
        VideoProcessor,
    )

    _repo: AssetRepository = FakeAssetRepository()
    _reader: MetadataReader = FakeMetadataReader()
    _sidecars: SidecarStore = FakeSidecarStore()
    _hasher: Hasher = FakeHasher()
    _thumb: Thumbnailer = FakeThumbnailer()
    _video: VideoProcessor = FakeVideoProcessor()
    _store: DerivativeStore = FakeDerivativeStore()
    _renderer: SiteRenderer = FakeSiteRenderer()
