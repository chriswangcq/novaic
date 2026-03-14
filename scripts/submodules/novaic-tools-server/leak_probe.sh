#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

python3 - <<'PY'
import asyncio
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from tools_server.executor import ToolExecutor, BUILTIN_TOOL_NAMES

try:
    from tools_server.reliability import ToolsReliabilityPolicy
except ImportError:
    ToolsReliabilityPolicy = None


def _fd_count(pid: int) -> int:
    out = subprocess.check_output(["lsof", "-p", str(pid)], text=True)
    return max(0, len(out.strip().splitlines()) - 1)


async def _run_probe() -> None:
    policy = (
        ToolsReliabilityPolicy(
            request_timeout_seconds=1.0,
            execution_timeout_seconds=0.01,
            global_timeout_seconds=1.0,
            max_concurrent_tools_per_runtime=4,
        )
        if ToolsReliabilityPolicy
        else None
    )
    executor = ToolExecutor(
        context_key="agent-leak-probe:main-leak-probe",
        agent_id="agent-leak-probe",
        subagent_id="main-leak-probe",
    )
    original = set(BUILTIN_TOOL_NAMES)
    BUILTIN_TOOL_NAMES.add("fake_timeout_tool")
    try:
        async def _slow_builtin(_tool_name, _args):
            await asyncio.sleep(0.2)
            return {"success": True}

        executor._execute_builtin = _slow_builtin  # type: ignore[method-assign]
        for _ in range(80):
            result = await executor.execute("fake_timeout_tool", {})
            assert result.get("success") is False
            assert "timeout" in (result.get("error") or "").lower()
    finally:
        BUILTIN_TOOL_NAMES.clear()
        BUILTIN_TOOL_NAMES.update(original)
        await executor.close()


def main() -> None:
    pid = os.getpid()
    before = _fd_count(pid)
    asyncio.run(_run_probe())
    after = _fd_count(pid)
    delta = after - before
    print(f"[leak-probe] fd_before={before} fd_after={after} delta={delta}")
    if delta > 3:
        raise SystemExit(f"[leak-probe] FAIL: fd leak suspected, delta={delta}")
    print("[leak-probe] PASS")


if __name__ == "__main__":
    main()
PY
