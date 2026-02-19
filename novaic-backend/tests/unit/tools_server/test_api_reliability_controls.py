import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


@pytest.mark.asyncio
async def test_call_tool_request_timeout_closes_executor():
    from tools_server.api import call_tool, CallToolRequest
    from tools_server.reliability import ToolsReliabilityPolicy

    runtime = SimpleNamespace(
        runtime_id="rt-1",
        agent_id="a1",
        subagent_id="main-1",
        execution_semaphore=asyncio.Semaphore(1),
    )

    class FakeManager:
        def get(self, runtime_id: str):
            return runtime if runtime_id == "rt-1" else None

    class FakeExecutor:
        close_count = 0

        def __init__(self, *args, **kwargs):
            pass

        async def execute(self, tool_name, arguments):
            await asyncio.sleep(0.05)
            return {"success": True, "result": {"ok": True}}

        async def close(self):
            FakeExecutor.close_count += 1

    policy = ToolsReliabilityPolicy(
        request_timeout_seconds=0.01,
        execution_timeout_seconds=None,
        global_timeout_seconds=10.0,
        max_concurrent_tools_per_runtime=1,
    )

    with patch("tools_server.runtime_manager.get_runtime_manager", return_value=FakeManager()):
        with patch("tools_server.executor.ToolExecutor", FakeExecutor):
            with patch("tools_server.api.get_tools_reliability_policy", return_value=policy):
                resp = await call_tool("rt-1", CallToolRequest(name="shell_exec", arguments={}))

    assert resp.success is False
    assert "timeout" in (resp.error or "").lower()
    assert FakeExecutor.close_count == 1


@pytest.mark.asyncio
async def test_call_tool_enforces_runtime_semaphore_under_load():
    from tools_server.api import call_tool, CallToolRequest
    from tools_server.reliability import ToolsReliabilityPolicy

    runtime = SimpleNamespace(
        runtime_id="rt-1",
        agent_id="a1",
        subagent_id="main-1",
        execution_semaphore=asyncio.Semaphore(3),
    )

    class FakeManager:
        def get(self, runtime_id: str):
            return runtime if runtime_id == "rt-1" else None

    class FakeExecutor:
        close_count = 0
        current_running = 0
        max_running = 0

        def __init__(self, *args, **kwargs):
            pass

        async def execute(self, tool_name, arguments):
            FakeExecutor.current_running += 1
            FakeExecutor.max_running = max(FakeExecutor.max_running, FakeExecutor.current_running)
            await asyncio.sleep(0.01)
            FakeExecutor.current_running -= 1
            return {"success": True, "result": {"tool": tool_name}}

        async def close(self):
            FakeExecutor.close_count += 1

    class FakeTrsClient:
        def create_from_raw(self, *args, **kwargs):
            return "trs-result-1"

    policy = ToolsReliabilityPolicy(
        request_timeout_seconds=2.0,
        execution_timeout_seconds=None,
        global_timeout_seconds=10.0,
        max_concurrent_tools_per_runtime=3,
    )

    async def _one_call():
        return await call_tool("rt-1", CallToolRequest(name="shell_exec", arguments={}))

    with patch("tools_server.runtime_manager.get_runtime_manager", return_value=FakeManager()):
        with patch("tools_server.executor.ToolExecutor", FakeExecutor):
            with patch("tools_server.api.get_tools_reliability_policy", return_value=policy):
                with patch("task_queue.utils.trs_sdk.get_trs_client", return_value=FakeTrsClient()):
                    responses = await asyncio.gather(*[_one_call() for _ in range(24)])

    assert all(r.success for r in responses)
    assert FakeExecutor.max_running <= 3
    assert FakeExecutor.close_count == 24


@pytest.mark.asyncio
async def test_call_tool_enforces_runtime_semaphore_high_concurrency_variant():
    from tools_server.api import call_tool, CallToolRequest
    from tools_server.reliability import ToolsReliabilityPolicy

    semaphore_limit = 5
    request_count = 80
    runtime = SimpleNamespace(
        runtime_id="rt-high-load",
        agent_id="a1",
        subagent_id="main-1",
        execution_semaphore=asyncio.Semaphore(semaphore_limit),
    )

    class FakeManager:
        def get(self, runtime_id: str):
            return runtime if runtime_id == "rt-high-load" else None

    class FakeExecutor:
        close_count = 0
        current_running = 0
        max_running = 0

        def __init__(self, *args, **kwargs):
            pass

        async def execute(self, tool_name, arguments):
            FakeExecutor.current_running += 1
            FakeExecutor.max_running = max(FakeExecutor.max_running, FakeExecutor.current_running)
            await asyncio.sleep(0.01)
            FakeExecutor.current_running -= 1
            return {"success": True, "result": {"tool": tool_name}}

        async def close(self):
            FakeExecutor.close_count += 1

    class FakeTrsClient:
        def create_from_raw(self, *args, **kwargs):
            return "trs-result-high-load"

    policy = ToolsReliabilityPolicy(
        request_timeout_seconds=5.0,
        execution_timeout_seconds=None,
        global_timeout_seconds=30.0,
        max_concurrent_tools_per_runtime=semaphore_limit,
    )

    async def _one_call():
        return await call_tool("rt-high-load", CallToolRequest(name="shell_exec", arguments={}))

    with patch("tools_server.runtime_manager.get_runtime_manager", return_value=FakeManager()):
        with patch("tools_server.executor.ToolExecutor", FakeExecutor):
            with patch("tools_server.api.get_tools_reliability_policy", return_value=policy):
                with patch("task_queue.utils.trs_sdk.get_trs_client", return_value=FakeTrsClient()):
                    responses = await asyncio.gather(*[_one_call() for _ in range(request_count)])

    assert all(r.success for r in responses)
    assert FakeExecutor.max_running <= semaphore_limit
    assert FakeExecutor.close_count == request_count
