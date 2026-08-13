"""baffin serve: builds then serves; --watch re-renders, never regenerates."""

import hashlib
from pathlib import Path

import pytest
from PIL import Image
from typer.testing import CliRunner

from baffin.application.config import GalleryConfig
from baffin.interface.cli import app as cli
from baffin.interface.cli.pipeline import render_only, run_build

runner = CliRunner()


def _photos(root: Path) -> None:
    root.mkdir(parents=True)
    Image.new("RGB", (400, 300), (200, 40, 40)).save(root / "a.jpg", "JPEG")


def _derivative_bytes(out: Path) -> dict[str, str]:
    prints: dict[str, str] = {}
    for tier in ("thumb", "low", "med"):
        for jpg in (out / tier).glob("*.jpg"):
            prints[str(jpg.relative_to(out))] = hashlib.sha256(
                jpg.read_bytes()
            ).hexdigest()
    return prints


def test_serve_builds_the_site_then_hands_off(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    photos, out = tmp_path / "photos", tmp_path / "site"
    _photos(photos)
    served: list[Path] = []
    monkeypatch.setattr(
        cli, "_serve_directory", lambda directory, host, port: served.append(directory)
    )

    result = runner.invoke(
        cli.app, ["serve", "--source", str(photos), "--output", str(out)]
    )
    assert result.exit_code == 0, result.output
    assert (out / "index.html").exists()
    assert served == [out]


def test_render_only_reflows_html_without_regenerating_images(tmp_path: Path) -> None:
    photos, out = tmp_path / "photos", tmp_path / "site"
    _photos(photos)
    config = GalleryConfig(source=photos, output=out)
    run_build(config)

    before = _derivative_bytes(out)
    index_before = (out / "index.html").read_text()

    template = _template_path()
    original = template.read_text()
    try:
        template.write_text(original.replace("</main>", "<p>live</p></main>"))
        render_only(config)
        assert _derivative_bytes(out) == before  # no image bytes rewritten
        assert (out / "index.html").read_text() != index_before  # HTML re-rendered
    finally:
        template.write_text(original)


def _template_path() -> Path:
    from baffin.adapters.render import renderer

    return Path(renderer.__file__).parent / "templates" / "base.html.j2"
