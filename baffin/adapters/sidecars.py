"""Markdown sidecar store (SPEC §13): YAML front-matter + caption body.

Sidecars live in a ``meta/`` tree mirroring the source layout by relative path,
so the camera folder stays pristine. This adapter writes *only* sidecar files —
never a photo's bytes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from baffin.domain import AssetMeta, SourceRef

_TEMPLATE = """\
---
title:
credit:
alt:
---
"""


@dataclass
class MarkdownSidecarStore:
    source_root: Path
    meta_root: Path

    def path_for(self, ref: SourceRef) -> Path:
        try:
            rel = ref.path.relative_to(self.source_root)
        except ValueError:
            rel = Path(ref.path.name)
        return (self.meta_root / rel).with_suffix(".md")

    def read(self, ref: SourceRef) -> AssetMeta | None:
        path = self.path_for(ref)
        if not path.exists():
            return None
        front, body = _split(path.read_text())
        caption = body.strip() or None
        return AssetMeta(
            title=_str(front.get("title")),
            caption=caption,
            credit=_str(front.get("credit")),
            alt=_str(front.get("alt")),
        )

    def write(self, ref: SourceRef, meta: AssetMeta) -> None:
        path = self.path_for(ref)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_render(meta))

    def ensure_template(self, ref: SourceRef) -> Path:
        """Create a blank sidecar template if none exists; return its path."""
        path = self.path_for(ref)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(_TEMPLATE)
        return path


def _split(text: str) -> tuple[dict[str, object], str]:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                front = yaml.safe_load("\n".join(lines[1:i])) or {}
                return dict(front), "\n".join(lines[i + 1 :])
    return {}, text


def _render(meta: AssetMeta) -> str:
    front = {
        key: value
        for key, value in (
            ("title", meta.title),
            ("credit", meta.credit),
            ("alt", meta.alt),
        )
        if value
    }
    out = ""
    if front:
        dumped = yaml.safe_dump(front, sort_keys=False, allow_unicode=True)
        out += f"---\n{dumped}---\n"
    if meta.caption:
        out += f"{meta.caption}\n"
    return out


def _str(value: object) -> str | None:
    return str(value) if value is not None else None


if TYPE_CHECKING:
    from baffin.application.ports import SidecarStore

    _conforms: SidecarStore = MarkdownSidecarStore(Path(), Path())
