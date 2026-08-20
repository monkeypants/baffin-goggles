"""Prescriptive end-to-end spec for the lightbox, driven through a real browser.

These tests describe how viewing and navigation must behave — they are the
specification, not smoke checks. Token-presence assertions over ``app.js``
cannot see layout; panning, scrolling, and fit-vs-native sizing only exist once
a browser computes the box model, so we render a gallery to disk and drive it
over ``file://`` with Playwright.

The spec (Native-size tiers + Fit default):

* The lightbox opens in **Fit**: the image is scaled to the window and never
  scrolls.
* The switcher offers **Fit** plus every built tier (**S / M / Full**).
* Selecting a tier shows that file at its **native pixel size**: centered when
  it fits, **pannable on both axes** (drag or wheel) when it overflows.
* While the lightbox is open the **page background never scrolls**.
* Prev/next buttons and Left/Right arrows move between photos; Esc and the close
  button dismiss; a drag that pans must not dismiss.

Run with ``make e2e``.
"""

import os
from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image

from baffin.adapters.render.renderer import Jinja2Renderer
from baffin.domain import Asset, DerivativeSpec, Group, Site, SourceRef

pytestmark = pytest.mark.browser

_VIEWPORT = {"width": 1280, "height": 720}
_SPECS = (
    DerivativeSpec("thumb", 300, 80),
    DerivativeSpec("low", 800, 82),
    DerivativeSpec("med", 1600, 85),
    DerivativeSpec("full", None, 95),
)
# Relative to the ~1280x720 viewport: S fits (centered, no scroll), M overflows,
# Full overflows hard. Distinct native widths prove the tiers really differ.
_SIZES = {
    "thumb": (300, 200),
    "low": (800, 533),
    "med": (1600, 1067),
    "full": (3000, 2000),
}
_DAY1 = [f"a{i:02d}" for i in range(60)]  # a tall grid, so the page can scroll
_DAY2 = ["b00"]
# Only these get the heavy low/med/full files; the rest are thumbnail-only (the
# grid just needs to be tall). Tests only open the first few.
_DETAILED = set(_DAY1[:3])


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
        assets=tuple(_asset(t) for t in _DAY1),
    )
    day2 = Group(
        key="day-02",
        label="Day 2",
        span=(datetime(2025, 7, 13), datetime(2025, 7, 13)),
        assets=tuple(_asset(t) for t in _DAY2),
    )
    site = Site(
        title="Trip", base_url="", peers=(), groups=(day1, day2), photo_tiers=_SPECS
    )
    Jinja2Renderer().render(site, out)
    for tag in _DAY1 + _DAY2:
        tiers = _SIZES if tag in _DETAILED else {"thumb": _SIZES["thumb"]}
        for tier, (w, h) in tiers.items():
            path = out / tier / f"{tag}.jpg"
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.frombytes("RGB", (w, h), os.urandom(w * h * 3)).save(path, "JPEG")
    return out


@pytest.fixture(scope="session")
def named_gallery_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A gallery built with show_filenames enabled (one photo)."""
    out = tmp_path_factory.mktemp("named")
    day = Group(
        key="day-01",
        label="Day 1",
        span=(datetime(2025, 7, 12), datetime(2025, 7, 12)),
        assets=(_asset("shot01"),),
    )
    site = Site(
        title="Trip",
        base_url="",
        peers=(),
        groups=(day,),
        photo_tiers=_SPECS,
        show_filenames=True,
    )
    Jinja2Renderer().render(site, out)
    for tier, (w, h) in _SIZES.items():
        path = out / tier / "shot01.jpg"
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.frombytes("RGB", (w, h), os.urandom(w * h * 3)).save(path, "JPEG")
    return out


@pytest.fixture(scope="session")
def full_off_gallery_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A gallery built without the ``full`` tier (``include_full = false``).

    The tier drives two visible features, so the off state needs its own
    fixture: with it absent the switcher must not offer **Full** and the
    download button must stay hidden.
    """
    out = tmp_path_factory.mktemp("full-off")
    day = Group(
        key="day-01",
        label="Day 1",
        span=(datetime(2025, 7, 12), datetime(2025, 7, 12)),
        assets=(_asset("a00"),),
    )
    site = Site(
        title="Trip",
        base_url="",
        peers=(),
        groups=(day,),
        photo_tiers=_SPECS[:3],  # thumb, low, med — no full
    )
    Jinja2Renderer().render(site, out)
    for tier in ("thumb", "low", "med"):
        w, h = _SIZES[tier]
        path = out / tier / "a00.jpg"
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.frombytes("RGB", (w, h), os.urandom(w * h * 3)).save(path, "JPEG")
    return out


