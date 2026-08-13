"""BaffinSettings: parse baffin.toml, validation, and resolution precedence."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from baffin.adapters.settings import BaffinSettings
from baffin.domain import DerivativeSpec

SAMPLE = """\
title = "Akshayuk Pass"
base_url = "https://chris.example.com/baffin/"
source = "photos/"
output = "site/"
grouping = "day"
include_full = true

[[derivatives]]
name = "thumb"
max_edge = 320
quality = 80
"""


def _write_toml(tmp_path: Path, body: str = SAMPLE) -> None:
    (tmp_path / "baffin.toml").write_text(body)


def test_parses_sample_toml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_toml(tmp_path)
    monkeypatch.chdir(tmp_path)
    settings = BaffinSettings()
    assert settings.title == "Akshayuk Pass"
    assert settings.include_full is True

    config = settings.to_config()
    assert config.grouping.mode == "day"
    assert config.specs == (DerivativeSpec("thumb", 320, 80),)


def test_defaults_apply_without_a_toml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    settings = BaffinSettings()
    assert settings.title == "baffin gallery"
    assert settings.to_config().include_full is False


def test_env_overrides_toml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_toml(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BAFFIN_TITLE", "From Env")
    assert BaffinSettings().title == "From Env"


def test_init_args_override_env_and_toml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_toml(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BAFFIN_TITLE", "From Env")
    assert BaffinSettings(title="From CLI").title == "From CLI"


def test_invalid_derivative_is_a_validation_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_toml(
        tmp_path,
        'title = "x"\n[[derivatives]]\nname = "thumb"\nquality = "not-an-int"\n',
    )
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValidationError):
        BaffinSettings()
