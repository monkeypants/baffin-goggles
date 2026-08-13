"""baffin doctor: reports deps, exits nonzero when one is missing."""

import pytest
from typer.testing import CliRunner

from baffin.interface.cli import app as cli

runner = CliRunner()


def test_doctor_reports_present_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "libvips_version", lambda: "8.18")
    monkeypatch.setattr(cli, "ffmpeg_version", lambda: "ffmpeg version 8.1.2")
    result = runner.invoke(cli.app, ["doctor"])
    assert result.exit_code == 0
    assert "libvips: 8.18" in result.stdout
    assert "All good." in result.stdout


def test_doctor_exits_nonzero_when_ffmpeg_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "libvips_version", lambda: "8.18")
    monkeypatch.setattr(cli, "ffmpeg_version", lambda: None)
    result = runner.invoke(cli.app, ["doctor"])
    assert result.exit_code == 1
    assert "ffmpeg:  MISSING" in result.stdout


def test_doctor_exits_nonzero_when_libvips_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "libvips_version", lambda: None)
    monkeypatch.setattr(cli, "ffmpeg_version", lambda: "ffmpeg version 8.1.2")
    result = runner.invoke(cli.app, ["doctor"])
    assert result.exit_code == 1
