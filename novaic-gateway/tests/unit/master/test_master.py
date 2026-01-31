"""
Unit Tests for Master Component

Tests the core Master scheduler functionality:
- Runtime creation and destruction
- MCP Server lifecycle management (v2.6)
- Agent state management
- wait_runtime_complete for SubAgent execution
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


class TestMasterRuntimeCreation:
    """Tests for Master.create_main_runtime and create_sub_runtime."""
    
    @pytest_asyncio.fixture
    async def master(self, db, mock_sse_broadcaster):
        """Create a Master instance for testing."""
        with patch('mcp_gateway.manager.get_mcp_gateway_manager') as mock_gateway_mgr, \
             patch('mcp_servers.manager.get_sub_mcp_manager') as mock_sub_mcp_mgr:
            
            # Mock MCP managers
            mock_gateway_mgr.return_value = MagicMock(
                gateways={},
                add_gateway=AsyncMock(),
            )
            mock_sub_mcp_mgr.return_value = MagicMock(
                create_runtime_server=AsyncMock(),
                remove_runtime_server=AsyncMock(),
            )
            
            from master import Master, MasterConfig
            master = Master(db, mock_sse_broadcaster, MasterConfig())
            
            # Store mocks for assertions
            master._mock_gateway_mgr = mock_gateway_mgr
            master._mock_sub_mcp_mgr = mock_sub_mcp_mgr
            
            yield master
    
    @pytest.mark.asyncio
    async def test_create_main_runtime_creates_record(self, master, db_with_agent):
        """Creating a Main Runtime creates a record in agent_runtimes."""
        db, agent_id = db_with_agent
        master.db = db
        
        from db.repositories.runtime import RuntimeRepository
        master.runtime_repo = RuntimeRepository(db)
        
        runtime = await master.create_main_runtime(agent_id)
        
        assert runtime is not None
        assert runtime.subagent_id.startswith("main-")
        assert runtime.agent_id == agent_id
        assert runtime.type == "main"
        assert runtime.phase == "need_think"
    
    @pytest.mark.asyncio
    async def test_create_main_runtime_sets_agent_awake(self, master, db_with_agent):
        """Creating a Main Runtime sets the agent state to awake."""
        db, agent_id = db_with_agent
        master.db = db
        
        from db.repositories.runtime import RuntimeRepository
        from db.repositories.agent_state import AgentStateRepository
        master.runtime_repo = RuntimeRepository(db)
        master.agent_state_repo = AgentStateRepository(db)
        
        await master.create_main_runtime(agent_id)
        
        state_data = await master.agent_state_repo.get_state(agent_id)
        assert state_data["state"] == "awake"
    
    @pytest.mark.asyncio
    async def test_create_main_runtime_creates_mcp_server(self, master, db_with_agent):
        """v2.6: Creating a Main Runtime creates a Runtime MCP Server."""
        db, agent_id = db_with_agent
        master.db = db
        
        from db.repositories.runtime import RuntimeRepository
        master.runtime_repo = RuntimeRepository(db)
        
        with patch('mcp_servers.manager.get_sub_mcp_manager') as mock_mgr:
            mock_mgr.return_value = MagicMock(
                create_runtime_server=AsyncMock(),
            )
            
            runtime = await master.create_main_runtime(agent_id)
            
            # Verify MCP server was created
            mock_mgr.return_value.create_runtime_server.assert_called_once()
            call_args = mock_mgr.return_value.create_runtime_server.call_args
            assert call_args.kwargs.get('agent_id') == agent_id
            assert call_args.kwargs.get('subagent_id') == runtime.subagent_id
    
    @pytest.mark.asyncio
    async def test_create_sub_runtime_with_initial_task(self, master, db_with_agent):
        """Creating a SubAgent Runtime includes initial task in context."""
        db, agent_id = db_with_agent
        master.db = db
        
        from db.repositories.runtime import RuntimeRepository
        master.runtime_repo = RuntimeRepository(db)
        
        # First create a main runtime
        main_runtime = await master.create_main_runtime(agent_id)
        
        with patch('mcp_servers.manager.get_sub_mcp_manager') as mock_mgr:
            mock_mgr.return_value = MagicMock(create_runtime_server=AsyncMock())
            
            sub_runtime = await master.create_sub_runtime(
                agent_id=agent_id,
                parent_subagent_id=main_runtime.subagent_id,
                initial_task="Do something specific",
            )
        
        assert sub_runtime.subagent_id.startswith("sub-")
        assert sub_runtime.type == "sub"
        assert sub_runtime.parent_subagent_id == main_runtime.subagent_id
        # Check initial task is in context
        assert any("[SubAgent Task]" in msg.get("content", "") for msg in sub_runtime.context)
    
    @pytest.mark.asyncio
    async def test_create_sub_runtime_shares_context(self, master, db_with_agent):
        """SubAgent can inherit parent's context when share_context=True."""
        db, agent_id = db_with_agent
        master.db = db
        
        from db.repositories.runtime import RuntimeRepository
        master.runtime_repo = RuntimeRepository(db)
        
        # Create main runtime with some context
        main_runtime = await master.create_main_runtime(agent_id)
        main_runtime.context = [{"role": "user", "content": "Parent context"}]
        await master.runtime_repo.update_context(main_runtime.subagent_id, main_runtime.context)
        
        with patch('mcp_servers.manager.get_sub_mcp_manager') as mock_mgr:
            mock_mgr.return_value = MagicMock(create_runtime_server=AsyncMock())
            
            sub_runtime = await master.create_sub_runtime(
                agent_id=agent_id,
                parent_subagent_id=main_runtime.subagent_id,
                share_context=True,
            )
        
        # Sub should have parent's context
        assert len(sub_runtime.context) >= 1


