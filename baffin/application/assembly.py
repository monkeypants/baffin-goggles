"""Shared asset assembly: turn source refs into domain Assets (SPEC §8).

Hashing and metadata reads are the fallible per-asset steps, so they run under
the skip-and-report guard — a bad file is skipped, not fatal (unless --strict).
"""

from __future__ import annotations

from collections.abc import Iterable

from baffin.application.ports import Hasher, MetadataReader
from baffin.application.reporting import BuildReport, per_asset
from baffin.domain import Asset, SourceRef


def assemble_assets(
    refs: Iterable[SourceRef],
    hasher: Hasher,
    reader: MetadataReader,
    *,
    report: BuildReport,
    strict: bool,
) -> list[Asset]:
    """Read + hash each ref into an Asset; skip (and report) the unreadable."""
    assets: list[Asset] = []
    for ref in refs:
        with per_asset(report, str(ref.path), strict=strict):
            raw = reader.read(ref)
            content_hash = hasher.hash_file(ref)
            assets.append(
                Asset(
                    ref=ref,
                    content_hash=content_hash,
                    kind=raw.kind,
                    captured_at=raw.captured_at,
                    width=raw.width,
                    height=raw.height,
                    orientation=raw.orientation,
                    camera=raw.camera,
                    gps=raw.gps,
                )
            )
    return assets
