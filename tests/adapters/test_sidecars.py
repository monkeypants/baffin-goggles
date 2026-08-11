"""MarkdownSidecarStore: round-trip, mirrored paths, templates, source safety."""

import hashlib
from pathlib import Path

from baffin.adapters.sidecars import MarkdownSidecarStore
from baffin.domain import AssetMeta, SourceRef


def _store(tmp_path: Path) -> MarkdownSidecarStore:
    return MarkdownSidecarStore(
        source_root=tmp_path / "photos", meta_root=tmp_path / "meta"
    )


def _ref(tmp_path: Path) -> SourceRef:
    return SourceRef(path=tmp_path / "photos" / "2025" / "DSC1.JPG", size=1, mtime_ns=1)


def test_sidecar_path_mirrors_source_layout(tmp_path: Path) -> None:
    path = _store(tmp_path).path_for(_ref(tmp_path))
    assert path == tmp_path / "meta" / "2025" / "DSC1.md"


def test_absent_sidecar_reads_as_none(tmp_path: Path) -> None:
    assert _store(tmp_path).read(_ref(tmp_path)) is None


def test_round_trip_preserves_all_fields(tmp_path: Path) -> None:
    store = _store(tmp_path)
    meta = AssetMeta(
        title="River crossing",
        caption="A short caption for one photo.",
        credit="Chris Gough",
        alt="A hiker fording a braided glacial river",
    )
    store.write(_ref(tmp_path), meta)
    assert store.read(_ref(tmp_path)) == meta


def test_caption_only_sidecar_round_trips(tmp_path: Path) -> None:
    store = _store(tmp_path)
    meta = AssetMeta(caption="Just a caption, no front-matter fields.")
    store.write(_ref(tmp_path), meta)
    assert store.read(_ref(tmp_path)) == meta


def test_ensure_template_creates_a_blank_sidecar(tmp_path: Path) -> None:
    store = _store(tmp_path)
    path = store.ensure_template(_ref(tmp_path))
    assert path.exists()
    assert "title:" in path.read_text()
    assert store.read(_ref(tmp_path)) == AssetMeta()  # all fields blank


def test_writing_never_touches_the_original(tmp_path: Path) -> None:
    (tmp_path / "photos" / "2025").mkdir(parents=True)
    original = tmp_path / "photos" / "2025" / "DSC1.JPG"
    original.write_bytes(b"camera bytes")
    before = hashlib.sha256(original.read_bytes()).hexdigest()

    _store(tmp_path).write(_ref(tmp_path), AssetMeta(title="Hi"))

    assert hashlib.sha256(original.read_bytes()).hexdigest() == before
    assert (tmp_path / "meta" / "2025" / "DSC1.md").exists()
