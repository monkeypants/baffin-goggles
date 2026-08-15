"""Compose concrete adapters for the CLI (the composition root).

Resolves configuration and assembles the imperative-shell adapters
that back the application use cases.
This is the only place the CLI knows which adapter is which;
everything downstream sees ports.
"""

from __future__ import annotations

from typing import Any

from baffin.adapters.hashing import StatMemo, XxHasher
from baffin.adapters.metadata import ExifMetadataReader
from baffin.adapters.render.renderer import Jinja2Renderer
from baffin.adapters.repository import FsAssetRepository
from baffin.adapters.settings import BaffinSettings
from baffin.adapters.sidecars import MarkdownSidecarStore
from baffin.adapters.store import FileDerivativeStore
from baffin.adapters.thumbnails import VipsThumbnailer
from baffin.application.build import BuildGallery
from baffin.application.clean import CleanGallery
from baffin.application.config import GalleryConfig
from baffin.application.origin import ResolveOrigins
from baffin.application.scan import ScanGallery


def load_config(**overrides: Any) -> GalleryConfig:
    """Resolve CLI overrides > env > baffin.toml > defaults into a GalleryConfig."""
    provided = {key: value for key, value in overrides.items() if value is not None}
    return BaffinSettings(**provided).to_config()


def _hasher(config: GalleryConfig) -> XxHasher:
    return XxHasher(StatMemo(config.output / ".baffin" / "memo.json"))


def _sidecars(config: GalleryConfig) -> MarkdownSidecarStore:
    return MarkdownSidecarStore(
        source_root=config.source, meta_root=config.output.parent / "meta"
    )


def build_scanner(config: GalleryConfig) -> ScanGallery:
    return ScanGallery(
        repo=FsAssetRepository(),
        hasher=_hasher(config),
        reader=ExifMetadataReader(),
        store=FileDerivativeStore(config.output),
    )


def build_builder(config: GalleryConfig) -> BuildGallery:
    return BuildGallery(
        repo=FsAssetRepository(),
        hasher=_hasher(config),
        reader=ExifMetadataReader(),
        sidecars=_sidecars(config),
        thumbnailer=VipsThumbnailer(),
        store=FileDerivativeStore(config.output),
        renderer=Jinja2Renderer(),
    )


def build_cleaner(config: GalleryConfig) -> CleanGallery:
    return CleanGallery(
        repo=FsAssetRepository(),
        hasher=_hasher(config),
        reader=ExifMetadataReader(),
        store=FileDerivativeStore(config.output),
    )


def build_origin_resolver(config: GalleryConfig) -> ResolveOrigins:
    return ResolveOrigins(repo=FsAssetRepository(), hasher=_hasher(config))


def sidecar_store(config: GalleryConfig) -> MarkdownSidecarStore:
    return _sidecars(config)
