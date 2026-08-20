"""Every command that rebuilds the site must carry the options controlling it.

``build`` and ``serve`` share one rebuild path but are separate Typer callbacks,
so each has to plumb the same options through by hand — and a forgotten one
fails quietly in a different way depending on what it controls:

* ``--full`` decides what the pages contain. ``data-full`` (which the lightbox
  gates its download button on) and the "Full" switcher entry are both derived
  from that tier, so a command that rebuilds without the flag strips two visible
  features while leaving ``full/*.jpg`` on disk. That is exactly how a ``serve``
  run re-rendered a ``build --full`` gallery into a broken one: the renderer was
  covered in both states, but nothing checked that a *command* picked the right
  one.
* ``--jobs`` decides only how fast the work runs, so an ignored value leaves
  byte-identical output. Nothing observable in the site can catch it; the value
  has to be watched on its way in.
"""

import inspect
from pathlib import Path
from typing import Any

import pytest
from PIL import Image
from typer.testing import CliRunner

from baffin.interface.cli import app as cli

runner = CliRunner()

# Commands that rebuild and re-render the site before doing their own job.
REBUILDING_COMMANDS = ["build", "serve"]

# build-only options that neither change the pages nor need to reach serve.
BUILD_ONLY = {"force"}


@pytest.fixture(autouse=True)
def stub_the_blocking_server(monkeypatch: pytest.MonkeyPatch) -> None:
    """``serve`` ends in a blocking accept loop; let it return instead."""
    monkeypatch.setattr(cli, "_serve_directory", lambda directory, host, port: None)


def _render(command: str, tmp_path: Path, *extra: str) -> Path:
    photos, out = tmp_path / "photos", tmp_path / "site"
    photos.mkdir(parents=True)
    for name, color in (("a.jpg", (200, 40, 40)), ("b.jpg", (40, 200, 40))):
        Image.new("RGB", (1200, 900), color).save(photos / name, "JPEG")
    result = runner.invoke(
        cli.app, [command, "--source", str(photos), "--output", str(out), *extra]
    )
    assert result.exit_code == 0, result.output
    return out


@pytest.mark.parametrize("command", REBUILDING_COMMANDS)
def test_full_flag_reaches_the_rendered_page(command: str, tmp_path: Path) -> None:
    out = _render(command, tmp_path, "--full")
    html = (out / "day-01" / "index.html").read_text()
    assert "data-full=" in html  # the download button's href
    assert '"label": "Full"' in html  # the switcher's native-size entry
    assert len(list((out / "full").glob("*.jpg"))) == 2


@pytest.mark.parametrize("command", REBUILDING_COMMANDS)
def test_without_the_flag_the_full_tier_is_absent(command: str, tmp_path: Path) -> None:
    out = _render(command, tmp_path)
    html = (out / "day-01" / "index.html").read_text()
    assert "data-full=" not in html
    assert '"label": "Full"' not in html
    assert not (out / "full").exists()


@pytest.mark.parametrize("command", REBUILDING_COMMANDS)
def test_jobs_flag_reaches_the_build(
    command: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A worker count that is accepted and then dropped is invisible in the
    output, so assert on the value arriving rather than on the site."""
    seen: dict[str, int] = {}
    build = cli.run_build

    def spy(config: Any, *, jobs: int = 1) -> Any:
        seen["jobs"] = jobs
        return build(config, jobs=jobs)

    monkeypatch.setattr(cli, "run_build", spy)
    _render(command, tmp_path, "--jobs", "3")
    assert seen["jobs"] == 3


def test_serving_after_a_full_build_keeps_the_full_tier(tmp_path: Path) -> None:
    """The sequence that broke a published gallery: ``build --full``, then a
    plain ``serve``.

    A rebuild must not retract what is already on disk. The pages advertise the
    derivatives the output holds, so re-rendering with a quieter config cannot
    strip the download button from photos that still have a full-size file.
    """
    photos, out = tmp_path / "photos", tmp_path / "site"
    photos.mkdir(parents=True)
    Image.new("RGB", (1200, 900), (200, 40, 40)).save(photos / "a.jpg", "JPEG")
    where = ["--source", str(photos), "--output", str(out)]

    built = runner.invoke(cli.app, ["build", *where, "--full"])
    assert built.exit_code == 0, built.output
    assert "data-full=" in (out / "day-01" / "index.html").read_text()

    served = runner.invoke(cli.app, ["serve", *where])  # note: no --full
    assert served.exit_code == 0, served.output

    html = (out / "day-01" / "index.html").read_text()
    assert list((out / "full").glob("*.jpg"))  # the file is still there...
    assert "data-full=" in html  # ...so the button must still be too
    assert '"label": "Full"' in html


def _option_names(command: str) -> set[str]:
    for info in cli.app.registered_commands:
        if (info.name or info.callback.__name__) == command:  # type: ignore[union-attr]
            return set(inspect.signature(info.callback).parameters)  # type: ignore[arg-type]
    raise AssertionError(f"no registered command named {command!r}")


def test_serve_exposes_every_option_that_shapes_the_build() -> None:
    """Catch the next flag that gets plumbed into one rebuild path but not both.

    This compares option *names* only, so it proves the surface exists — not
    that both commands give it the same meaning. The parametrized tests above
    are what pin the behaviour.
    """
    shared = _option_names("build") - BUILD_ONLY
    missing = shared - _option_names("serve")
    assert not missing, f"serve cannot express: {sorted(missing)}"
