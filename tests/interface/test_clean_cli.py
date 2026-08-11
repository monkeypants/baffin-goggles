"""baffin clean: prune orphans after a tier is turned off; --all wipes."""

import json
from pathlib import Path

from PIL import Image
from typer.testing import CliRunner

from baffin.interface.cli.app import app

runner = CliRunner()


def _photos(root: Path) -> None:
    root.mkdir(parents=True)
    Image.new("RGB", (800, 600), (200, 40, 40)).save(root / "a.jpg", "JPEG")
    Image.new("RGB", (800, 600), (40, 200, 40)).save(root / "b.jpg", "JPEG")


def test_clean_prunes_the_orphaned_full_tier(tmp_path: Path) -> None:
    photos, out = tmp_path / "photos", tmp_path / "site"
    _photos(photos)
    args = ["--source", str(photos), "--output", str(out)]
    runner.invoke(app, ["build", *args, "--full"])
    assert len(list((out / "full").glob("*.jpg"))) == 2

    # Rebuild without full, then clean: full tier is now orphaned.
    runner.invoke(app, ["build", *args])
    result = runner.invoke(app, ["clean", *args])
    assert result.exit_code == 0
    assert "Removed 2 derivative(s)" in result.stdout
    assert len(list((out / "full").glob("*.jpg"))) == 0
    assert len(list((out / "thumb").glob("*.jpg"))) == 2


def test_clean_all_empties_the_cache(tmp_path: Path) -> None:
    photos, out = tmp_path / "photos", tmp_path / "site"
    _photos(photos)
    runner.invoke(app, ["build", "--source", str(photos), "--output", str(out)])

    result = runner.invoke(
        app, ["clean", "--source", str(photos), "--output", str(out), "--all"]
    )
    assert result.exit_code == 0
    manifest = json.loads((out / ".baffin" / "manifest.json").read_text())
    assert manifest == {}
    assert len(list((out / "thumb").glob("*.jpg"))) == 0