def _open_gallery(page, gallery_dir: Path, rel: str = "day-01/index.html"):
    page.set_viewport_size(_VIEWPORT)
    page.goto((gallery_dir / rel).as_uri())


def _open_lightbox(page, gallery_dir: Path):
    _open_gallery(page, gallery_dir)
    page.locator("a.cell").first.click()
    assert page.locator(".lightbox").is_visible()


def _select(page, label: str):
    page.get_by_role("button", name=label, exact=True).click()


def _overflows(page) -> bool:
    return page.locator(".lb-figure").evaluate(
        "el => el.scrollWidth > el.clientWidth || el.scrollHeight > el.clientHeight"
    )


def _natural_width(page) -> int:
    return page.locator(".lb-figure img").evaluate("el => el.naturalWidth")


def _wait_natural(page, width: int) -> None:
    page.wait_for_function(
        "w => document.querySelector('.lb-figure img').naturalWidth === w",
        arg=width,
    )


def _drag(page, dx: int, dy: int):
    box = page.locator(".lb-figure").bounding_box()
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(cx, cy)
    page.mouse.down()
    page.mouse.move(cx + dx, cy + dy, steps=10)
    page.mouse.up()


# --- Fit default ----------------------------------------------------------


def test_opens_in_fit_and_fit_never_scrolls(page, gallery_dir: Path) -> None:
    _open_lightbox(page, gallery_dir)
    assert (
        page.get_by_role("button", name="Fit", exact=True)
        .get_attribute("class")
        .find("is-active")
        >= 0
    )
    page.wait_for_selector(".lb-figure img")
    assert _overflows(page) is False


def test_switcher_offers_fit_and_each_built_tier(page, gallery_dir: Path) -> None:
    _open_lightbox(page, gallery_dir)
    labels = page.locator(".lb-tiers button").all_inner_texts()
    assert labels == ["Fit", "S", "M", "Full"]


# --- The full tier's two visible features ---------------------------------
#
# Both are derived from the same tier, and the HTML-level tests can only prove
# the `data-full` attribute is present. Whether the button is actually *usable*
# is a JS/CSS question (`app.js` toggles `download.hidden`), so it belongs here.


def test_download_button_offers_the_full_size_file(page, gallery_dir: Path) -> None:
    _open_lightbox(page, gallery_dir)
    download = page.locator(".lb-download")
    assert download.is_visible()
    assert download.get_attribute("href").endswith("full/a00.jpg")
    assert download.get_attribute("download") is not None  # saves, never navigates


def test_download_button_follows_the_photo_while_browsing(
    page, gallery_dir: Path
) -> None:
    # One <a> is reused across photos, so a stale href would silently hand the
    # viewer the previous picture's file.
    _open_lightbox(page, gallery_dir)
    first = page.locator(".lb-download").get_attribute("href")
    page.keyboard.press("ArrowRight")
    page.wait_for_function(
        "h => document.querySelector('.lb-download').getAttribute('href') !== h",
        arg=first,
    )
    assert page.locator(".lb-download").get_attribute("href").endswith("full/a01.jpg")


def test_without_the_full_tier_there_is_no_full_option_or_download(
    page, full_off_gallery_dir: Path
) -> None:
    _open_lightbox(page, full_off_gallery_dir)
    assert page.locator(".lb-tiers button").all_inner_texts() == ["Fit", "S", "M"]
    assert page.locator(".lb-download").is_hidden()


# --- Native-size tiers ----------------------------------------------------


def test_tiers_load_distinct_resolutions(page, gallery_dir: Path) -> None:
    # The heart of the "M looks like S" complaint: each tier must load a
    # different-resolution file and show it at that size.
    _open_lightbox(page, gallery_dir)
    _select(page, "S")
    _wait_natural(page, 800)
    small = _natural_width(page)
    _select(page, "M")
    _wait_natural(page, 1600)
    medium = _natural_width(page)
    _select(page, "Full")
    _wait_natural(page, 3000)
    full = _natural_width(page)
    assert small < medium < full == 3000


