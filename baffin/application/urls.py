"""Portable in-site URLs (see :doc:`/functional-core`): relative links plus
absolute-for-metadata.

In-site links are **relative** to the page they appear on, so the generated
site is portable across a domain root, a ``/baffin/`` subpath, or ``file://``
with no rewriting. ``base_url`` is used only for OpenGraph tags and the sitemap.
"""

from __future__ import annotations

import posixpath


def url_for(target: str, *, current: str = "index.html") -> str:
    """Relative link from ``current`` page to a site-relative ``target``.

    Both are site-relative POSIX paths (e.g. ``"thumb/ab.jpg"``,
    ``"2025/07/index.html"``). The result carries no leading slash and no host,
    so the same HTML resolves correctly wherever the site is mounted.

    >>> from baffin.application.urls import url_for
    >>> url_for("thumb/ab.jpg", current="index.html")
    'thumb/ab.jpg'
    >>> url_for("thumb/ab.jpg", current="2025/07/index.html")
    '../../thumb/ab.jpg'
    """
    start = posixpath.dirname(current) or "."
    return posixpath.relpath(target, start)


def absolute_url(target: str, base_url: str) -> str:
    """Absolute URL for OpenGraph / sitemap only (never for in-site links)."""
    return base_url.rstrip("/") + "/" + target.lstrip("/")
