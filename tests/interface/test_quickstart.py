"""The documented surface works:
the help lists every command,
and the sample baffin.toml from the Getting Started chapter
parses into the expected config.
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from baffin.adapters.settings import BaffinSettings
from baffin.interface.cli.app import app

runner = CliRunner()

# The sample from the Getting Started chapter (docs/getting-started.rst).
SAMPLE_TOML = """\
title    = "Akshayuk Pass — Chris"
base_url = "https://chris.example.com/baffin/"
source   = "photos/"
output   = "site/"
grouping = "adaptive"
strip_gps = true
include_full = false

[[derivatives]]
name = "thumb"
max_edge = 300
quality = 80
"""


def test_help_lists_every_documented_command() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("build", "scan", "serve", "clean", "meta", "doctor"):
        assert command in result.stdout


def test_documented_sample_config_parses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "baffin.toml").write_text(SAMPLE_TOML)
    monkeypatch.chdir(tmp_path)

    config = BaffinSettings().to_config()
    assert config.title == "Akshayuk Pass — Chris"
    assert config.grouping.mode == "adaptive"
    assert config.include_full is False
    assert config.specs[0].max_edge == 300
