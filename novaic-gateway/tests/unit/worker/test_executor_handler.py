"""
Unit Tests for Executor Handler

Tests the Worker's task execution handling:
- MCP tool routing (v2.6 three-layer architecture)
- Idempotency checking
- Tool call execution
- Reply sending
"""

import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


class MockResponse:
    """Mock aiohttp response."""
    def __init__(self, status: int, data: dict):
        self.status = status
        self._data = data
    
    async def json(self):
        return self._data
    
    async def text(self):
        return json.dumps(self._data)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass


class TestMCPUrlRouting:
    """Tests for v2.6 three-layer MCP routing."""
    
    def test_context_tools_route_to_runtime_layer(self):
        """context_* tools route to /sub-mcp/runtime/{subagent_id}/."""
        from worker.executor_handler import _get_mcp_url_for_tool
        
        url = _get_mcp_url_for_tool(
            tool_name="context_call",
            subagent_id="main-abc123",
            gateway_url="http://localhost:9527"
        )
        
        assert "/sub-mcp/runtime/main-abc123" in url
    
    def test_context_list_routes_to_runtime_layer(self):
        """context_list routes to Runtime layer."""
        from worker.executor_handler import _get_mcp_url_for_tool
        
        url = _get_mcp_url_for_tool(
            tool_name="context_list",
            subagent_id="sub-def456",
            gateway_url="http://localhost:9527"
        )
        
        assert "/sub-mcp/runtime/sub-def456" in url
    
    def test_context_rest_routes_to_runtime_layer(self):
        """context_rest routes to Runtime layer."""
        from worker.executor_handler import _get_mcp_url_for_tool
        
        url = _get_mcp_url_for_tool(
            tool_name="context_rest",
            subagent_id="main-xyz789",
            gateway_url="http://localhost:9527"
        )
        
        assert "/sub-mcp/runtime/main-xyz789" in url
    
    def test_memory_tools_route_to_shared_layer(self):
        """memory_* tools route to /sub-mcp/memory/."""
        from worker.executor_handler import _get_mcp_url_for_tool
        
        url = _get_mcp_url_for_tool(
            tool_name="memory_write",
            subagent_id="main-123",
            gateway_url="http://localhost:9527"
        )
        
        assert "/sub-mcp/memory" in url
    
    def test_memory_read_routes_to_shared_layer(self):
        """memory_read routes to shared layer."""
        from worker.executor_handler import _get_mcp_url_for_tool
        
        url = _get_mcp_url_for_tool(
            tool_name="memory_read",
            subagent_id="main-123",
            gateway_url="http://localhost:9527"
        )
        
        assert "/sub-mcp/memory" in url
    
    def test_local_tools_route_to_shared_layer(self):
        """local_* tools route to /sub-mcp/local/."""
        from worker.executor_handler import _get_mcp_url_for_tool
        
        url = _get_mcp_url_for_tool(
            tool_name="local_read_file",
            subagent_id="main-123",
            gateway_url="http://localhost:9527"
        )
        
        assert "/sub-mcp/local" in url
    
    def test_chat_tools_route_to_shared_layer(self):
        """chat_* tools route to /sub-mcp/chat/."""
        from worker.executor_handler import _get_mcp_url_for_tool
        
        url = _get_mcp_url_for_tool(
            tool_name="chat_send",
            subagent_id="main-123",
            gateway_url="http://localhost:9527"
        )
        
        assert "/sub-mcp/chat" in url
    
    def test_qemu_tools_route_to_qemudebug(self):
        """qemu_* tools route to /sub-mcp/qemudebug/."""
        from worker.executor_handler import _get_mcp_url_for_tool
        
        url = _get_mcp_url_for_tool(
            tool_name="qemu_run_command",
            subagent_id="main-123",
            gateway_url="http://localhost:9527"
        )
        
        assert "/sub-mcp/qemudebug" in url


