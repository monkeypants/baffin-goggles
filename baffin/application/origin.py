"""Map gallery images back to their originals (see :doc:`/use-cases`).

Derivatives are content-addressed, so a gallery URL like ``full/069f10b0a11b9961.jpg``
carries the content hash but not the source name.
:func:`content_hash_of` recovers the hash from such a reference,
and :class:`ResolveOrigins` maps hashes back to the source paths that produced them
(hash → original), the inverse of the build.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from baffin.application.ports import AssetRepository, Hasher

# A content hash is an xxh3_64 digest: exactly 16 hex chars, standing alone
# (not a slice of the longer SHA-256 cache key).
_HASH = re.compile(r"(?<![0-9a-f])[0-9a-f]{16}(?![0-9a-f])")


def content_hash_of(reference: str) -> str | None:
    """Extract the content hash from a hash, derivative path, or image URL.

    >>> from baffin.application.origin import content_hash_of
    >>> content_hash_of("http://host/full/069f10b0a11b9961.jpg")
    '069f10b0a11b9961'
    >>> content_hash_of("069f10b0a11b9961")
    '069f10b0a11b9961'
    >>> content_hash_of("DSC00003.JPG") is None
    True
    """
    match = _HASH.search(reference)
    return match.group(0) if match else None


@dataclass(frozen=True)
class ResolveOrigins:
    """Build a content-hash → original-path index over the source tree.

    Depends only on the discovery and hashing ports;
    the hasher's stat memo makes a re-index after a build effectively free.
    """

    repo: AssetRepository
    hasher: Hasher

    def index(self, source: Path) -> dict[str, Path]:
        origins: dict[str, Path] = {}
        for ref in self.repo.discover(source):
            origins.setdefault(self.hasher.hash_file(ref), ref.path)
        return origins
