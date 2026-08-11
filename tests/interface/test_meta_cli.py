"""baffin meta: set writes a sidecar, show reads it, originals untouched."""

import hashlib
from pathlib import Path

import pytest
from PIL import Image
from typer.testing import CliRunner

from baffin.interface.cli.app import app

runner = CliRunner()


def _photos(root: Path) -> None:
    root.mkdir(parents=True)
    Image.new("RGB", (100, 100), (200, 40, 40)).save(root / "a.jpg", "JPEG")
    Image.new("RGB", (100, 100), (40, 200, 40)).save(root / "b.jpg", "JPEG")


def _roots(tmp_path: Path) -> tuple[Path, list[str]]:
    photos = tmp_path / "photos"
    _photos(photos)
    return photos, ["--source", str(photos), "--output", str(tmp_path / "site")]


def test_set_writes_sidecar_and_show_reads_it(tmp_path: Path) -> None:
    photos, args = _roots(tmp_path)
    photo = str(photos / "a.jpg")

    result = runner.invoke(app, ["meta", "set", photo, *args, "--title", "River"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "meta" / "a.md").exists()

    shown = runner.invoke(app, ["meta", "show", photo, *args])
    assert "title: River" in shown.stdout


def test_set_never_touches_the_original(tmp_path: Path) -> None:
    photos, args = _roots(tmp_path)
    photo = photos / "a.jpg"
    before = hashlib.sha256(photo.read_bytes()).hexdigest()
    runner.invoke(app, ["meta", "set", str(photo), *args, "--caption", "hi"])
    assert hashlib.sha256(photo.read_bytes()).hexdigest() == before


def test_set_all_writes_a_sidecar_per_photo(tmp_path: Path) -> None:
    _photos_root, args = _roots(tmp_path)
    result = runner.invoke(app, ["meta", "set", *args, "--all", "--credit", "Chris"])
    assert result.exit_code == 0
    assert (tmp_path / "meta" / "a.md").exists()
    assert (tmp_path / "meta" / "b.md").exists()


def test_edit_creates_a_template(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    photos, args = _roots(tmp_path)
    monkeypatch.setenv("EDITOR", "true")  # no-op editor
    runner.invoke(app, ["meta", "edit", str(photos / "a.jpg"), *args])
    assert (tmp_path / "meta" / "a.md").exists()
