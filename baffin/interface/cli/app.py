"""Typer application shell and the doctor command (see :doc:`/cli`).

Each command is a thin translation from argv into a use case;
doctor checks the system dependencies and reports the resolved configuration.
"""

from __future__ import annotations

import functools
import http.server
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Annotated

import typer

from baffin.adapters.settings import BaffinSettings
from baffin.application.origin import content_hash_of
from baffin.interface.cli.meta import meta_app
from baffin.interface.cli.pipeline import run_build, watch_templates
from baffin.interface.cli.wiring import (
    build_cleaner,
    build_origin_resolver,
    build_scanner,
    load_config,
)

SourceOpt = Annotated[Path | None, typer.Option(help="Source folder of originals.")]
OutputOpt = Annotated[Path | None, typer.Option(help="Output site directory.")]
FullOpt = Annotated[bool, typer.Option(help="Publish full-res scrubbed copies.")]
ForceOpt = Annotated[bool, typer.Option(help="Bypass caches; regenerate all.")]
JobsOpt = Annotated[int, typer.Option(help="Parallel workers.")]
HostOpt = Annotated[str, typer.Option(help="Bind address.")]
PortOpt = Annotated[int, typer.Option(help="Bind port.")]
WatchOpt = Annotated[bool, typer.Option(help="Re-render templates on change.")]

app = typer.Typer(
    help="baffin: publish a folder of photos as a static gallery.",
    no_args_is_help=True,
    add_completion=False,
)


app.add_typer(meta_app, name="meta")


@app.callback()
def main() -> None:
    """baffin: publish a folder of photos as a static gallery."""


def libvips_version() -> str | None:
    try:
        import pyvips

        return f"{pyvips.version(0)}.{pyvips.version(1)}"
    except Exception:
        return None


def ffmpeg_version() -> str | None:
    exe = shutil.which("ffmpeg")
    if not exe:
        return None
    try:
        out = subprocess.run(
            [exe, "-version"], capture_output=True, text=True, check=True
        )
    except (subprocess.CalledProcessError, OSError):
        return None
    first = out.stdout.splitlines()
    return first[0] if first else exe


@app.command()
def doctor() -> None:
    """Verify system dependencies and configuration sanity."""
    healthy = True

    vips = libvips_version()
    if vips:
        typer.echo(f"libvips: {vips}")
    else:
        typer.echo("libvips: MISSING (install via `brew install vips`)")
        healthy = False

    ffmpeg = ffmpeg_version()
    if ffmpeg:
        typer.echo(f"ffmpeg:  {ffmpeg}")
    else:
        typer.echo("ffmpeg:  MISSING (install via `brew install ffmpeg`)")
        healthy = False

    settings = BaffinSettings()
    typer.echo(f"source:  {settings.source}")
    typer.echo(f"output:  {settings.output}")

    if not healthy:
        raise typer.Exit(code=1)
    typer.echo("All good.")


@app.command()
def scan(source: SourceOpt = None, output: OutputOpt = None) -> None:
    """Dry run: report assets, groups, and the cache HIT/MISS plan."""
    config = load_config(source=source, output=output)
    result = build_scanner(config).execute(config)
    typer.echo(f"Assets: {len(result.assets)}")
    typer.echo(f"Groups: {len(result.groups)}")
    typer.echo(f"Plan:   {result.hits} HIT / {result.misses} MISS")
    for label, error in result.report.skipped:
        typer.echo(f"skipped {label}: {error}")


@app.command()
def origin(
    items: list[str],
    source: SourceOpt = None,
    output: OutputOpt = None,
) -> None:
    """Print the original source path for gallery images.

    Accepts content hashes, derivative paths (``full/HASH.jpg``), or pasted
    image URLs. The printed path can be piped to another tool:
    ``open -a Hugin $(baffin origin ...)``.
    """
    config = load_config(source=source, output=output)
    index = build_origin_resolver(config).index(config.source)
    missing = False
    for item in items:
        content_hash = content_hash_of(item)
        path = index.get(content_hash) if content_hash else None
        if path is not None:
            typer.echo(path)
        else:
            typer.echo(f"no original found for {item!r}", err=True)
            missing = True
    if missing:
        raise typer.Exit(code=1)


@app.command()
def build(
    source: SourceOpt = None,
    output: OutputOpt = None,
    full: FullOpt = False,
    force: ForceOpt = False,
    jobs: JobsOpt = 1,
) -> None:
    """Lazily build the gallery, generating only what the cache is missing."""
    config = load_config(
        source=source, output=output, include_full=True if full else None
    )
    if force:
        shutil.rmtree(config.output / ".baffin", ignore_errors=True)

    summary = run_build(config, jobs=jobs)
    typer.echo(f"Generated {summary.generated} derivative(s)")
    typer.echo(f"Groups:    {summary.groups}")
    for label, error in summary.skipped:
        typer.echo(f"skipped {label}: {error}")


@app.command()
def clean(
    source: SourceOpt = None,
    output: OutputOpt = None,
    wipe: Annotated[bool, typer.Option("--all", help="Wipe the whole cache.")] = False,
) -> None:
    """Prune orphaned derivatives; --all wipes the cache."""
    config = load_config(source=source, output=output)
    result = build_cleaner(config).execute(config, wipe=wipe)
    typer.echo(f"Removed {len(result.removed)} derivative(s)")


def _template_dir() -> Path:
    from baffin.adapters.render import renderer

    return Path(renderer.__file__).parent / "templates"


def _serve_directory(directory: Path, host: str, port: int) -> None:  # pragma: no cover
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(directory)
    )
    with http.server.ThreadingHTTPServer((host, port), handler) as httpd:
        httpd.serve_forever()


@app.command()
def serve(
    source: SourceOpt = None,
    output: OutputOpt = None,
    full: FullOpt = False,
    jobs: JobsOpt = 1,
    host: HostOpt = "127.0.0.1",
    port: PortOpt = 8000,
    watch: WatchOpt = False,
) -> None:
    """Build then serve the site locally; --watch re-renders templates.

    ``serve`` rebuilds before serving, so it takes the build options too.
    ``--full`` decides what the pages contain; serving without it re-renders a
    ``build --full`` site without its download button. ``--jobs`` sets the
    worker count for a cold cache.
    """
    config = load_config(
        source=source, output=output, include_full=True if full else None
    )
    run_build(config, jobs=jobs)
    if watch:
        threading.Thread(
            target=watch_templates,
            args=(config, _template_dir()),
            daemon=True,
        ).start()
    typer.echo(f"Serving {config.output} at http://{host}:{port}")
    _serve_directory(config.output, host, port)