def test_small_tier_that_fits_is_centered_and_not_scrollable(
    page, gallery_dir: Path
) -> None:
    _open_lightbox(page, gallery_dir)
    _select(page, "S")
    page.wait_for_selector(".lb-figure.is-native")
    assert _overflows(page) is False  # 800px fits the viewport


def test_full_shows_native_size_and_pans_both_axes(page, gallery_dir: Path) -> None:
    _open_lightbox(page, gallery_dir)
    _select(page, "Full")
    page.wait_for_function(
        "() => { const f = document.querySelector('.lb-figure');"
        " return f.scrollWidth > f.clientWidth && f.scrollHeight > f.clientHeight; }"
    )
    fig = page.locator(".lb-figure")
    before = fig.evaluate("el => [el.scrollLeft, el.scrollTop]")
    _drag(page, -220, -220)  # drag up-left pans toward bottom-right
    after = fig.evaluate("el => [el.scrollLeft, el.scrollTop]")
    assert after[0] > before[0], "horizontal pan did not move"
    assert after[1] > before[1], "vertical pan did not move"
    assert page.locator(".lightbox").is_visible(), "releasing the drag closed it"


# --- Background never scrolls --------------------------------------------


def test_page_background_is_locked_while_open(page, gallery_dir: Path) -> None:
    _open_gallery(page, gallery_dir)
    page.evaluate("window.scrollTo(0, 40)")
    assert page.evaluate("() => window.scrollY") == 40  # the page really scrolls
    page.locator("a.cell").first.click()
    assert page.evaluate("() => getComputedStyle(document.body).overflow === 'hidden'")
    locked_y = page.evaluate("() => window.scrollY")
    page.mouse.wheel(0, 600)  # wheeling must not move the background
    assert page.evaluate("() => window.scrollY") == locked_y, "background scrolled"


def test_closing_restores_page_scroll_position(page, gallery_dir: Path) -> None:
    _open_gallery(page, gallery_dir)
    page.evaluate("window.scrollTo(0, 40)")
    page.locator("a.cell").first.click()
    page.locator(".lb-close").click()
    assert page.locator(".lightbox").is_hidden()
    assert page.evaluate("() => getComputedStyle(document.body).overflow !== 'hidden'")
    assert page.evaluate("() => window.scrollY") == 40  # place restored


# --- Navigation -----------------------------------------------------------


def test_arrows_and_buttons_move_between_photos(page, gallery_dir: Path) -> None:
    _open_lightbox(page, gallery_dir)
    total = len(_DAY1)
    counter = page.locator(".lb-counter")
    assert counter.inner_text() == f"1 / {total}"
    page.keyboard.press("ArrowRight")
    assert counter.inner_text() == f"2 / {total}"
    page.locator(".lb-next").click()
    assert counter.inner_text() == f"3 / {total}"
    page.locator(".lb-prev").click()
    assert counter.inner_text() == f"2 / {total}"


def test_escape_and_backdrop_and_image_click(page, gallery_dir: Path) -> None:
    _open_lightbox(page, gallery_dir)
    page.locator(".lb-figure img").click()  # clicking the image keeps it open
    assert page.locator(".lightbox").is_visible()
    page.keyboard.press("Escape")
    assert page.locator(".lightbox").is_hidden()


def test_original_filename_shows_when_enabled(page, named_gallery_dir: Path) -> None:
    _open_gallery(page, named_gallery_dir)
    page.locator("a.cell").first.click()
    assert page.locator(".lb-name").inner_text() == "shot01.jpg"


def test_original_filename_absent_by_default(page, gallery_dir: Path) -> None:
    _open_lightbox(page, gallery_dir)
    assert page.locator(".lb-name").inner_text() == ""


def test_group_pages_link_prev_and_next(page, gallery_dir: Path) -> None:
    _open_gallery(page, gallery_dir, "day-01/index.html")
    page.get_by_role("link", name="Day 2").first.click()  # next
    assert page.url.endswith("day-02/index.html")
    page.get_by_role("link", name="Day 1").first.click()  # prev
    assert page.url.endswith("day-01/index.html")
