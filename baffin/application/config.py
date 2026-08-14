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

    @property
    def active_photo_specs(self) -> tuple[DerivativeSpec, ...]:
        """The photo tiers this build produces (``full`` only when opted in)."""
        return tuple(s for s in self.specs if s.name != "full" or self.include_full)
