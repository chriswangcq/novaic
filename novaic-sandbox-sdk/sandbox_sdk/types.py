"""Sandboxd service-boundary DTOs.

These types describe a remote sandbox execution request/result. They are not
process substrate types and intentionally use JSON-friendly primitives.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class SandboxBindMount:
    source_root: str
    mount_point: str
    stable_cwd: str


@dataclass(frozen=True)
class SandboxExecSpec:
    command: str
    cwd: str
    env: Mapping[str, str]
    timeout: int
    display_command: str = ""
    mount: SandboxBindMount | None = None


@dataclass(frozen=True)
class SandboxExecResult:
    stdout: bytes
    stderr: bytes
    exit_code: int
    duration_s: float