class TestMasterRuntimeDestruction:
    """Tests for Master.destroy_runtime."""
    
    @pytest.mark.asyncio
    async def test_destroy_runtime_removes_record(self, db_with_agent):
        """Destroying a Runtime removes the database record."""
        db, agent_id = db_with_agent
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        
        # Create a runtime
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        # Verify it exists
        assert await runtime_repo.get_by_id(runtime.subagent_id) is not None
        
        # Create master and destroy
        with patch('mcp_gateway.manager.get_mcp_gateway_manager'), \
             patch('mcp_servers.manager.get_sub_mcp_manager') as mock_sub_mgr:
            mock_sub_mgr.return_value = MagicMock(remove_runtime_server=AsyncMock())
            
            from master import Master, MasterConfig
            
            master = Master(db, MagicMock(), MasterConfig())
            master.runtime_repo = runtime_repo
            
            await master.destroy_runtime(runtime.subagent_id)
        
        # Verify it's gone
        assert await runtime_repo.get_by_id(runtime.subagent_id) is None
    
    @pytest.mark.asyncio
    async def test_destroy_runtime_removes_mcp_server(self, db_with_agent):
        """v2.6: Destroying a Runtime removes its MCP Server."""
        db, agent_id = db_with_agent
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        with patch('mcp_gateway.manager.get_mcp_gateway_manager'), \
             patch('mcp_servers.manager.get_sub_mcp_manager') as mock_sub_mgr:
            mock_sub_mgr.return_value = MagicMock(remove_runtime_server=AsyncMock())
            
            from master import Master, MasterConfig
            
            master = Master(db, MagicMock(), MasterConfig())
            master.runtime_repo = runtime_repo
            
            await master.destroy_runtime(runtime.subagent_id)
            
            # Verify MCP server removal was called
            mock_sub_mgr.return_value.remove_runtime_server.assert_called_once_with(
                runtime.subagent_id
            )