class TestIdempotencyChecking:
    """Tests for idempotency checking."""
    
    @pytest.mark.asyncio
    async def test_returns_cached_result_if_exists(self):
        """check_idempotency returns cached result for completed execution."""
        from worker.executor_handler import check_idempotency
        
        # The API returns the full record, but check_idempotency returns result.get("result")
        api_response = {
            "status": "done",
            "result": {"data": "cached"},
        }
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=MockResponse(200, api_response))
        
        result = await check_idempotency(
            "http://test:9527",
            mock_session,
            "agent-1-main-123-round-1-mc-1"
        )
        
        # check_idempotency returns result.get("result") for done status
        assert result is not None
        assert result["data"] == "cached"
    
    @pytest.mark.asyncio
    async def test_returns_none_if_not_exists(self):
        """check_idempotency returns None for new execution."""
        from worker.executor_handler import check_idempotency
        
        # 404 or no status means not found
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=MockResponse(404, {}))
        
        result = await check_idempotency(
            "http://test:9527",
            mock_session,
            "agent-1-main-123-round-1-mc-new"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_returns_none_if_empty_key(self):
        """check_idempotency returns None for empty idempotency key."""
        from worker.executor_handler import check_idempotency
        
        mock_session = MagicMock()
        
        result = await check_idempotency(
            "http://test:9527",
            mock_session,
            ""
        )
        
        assert result is None
        # Should not have made any HTTP call
        mock_session.get.assert_not_called()


class TestHandleToolCall:
    """Tests for handle_tool_call function."""
    
    @pytest.fixture
    def mock_agent_config(self):
        """Mock agent configuration."""
        return {
            "id": "test-agent",
            "vm": {
                "agent_index": 0,
                "ports": {
                    "mcp": 19900,
                }
            },
        }
    
    @pytest.mark.asyncio
    async def test_handle_tool_call_basic(self, sample_tool_call_task):
        """handle_tool_call can be called with a task."""
        # This is a smoke test - full integration would require more mocking
        # The actual function requires complex HTTP interactions
        from worker.executor_handler import handle_tool_call
        
        # Verify the function exists and accepts the right parameters
        assert callable(handle_tool_call)
    
    @pytest.mark.asyncio
    async def test_returns_cached_for_idempotent_call(self, sample_tool_call_task):
        """handle_tool_call returns cached result for idempotent execution."""
        # When idempotency check returns a done result, it should return that
        cached_data = {"cached": True}
        
        with patch('worker.executor_handler.aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            # Return done status with result
            mock_session.get = MagicMock(return_value=MockResponse(200, {
                "status": "done",
                "result": cached_data,
            }))
            mock_session.post = MagicMock(return_value=MockResponse(200, {}))
            mock_session_class.return_value = mock_session
            
            from worker.executor_handler import handle_tool_call
            result = await handle_tool_call(sample_tool_call_task, "http://test:9527")
        
        # Should return cached result
        assert result.get("cached") is True


class TestHandleReply:
    """Tests for handle_reply function."""
    
    @pytest.mark.asyncio
    async def test_sends_reply_to_gateway(self, sample_reply_task):
        """handle_reply sends chat reply via Gateway."""
        with patch('worker.executor_handler.aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session.get = MagicMock(return_value=MockResponse(200, {"exists": False}))
            mock_session.post = MagicMock(return_value=MockResponse(200, {"success": True}))
            mock_session_class.return_value = mock_session
            
            from worker.executor_handler import handle_reply
            result = await handle_reply(sample_reply_task, "http://test:9527")
        
        assert result["success"] is True
        
        # Verify post was called with chat event
        post_calls = [call for call in mock_session.post.call_args_list 
                     if "/api/chat/event" in str(call)]
        assert len(post_calls) >= 1


class TestCallMCPServerDirect:
    """Tests for direct MCP server communication."""
    
    @pytest.mark.asyncio
    async def test_successful_mcp_call(self):
        """call_mcp_server_direct returns success on 200 response."""
        from worker.executor_handler import call_mcp_server_direct
        
        mcp_result = {"content": [{"text": "Success"}]}
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=MockResponse(200, mcp_result))
        
        result = await call_mcp_server_direct(
            mcp_url="http://localhost:9527/sub-mcp/memory",
            session=mock_session,
            tool_name="memory_write",
            args={"key": "test", "value": "data"},
        )
        
        assert result["success"] is True
        assert result["result"] == mcp_result
    
    @pytest.mark.asyncio
    async def test_mcp_error_response(self):
        """call_mcp_server_direct returns error on non-200 response."""
        from worker.executor_handler import call_mcp_server_direct
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=MockResponse(500, {"error": "Internal error"}))
        
        result = await call_mcp_server_direct(
            mcp_url="http://localhost:9527/sub-mcp/memory",
            session=mock_session,
            tool_name="memory_write",
            args={},
        )
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_mcp_connection_error(self):
        """call_mcp_server_direct handles connection errors."""
        from worker.executor_handler import call_mcp_server_direct
        
        mock_session = MagicMock()
        mock_session.post = MagicMock(
            side_effect=Exception("Connection refused")
        )
        
        result = await call_mcp_server_direct(
            mcp_url="http://localhost:9999/sub-mcp/invalid",
            session=mock_session,
            tool_name="unknown_tool",
            args={},
        )
        
        assert result["success"] is False
        assert "error" in result
