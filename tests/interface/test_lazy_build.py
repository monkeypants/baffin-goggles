"""The lazy-build promise (see :doc:`/lazy-build`), end to end: a re-run is all
cache hits, and editing a template rewrites ZERO image bytes."""

from pathlib import Path

from PIL import Image
from typer.testing import CliRunner

from baffin.interface.cli.app import app

runner = CliRunner()


def _photo(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (1200, 900), color).save(path, "JPEG")


def _run_build(photos: Path, out: Path) -> str:
    result = runner.invoke(
        app, ["build", "--source", str(photos), "--output", str(out)]
    )
    assert result.exit_code == 0, result.output
    return result.output


def _derivative_fingerprints(out: Path) -> dict[str, tuple[int, bytes]]:
    prints: dict[str, tuple[int, bytes]] = {}
    for tier in ("thumb", "low", "med"):
        for jpg in (out / tier).glob("*.jpg"):
            data = jpg.read_bytes()
            prints[str(jpg.relative_to(out))] = (jpg.stat().st_mtime_ns, data)
    return prints


def test_second_run_is_all_hits_and_template_edit_rewrites_no_image_bytes(
    tmp_path: Path,
) -> None:
    photos = tmp_path / "photos"
    _photo(photos / "a.jpg", (200, 40, 40))
    _photo(photos / "b.jpg", (40, 200, 40))
    out = tmp_path / "site"

    first = _run_build(photos, out)
    assert "Generated 6 derivative(s)" in first
    before = _derivative_fingerprints(out)
    assert len(before) == 6

    # Second run: nothing changed -> every tier is a cache hit, none regenerated.
    second = _run_build(photos, out)
    assert "Generated 0 derivative(s)" in second
    assert _derivative_fingerprints(out) == before

    # Edit a template and rebuild: HTML re-renders, image bytes are untouched.
    index_before = (out / "index.html").read_text()
    template = _template_path()
    original = template.read_text()
    try:
        template.write_text(
            original.replace("</main>", "<footer>edited</footer></main>")
        )
        third = _run_build(photos, out)
        assert "Generated 0 derivative(s)" in third
        assert _derivative_fingerprints(out) == before  # zero image bytes rewritten
        assert (out / "index.html").read_text() != index_before  # HTML re-rendered
    finally:
        template.write_text(original)


def _template_path() -> Path:
    from baffin.adapters.render import renderer

    return Path(renderer.__file__).parent / "templates" / "base.html.j2"
