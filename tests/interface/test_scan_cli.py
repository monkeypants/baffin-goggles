"""baffin scan: assembles adapters over fixtures and reports the plan."""

from pathlib import Path

from PIL import Image
from typer.testing import CliRunner

from baffin.interface.cli.app import app

runner = CliRunner()


def _photo(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (120, 90), (40, 90, 160)).save(path, "JPEG")


def test_scan_reports_assets_groups_and_plan(tmp_path: Path) -> None:
    photos = tmp_path / "photos"
    _photo(photos / "a.jpg")
    _photo(photos / "b.jpg")

    result = runner.invoke(
        app,
        ["scan", "--source", str(photos), "--output", str(tmp_path / "site")],
    )
    assert result.exit_code == 0, result.stdout
    assert "Assets: 2" in result.stdout
    # 2 assets tiers (thumb/low/med; full off) all missing on a cold cache.
    assert "0 HIT / 6 MISS" in result.stdout
