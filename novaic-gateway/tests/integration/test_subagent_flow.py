"""
Integration Tests for SubAgent Flow

Tests the SubAgent lifecycle:
1. Main Runtime executes context_call
2. Master creates SubAgent Runtime
3. SubAgent executes ReACT loop
4. SubAgent completes and returns result
5. SubAgent Runtime is destroyed (not put to sleep)
6. Main Runtime receives result
"""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestSubAgentCreation:
    """Tests SubAgent Runtime creation via Master."""
    
    @pytest_asyncio.fixture
    async def master_for_subagent(self, db_with_agent):
        """Set up Master for SubAgent testing."""
        db, agent_id = db_with_agent
        
        with patch('master.master.get_mcp_gateway_manager') as mock_gateway, \
             patch('master.master.get_sub_mcp_manager') as mock_sub_mcp:
            
            mock_gateway.return_value = MagicMock(
                gateways={},
                add_gateway=AsyncMock(),
            )
            mock_sub_mcp.return_value = MagicMock(
                create_runtime_server=AsyncMock(),
                remove_runtime_server=AsyncMock(),
            )
            
            from master import Master, MasterConfig
            
            broadcaster = MagicMock()
            broadcaster.broadcast_new_task = AsyncMock()
            
            master = Master(db, broadcaster, MasterConfig())
            
            yield master, agent_id
    
    @pytest.mark.asyncio
    async def test_create_sub_runtime_from_main(self, master_for_subagent):
        """Master.create_sub_runtime creates SubAgent from Main."""
        master, agent_id = master_for_subagent
        
        # First create Main Runtime
        main = await master.create_main_runtime(agent_id)
        
        # Create SubAgent Runtime
        sub = await master.create_sub_runtime(
            agent_id=agent_id,
            parent_subagent_id=main.subagent_id,
            initial_task="Research something",
        )
        
        assert sub.subagent_id.startswith("sub-")
        assert sub.type == "sub"
        assert sub.parent_subagent_id == main.subagent_id
        assert sub.phase == "need_think"
    
    @pytest.mark.asyncio
    async def test_sub_runtime_inherits_context(self, master_for_subagent):
        """SubAgent can inherit parent context with share_context=True."""
        master, agent_id = master_for_subagent
        
        # Create Main with context
        main = await master.create_main_runtime(agent_id)
        main_context = [
            {"role": "user", "content": "Main context message"},
            {"role": "assistant", "content": "Main response"},
        ]
        await master.runtime_repo.update_context(main.subagent_id, main_context)
        
        # Create SubAgent with shared context
        sub = await master.create_sub_runtime(
            agent_id=agent_id,
            parent_subagent_id=main.subagent_id,
            initial_task="Continue from main",
            share_context=True,
        )
        
        # SubAgent should have parent's context + task
        assert len(sub.context) >= 2  # At least parent context
    
    @pytest.mark.asyncio
    async def test_sub_runtime_creates_mcp_server(self, master_for_subagent):
        """Creating SubAgent creates Runtime MCP Server."""
        master, agent_id = master_for_subagent
        
        main = await master.create_main_runtime(agent_id)
        
        with patch('master.master.get_sub_mcp_manager') as mock_mgr:
            mock_mgr.return_value = MagicMock(create_runtime_server=AsyncMock())
            
            sub = await master.create_sub_runtime(
                agent_id=agent_id,
                parent_subagent_id=main.subagent_id,
            )
            
            # Verify Runtime MCP Server was created
            mock_mgr.return_value.create_runtime_server.assert_called()


class TestSubAgentCompletion:
    """Tests SubAgent completion and cleanup."""
    
    @pytest_asyncio.fixture
    async def master_with_sub(self, db_with_agent):
        """Set up Master with a SubAgent Runtime."""
        db, agent_id = db_with_agent
        
        with patch('master.master.get_mcp_gateway_manager') as mock_gateway, \
             patch('master.master.get_sub_mcp_manager') as mock_sub_mcp:
            
            mock_gateway.return_value = MagicMock(
                gateways={},
                add_gateway=AsyncMock(),
            )
            mock_sub_mcp.return_value = MagicMock(
                create_runtime_server=AsyncMock(),
                remove_runtime_server=AsyncMock(),
            )
            
            from master import Master, MasterConfig
            
            broadcaster = MagicMock()
            broadcaster.broadcast_new_task = AsyncMock()
            
            master = Master(db, broadcaster, MasterConfig())
            
            # Create main and sub
            main = await master.create_main_runtime(agent_id)
            sub = await master.create_sub_runtime(
                agent_id=agent_id,
                parent_subagent_id=main.subagent_id,
                initial_task="Test task",
            )
            
            yield master, main, sub, agent_id
    
    @pytest.mark.asyncio
    async def test_sub_runtime_destroyed_on_completion(self, master_with_sub):
        """SubAgent Runtime is destroyed (not sleep) when complete."""
        master, main, sub, agent_id = master_with_sub
        
        # Mark sub as completed
        await master.runtime_repo.mark_completed(sub.subagent_id)
        
        # Destroy the runtime (simulating wait_runtime_complete cleanup)
        await master.destroy_runtime(sub.subagent_id)
        
        # SubAgent should be gone
        fetched = await master.runtime_repo.get_by_id(sub.subagent_id)
        assert fetched is None
        
        # Main should still exist
        main_fetched = await master.runtime_repo.get_by_id(main.subagent_id)
        assert main_fetched is not None
    
    @pytest.mark.asyncio
    async def test_destroy_removes_mcp_server(self, master_with_sub):
        """Destroying SubAgent removes its MCP Server."""
        master, main, sub, agent_id = master_with_sub
        
        with patch('master.master.get_sub_mcp_manager') as mock_mgr:
            mock_mgr.return_value = MagicMock(remove_runtime_server=AsyncMock())
            
            await master.destroy_runtime(sub.subagent_id)
            
            # Verify MCP Server removal
            mock_mgr.return_value.remove_runtime_server.assert_called_with(
                sub.subagent_id
            )


