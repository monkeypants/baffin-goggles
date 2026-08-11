"""Per-asset processor composite (SPEC §8): the process-pool submission unit.

Runs hash -> read -> render for ONE asset and returns its derivatives. It is a
shell-side composite, deliberately NOT an application port — the core plans, the
shell executes. Its inputs and outputs are picklable and its adapters are
re-constructable in a worker (``from_config``), so a ProcessPoolExecutor can fan
it out.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from baffin.application.config import GalleryConfig
from baffin.application.ports import (
    Hasher,
    MetadataReader,
    SidecarStore,
    Thumbnailer,
    VideoProcessor,
)
from baffin.domain import Asset, Derivative, DerivativeSpec, SourceRef

_POSTER_SPEC = DerivativeSpec("poster", 800, 85)


@dataclass(frozen=True)
class AssetJob:
    ref: SourceRef
    specs: tuple[DerivativeSpec, ...]


@dataclass(frozen=True)
class GeneratedDerivative:
    cache_key: str
    derivative: Derivative


@dataclass(frozen=True)
class AssetResult:
    content_hash: str
    generated: tuple[GeneratedDerivative, ...]


@dataclass
class AssetProcessor:
    output: Path
    hasher: Hasher
    reader: MetadataReader
    sidecars: SidecarStore
    thumbnailer: Thumbnailer
    video: VideoProcessor
    strip_gps: bool = True

    @classmethod
    def from_config(cls, config: GalleryConfig) -> AssetProcessor:
        from baffin.adapters.hashing import StatMemo, XxHasher
        from baffin.adapters.metadata import ExifMetadataReader
        from baffin.adapters.sidecars import MarkdownSidecarStore
        from baffin.adapters.thumbnails import VipsThumbnailer
        from baffin.adapters.video import FfmpegVideo

        return cls(
            output=config.output,
            hasher=XxHasher(StatMemo(config.output / ".baffin" / "memo.json")),
            reader=ExifMetadataReader(),
            sidecars=MarkdownSidecarStore(
                source_root=config.source, meta_root=config.output.parent / "meta"
            ),
            thumbnailer=VipsThumbnailer(),
            video=FfmpegVideo(),
            strip_gps=config.strip_gps,
        )

    def process(self, job: AssetJob) -> AssetResult:
        content_hash = self.hasher.hash_file(job.ref)
        raw = self.reader.read(job.ref)
        asset = Asset(
            ref=job.ref,
            content_hash=content_hash,
            kind=raw.kind,
            captured_at=raw.captured_at,
            width=raw.width,
            height=raw.height,
            orientation=raw.orientation,
            camera=raw.camera,
            gps=raw.gps,
        )
        if asset.kind == "video":
            return AssetResult(content_hash, self._video(asset, content_hash))
        return AssetResult(content_hash, self._photo(asset, job.specs, content_hash))

    def _photo(
        self, asset: Asset, specs: tuple[DerivativeSpec, ...], content_hash: str
    ) -> tuple[GeneratedDerivative, ...]:
        embed = self.sidecars.read(asset.ref)
        out: list[GeneratedDerivative] = []
        for spec in specs:
            dst = self.output / spec.name / f"{content_hash}.jpg"
            deriv = self.thumbnailer.render(
                asset.ref, spec, dst, strip_gps=self.strip_gps, embed=embed
            )
            out.append(GeneratedDerivative(spec.cache_key(asset), deriv))
        return tuple(out)

    def _video(
        self, asset: Asset, content_hash: str
    ) -> tuple[GeneratedDerivative, ...]:
        poster = self.video.poster(
            asset.ref, _POSTER_SPEC, self.output / "poster" / f"{content_hash}.jpg"
        )
        clip_path = self.video.publish_clip(
            asset.ref,
            self.output / "video" / f"{content_hash}.mp4",
            strip_gps=self.strip_gps,
        )
        clip = Derivative(
            asset_hash=content_hash,
            spec_name="video",
            rel_path=clip_path,
            width=0,
            height=0,
        )
        return (
            GeneratedDerivative(_POSTER_SPEC.cache_key(asset), poster),
            GeneratedDerivative(f"{content_hash}:video", clip),
        )
