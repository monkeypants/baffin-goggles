"""url_for: relative links that survive being mounted anywhere."""

import posixpath

from baffin.application.urls import absolute_url, url_for


def test_link_from_root_page() -> None:
    assert url_for("thumb/ab.jpg", current="index.html") == "thumb/ab.jpg"


def test_link_from_flat_group_page_climbs_one_level() -> None:
    assert url_for("thumb/ab.jpg", current="day-03/index.html") == "../thumb/ab.jpg"
    assert url_for("index.html", current="day-03/index.html") == "../index.html"


def test_link_from_nested_group_page_climbs_two_levels() -> None:
    assert url_for("thumb/ab.jpg", current="2025/07/index.html") == "../../thumb/ab.jpg"


def test_absolute_url_is_for_metadata_only() -> None:
    assert (
        absolute_url("sitemap.xml", "https://chris.example.com/baffin/")
        == "https://chris.example.com/baffin/sitemap.xml"
    )


def test_relative_link_is_portable_across_mount_points() -> None:
    """The same relative string resolves correctly under a domain root, a
    subpath, and file:// — that is the whole point (SPEC §10)."""
    page = "2025/07/index.html"
    link = url_for("thumb/ab.jpg", current=page)  # base-independent string

    for mount in ("/", "/baffin/", "/home/me/site/"):
        page_dir = posixpath.dirname(mount + page)
        resolved = posixpath.normpath(posixpath.join(page_dir, link))
        assert resolved == posixpath.normpath(mount + "thumb/ab.jpg")
