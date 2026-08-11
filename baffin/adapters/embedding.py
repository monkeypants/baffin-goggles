"""Embed authored sidecar text into an output JPEG's IPTC/XMP (SPEC §6, §13).

Shared by the thumbnailer adapters. Writes only the derivative copy — originals
are never touched.
"""

from __future__ import annotations

from pathlib import Path

import pyexiv2

from baffin.domain import AssetMeta


def embed_meta(path: Path, meta: AssetMeta) -> None:
    iptc: dict[str, str] = {}
    xmp: dict[str, str] = {}
    if meta.title:
        iptc["Iptc.Application2.Headline"] = meta.title
    if meta.caption:
        iptc["Iptc.Application2.Caption"] = meta.caption
    if meta.credit:
        iptc["Iptc.Application2.Credit"] = meta.credit
    if meta.alt:
        xmp["Xmp.dc.description"] = meta.alt
    if not iptc and not xmp:
        return
    with pyexiv2.Image(str(path)) as handle:
        if iptc:
            handle.modify_iptc(iptc)
        if xmp:
            handle.modify_xmp(xmp)
