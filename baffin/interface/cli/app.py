"""Typer application shell and the doctor command (SPEC §12).

Each command is a thin translation from argv into a use case; doctor checks the
system dependencies and reports the resolved configuration.
"""

from __future__ import annotations

import shutil
import subprocess

import typer

from baffin.adapters.settings import BaffinSettings

app = typer.Typer(
    help="baffin — publish a folder of photos as a static gallery.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def main() -> None:
    """baffin — publish a folder of photos as a static gallery."""


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
