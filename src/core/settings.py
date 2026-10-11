"""Shared application settings loaded from the project config file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.core.schemas import NonEmptyText, SchemaModel


class ApiSettings(SchemaModel):
    """HTTP server configuration for the application API layer."""

    host: NonEmptyText = "0.0.0.0"
    port: int = 8000
    log_level: NonEmptyText = "INFO"


class TemporalSettings(SchemaModel):
    """Temporal workflow connection configuration."""

    target: NonEmptyText = "localhost:7233"
    namespace: NonEmptyText = "hapa"
    workflow_queue: NonEmptyText = "hapa-workflows"


class DockerSettings(SchemaModel):
    """Container runtime connectivity used by execution sandboxes."""

    socket_url: NonEmptyText = "unix:///var/run/docker.sock"
    network: NonEmptyText = "hapa-network"
    timeout_seconds: int = 30
    use_rootless: bool = True


class BrowserSettings(SchemaModel):
    """Browser automation settings shared by visual execution tasks."""

    headless: bool = True
    screenshot_dir: NonEmptyText = "artifacts/screenshots"


class AppSettings(SchemaModel):
    """Top-level settings for the HAPA application bootstrap."""

    name: NonEmptyText
    environment: NonEmptyText = "development"
    debug: bool = False
    workspace_root: NonEmptyText = "."
    api: ApiSettings = ApiSettings()
    temporal: TemporalSettings = TemporalSettings()
    docker: DockerSettings = DockerSettings()
    browser: BrowserSettings = BrowserSettings()

    @classmethod
    def from_yaml(cls, path: str | Path | None = None) -> AppSettings:
        settings_path = Path(path) if path is not None else _default_settings_path()
        if not settings_path.exists():
            raise FileNotFoundError(f"Settings file not found: {settings_path}")

        with settings_path.open("r", encoding="utf-8") as file_handle:
            raw_config = yaml.safe_load(file_handle) or {}

        if not isinstance(raw_config, dict):
            raise ValueError("Settings YAML must be a mapping at the top level")

        return cls.model_validate(raw_config)


def _default_settings_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "settings.yaml"


def load_settings(path: str | Path | None = None) -> AppSettings:
    """Load application settings from YAML configuration."""

    return AppSettings.from_yaml(path)


settings = load_settings()
__all__ = ["ApiSettings", "AppSettings", "BrowserSettings", "DockerSettings", "TemporalSettings", "load_settings", "settings"]
