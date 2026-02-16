"""
Unit tests for tools_server executor QEMU tool handling with unified internal contract.

Unified contract: operation failures return HTTP 200 with {success: false, error};
4xx may still indicate not-found/validation. Executor must interpret body, not just HTTP status.
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


class TestExecutorQemuUnifiedContract:
    """Verify executor handles unified QEMU contract (success:false, error propagation)."""

    @pytest.mark.asyncio
    async def test_qemu_ssh_exec_propagates_success_false(self):
        """qemu_ssh_exec: 200 + {success: false, error} is returned as failure with error."""
        from tools_server.executor import ToolExecutor

        executor = ToolExecutor(runtime_id="rt-1", agent_id="a1", subagent_id="main-1")
        mock_resp = _mk_json_response(200, {"success": False, "error": "Command timed out after 30s"})

        with patch.object(executor, "_get_http_client", new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.is_closed = False
            mock_get_client.return_value = mock_client

            result = await executor.execute("qemu_ssh_exec", {"command": "sleep 60", "timeout": 5})

        assert result["success"] is False
        assert result.get("error") == "Command timed out after 30s"
        await executor.close()

    @pytest.mark.asyncio
    async def test_qemu_status_propagates_success_false(self):
        """qemu_status: 200 + {success: false, error} is returned as failure."""
        from tools_server.executor import ToolExecutor

        executor = ToolExecutor(runtime_id="rt-1", agent_id="a1", subagent_id="main-1")
        mock_resp = _mk_json_response(200, {"success": False, "error": "vmcontrol unavailable"})

        with patch.object(executor, "_get_http_client", new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.is_closed = False
            mock_get_client.return_value = mock_client

            result = await executor.execute("qemu_status", {})

        assert result["success"] is False
        assert result.get("error") == "vmcontrol unavailable"
        await executor.close()

    @pytest.mark.asyncio
    async def test_qemu_start_vm_propagates_success_false(self):
        """qemu_start_vm: 200 + {success: false, error} is returned as failure."""
        from tools_server.executor import ToolExecutor

        executor = ToolExecutor(runtime_id="rt-1", agent_id="a1", subagent_id="main-1")
        mock_resp = _mk_json_response(200, {"success": False, "error": "Image path not found"})

        with patch.object(executor, "_get_http_client", new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.is_closed = False
            mock_get_client.return_value = mock_client

            result = await executor.execute("qemu_start_vm", {"memory": "4096", "cpus": 4})

        assert result["success"] is False
        assert result.get("error") == "Image path not found"
        await executor.close()

    @pytest.mark.asyncio
    async def test_qemu_restart_vm_propagates_success_false(self):
        """qemu_restart_vm: 200 + {success: false, error} is returned as failure."""
        from tools_server.executor import ToolExecutor

        executor = ToolExecutor(runtime_id="rt-1", agent_id="a1", subagent_id="main-1")
        mock_resp = _mk_json_response(200, {"success": False, "error": "VM stop failed"})

        with patch.object(executor, "_get_http_client", new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.is_closed = False
            mock_get_client.return_value = mock_client

            result = await executor.execute("qemu_restart_vm", {"graceful": True})

        assert result["success"] is False
        assert result.get("error") == "VM stop failed"
        await executor.close()

    @pytest.mark.asyncio
    async def test_qemu_shutdown_vm_propagates_success_false(self):
        """qemu_shutdown_vm: 200 + {success: false, error} is returned as failure."""
        from tools_server.executor import ToolExecutor

        executor = ToolExecutor(runtime_id="rt-1", agent_id="a1", subagent_id="main-1")
        mock_resp = _mk_json_response(200, {"success": False, "error": "QMP connection failed"})

        with patch.object(executor, "_get_http_client", new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.is_closed = False
            mock_get_client.return_value = mock_client

            result = await executor.execute("qemu_shutdown_vm", {"graceful": True, "quick": False})

        assert result["success"] is False
        assert result.get("error") == "QMP connection failed"
        await executor.close()

    @pytest.mark.asyncio
    async def test_qemu_status_propagates_success_true(self):
        """qemu_status: 200 + {success: true, ...} is returned as success."""
        from tools_server.executor import ToolExecutor

        executor = ToolExecutor(runtime_id="rt-1", agent_id="a1", subagent_id="main-1")
        mock_resp = _mk_json_response(200, {
            "success": True,
            "qemu_running": True,
            "qemu_pid": 12345,
            "ports": {"ssh": 20000},
            "agent_id": "a1",
        })

        with patch.object(executor, "_get_http_client", new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.is_closed = False
            mock_get_client.return_value = mock_client

            result = await executor.execute("qemu_status", {})

        assert result["success"] is True
        assert result.get("qemu_running") is True
        assert result.get("qemu_pid") == 12345
        await executor.close()

    @pytest.mark.asyncio
    async def test_handle_response_infers_success_false_when_error_present(self):
        """_handle_response: body with error but no success -> success inferred as False."""
        from tools_server.executor import ToolExecutor

        executor = ToolExecutor(runtime_id="rt-1", agent_id="a1", subagent_id="main-1")
        # Legacy/edge case: backend returns {error: "x"} without explicit success
        mock_resp = _mk_json_response(200, {"error": "Legacy error format"})

        with patch.object(executor, "_get_http_client", new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.is_closed = False
            mock_get_client.return_value = mock_client

            result = await executor.execute("qemu_ssh_exec", {"command": "echo hi", "timeout": 5})

        assert result["success"] is False
        assert result.get("error") == "Legacy error format"
        await executor.close()
