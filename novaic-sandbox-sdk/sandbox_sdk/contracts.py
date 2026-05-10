"""JSON wire contracts for sandboxd."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, Mapping

from sandbox_sdk.types import SandboxBindMount, SandboxExecResult, SandboxExecSpec

JsonObject = dict[str, Any]


def _require_str(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _require_int(data: Mapping[str, Any], key: str) -> int:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _optional_str(data: Mapping[str, Any], key: str, default: str = "") -> str:
    value = data.get(key, default)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


@dataclass(frozen=True)
class SandboxdExecuteRequest:
    command: str
    cwd: str
    env: Mapping[str, str]
    timeout: int
    display_command: str = ""
    mount: SandboxBindMount | None = None

    @classmethod
    def from_spec(cls, spec: SandboxExecSpec) -> "SandboxdExecuteRequest":
        return cls(
            command=spec.command,
            cwd=spec.cwd,
            env=dict(spec.env),
            timeout=spec.timeout,
            display_command=spec.display_command,
            mount=spec.mount,
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SandboxdExecuteRequest":
        env_raw = data.get("env", {})
        if not isinstance(env_raw, Mapping):
            raise ValueError("env must be an object")
        env: dict[str, str] = {}
        for key, value in env_raw.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("env keys and values must be strings")
            env[key] = value

        mount_raw = data.get("mount")
        mount: SandboxBindMount | None = None
        if mount_raw is not None:
            if not isinstance(mount_raw, Mapping):
                raise ValueError("mount must be an object or null")
            mount = SandboxBindMount(
                source_root=_require_str(mount_raw, "source_root"),
                mount_point=_require_str(mount_raw, "mount_point"),
                stable_cwd=_require_str(mount_raw, "stable_cwd"),
            )

        return cls(
            command=_require_str(data, "command"),
            cwd=_require_str(data, "cwd"),
            env=env,
            timeout=_require_int(data, "timeout"),
            display_command=_optional_str(data, "display_command"),
            mount=mount,
        )

    def to_spec(self) -> SandboxExecSpec:
        return SandboxExecSpec(
            command=self.command,
            cwd=self.cwd,
            env=dict(self.env),
            timeout=self.timeout,
            display_command=self.display_command,
            mount=self.mount,
        )

    def to_dict(self) -> JsonObject:
        mount: JsonObject | None = None
        if self.mount is not None:
            mount = {
                "source_root": self.mount.source_root,
                "mount_point": self.mount.mount_point,
                "stable_cwd": self.mount.stable_cwd,
            }
        return {
            "command": self.command,
            "cwd": self.cwd,
            "env": dict(self.env),
            "timeout": self.timeout,
            "display_command": self.display_command,
            "mount": mount,
        }


@dataclass(frozen=True)
class SandboxdExecuteResponse:
    stdout: bytes
    stderr: bytes
    exit_code: int
    duration_s: float

    @classmethod
    def from_result(cls, result: SandboxExecResult) -> "SandboxdExecuteResponse":
        return cls(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            duration_s=result.duration_s,
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SandboxdExecuteResponse":
        duration = data.get("duration_s")
        if not isinstance(duration, (int, float)) or isinstance(duration, bool):
            raise ValueError("duration_s must be a number")
        return cls(
            stdout=base64.b64decode(_require_str(data, "stdout_b64")),
            stderr=base64.b64decode(_require_str(data, "stderr_b64")),
            exit_code=_require_int(data, "exit_code"),
            duration_s=float(duration),
        )

    def to_result(self) -> SandboxExecResult:
        return SandboxExecResult(
            stdout=self.stdout,
            stderr=self.stderr,
            exit_code=self.exit_code,
            duration_s=self.duration_s,
        )

    def to_dict(self) -> JsonObject:
        return {
            "stdout_b64": base64.b64encode(self.stdout).decode("ascii"),
            "stderr_b64": base64.b64encode(self.stderr).decode("ascii"),
            "exit_code": self.exit_code,
            "duration_s": self.duration_s,
        }
