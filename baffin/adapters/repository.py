"""Read-only filesystem asset repository.

Discovers JPEG/MP4/MOV under a source root. It only ever *stats* files, so the
camera folder stays byte-for-byte pristine, honouring the immutable-originals
invariant (see :ref:`rationale-principles`).
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from baffin.domain import SourceRef

MEDIA_SUFFIXES = frozenset({".jpg", ".jpeg", ".mp4", ".mov"})


class FsAssetRepository:
    def discover(self, root: Path) -> Iterable[SourceRef]:
        def _walk() -> Iterator[SourceRef]:
            for path in sorted(root.rglob("*")):
                if path.is_file() and path.suffix.lower() in MEDIA_SUFFIXES:
                    stat = path.stat()
                    yield SourceRef(
                        path=path, size=stat.st_size, mtime_ns=stat.st_mtime_ns
                    )

        return list(_walk())


if TYPE_CHECKING:
    from baffin.application.ports import AssetRepository

    _conforms: AssetRepository = FsAssetRepository()
