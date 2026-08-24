"""Plain in-app configuration (see :doc:`/cli`).

Parsed and validated at the edge (Pydantic, Phase 5),
then handed inward as this framework-free object.
The core never sees a TOML file or an env var.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from baffin.application.grouping import GroupingPolicy
from baffin.domain import DerivativeSpec

DEFAULT_SPECS: tuple[DerivativeSpec, ...] = (
    DerivativeSpec("thumb", 300, 80),
    DerivativeSpec("low", 800, 82),
    DerivativeSpec("med", 1600, 85),
    DerivativeSpec("full", None, 95),
)


@dataclass(frozen=True)
class GalleryConfig:
    """Everything a use case needs, resolved and delivery-agnostic."""

    source: Path
    output: Path
    title: str = "baffin gallery"
    base_url: str = ""
    specs: tuple[DerivativeSpec, ...] = DEFAULT_SPECS
    grouping: GroupingPolicy = field(default_factory=GroupingPolicy)
    include_full: bool = False
    strict: bool = False
    strip_gps: bool = True
    show_filenames: bool = False

    def offerable_tiers(self, present: frozenset[str]) -> tuple[DerivativeSpec, ...]:
        """The tiers the pages may advertise, given what the output holds.

        ``include_full`` decides what gets *generated* (it gates the ``full``
        spec out of the plan); this decides what gets *advertised*, from the
        derivatives that actually exist. Keeping the two apart is what stops a
        rebuild under a quieter config from retracting a tier whose files are
        still on disk.

        >>> from pathlib import Path
        >>> from baffin.application.config import GalleryConfig
        >>> config = GalleryConfig(source=Path("photos"), output=Path("site"))
        >>> [s.name for s in config.offerable_tiers(frozenset({"thumb", "full"}))]
        ['thumb', 'full']
        """
        return tuple(spec for spec in self.specs if spec.name in present)
