"""Configuration model and loader (SPEC §11).

Pydantic Settings parse and validate ``baffin.toml`` / env vars at the edge, then
hand a plain :class:`GalleryConfig` inward. Resolution order (highest first):
CLI/init args → env vars (``BAFFIN_*``) → ``baffin.toml`` → defaults.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from baffin.application.config import DEFAULT_SPECS, GalleryConfig
from baffin.application.grouping import GroupingPolicy, GroupMode, Order
from baffin.domain import DerivativeSpec, Peer


class DerivativeSetting(BaseModel):
    name: Literal["thumb", "low", "med", "full"]
    max_edge: int | None
    quality: int


class PeerSetting(BaseModel):
    name: str
    url: str


class BaffinSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="baffin_", toml_file="baffin.toml", extra="ignore"
    )

    title: str = "baffin gallery"
    base_url: str = ""
    source: Path = Path("photos")
    output: Path = Path("site")
    meta: str = "meta"
    grouping: GroupMode = "adaptive"
    order: Order = "oldest-first"
    strip_gps: bool = True
    show_camera_settings: bool = False
    include_full: bool = False
    derivatives: list[DerivativeSetting] = []
    peers: list[PeerSetting] = []

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Highest priority first: init (CLI) > env > baffin.toml > defaults.
        return (
            init_settings,
            env_settings,
            TomlConfigSettingsSource(settings_cls),
        )

    def to_config(self) -> GalleryConfig:
        specs = (
            tuple(
                DerivativeSpec(d.name, d.max_edge, d.quality) for d in self.derivatives
            )
            or DEFAULT_SPECS
        )
        return GalleryConfig(
            source=self.source,
            output=self.output,
            title=self.title,
            base_url=self.base_url,
            specs=specs,
            grouping=GroupingPolicy(mode=self.grouping, order=self.order),
            include_full=self.include_full,
            strip_gps=self.strip_gps,
        )

    def peer_models(self) -> tuple[Peer, ...]:
        return tuple(Peer(name=p.name, url=p.url) for p in self.peers)
