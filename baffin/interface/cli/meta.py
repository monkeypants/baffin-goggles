"""The `baffin meta` command group (see :doc:`/cli`).

show / edit / set, all routed through the EditAssetMeta use case. Authoring
writes sidecars only, never the photo bytes.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Annotated

import typer

from baffin.adapters.repository import FsAssetRepository
from baffin.application.config import GalleryConfig
from baffin.application.editmeta import EditAssetMeta
from baffin.domain import AssetMeta, SourceRef
from baffin.interface.cli.wiring import load_config, sidecar_store

meta_app = typer.Typer(help="Read/write per-image metadata sidecars.")

SourceOpt = Annotated[Path | None, typer.Option(help="Source folder of originals.")]
OutputOpt = Annotated[Path | None, typer.Option(help="Output site directory.")]
PhotoArg = Annotated[Path | None, typer.Argument(help="Photo the sidecar describes.")]
StrOpt = Annotated[str | None, typer.Option()]


def _ref(photo: Path) -> SourceRef:
    stat = photo.stat()
    return SourceRef(path=photo, size=stat.st_size, mtime_ns=stat.st_mtime_ns)


@meta_app.command("show")
def show(photo: Path, source: SourceOpt = None, output: OutputOpt = None) -> None:
    """Print a photo's sidecar metadata."""
    config = load_config(source=source, output=output)
    meta = sidecar_store(config).read(_ref(photo))
    if meta is None:
        typer.echo("(no sidecar)")
        return
    for field in ("title", "caption", "credit", "alt"):
        typer.echo(f"{field}: {getattr(meta, field) or ''}")


@meta_app.command("set")
def set_meta(
    photo: PhotoArg = None,
    title: StrOpt = None,
    caption: StrOpt = None,
    credit: StrOpt = None,
    alt: StrOpt = None,
    bulk: Annotated[bool, typer.Option("--all", help="Apply to every asset.")] = False,
    source: SourceOpt = None,
    output: OutputOpt = None,
) -> None:
    """Write sidecar fields for one photo, or every photo with --all."""
    config = load_config(source=source, output=output)
    edit = EditAssetMeta(sidecars=sidecar_store(config))
    changes = AssetMeta(title=title, caption=caption, credit=credit, alt=alt)

    if bulk:
        for ref in FsAssetRepository().discover(config.source):
            edit.execute(ref, changes)
        return
    if photo is None:
        raise typer.BadParameter("give a photo path or use --all")
    edit.execute(_ref(photo), changes)


@meta_app.command("edit")
def edit(photo: Path, source: SourceOpt = None, output: OutputOpt = None) -> None:
    """Open the sidecar in $EDITOR, creating a template if absent."""
    config = load_config(source=source, output=output)
    store = _sidecar_store_with_template(config, _ref(photo))
    subprocess.run([os.environ.get("EDITOR", "vi"), str(store)], check=False)


def _sidecar_store_with_template(config: GalleryConfig, ref: SourceRef) -> Path:
    return sidecar_store(config).ensure_template(ref)
