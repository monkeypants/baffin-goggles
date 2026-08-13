"""xxhash file hasher with a persistent stat->hash memo (see :doc:`/lazy-build`).

Re-hashing gigabytes every run is wasteful, so ``(path, size, mtime_ns)`` maps
to a previously computed content hash. An unchanged stat trusts the memo; a
changed stat re-hashes. The memo is a small JSON table under ``.baffin/``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import xxhash

from baffin.application.errors import SourceUnreadable
from baffin.domain import SourceRef

_CHUNK = 1 << 20  # 1 MiB streaming reads


class StatMemo:
    """A JSON-backed ``(path, size, mtime_ns) -> content_hash`` table."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._data: dict[str, str] = {}
        if path.exists():
            try:
                self._data = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                self._data = {}

    @staticmethod
    def _key(ref: SourceRef) -> str:
        return f"{ref.path}|{ref.size}|{ref.mtime_ns}"

    def get(self, ref: SourceRef) -> str | None:
        return self._data.get(self._key(ref))

    def put(self, ref: SourceRef, content_hash: str) -> None:
        self._data[self._key(ref)] = content_hash
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2, sort_keys=True))


@dataclass
class XxHasher:
    """Content hash of a file's bytes, memoised on stat."""

    memo: StatMemo

    def hash_file(self, ref: SourceRef) -> str:
        cached = self.memo.get(ref)
        if cached is not None:
            return cached
        try:
            digest = xxhash.xxh3_64()
            with ref.path.open("rb") as fh:
                for chunk in iter(lambda: fh.read(_CHUNK), b""):
                    digest.update(chunk)
        except OSError as exc:
            raise SourceUnreadable(str(ref.path)) from exc
        content_hash: str = digest.hexdigest()
        self.memo.put(ref, content_hash)
        return content_hash


if TYPE_CHECKING:
    from baffin.application.ports import Hasher

    _conforms: Hasher = XxHasher(StatMemo(Path()))
