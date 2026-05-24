"""Configuration loading for the NovAIC release controller."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from release_controller.models import ControllerConfig


class ConfigError(ValueError):
    """Raised when controller configuration is missing or invalid."""


def load_config(path: str | Path) -> ControllerConfig:
    """Load and validate controller configuration from a JSON file."""

    config_path = Path(path)
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"config file does not exist: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"config file is not valid JSON: {config_path}: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ConfigError("config root must be a JSON object")
    try:
        return ControllerConfig.from_mapping(raw)
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc


def require_mapping(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    item = value.get(key)
    if not isinstance(item, Mapping):
        raise ConfigError(f"{key} must be an object")
    return item
