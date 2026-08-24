"""FileDerivativeStore: real HIT/MISS, existence pre-check, orphans, manifest."""

import json
from pathlib import Path

from baffin.adapters.store import FileDerivativeStore
from baffin.domain import Derivative


def _deriv(spec: str, h: str) -> Derivative:
    return Derivative(
        asset_hash=h,
        spec_name=spec,
        rel_path=Path(spec) / f"{h}.jpg",
        width=1,
        height=1,
    )


def _write_file(output: Path, rel: str) -> None:
    path = output / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"jpeg")


def test_recorded_and_present_key_is_a_hit_across_runs(tmp_path: Path) -> None:
    _write_file(tmp_path, "thumb/abc.jpg")
    FileDerivativeStore(tmp_path).record("key-1", _deriv("thumb", "abc"))

    # A fresh instance (a second run) reads the persisted manifest.
    assert "key-1" in FileDerivativeStore(tmp_path).snapshot().present


def test_snapshot_omits_keys_whose_file_vanished(tmp_path: Path) -> None:
    _write_file(tmp_path, "thumb/abc.jpg")
    store = FileDerivativeStore(tmp_path)
    store.record("key-1", _deriv("thumb", "abc"))

    (tmp_path / "thumb" / "abc.jpg").unlink()  # cache file deleted out from under us
    assert store.snapshot().present == frozenset()


def test_orphans_are_the_non_live_recorded_paths(tmp_path: Path) -> None:
    _write_file(tmp_path, "thumb/a.jpg")
    _write_file(tmp_path, "full/a.jpg")
    store = FileDerivativeStore(tmp_path)
    store.record("live", _deriv("thumb", "a"))
    store.record("stale", _deriv("full", "a"))

    orphans = list(store.orphans(live_keys={"live"}))
    assert orphans == [tmp_path / "full" / "a.jpg"]


def test_delete_removes_file_and_manifest_entry(tmp_path: Path) -> None:
    _write_file(tmp_path, "full/a.jpg")
    store = FileDerivativeStore(tmp_path)
    store.record("stale", _deriv("full", "a"))

    store.delete(tmp_path / "full" / "a.jpg")
    assert not (tmp_path / "full" / "a.jpg").exists()
    assert store.snapshot().present == frozenset()


def test_present_spec_names_reports_only_tiers_holding_files(tmp_path: Path) -> None:
    # The renderer asks this to decide what the pages may offer, so an empty or
    # missing tier directory must not count as available.
    _write_file(tmp_path, "thumb/a.jpg")
    _write_file(tmp_path, "full/a.jpg")
    (tmp_path / "med").mkdir()  # created but never filled

    present = FileDerivativeStore(tmp_path).present_spec_names(
        ["thumb", "low", "med", "full"]
    )
    assert present == frozenset({"thumb", "full"})


def test_present_spec_names_follows_files_disappearing(tmp_path: Path) -> None:
    _write_file(tmp_path, "full/a.jpg")
    store = FileDerivativeStore(tmp_path)
    assert store.present_spec_names(["full"]) == frozenset({"full"})

    (tmp_path / "full" / "a.jpg").unlink()  # e.g. reaped by a tmp cleaner
    assert store.present_spec_names(["full"]) == frozenset()


def test_manifest_is_diffable_sorted_json(tmp_path: Path) -> None:
    _write_file(tmp_path, "thumb/b.jpg")
    _write_file(tmp_path, "thumb/a.jpg")
    store = FileDerivativeStore(tmp_path)
    store.record("k-b", _deriv("thumb", "b"))
    store.record("k-a", _deriv("thumb", "a"))

    text = store.manifest_path.read_text()
    assert list(json.loads(text)) == ["k-a", "k-b"]  # keys sorted
    assert text.endswith("\n")
