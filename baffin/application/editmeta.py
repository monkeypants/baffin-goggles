"""EditAssetMeta: author one asset's sidecar (SPEC §12/§13, `baffin meta`).

Read → merge → write a single sidecar. It depends on nothing but the
``SidecarStore``, so it *cannot* touch image bytes — the same use case backs the
v1 CLI and the reserved v2 web form.
"""

from __future__ import annotations

from dataclasses import dataclass

from baffin.application.ports import SidecarStore
from baffin.domain import AssetMeta, SourceRef


def merge_meta(base: AssetMeta | None, overlay: AssetMeta) -> AssetMeta:
    """Overlay non-``None`` fields onto ``base``; unset overlay fields keep base."""
    base = base or AssetMeta()
    return AssetMeta(
        title=overlay.title if overlay.title is not None else base.title,
        caption=overlay.caption if overlay.caption is not None else base.caption,
        credit=overlay.credit if overlay.credit is not None else base.credit,
        alt=overlay.alt if overlay.alt is not None else base.alt,
    )


@dataclass(frozen=True)
class EditAssetMeta:
    sidecars: SidecarStore

    def execute(self, ref: SourceRef, changes: AssetMeta) -> AssetMeta:
        merged = merge_meta(self.sidecars.read(ref), changes)
        self.sidecars.write(ref, merged)
        return merged
