"""Strict single-file configuration loader.

This module is the only runtime source of service configuration.
It intentionally does not read environment variables or use implicit fallbacks.
"""

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
    """Normalized strict config payload."""

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

    # Keep strict behavior for non-default explicit path.
    if requested != DEFAULT_CONFIG_PATH:
        return requested.resolve()

    candidates: list[Path] = []

    # 1) Bundle default (PyInstaller onefile temp dir, source tree).
    candidates.append(DEFAULT_CONFIG_PATH)

    # 2) Current working directory (dev scripts often run from repo root).
    candidates.append(Path.cwd() / "config" / "services.json")

    # 3) Next to executable (PyInstaller/onedir layouts).
    exe_parent = Path(sys.executable).resolve().parent
    candidates.append(exe_parent / "config" / "services.json")

    # 4) macOS app bundle resource layouts.
    candidates.append(exe_parent.parent / "Resources" / "config" / "services.json")
    candidates.append(exe_parent.parent.parent / "Resources" / "config" / "services.json")

    # 5) App data override path for desktop app deployments.
    candidates.append(Path.home() / "Library" / "Application Support" / "com.novaic.app" / "config" / "services.json")

    # 6) PyInstaller extraction directory (if available).
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "config" / "services.json")

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    return requested.resolve()


def _expect_type(name: str, value: Any, typ: type) -> None:
    if not isinstance(value, typ):
        raise ConfigError(f"Config key '{name}' must be {typ.__name__}, got {type(value).__name__}")


def _validate_required_keys(data: Dict[str, Any]) -> None:
    required_roots = [
        "paths",
        "database",
        "services",
        "tools_reliability",
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

    # Basic structural validation.
    _expect_type("paths", data["paths"], dict)
    _expect_type("database", data["database"], dict)
    _expect_type("services", data["services"], dict)
    _expect_type("tools_reliability", data["tools_reliability"], dict)
    _expect_type("timeouts", data["timeouts"], dict)
    _expect_type("worker", data["worker"], dict)
    _expect_type("runtime", data["runtime"], dict)
    _expect_type("llm", data["llm"], dict)
    _expect_type("text_truncate", data["text_truncate"], dict)
    _expect_type("auto_truncate", data["auto_truncate"], dict)
    _expect_type("image", data["image"], dict)
    _expect_type("retry", data["retry"], dict)

    # Required leaf keys consumed by ServiceConfig.
    leaf_keys = [
        ("paths", "data_dir"),
        ("database", "gateway_db_file"),
        ("database", "runtime_orchestrator_db_file"),
        ("services", "gateway", "host"),
        ("services", "gateway", "port"),
        ("services", "gateway", "url"),
        ("services", "queue_service", "url"),
        ("services", "queue_service", "port"),
        ("services", "tools_server", "url"),
        ("services", "tools_server", "port"),
        ("services", "vmcontrol", "host"),
        ("services", "vmcontrol", "port"),
        ("services", "vmcontrol", "url"),
        ("services", "file_service", "url"),
        ("services", "file_service", "port"),
        ("services", "tool_result_service", "url"),
        ("services", "tool_result_service", "port"),
        ("services", "runtime_orchestrator", "host"),
        ("services", "runtime_orchestrator", "port"),
        ("services", "runtime_orchestrator", "url"),
        ("tools_reliability", "request_timeout_seconds"),
        ("tools_reliability", "execution_timeout_seconds"),
        ("tools_reliability", "global_timeout_seconds"),
        ("tools_reliability", "max_concurrent_per_runtime"),
        ("timeouts", "task_timeout"),
        ("timeouts", "saga_step_timeout"),
        ("timeouts", "saga_timeout"),
        ("timeouts", "http_timeout"),
        ("timeouts", "http_timeout_short"),
        ("timeouts", "llm_call_timeout"),
        ("timeouts", "mcp_call_timeout"),
        ("timeouts", "db_transaction_timeout"),
        ("timeouts", "db_transaction_timeout_long"),
        ("timeouts", "internal_http_trust_env"),
        ("worker", "heartbeat_interval"),
        ("worker", "poll_interval"),
        ("worker", "num_workers"),
        ("worker", "max_concurrent_sagas"),
    ]
    for path in leaf_keys:
        node: Any = data
        for key in path:
            if not isinstance(node, dict) or key not in node:
                dotted = ".".join(path)
                raise ConfigError(f"Missing required config key: {dotted}")
            node = node[key]


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
    """Load strict services config from one file with mtime cache."""
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

