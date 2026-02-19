"""
Tools Server reliability policy.

Defines deterministic timeout and isolation controls for tool execution.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Optional

from common.config import ServiceConfig


def _parse_positive_float(raw: Optional[str], default: Optional[float]) -> Optional[float]:
    if raw is None or str(raw).strip() == "":
        return default
    value = float(raw)
    if value <= 0:
        return None
    return value


def _parse_positive_int(raw: Optional[str], default: int) -> int:
    if raw is None or str(raw).strip() == "":
        return default
    value = int(raw)
    return value if value > 0 else default


@dataclass(frozen=True)
class ToolsReliabilityPolicy:
    # HTTP API level timeout for /internal/runtimes/{id}/tools/call request.
    request_timeout_seconds: Optional[float]
    # Per tool execution timeout (applies inside ToolExecutor).
    execution_timeout_seconds: Optional[float]
    # Hard cap above all timeouts, avoids pathological hangs.
    global_timeout_seconds: Optional[float]
    # Per-runtime concurrency isolation.
    max_concurrent_tools_per_runtime: int

    @classmethod
    def from_env(cls) -> "ToolsReliabilityPolicy":
        default_execution_timeout = ServiceConfig.TOOLS_EXECUTION_TIMEOUT_SECONDS
        return cls(
            request_timeout_seconds=_parse_positive_float(
                os.getenv("NOVAIC_TOOLS_REQUEST_TIMEOUT_SECONDS"),
                ServiceConfig.TOOLS_REQUEST_TIMEOUT_SECONDS,
            ),
            execution_timeout_seconds=_parse_positive_float(
                os.getenv("NOVAIC_TOOLS_EXECUTION_TIMEOUT_SECONDS"),
                default_execution_timeout,
            ),
            global_timeout_seconds=_parse_positive_float(
                os.getenv("NOVAIC_TOOLS_GLOBAL_TIMEOUT_SECONDS"),
                ServiceConfig.TOOLS_GLOBAL_TIMEOUT_SECONDS,
            ),
            max_concurrent_tools_per_runtime=_parse_positive_int(
                os.getenv("NOVAIC_TOOLS_MAX_CONCURRENT_PER_RUNTIME"),
                ServiceConfig.TOOLS_MAX_CONCURRENT_PER_RUNTIME,
            ),
        )

    def resolve_execution_timeout(self, tool_name: str, arguments: Optional[Dict[str, Any]]) -> Optional[float]:
        timeout = self.execution_timeout_seconds
        if timeout is not None and self.global_timeout_seconds is not None:
            timeout = min(timeout, self.global_timeout_seconds)

        args = arguments or {}
        caller_timeout = args.get("timeout")
        if caller_timeout is not None:
            try:
                caller_timeout_float = float(caller_timeout)
                if caller_timeout_float > 0:
                    timeout = caller_timeout_float if timeout is None else min(timeout, caller_timeout_float)
            except (TypeError, ValueError):
                # Ignore invalid timeout values and keep policy timeout.
                pass

        if timeout is not None and self.global_timeout_seconds is not None:
            timeout = min(timeout, self.global_timeout_seconds)
        return timeout


@lru_cache(maxsize=1)
def get_tools_reliability_policy() -> ToolsReliabilityPolicy:
    return ToolsReliabilityPolicy.from_env()
