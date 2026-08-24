"""pyvips thumbnailer (see :doc:`/lazy-build`):
downscale + auto-orient + sharpen, one pass.

GPS is stripped from every derivative by default;
authored IPTC/XMP is embedded afterward.
The original is only ever read.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pyvips
from PIL import Image, ImageFilter, ImageOps

from baffin.adapters.embedding import embed_meta
from baffin.application.errors import DerivativeFailed
from baffin.domain import AssetMeta, Derivative, DerivativeSpec, SourceRef


class VipsThumbnailer:
    def render(
        self,
        src: SourceRef,
        spec: DerivativeSpec,
        dst: Path,
        *,
        strip_gps: bool,
        embed: AssetMeta | None,
    ) -> Derivative:
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            if spec.max_edge is None:
                # Random access (the default): autorot() + sharpen() re-read
                # lines out of order, which a sequential-access source rejects
                # ("out of order read") on rotated originals.
                image = pyvips.Image.new_from_file(str(src.path)).autorot()
            else:
                image = pyvips.Image.thumbnail(
                    str(src.path), spec.max_edge, height=spec.max_edge, size="down"
                )
            image = image.sharpen()
            image.write_to_file(str(dst), Q=spec.quality, strip=strip_gps)
        except pyvips.Error as exc:
            raise DerivativeFailed(str(src.path)) from exc

        if embed is not None:
            embed_meta(dst, embed)
        return Derivative(
            asset_hash=dst.stem,
            spec_name=spec.name,
            rel_path=dst,
            width=image.width,
            height=image.height,
        )


class PillowThumbnailer:
    """No-libvips fallback:
    the same :class:`Thumbnailer` port without the libvips dependency.
    Never carries source metadata forward, so GPS is dropped;
    authored IPTC/XMP is re-embedded after."""

    def render(
        self,
        src: SourceRef,
        spec: DerivativeSpec,
        dst: Path,
        *,
        strip_gps: bool,
        embed: AssetMeta | None,
    ) -> Derivative:
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            with Image.open(src.path) as opened:
                oriented = ImageOps.exif_transpose(opened) or opened
                image = oriented.convert("RGB")
        except OSError as exc:
            raise DerivativeFailed(str(src.path)) from exc

        if spec.max_edge is not None:
            image.thumbnail((spec.max_edge, spec.max_edge), Image.Resampling.LANCZOS)
        image = image.filter(
            ImageFilter.UnsharpMask(radius=1.0, percent=60, threshold=2)
        )
        image.save(dst, "JPEG", quality=spec.quality)  # no exif => metadata dropped

        if embed is not None:
            embed_meta(dst, embed)
        return Derivative(
            asset_hash=dst.stem,
            spec_name=spec.name,
            rel_path=dst,
            width=image.width,
            height=image.height,
        )


if TYPE_CHECKING:
    from baffin.application.ports import Thumbnailer

    _vips: Thumbnailer = VipsThumbnailer()
    _pillow: Thumbnailer = PillowThumbnailer()
