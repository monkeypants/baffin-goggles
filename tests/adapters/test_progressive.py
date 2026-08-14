"""The JS layer enhances but is never load-bearing (see :doc:`/functional-core`)."""

import re
from datetime import datetime
from pathlib import Path

from baffin.adapters.render.renderer import Jinja2Renderer
from baffin.domain import Asset, DerivativeSpec, Group, Site, SourceRef

_SPECS = (
    DerivativeSpec("thumb", 300, 80),
    DerivativeSpec("low", 800, 82),
    DerivativeSpec("med", 1600, 85),
)


def _site() -> Site:
    assets = tuple(
        Asset(
            ref=SourceRef(path=Path(f"photos/{h}"), size=1, mtime_ns=1),
            content_hash=h,
            kind="photo",
            captured_at=datetime(2025, 7, 14, 9),
            width=800,
            height=600,
            orientation=1,
        )
        for h in ("aaa", "bbb")
    )
    group = Group(
        key="day-01",
        label="Day 1",
        span=(datetime(2025, 7, 12), datetime(2025, 7, 12)),
        assets=assets,
    )
    return Site(
        title="Trip", base_url="", peers=(), groups=(group,), photo_tiers=_SPECS
    )


def test_app_js_wires_lightbox_and_keyboard_nav(tmp_path: Path) -> None:
    Jinja2Renderer().render(_site(), tmp_path)
    js = (tmp_path / "assets" / "app.js").read_text()
    tokens = [
        "keydown",
        "Escape",
        "ArrowLeft",
        "ArrowRight",
        "preventDefault",
        # on-screen controls layered on top of the keyboard nav
        "lb-prev",
        "lb-next",
        "lb-tier",
        "download",
        # full renders at 1:1 in a pannable figure
        "is-actual",
        "pointermove",
    ]
    for token in tokens:
        assert token in js, token


def test_html_is_functional_without_js(tmp_path: Path) -> None:
    """Every thumbnail is a real <a href> to an image — no href="#", no inline
    JS handler that JS-off users would need."""
    Jinja2Renderer().render(_site(), tmp_path)
    html = (tmp_path / "day-01" / "index.html").read_text()
    cell_hrefs = re.findall(r'<a class="cell" href="([^"]+)"', html)
    assert len(cell_hrefs) == 2
    assert all(href.endswith(".jpg") for href in cell_hrefs)
    assert 'href="#"' not in html
    assert "onclick" not in html


def test_srcset_present_across_tiers(tmp_path: Path) -> None:
    Jinja2Renderer().render(_site(), tmp_path)
    html = (tmp_path / "day-01" / "index.html").read_text()
    assert "300w" in html and "800w" in html and "1600w" in html
