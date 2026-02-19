"""Strict single-file configuration loader."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any, Dict


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "services.json"


class ConfigError(RuntimeError):
    """Configuration loading/validation error."""


@dataclass(frozen=True)
class ServicesConfig:
    raw: Dict[str, Any]

    def get(self, *path: str) -> Any:
        node: Any = self.raw
        for key in path:
            if not isinstance(node, dict) or key not in node:
                dotted = ".".join(path)
                raise ConfigError(f"Missing required config key: {dotted}")
            node = node[key]
        return node


_CACHED_PATH: Path | None = None
_CACHED_MTIME_NS: int | None = None
_CACHED_CONFIG: ServicesConfig | None = None


def _resolve_config_path(path: str | Path) -> Path:
    requested = Path(path)
    if requested.exists():
        return requested.resolve()
    if requested != DEFAULT_CONFIG_PATH:
        return requested.resolve()

    candidates: list[Path] = []
    candidates.append(DEFAULT_CONFIG_PATH)
    candidates.append(Path.cwd() / "config" / "services.json")

    # Monorepo fallback during migration.
    candidates.append(Path(__file__).resolve().parents[3] / "novaic-backend" / "config" / "services.json")

    exe_parent = Path(sys.executable).resolve().parent
    candidates.append(exe_parent / "config" / "services.json")
    candidates.append(exe_parent.parent / "Resources" / "config" / "services.json")
    candidates.append(exe_parent.parent.parent / "Resources" / "config" / "services.json")
    candidates.append(
        Path.home() / "Library" / "Application Support" / "com.novaic.app" / "config" / "services.json"
    )
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "config" / "services.json")

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return requested.resolve()


def _validate_required_keys(data: Dict[str, Any]) -> None:
    required_roots = [
        "paths",
        "database",
        "services",
        "timeouts",
        "worker",
        "runtime",
        "llm",
        "text_truncate",
        "auto_truncate",
        "image",
        "retry",
    ]
    for key in required_roots:
        if key not in data:
            raise ConfigError(f"Missing required config section: {key}")


def _load_raw(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in config file {path}: {e}") from e
    if not isinstance(parsed, dict):
        raise ConfigError(f"Config root must be object: {path}")
    _validate_required_keys(parsed)
    return parsed


def load_services_config(path: str | Path = DEFAULT_CONFIG_PATH, force_reload: bool = False) -> ServicesConfig:
    global _CACHED_PATH, _CACHED_MTIME_NS, _CACHED_CONFIG

    cfg_path = _resolve_config_path(path)
    mtime_ns = cfg_path.stat().st_mtime_ns if cfg_path.exists() else None
    if (
        not force_reload
        and _CACHED_CONFIG is not None
        and _CACHED_PATH == cfg_path
        and _CACHED_MTIME_NS == mtime_ns
    ):
        return _CACHED_CONFIG

    raw = _load_raw(cfg_path)
    config = ServicesConfig(raw=raw)
    _CACHED_PATH = cfg_path
    _CACHED_MTIME_NS = mtime_ns
    _CACHED_CONFIG = config
    return config