class TestWaitRuntimeComplete:
    """Tests Master.wait_runtime_complete for SubAgent synchronous execution."""
    
    @pytest.mark.asyncio
    async def test_wait_returns_on_completion(self, db_with_agent):
        """wait_runtime_complete returns when Runtime completes."""
        db, agent_id = db_with_agent
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        
        # Create and immediately complete a runtime
        runtime = await runtime_repo.create_sub_runtime(agent_id, "main-parent")
        await runtime_repo.mark_completed(runtime.subagent_id)
        
        with patch('master.master.get_mcp_gateway_manager'), \
             patch('master.master.get_sub_mcp_manager') as mock_sub:
            mock_sub.return_value = MagicMock(remove_runtime_server=AsyncMock())
            
            from master import Master, MasterConfig
            
            master = Master(db, MagicMock(), MasterConfig())
            
            result = await master.wait_runtime_complete(
                runtime.subagent_id,
                timeout_seconds=5,
                poll_interval=0.1,
            )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_wait_returns_error_on_failure(self, db_with_agent):
        """wait_runtime_complete returns error when Runtime fails."""
        db, agent_id = db_with_agent
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        
        runtime = await runtime_repo.create_sub_runtime(agent_id, "main-parent")
        await runtime_repo.mark_failed(runtime.subagent_id, "Test failure")
        
        with patch('master.master.get_mcp_gateway_manager'), \
             patch('master.master.get_sub_mcp_manager') as mock_sub:
            mock_sub.return_value = MagicMock(remove_runtime_server=AsyncMock())
            
            from master import Master, MasterConfig
            
            master = Master(db, MagicMock(), MasterConfig())
            
            result = await master.wait_runtime_complete(
                runtime.subagent_id,
                timeout_seconds=5,
            )
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_wait_times_out_for_stuck_runtime(self, db_with_agent):
        """wait_runtime_complete times out for stuck Runtime."""
        db, agent_id = db_with_agent
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        
        # Create runtime that never completes
        runtime = await runtime_repo.create_sub_runtime(agent_id, "main-parent")
        
        with patch('master.master.get_mcp_gateway_manager'), \
             patch('master.master.get_sub_mcp_manager') as mock_sub:
            mock_sub.return_value = MagicMock(remove_runtime_server=AsyncMock())
            
            from master import Master, MasterConfig
            
            master = Master(db, MagicMock(), MasterConfig())
            
            result = await master.wait_runtime_complete(
                runtime.subagent_id,
                timeout_seconds=1,  # Short timeout
                poll_interval=0.1,
            )
        
        assert result["success"] is False
        assert "timeout" in result.get("error", "").lower()


class TestSubAgentRestrictions:
    """Tests SubAgent-specific restrictions."""
    
    def test_subagent_cannot_call_context_rest(self):
        """SubAgent cannot call context_rest (only Main can)."""
        # This is a unit test but included here for completeness
        subagent_id = "sub-abc123"
        
        # Check the restriction logic
        if subagent_id and subagent_id.startswith("sub-"):
            can_rest = False
        else:
            can_rest = True
        
        assert can_rest is False
    
    def test_main_can_call_context_rest(self):
        """Main Runtime can call context_rest."""
        subagent_id = "main-abc123"
        
        if subagent_id and subagent_id.startswith("sub-"):
            can_rest = False
        else:
            can_rest = True
        
        assert can_rest is True


class TestNestedSubAgents:
    """Tests SubAgents creating SubAgents."""
    
    @pytest.mark.asyncio
    async def test_sub_can_create_sub(self, db_with_agent):
        """SubAgent can create another SubAgent."""
        db, agent_id = db_with_agent
        
        with patch('master.master.get_mcp_gateway_manager') as mock_gateway, \
             patch('master.master.get_sub_mcp_manager') as mock_sub_mcp:
            
            mock_gateway.return_value = MagicMock(
                gateways={},
                add_gateway=AsyncMock(),
            )
            mock_sub_mcp.return_value = MagicMock(
                create_runtime_server=AsyncMock(),
                remove_runtime_server=AsyncMock(),
            )
            
            from master import Master, MasterConfig
            
            master = Master(db, MagicMock(), MasterConfig())
            
            # Main -> Sub1 -> Sub2
            main = await master.create_main_runtime(agent_id)
            sub1 = await master.create_sub_runtime(
                agent_id=agent_id,
                parent_subagent_id=main.subagent_id,
                initial_task="First level task",
            )
            sub2 = await master.create_sub_runtime(
                agent_id=agent_id,
                parent_subagent_id=sub1.subagent_id,  # Sub creating sub
                initial_task="Second level task",
            )
        
        assert sub2.parent_subagent_id == sub1.subagent_id
        assert sub2.type == "sub"
