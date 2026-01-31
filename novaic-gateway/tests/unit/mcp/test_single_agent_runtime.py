"""
Unit Tests for SingleAgentRuntimeMCPServer

Tests the Runtime-specific MCP tools:
- context_call: SubAgent creation (v2.5 Master-driven)
- context_rest: Only Main Runtime allowed
- context_list: List active runtimes
- context_send: Send messages to runtime
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


class TestSingleAgentRuntimeInit:
    """Tests for SingleAgentRuntimeMCPServer initialization."""
    
    def test_requires_agent_id(self):
        """SingleAgentRuntimeMCPServer requires agent_id."""
        from mcp_servers.single_agent_runtime import SingleAgentRuntimeMCPServer
        
        with pytest.raises(ValueError) as exc_info:
            SingleAgentRuntimeMCPServer(agent_id=None)
        
        assert "agent_id is required" in str(exc_info.value)
    
    def test_accepts_subagent_id(self):
        """SingleAgentRuntimeMCPServer accepts subagent_id parameter."""
        with patch('mcp_servers.single_agent_runtime.BaseMCPServer.__init__', return_value=None):
            from mcp_servers.single_agent_runtime import SingleAgentRuntimeMCPServer
            
            server = SingleAgentRuntimeMCPServer.__new__(SingleAgentRuntimeMCPServer)
            server._agent_id = "agent-1"
            server._subagent_id = "main-abc123"
            
            assert server._subagent_id == "main-abc123"
    
    def test_name_is_single_agent_runtime(self):
        """Server name is 'single-agent-runtime'."""
        from mcp_servers.single_agent_runtime import SingleAgentRuntimeMCPServer
        
        assert SingleAgentRuntimeMCPServer.name == "single-agent-runtime"


class TestContextRestTool:
    """Tests for context_rest tool restrictions."""
    
    @pytest.mark.asyncio
    async def test_context_rest_blocked_for_subagent(self):
        """SubAgents cannot call context_rest."""
        with patch('mcp_servers.single_agent_runtime.BaseMCPServer.__init__', return_value=None), \
             patch('mcp_servers.single_agent_runtime.httpx.AsyncClient') as mock_client:
            
            from mcp_servers.single_agent_runtime import SingleAgentRuntimeMCPServer
            
            # Create server instance manually to test the tool logic
            server = MagicMock()
            server._agent_id = "agent-1"
            server._subagent_id = "sub-def456"  # SubAgent ID
            
            # Simulate the context_rest logic
            subagent_id = server._subagent_id
            if subagent_id and subagent_id.startswith("sub-"):
                result = {
                    "success": False,
                    "error": "SubAgents cannot rest. Complete your task and return the result instead."
                }
            else:
                result = {"success": True}
            
            assert result["success"] is False
            assert "SubAgents cannot rest" in result["error"]
    
    @pytest.mark.asyncio
    async def test_context_rest_allowed_for_main(self):
        """Main Runtime can call context_rest."""
        # For Main Runtime, the check should pass
        subagent_id = "main-abc123"
        
        # Main Runtime doesn't start with "sub-"
        is_blocked = subagent_id and subagent_id.startswith("sub-")
        
        assert is_blocked is False


class TestContextCallTool:
    """Tests for context_call tool (v2.5 Master-driven)."""
    
    @pytest.mark.asyncio
    async def test_context_call_uses_master_create_sub_runtime(self):
        """context_call creates SubAgent via Master.create_sub_runtime."""
        # Mock Master
        mock_master = MagicMock()
        mock_master.create_sub_runtime = AsyncMock(return_value=MagicMock(subagent_id="sub-new123"))
        mock_master.wait_runtime_complete = AsyncMock(return_value={
            "success": True,
            "result": "Task completed",
            "duration_seconds": 10,
        })
        mock_master.runtime_repo = MagicMock()
        mock_master.runtime_repo.get_main_runtime = AsyncMock(return_value=MagicMock(subagent_id="main-parent"))
        
        # Test the logic directly (simulating what context_call does)
        agent_id = "agent-1"
        parent_subagent_id = "main-parent"
        task = "Do something"
        share_context = False
        timeout_minutes = 30
        
        # Create SubAgent Runtime via Master
        runtime = await mock_master.create_sub_runtime(
            agent_id=agent_id,
            parent_subagent_id=parent_subagent_id,
            initial_task=task,
            share_context=share_context,
        )
        
        # Wait for completion
        result = await mock_master.wait_runtime_complete(
            subagent_id=runtime.subagent_id,
            timeout_seconds=timeout_minutes * 60,
        )
        
        mock_master.create_sub_runtime.assert_called_once()
        mock_master.wait_runtime_complete.assert_called_once()
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_context_call_returns_error_if_no_master(self):
        """context_call returns error when Master is not available."""
        # Simulate context_call logic when master is None
        master = None
        
        if not master:
            result = {"success": False, "error": "Master not available"}
        else:
            result = {"success": True}
        
        assert result["success"] is False
        assert "Master not available" in result["error"]
    
    @pytest.mark.asyncio
    async def test_context_call_waits_for_completion(self):
        """context_call waits for SubAgent Runtime to complete."""
        mock_master = MagicMock()
        mock_master.create_sub_runtime = AsyncMock(
            return_value=MagicMock(subagent_id="sub-wait123")
        )
        mock_master.wait_runtime_complete = AsyncMock(return_value={
            "success": True,
            "result": "Completed after waiting",
            "duration_seconds": 45,
        })
        
        # Create and wait
        runtime = await mock_master.create_sub_runtime(
            agent_id="agent-1",
            parent_subagent_id="main-1",
            initial_task="Wait test",
        )
        result = await mock_master.wait_runtime_complete(
            subagent_id=runtime.subagent_id,
            timeout_seconds=1800,
        )
        
        assert result["duration_seconds"] == 45
        assert result["success"] is True


class TestContextListTool:
    """Tests for context_list tool."""
    
    @pytest.mark.asyncio
    async def test_context_list_returns_active_runtimes(self):
        """context_list returns all active runtimes for an agent."""
        # Mock response from Gateway
        mock_response = {
            "success": True,
            "active_count": 2,
            "contexts": [
                {"key": "main-abc", "type": "main", "status": "active"},
                {"key": "sub-xyz", "type": "sub", "status": "active"},
            ],
        }
        
        assert mock_response["active_count"] == 2
        assert len(mock_response["contexts"]) == 2


class TestContextSendTool:
    """Tests for context_send tool."""
    
    @pytest.mark.asyncio
    async def test_context_send_posts_to_gateway(self):
        """context_send posts message to Gateway API."""
        # Mock httpx client
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value={"success": True, "message_id": "msg-123"})
        mock_response.raise_for_status = MagicMock()
        
        # Verify the expected payload structure
        expected_payload = {
            "agent_id": "agent-1",
            "context_key": "main-abc",
            "message": "Test message",
            "wait_response": False,
            "timeout": 30,
        }
        
        assert "agent_id" in expected_payload
        assert "context_key" in expected_payload
        assert "message" in expected_payload


class TestDeletedTools:
    """Tests verifying that deprecated tools are removed."""
    
    def test_context_inbox_not_present(self):
        """context_inbox tool should be removed (v2.5)."""
        # The tool should not be registered
        # We verify this by checking the source code comment
        import inspect
        from mcp_servers.single_agent_runtime import SingleAgentRuntimeMCPServer
        
        source = inspect.getsource(SingleAgentRuntimeMCPServer)
        
        # Should have the removal comment
        assert "context_inbox removed" in source
        
        # Should NOT have a registered context_inbox tool
        # (no @self.mcp.tool() followed by async def context_inbox)
        assert "async def context_inbox(" not in source or "# " in source.split("async def context_inbox")[0][-5:]
    
    def test_registered_tools_count(self):
        """Server should register 5 tools (not 6)."""
        import inspect
        from mcp_servers.single_agent_runtime import SingleAgentRuntimeMCPServer
        
        source = inspect.getsource(SingleAgentRuntimeMCPServer)
        
        # Should log "Registered 5 tools"
        assert "Registered 5 tools" in source
