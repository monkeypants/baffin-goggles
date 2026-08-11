"""XxHasher: content hash, stat memo hits, and re-hash on change."""

from pathlib import Path

import pytest
import xxhash

from baffin.adapters.hashing import StatMemo, XxHasher
from baffin.application.errors import SourceUnreadable
from baffin.domain import SourceRef


def _ref(path: Path, *, mtime_ns: int = 1) -> SourceRef:
    return SourceRef(path=path, size=path.stat().st_size, mtime_ns=mtime_ns)


def _hasher(tmp_path: Path) -> XxHasher:
    return XxHasher(memo=StatMemo(tmp_path / ".baffin" / "memo.json"))


def test_hash_matches_the_bytes(tmp_path: Path) -> None:
    f = tmp_path / "a.bin"
    f.write_bytes(b"hello baffin")
    expected = xxhash.xxh3_64(b"hello baffin").hexdigest()
    assert _hasher(tmp_path).hash_file(_ref(f)) == expected


def test_unchanged_stat_hits_the_memo_without_re_reading(tmp_path: Path) -> None:
    f = tmp_path / "a.bin"
    f.write_bytes(b"original")
    hasher = _hasher(tmp_path)
    ref = _ref(f, mtime_ns=42)
    first = hasher.hash_file(ref)

    # Change the bytes but present the SAME stat: memo must return the old hash.
    f.write_bytes(b"tampered but same stat")
    assert hasher.hash_file(ref) == first


def test_changed_stat_triggers_a_re_hash(tmp_path: Path) -> None:
    f = tmp_path / "a.bin"
    f.write_bytes(b"original")
    hasher = _hasher(tmp_path)
    first = hasher.hash_file(_ref(f, mtime_ns=1))

    f.write_bytes(b"edited")
    rehashed = hasher.hash_file(_ref(f, mtime_ns=2))  # new mtime -> new key
    assert rehashed != first
    assert rehashed == xxhash.xxh3_64(b"edited").hexdigest()


def test_memo_persists_across_hasher_instances(tmp_path: Path) -> None:
    f = tmp_path / "a.bin"
    f.write_bytes(b"durable")
    memo_path = tmp_path / ".baffin" / "memo.json"
    first = XxHasher(memo=StatMemo(memo_path)).hash_file(_ref(f, mtime_ns=7))

    f.unlink()  # gone — only a persisted memo can answer now
    reloaded = XxHasher(memo=StatMemo(memo_path))
    assert reloaded.hash_file(_ref_from_values(f, size=7, mtime_ns=7)) == first


def _ref_from_values(path: Path, *, size: int, mtime_ns: int) -> SourceRef:
    return SourceRef(path=path, size=size, mtime_ns=mtime_ns)


def test_missing_file_raises_source_unreadable(tmp_path: Path) -> None:
    missing = SourceRef(path=tmp_path / "nope.bin", size=1, mtime_ns=1)
    with pytest.raises(SourceUnreadable):
        _hasher(tmp_path).hash_file(missing)
