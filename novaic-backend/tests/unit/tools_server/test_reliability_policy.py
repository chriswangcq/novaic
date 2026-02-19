import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


def test_policy_resolve_timeout_with_global_cap():
    from tools_server.reliability import ToolsReliabilityPolicy

    policy = ToolsReliabilityPolicy(
        request_timeout_seconds=60.0,
        execution_timeout_seconds=20.0,
        global_timeout_seconds=10.0,
        max_concurrent_tools_per_runtime=2,
    )

    resolved = policy.resolve_execution_timeout("shell_exec", {"timeout": 30})
    assert resolved == 10.0


@pytest.mark.asyncio
async def test_executor_returns_deterministic_timeout_error():
    from tools_server.executor import ToolExecutor, BUILTIN_TOOL_NAMES
    from tools_server.reliability import ToolsReliabilityPolicy

    policy = ToolsReliabilityPolicy(
        request_timeout_seconds=30.0,
        execution_timeout_seconds=0.01,
        global_timeout_seconds=1.0,
        max_concurrent_tools_per_runtime=4,
    )
    executor = ToolExecutor(runtime_id="rt-1", agent_id="a1", subagent_id="main-1", reliability_policy=policy)

    original = set(BUILTIN_TOOL_NAMES)
    BUILTIN_TOOL_NAMES.add("fake_timeout_tool")
    try:
        async def _slow_builtin(_tool_name, _arguments):
            await asyncio.sleep(0.2)
            return {"success": True}

        executor._execute_builtin = _slow_builtin  # type: ignore[method-assign]
        result = await executor.execute("fake_timeout_tool", {})
        assert result["success"] is False
        assert "timeout" in (result.get("error") or "").lower()
    finally:
        BUILTIN_TOOL_NAMES.clear()
        BUILTIN_TOOL_NAMES.update(original)
        await executor.close()