class TestMasterWaitRuntimeComplete:
    """Tests for Master.wait_runtime_complete (SubAgent synchronous execution)."""
    
    @pytest.mark.asyncio
    async def test_wait_returns_success_on_completion(self, db_with_agent):
        """wait_runtime_complete returns success when Runtime completes."""
        db, agent_id = db_with_agent
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        
        # Create main runtime first (as parent)
        main_runtime = await runtime_repo.create_main_runtime(agent_id)
        
        # Create a sub runtime that will be marked complete
        runtime = await runtime_repo.create_sub_runtime(
            agent_id, main_runtime.subagent_id
        )
        
        # Mark it as completed immediately
        await runtime_repo.mark_completed(runtime.subagent_id)
        
        with patch('mcp_gateway.manager.get_mcp_gateway_manager'), \
             patch('mcp_servers.manager.get_sub_mcp_manager') as mock_sub_mgr:
            mock_sub_mgr.return_value = MagicMock(remove_runtime_server=AsyncMock())
            
            from master import Master, MasterConfig
            
            master = Master(db, MagicMock(), MasterConfig())
            master.runtime_repo = runtime_repo
            
            result = await master.wait_runtime_complete(
                runtime.subagent_id,
                timeout_seconds=5,
                poll_interval=0.1
            )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_wait_returns_error_on_failure(self, db_with_agent):
        """wait_runtime_complete returns error when Runtime fails."""
        db, agent_id = db_with_agent
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        
        # Create main runtime first (as parent)
        main_runtime = await runtime_repo.create_main_runtime(agent_id)
        
        runtime = await runtime_repo.create_sub_runtime(
            agent_id, main_runtime.subagent_id
        )
        
        # Mark it as failed
        await runtime_repo.mark_failed(runtime.subagent_id, "Test error")
        
        with patch('mcp_gateway.manager.get_mcp_gateway_manager'), \
             patch('mcp_servers.manager.get_sub_mcp_manager') as mock_sub_mgr:
            mock_sub_mgr.return_value = MagicMock(remove_runtime_server=AsyncMock())
            
            from master import Master, MasterConfig
            
            master = Master(db, MagicMock(), MasterConfig())
            master.runtime_repo = runtime_repo
            
            result = await master.wait_runtime_complete(
                runtime.subagent_id,
                timeout_seconds=5,
                poll_interval=0.1
            )
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_wait_timeout(self, db_with_agent):
        """wait_runtime_complete times out for stuck Runtimes."""
        db, agent_id = db_with_agent
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        
        # Create main runtime first (as parent)
        main_runtime = await runtime_repo.create_main_runtime(agent_id)
        
        # Create a runtime that never completes
        runtime = await runtime_repo.create_sub_runtime(
            agent_id, main_runtime.subagent_id
        )
        
        with patch('mcp_gateway.manager.get_mcp_gateway_manager'), \
             patch('mcp_servers.manager.get_sub_mcp_manager') as mock_sub_mgr:
            mock_sub_mgr.return_value = MagicMock(remove_runtime_server=AsyncMock())
            
            from master import Master, MasterConfig
            
            master = Master(db, MagicMock(), MasterConfig())
            master.runtime_repo = runtime_repo
            
            result = await master.wait_runtime_complete(
                runtime.subagent_id,
                timeout_seconds=1,  # Short timeout
                poll_interval=0.1
            )
        
        assert result["success"] is False
        assert "timed out" in result.get("error", "").lower() or "timeout" in result.get("error", "").lower()


class TestMasterAgentState:
    """Tests for agent state management."""
    
    @pytest.mark.asyncio
    async def test_set_agent_awake(self, db_with_agent):
        """Master.set_agent_awake sets state to awake."""
        db, agent_id = db_with_agent
        
        from db.repositories.agent_state import AgentStateRepository
        state_repo = AgentStateRepository(db)
        
        with patch('mcp_gateway.manager.get_mcp_gateway_manager'), \
             patch('mcp_servers.manager.get_sub_mcp_manager'):
            
            from master import Master, MasterConfig
            
            master = Master(db, MagicMock(), MasterConfig())
            master.agent_state_repo = state_repo
            
            await master.set_agent_awake(agent_id)
            
            state_data = await state_repo.get_state(agent_id)
            assert state_data["state"] == "awake"
    
    @pytest.mark.asyncio
    async def test_set_agent_sleep(self, db_with_agent):
        """Master.set_agent_sleep sets state to sleep."""
        db, agent_id = db_with_agent
        
        from db.repositories.agent_state import AgentStateRepository
        state_repo = AgentStateRepository(db)
        
        # First set to awake
        await state_repo.set_state(agent_id, "awake")
        
        with patch('mcp_gateway.manager.get_mcp_gateway_manager'), \
             patch('mcp_servers.manager.get_sub_mcp_manager'):
            
            from master import Master, MasterConfig
            
            master = Master(db, MagicMock(), MasterConfig())
            master.agent_state_repo = state_repo
            
            await master.set_agent_sleep(agent_id)
            
            state_data = await state_repo.get_state(agent_id)
            assert state_data["state"] == "sleep"
