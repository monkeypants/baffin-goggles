"""baffin origin: map a gallery image (hash / URL / derivative) to its original."""

from pathlib import Path

import xxhash
from PIL import Image
from typer.testing import CliRunner

from baffin.interface.cli.app import app

runner = CliRunner()


def _photo(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (120, 90), (40, 90, 160)).save(path, "JPEG")


def _content_hash(path: Path) -> str:
    return xxhash.xxh3_64(path.read_bytes()).hexdigest()


def test_origin_prints_the_original_for_a_derivative(tmp_path: Path) -> None:
    photos = tmp_path / "photos"
    original = photos / "DSC42.JPG"
    _photo(original)
    content_hash = _content_hash(original)

    result = runner.invoke(
        app,
        [
            "origin",
            f"full/{content_hash}.jpg",
            "--source",
            str(photos),
            "--output",
            str(tmp_path / "site"),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert str(original) in result.stdout


def test_origin_fails_on_an_unknown_hash(tmp_path: Path) -> None:
    photos = tmp_path / "photos"
    _photo(photos / "a.jpg")

    result = runner.invoke(
        app,
        [
            "origin",
            "ffffffffffffffff",
            "--source",
            str(photos),
            "--output",
            str(tmp_path / "site"),
        ],
    )
    assert result.exit_code == 1
