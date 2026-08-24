"""Suite-wide isolation from ambient configuration.

``BaffinSettings`` resolves ``baffin.toml`` relative to the process CWD and reads
``BAFFIN_*`` environment variables, so whatever the developer happens to have in
the repo root or their shell would otherwise decide what the suite asserts. A
local ``include_full = true`` is enough to invert every "full is opt-in" test.

Every test therefore starts in an empty directory with no ``BAFFIN_*`` variables
set. Tests that want configuration write their own file and chdir to it (see
``tests/adapters/test_settings.py`` and ``tests/interface/test_quickstart.py``),
which still works: this runs first, and their ``monkeypatch.chdir`` wins.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def isolate_ambient_config(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pin every test to a clean CWD with no inherited ``BAFFIN_*`` settings."""
    for name in [key for key in os.environ if key.upper().startswith("BAFFIN_")]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path_factory.mktemp("cwd"))
