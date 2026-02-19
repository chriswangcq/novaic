"""
Unit tests for tools_server executor QEMU tool handling with unified internal contract.

Unified contract: operation failures return HTTP 200 with {success: false, error};
4xx may still indicate not-found/validation. Executor must interpret body, not just HTTP status.

Post-migration: qemu_* tools call vmcontrol (/api/vms/{agent_id}/*) or Gateway (/api/vm/start)
directly, not /internal/rt/*. Tests mock internal_async_client for vmcontrol calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

import sys
from pathlib import Path

# Add project root for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


def _mk_json_response(status: int, body: dict) -> httpx.Response:
    """Build an httpx Response with JSON body (request set for raise_for_status)."""
    import json
    req = httpx.Request("GET", "http://test/")
    return httpx.Response(
        status_code=status,
        content=json.dumps(body).encode("utf-8"),
        headers={"content-type": "application/json"},
        request=req,
    )


def _make_vmcontrol_mock(get_resp=None, post_resp=None):
    """Return a mock that works as async context manager, for internal_async_client(base_url=VMCONTROL_URL)."""
    mock_client = AsyncMock()
    if get_resp is not None:
        mock_client.get = AsyncMock(return_value=get_resp)
    if post_resp is not None:
        mock_client.post = AsyncMock(return_value=post_resp)
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=None)
    return mock_cm


class TestExecutorQemuUnifiedContract:
    """Verify executor handles unified QEMU contract (success:false, error propagation)."""

    @pytest.mark.asyncio
    async def test_qemu_ssh_exec_propagates_success_false(self):
        """qemu_ssh_exec: vmcontrol guest/exec returns {success: false} or timeout -> failure."""
        from tools_server.executor import ToolExecutor

        executor = ToolExecutor(runtime_id="rt-1", agent_id="a1", subagent_id="main-1")
        mock_resp = _mk_json_response(200, {"success": False, "error": "Command timed out after 30s"})
        vmc_mock = _make_vmcontrol_mock(post_resp=mock_resp)

        with patch("tools_server.executor.internal_async_client", return_value=vmc_mock):
            result = await executor.execute("qemu_ssh_exec", {"command": "sleep 60", "timeout": 5})

        assert result["success"] is False
        assert "Command timed out" in (result.get("error") or "") or "30s" in (result.get("error") or "")
        await executor.close()

    @pytest.mark.asyncio
    async def test_qemu_status_propagates_success_false(self):
        """qemu_status: vmcontrol unavailable or error -> failure with vmcontrol in message."""
        from tools_server.executor import ToolExecutor

        executor = ToolExecutor(runtime_id="rt-1", agent_id="a1", subagent_id="main-1")
        vmc_mock = _make_vmcontrol_mock(get_resp=_mk_json_response(200, {"success": False, "error": "vmcontrol unavailable"}))

        with patch("tools_server.executor.internal_async_client", return_value=vmc_mock):
            result = await executor.execute("qemu_status", {})

        assert result["success"] is False
        assert "vmcontrol" in (result.get("error") or "").lower()
        await executor.close()

    @pytest.mark.asyncio
    async def test_qemu_start_vm_removed_from_builtin_tools(self):
        """qemu_start_vm is removed and should no longer execute as builtin."""
        from tools_server.executor import ToolExecutor

        executor = ToolExecutor(runtime_id="rt-1", agent_id="a1", subagent_id="main-1")
        result = await executor.execute("qemu_start_vm", {"memory": "4096", "cpus": 4})

        assert result["success"] is False
        assert "requires MCP client" in (result.get("error") or "")
        await executor.close()

    @pytest.mark.asyncio
    async def test_qemu_restart_vm_removed_from_builtin_tools(self):
        """qemu_restart_vm is removed and should no longer execute as builtin."""
        from tools_server.executor import ToolExecutor

        executor = ToolExecutor(runtime_id="rt-1", agent_id="a1", subagent_id="main-1")
        result = await executor.execute("qemu_restart_vm", {"graceful": True})

        assert result["success"] is False
        assert "requires MCP client" in (result.get("error") or "")
        await executor.close()

    @pytest.mark.asyncio
    async def test_qemu_shutdown_vm_removed_from_builtin_tools(self):
        """qemu_shutdown_vm is removed and should no longer execute as builtin."""
        from tools_server.executor import ToolExecutor

        executor = ToolExecutor(runtime_id="rt-1", agent_id="a1", subagent_id="main-1")
        result = await executor.execute(
            "qemu_shutdown_vm", {"graceful": True, "quick": False}
        )

        assert result["success"] is False
        assert "requires MCP client" in (result.get("error") or "")
        await executor.close()

    @pytest.mark.asyncio
    async def test_qemu_status_propagates_success_true(self):
        """qemu_status: vmcontrol returns running VM info -> success with qemu_running, qemu_pid."""
        from tools_server.executor import ToolExecutor

        executor = ToolExecutor(runtime_id="rt-1", agent_id="a1", subagent_id="main-1")
        mock_resp = _mk_json_response(200, {"status": "running", "pid": 12345})
        vmc_mock = _make_vmcontrol_mock(get_resp=mock_resp)

        with patch("tools_server.executor.internal_async_client", return_value=vmc_mock):
            result = await executor.execute("qemu_status", {})

        assert result["success"] is True
        assert result.get("qemu_running") is True
        assert result.get("qemu_pid") == 12345
        await executor.close()

    @pytest.mark.asyncio
    async def test_qemu_ssh_exec_infers_success_false_when_error_in_body(self):
        """qemu_ssh_exec: vmcontrol returns {error, success: false} -> success False, error propagated."""
        from tools_server.executor import ToolExecutor

        executor = ToolExecutor(runtime_id="rt-1", agent_id="a1", subagent_id="main-1")
        mock_resp = _mk_json_response(200, {"success": False, "error": "Legacy error format", "exit_code": 1})
        vmc_mock = _make_vmcontrol_mock(post_resp=mock_resp)

        with patch("tools_server.executor.internal_async_client", return_value=vmc_mock):
            result = await executor.execute("qemu_ssh_exec", {"command": "echo hi", "timeout": 5})

        assert result["success"] is False
        assert result.get("error") == "Legacy error format"
        await executor.close()
