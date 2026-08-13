"""baffin build: fixtures -> build -> the documented site layout.

See :doc:`/lazy-build`.
"""

from pathlib import Path

from PIL import Image
from typer.testing import CliRunner

from baffin.interface.cli.app import app

runner = CliRunner()


def _photo(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (1200, 900), color).save(path, "JPEG")


def _build(tmp_path: Path, *extra: str) -> tuple[Path, object]:
    photos = tmp_path / "photos"
    _photo(photos / "a.jpg", (200, 40, 40))
    _photo(photos / "b.jpg", (40, 200, 40))
    out = tmp_path / "site"
    result = runner.invoke(
        app, ["build", "--source", str(photos), "--output", str(out), *extra]
    )
    assert result.exit_code == 0, result.output
    return out, result


def test_build_emits_the_expected_site_layout(tmp_path: Path) -> None:
    out, _ = _build(tmp_path)

    assert (out / "index.html").exists()
    assert (out / "day-01" / "index.html").exists()
    assert (out / "sitemap.xml").exists()
    assert (out / "assets" / "app.css").exists()
    assert (out / "assets" / "app.js").exists()
    assert (out / ".baffin" / "manifest.json").exists()

    for tier in ("thumb", "low", "med"):
        assert len(list((out / tier).glob("*.jpg"))) == 2, tier
    assert not (out / "full").exists()  # full is opt-in


def test_full_flag_adds_the_full_tier(tmp_path: Path) -> None:
    out, _ = _build(tmp_path, "--full")
    assert len(list((out / "full").glob("*.jpg"))) == 2


def test_jobs_flag_builds_the_same_layout(tmp_path: Path) -> None:
    out, _ = _build(tmp_path, "--jobs", "2")
    for tier in ("thumb", "low", "med"):
        assert len(list((out / tier).glob("*.jpg"))) == 2
