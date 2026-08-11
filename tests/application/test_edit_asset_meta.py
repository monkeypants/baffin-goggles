"""EditAssetMeta: merge semantics; only the sidecar store is written."""

from pathlib import Path

from baffin.application.editmeta import EditAssetMeta, merge_meta
from baffin.domain import AssetMeta, SourceRef
from baffin.testing.fakes import FakeSidecarStore

REF = SourceRef(path=Path("photos/a.jpg"), size=1, mtime_ns=1)


def test_merge_overlays_set_fields_and_keeps_the_rest() -> None:
    base = AssetMeta(title="Old title", caption="Keep me", credit="Chris")
    overlay = AssetMeta(title="New title", alt="A hiker")
    merged = merge_meta(base, overlay)
    assert merged.title == "New title"  # overwritten
    assert merged.caption == "Keep me"  # preserved (overlay was None)
    assert merged.credit == "Chris"  # preserved
    assert merged.alt == "A hiker"  # added


def test_merge_onto_absent_sidecar_starts_blank() -> None:
    merged = merge_meta(None, AssetMeta(caption="First words"))
    assert merged.caption == "First words"
    assert merged.title is None


def test_execute_reads_merges_and_writes_only_the_sidecar() -> None:
    store = FakeSidecarStore(initial={REF.path: AssetMeta(credit="Chris")})
    edit = EditAssetMeta(sidecars=store)

    result = edit.execute(REF, AssetMeta(title="River crossing"))

    assert result == AssetMeta(title="River crossing", credit="Chris")
    assert store.writes == [(REF.path, result)]
    assert store.read(REF) == result
