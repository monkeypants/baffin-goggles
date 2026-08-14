"""End-to-end lightbox behaviour, driven through a real headless browser.

Token-presence assertions over ``app.js`` cannot tell whether panning, close,
or tier switching actually work — those are layout behaviours that only exist
once a browser computes the box model. These tests render a gallery to disk and
drive it over ``file://`` with Playwright, so they exercise the real thing.

Run with ``make e2e`` (needs the ``e2e`` group and ``playwright install``).
"""

import os
from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image

from baffin.adapters.render.renderer import Jinja2Renderer
from baffin.domain import Asset, DerivativeSpec, Group, Site, SourceRef

pytestmark = pytest.mark.browser

_SPECS = (
    DerivativeSpec("thumb", 300, 80),
    DerivativeSpec("low", 800, 82),
    DerivativeSpec("med", 1600, 85),
    DerivativeSpec("full", None, 95),
)
# Full is far larger than Playwright's default 1280x720 viewport, so it
# overflows and must be panned; the smaller tiers fit.
_SIZES = {
    "thumb": (300, 200),
    "low": (800, 533),
    "med": (1600, 1067),
    "full": (3000, 2000),
}


def _asset(tag: str) -> Asset:
    return Asset(
        ref=SourceRef(path=Path(f"photos/{tag}.jpg"), size=1, mtime_ns=1),
        content_hash=tag,
        kind="photo",
        captured_at=datetime(2025, 7, 14, 9),
        width=3000,
        height=2000,
        orientation=1,
    )


@pytest.fixture(scope="session")
def gallery_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("site")
    day1 = Group(
        key="day-01",
        label="Day 1",
        span=(datetime(2025, 7, 12), datetime(2025, 7, 12)),
        assets=(_asset("aaa"), _asset("bbb")),
    )
    day2 = Group(
        key="day-02",
        label="Day 2",
        span=(datetime(2025, 7, 13), datetime(2025, 7, 13)),
        assets=(_asset("ccc"),),
    )
    site = Site(
        title="Trip", base_url="", peers=(), groups=(day1, day2), photo_tiers=_SPECS
    )
    Jinja2Renderer().render(site, out)
    for tag in ("aaa", "bbb", "ccc"):
        for tier, (w, h) in _SIZES.items():
            path = out / tier / f"{tag}.jpg"
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.frombytes("RGB", (w, h), os.urandom(w * h * 3)).save(path, "JPEG")
    return out


def _open(page, gallery_dir: Path, rel: str = "day-01/index.html") -> None:
    page.goto((gallery_dir / rel).as_uri())


_OVERFLOWS = (
    "() => { const f = document.querySelector('.lb-figure');"
    " return f.scrollWidth > f.clientWidth; }"
)


def test_full_tier_pans_both_axes_and_stays_open(page, gallery_dir: Path) -> None:
    _open(page, gallery_dir)
    page.locator("a.cell").first.click()
    page.get_by_role("button", name="Full").click()
    page.wait_for_function(_OVERFLOWS)  # full image loaded and overflowing

    fig = page.locator(".lb-figure")
    before = fig.evaluate("el => [el.scrollLeft, el.scrollTop]")
    box = fig.bounding_box()
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(cx, cy)
    page.mouse.down()
    page.mouse.move(cx - 200, cy - 200, steps=10)
    page.mouse.up()
    after = fig.evaluate("el => [el.scrollLeft, el.scrollTop]")

    assert after[0] > before[0], "horizontal pan did not move"
    assert after[1] > before[1], "vertical pan did not move"
    assert page.locator(".lightbox").is_visible(), "releasing the drag closed it"


def test_medium_tier_fits_without_scrolling(page, gallery_dir: Path) -> None:
    _open(page, gallery_dir)
    page.locator("a.cell").first.click()  # opens at the default (med) tier
    page.wait_for_selector(".lb-figure img")
    fig = page.locator(".lb-figure")
    overflows = fig.evaluate(
        "el => el.scrollWidth > el.clientWidth || el.scrollHeight > el.clientHeight"
    )
    assert overflows is False


def test_switching_tiers_toggles_pan_mode(page, gallery_dir: Path) -> None:
    _open(page, gallery_dir)
    page.locator("a.cell").first.click()
    page.get_by_role("button", name="Full").click()
    page.wait_for_function(_OVERFLOWS)
    fig = page.locator(".lb-figure")
    assert "is-actual" in (fig.get_attribute("class") or "")
    page.get_by_role("button", name="M", exact=True).click()
    page.wait_for_selector(".lb-figure:not(.is-actual)")
    assert "is-actual" not in (fig.get_attribute("class") or "")


def test_keyboard_navigation_and_escape(page, gallery_dir: Path) -> None:
    _open(page, gallery_dir)
    page.locator("a.cell").first.click()
    counter = page.locator(".lb-counter")
    assert counter.inner_text().startswith("1 /")
    page.keyboard.press("ArrowRight")
    assert counter.inner_text().startswith("2 /")
    page.keyboard.press("Escape")
    assert page.locator(".lightbox").is_hidden()


def test_clicking_the_image_does_not_close(page, gallery_dir: Path) -> None:
    _open(page, gallery_dir)
    page.locator("a.cell").first.click()
    page.locator(".lb-figure img").click()
    assert page.locator(".lightbox").is_visible()


def test_group_pages_link_prev_and_next(page, gallery_dir: Path) -> None:
    _open(page, gallery_dir, "day-01/index.html")
    page.get_by_role("link", name="Day 2").first.click()  # next
    assert page.url.endswith("day-02/index.html")
    page.get_by_role("link", name="Day 1").first.click()  # prev
    assert page.url.endswith("day-01/index.html")
