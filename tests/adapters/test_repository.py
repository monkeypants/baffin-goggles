"""FsAssetRepository: media discovery and the read-only source invariant."""

import hashlib
from pathlib import Path

from baffin.adapters.repository import FsAssetRepository


def _tree(root: Path) -> None:
    (root / "2025").mkdir(parents=True)
    (root / "2025" / "DSC1.JPG").write_bytes(b"jpeg-bytes")
    (root / "2025" / "clip.MP4").write_bytes(b"mp4-bytes")
    (root / "phone.mov").write_bytes(b"mov-bytes")
    (root / "notes.txt").write_bytes(b"not media")
    (root / "thumbs.db").write_bytes(b"junk")


def test_discovers_only_media_files(tmp_path: Path) -> None:
    _tree(tmp_path)
    found = {r.path.name for r in FsAssetRepository().discover(tmp_path)}
    assert found == {"DSC1.JPG", "clip.MP4", "phone.mov"}


def test_source_ref_carries_size_and_mtime(tmp_path: Path) -> None:
    _tree(tmp_path)
    refs = {r.path.name: r for r in FsAssetRepository().discover(tmp_path)}
    ref = refs["phone.mov"]
    assert ref.size == len(b"mov-bytes")
    assert ref.mtime_ns == (tmp_path / "phone.mov").stat().st_mtime_ns


def _fingerprint(root: Path) -> dict[str, tuple[int, str]]:
    out: dict[str, tuple[int, str]] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            data = p.read_bytes()
            out[str(p.relative_to(root))] = (
                len(data),
                hashlib.sha256(data).hexdigest(),
            )
    return out


def test_discovery_leaves_the_source_tree_untouched(tmp_path: Path) -> None:
    _tree(tmp_path)
    before = _fingerprint(tmp_path)
    list(FsAssetRepository().discover(tmp_path))
    assert _fingerprint(tmp_path) == before
