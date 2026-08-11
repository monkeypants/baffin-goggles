"""Jinja2Renderer: complete, navigable HTML with no JS; relative in-site links."""

import posixpath
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

from baffin.adapters.render.renderer import Jinja2Renderer
from baffin.domain import Asset, Group, Site, SourceRef


def _asset(tag: str, kind: str = "photo") -> Asset:
    return Asset(
        ref=SourceRef(path=Path(f"photos/{tag}"), size=1, mtime_ns=1),
        content_hash=tag,
        kind=kind,  # type: ignore[arg-type]
        captured_at=datetime(2025, 7, 14, 9),
        width=800,
        height=600,
        orientation=1,
    )


def _site() -> Site:
    day = Group(
        key="day-01",
        label="Day 1 — 12 Jul",
        span=(datetime(2025, 7, 12), datetime(2025, 7, 12)),
        assets=(_asset("aaa"), _asset("bbb")),
    )
    month = Group(
        key="2025/07",
        label="July 2025",
        span=(datetime(2025, 7, 1), datetime(2025, 7, 31)),
        assets=(_asset("ccc"), _asset("ddd", kind="video")),
    )
    return Site(
        title="Akshayuk Pass",
        base_url="https://chris.example.com/baffin/",
        peers=(),
        groups=(day, month),
    )


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.srcs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name == "href" and value:
                self.hrefs.append(value)
            if name == "src" and value:
                self.srcs.append(value)


def _links(path: Path) -> _Links:
    parser = _Links()
    parser.feed(path.read_text())
    return parser


def test_writes_the_expected_site_layout(tmp_path: Path) -> None:
    Jinja2Renderer().render(_site(), tmp_path)
    for rel in [
        "index.html",
        "day-01/index.html",
        "2025/07/index.html",
        "sitemap.xml",
        "assets/app.css",
        "assets/app.js",
    ]:
        assert (tmp_path / rel).exists(), rel


def test_in_site_links_are_relative(tmp_path: Path) -> None:
    Jinja2Renderer().render(_site(), tmp_path)
    for page in ["index.html", "day-01/index.html", "2025/07/index.html"]:
        links = _links(tmp_path / page)
        for url in links.hrefs + links.srcs:
            assert not url.startswith("/"), f"{page}: absolute path {url}"
            assert "://" not in url, f"{page}: absolute URL {url}"


def test_nested_group_page_climbs_the_right_depth(tmp_path: Path) -> None:
    Jinja2Renderer().render(_site(), tmp_path)
    srcs = _links(tmp_path / "2025" / "07" / "index.html").srcs
    assert any(s == "../../thumb/ccc.jpg" for s in srcs)
    assert any(
        h == "../../assets/app.css"
        for h in _links(tmp_path / "2025" / "07" / "index.html").hrefs
    )


def test_site_is_navigable_without_js(tmp_path: Path) -> None:
    """Follow every in-site .html link from the index; each must resolve to a
    real file — no JavaScript involved."""
    Jinja2Renderer().render(_site(), tmp_path)
    index_dir = "."
    for href in _links(tmp_path / "index.html").hrefs:
        if href.endswith(".html"):
            target = posixpath.normpath(posixpath.join(index_dir, href))
            assert (tmp_path / target).exists(), href


def test_srcset_spans_thumb_low_med_for_photos(tmp_path: Path) -> None:
    Jinja2Renderer().render(_site(), tmp_path)
    html = (tmp_path / "day-01" / "index.html").read_text()
    assert "../thumb/aaa.jpg 300w" in html
    assert "../low/aaa.jpg 800w" in html
    assert "../med/aaa.jpg 1600w" in html
