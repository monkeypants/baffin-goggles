"""File derivative store + JSON manifest (see :doc:`/lazy-build`).

The manifest (``.baffin/manifest.json``) maps cache key → derivative record.
``snapshot`` reads it AND pre-checks that each file still exists on disk,
so the pure ``diff_plan`` gets a truthful :class:`StoreState` and never does I/O itself.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from baffin.domain import Derivative, StoreState


@dataclass
class FileDerivativeStore:
    output: Path

    @property
    def manifest_path(self) -> Path:
        return self.output / ".baffin" / "manifest.json"

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.manifest_path.exists():
            return {}
        try:
            data: dict[str, dict[str, Any]] = json.loads(self.manifest_path.read_text())
            return data
        except (OSError, json.JSONDecodeError):
            return {}

    def _write(self, manifest: dict[str, dict[str, Any]]) -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )

    def _relative(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.output))
        except ValueError:
            return str(path)

    def snapshot(self) -> StoreState:
        manifest = self._load()
        present = {
            key
            for key, rec in manifest.items()
            if (self.output / rec["rel_path"]).exists()
        }
        return StoreState(present=frozenset(present))

    def present_spec_names(self, names: Iterable[str]) -> frozenset[str]:
        """Which of ``names`` the output actually holds derivatives for.

        The renderer needs this because a tier is only offerable once its files
        exist. Deriving it from the build flag instead is what let a ``serve``
        without ``--full`` re-render a ``build --full`` gallery into one whose
        download button was gone while every full-size file was still on disk.
        """
        return frozenset(
            name
            for name in names
            if next((self.output / name).glob("*.jpg"), None) is not None
        )

    def record(self, key: str, deriv: Derivative) -> None:
        manifest = self._load()
        manifest[key] = {
            "rel_path": self._relative(deriv.rel_path),
            "spec_name": deriv.spec_name,
            "asset_hash": deriv.asset_hash,
            "width": deriv.width,
            "height": deriv.height,
        }
        self._write(manifest)

    def orphans(self, live_keys: set[str]) -> Iterable[Path]:
        manifest = self._load()
        return [
            self.output / rec["rel_path"]
            for key, rec in manifest.items()
            if key not in live_keys
        ]

    def delete(self, path: Path) -> None:
        if path.exists():
            path.unlink()
        rel = self._relative(path)
        manifest = self._load()
        for key in [k for k, rec in manifest.items() if rec["rel_path"] == rel]:
            del manifest[key]
        self._write(manifest)


if TYPE_CHECKING:
    from baffin.application.ports import DerivativeStore

    _conforms: DerivativeStore = FileDerivativeStore(Path())
