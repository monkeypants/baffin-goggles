"""Jinja2 site renderer (see :doc:`/functional-core`): index timeline, group
pages, sitemap.

Server-rendered HTML is fully navigable with no JavaScript: every group is a
real page and every thumbnail links to a real image. In-site links are relative
(via ``url_for``), so the site is portable; ``base_url`` is used only for the
sitemap.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from baffin.application.urls import absolute_url, url_for
from baffin.domain import Asset, Group, Site

_HERE = Path(__file__).parent
_TEMPLATES = _HERE / "templates"
_STATIC = _HERE / "static"


class Jinja2Renderer:
    def __init__(self) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES)),
            autoescape=select_autoescape(["html", "xml", "j2"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, site: Site, out: Path) -> None:
        out.mkdir(parents=True, exist_ok=True)
        self._copy_static(out)

        self._write(
            out / "index.html",
            "index.html.j2",
            {
                **self._chrome(site, "index.html"),
                "groups": [self._summary(g, "index.html") for g in site.groups],
            },
        )
        for group in site.groups:
            page = f"{group.key}/index.html"
            self._write(
                out / group.key / "index.html",
                "group.html.j2",
                {
                    **self._chrome(site, page),
                    "group": group,
                    "assets": [self._asset_view(a, page) for a in group.assets],
                },
            )
        self._write(
            out / "sitemap.xml",
            "sitemap.xml.j2",
            {"locs": self._sitemap_locs(site)},
        )

    def _write(self, path: Path, template: str, context: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self._env.get_template(template).render(**context))

    def _copy_static(self, out: Path) -> None:
        assets = out / "assets"
        assets.mkdir(parents=True, exist_ok=True)
        for item in _STATIC.iterdir():
            if item.is_file():
                shutil.copy2(item, assets / item.name)

    def _chrome(self, site: Site, page: str) -> dict[str, Any]:
        return {
            "site": site,
            "css_href": url_for("assets/app.css", current=page),
            "js_href": url_for("assets/app.js", current=page),
            "home_href": url_for("index.html", current=page),
        }

    def _summary(self, group: Group, page: str) -> dict[str, Any]:
        cover = self._thumb_url(group.assets[0], page) if group.assets else None
        return {
            "href": url_for(f"{group.key}/index.html", current=page),
            "label": group.label,
            "count": len(group.assets),
            "cover": cover,
        }

    def _thumb_url(self, asset: Asset, page: str) -> str:
        tier = "poster" if asset.kind == "video" else "thumb"
        return url_for(f"{tier}/{asset.content_hash}.jpg", current=page)

    def _asset_view(self, asset: Asset, page: str) -> dict[str, Any]:
        h = asset.content_hash
        if asset.kind == "video":
            return {
                "kind": "video",
                "thumb": url_for(f"poster/{h}.jpg", current=page),
                "href": url_for(f"video/{h}.mp4", current=page),
                "srcset": "",
                "width": asset.width or 0,
                "height": asset.height or 0,
                "alt": "",
            }
        thumb = url_for(f"thumb/{h}.jpg", current=page)
        low = url_for(f"low/{h}.jpg", current=page)
        med = url_for(f"med/{h}.jpg", current=page)
        return {
            "kind": "photo",
            "thumb": thumb,
            "href": med,
            "srcset": f"{thumb} 300w, {low} 800w, {med} 1600w",
            "width": asset.width,
            "height": asset.height,
            "alt": "",
        }

    def _sitemap_locs(self, site: Site) -> list[str]:
        pages = ["index.html"] + [f"{g.key}/index.html" for g in site.groups]
        return [absolute_url(p, site.base_url) for p in pages]


if TYPE_CHECKING:
    from baffin.application.ports import SiteRenderer

    _conforms: SiteRenderer = Jinja2Renderer()
