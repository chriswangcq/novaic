#!/usr/bin/env bash
set -euo pipefail

# OS-level leak probe for tools-server timeout/cancel paths.
# Checks the probe process itself for fd/process leak drift.
#
# ============================================================
# HOST DEPENDENCY POLICY (Round 007 Decision, finalized)
# ============================================================
# This script requires: lsof, pgrep, python3.
#
# Policy Choice: Option A — supported on Linux (Ubuntu/Debian) and macOS.
#   - Linux CI: dependencies guaranteed via ci_preflight_probe_prereqs.sh.
#   - macOS local dev: lsof and pgrep are native; no install needed.
#   - Non-Linux CI runners: NOT supported; probe will fail fast below.
#
# If a required command is missing, the script exits immediately with
# a human-readable error and a fix hint.  There is NO silent fallback.
# This is intentional to avoid masking environment misconfiguration.
# ============================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

echo "[leak-probe] starting tools-server leak probe"

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[leak-probe] FAIL: missing required command '$cmd'" >&2
    echo "[leak-probe] hint: install '$cmd' and re-run probe" >&2
    exit 2
  fi
}

require_cmd lsof
require_cmd pgrep
require_cmd python3

python3 - <<'PY'
import asyncio
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from tools_server.executor import ToolExecutor, BUILTIN_TOOL_NAMES
from tools_server.reliability import ToolsReliabilityPolicy


def _fd_count(pid: int) -> int:
    out = subprocess.check_output(["lsof", "-p", str(pid)], text=True)
    return max(0, len(out.strip().splitlines()) - 1)


def _child_pids(pid: int) -> set[int]:
    out = subprocess.run(
        ["pgrep", "-P", str(pid)],
        text=True,
        capture_output=True,
        check=False,
    )
    if out.returncode != 0 or not out.stdout.strip():
        return set()
    return {int(x) for x in out.stdout.strip().splitlines() if x.strip().isdigit()}


async def _run_probe() -> dict:
    policy = ToolsReliabilityPolicy(
        request_timeout_seconds=1.0,
        execution_timeout_seconds=0.01,
        global_timeout_seconds=1.0,
        max_concurrent_tools_per_runtime=4,
    )
    executor = ToolExecutor(
        runtime_id="rt-leak-probe",
        agent_id="agent-leak-probe",
        subagent_id="main-leak-probe",
        reliability_policy=policy,
    )

    original_names = set(BUILTIN_TOOL_NAMES)
    BUILTIN_TOOL_NAMES.add("fake_timeout_tool")
    try:
        async def _slow_builtin(_tool_name, _args):
            await asyncio.sleep(0.2)
            return {"success": True, "result": {"ok": True}}

        executor._execute_builtin = _slow_builtin  # type: ignore[method-assign]

        for _ in range(150):
            result = await executor.execute("fake_timeout_tool", {})
            if result.get("success"):
                raise RuntimeError("Expected timeout failure, got success")
            if "timeout" not in (result.get("error") or "").lower():
                raise RuntimeError(f"Expected timeout error, got: {result}")
        await executor.close()
    finally:
        BUILTIN_TOOL_NAMES.clear()
        BUILTIN_TOOL_NAMES.update(original_names)
        await executor.close()

    return {"loops": 150}


def main() -> None:
    pid = os.getpid()
    fd_before = _fd_count(pid)
    children_before = _child_pids(pid)
    probe_info = asyncio.run(_run_probe())
    fd_after = _fd_count(pid)
    children_after = _child_pids(pid)
    leaked_children = sorted(children_after - children_before)
    fd_delta = fd_after - fd_before

    print(f"[leak-probe] loops={probe_info['loops']}")
    print(f"[leak-probe] fd_before={fd_before} fd_after={fd_after} delta={fd_delta}")
    print(
        f"[leak-probe] children_before={sorted(children_before)} "
        f"children_after={sorted(children_after)} leaked={leaked_children}"
    )

    # Allow tiny FD jitter from interpreter internals, but fail on sustained leak.
    if fd_delta > 3:
        raise SystemExit(f"[leak-probe] FAIL: fd leak suspected, delta={fd_delta}")
    if leaked_children:
        raise SystemExit(f"[leak-probe] FAIL: leaked child processes: {leaked_children}")

    print("[leak-probe] PASS")


if __name__ == "__main__":
    main()
PY
