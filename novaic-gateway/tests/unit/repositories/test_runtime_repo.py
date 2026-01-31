"""
Unit Tests for RuntimeRepository

Tests the agent_runtimes table operations:
- Runtime creation (main and sub)
- Phase updates
- Status queries
- Cleanup operations
"""

import pytest
import pytest_asyncio

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


class TestRuntimeCreation:
    """Tests for creating Runtimes."""
    
    @pytest.mark.asyncio
    async def test_create_main_runtime(self, runtime_repo, db_with_agent):
        """create_main_runtime creates a Main Runtime."""
        db, agent_id = db_with_agent
        runtime_repo.db = db
        
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        assert runtime is not None
        assert runtime.subagent_id.startswith("main-")
        assert runtime.agent_id == agent_id
        assert runtime.type == "main"
        assert runtime.phase == "need_think"
        assert runtime.status == "active"
        assert runtime.current_round_num == 1
    
    @pytest.mark.asyncio
    async def test_create_sub_runtime(self, runtime_repo, db_with_agent):
        """create_sub_runtime creates a SubAgent Runtime."""
        db, agent_id = db_with_agent
        runtime_repo.db = db
        
        # First create a main runtime
        main = await runtime_repo.create_main_runtime(agent_id)
        
        # Then create sub runtime
        sub = await runtime_repo.create_sub_runtime(
            agent_id=agent_id,
            parent_subagent_id=main.subagent_id,
        )
        
        assert sub.subagent_id.startswith("sub-")
        assert sub.type == "sub"
        assert sub.parent_subagent_id == main.subagent_id
    
    @pytest.mark.asyncio
    async def test_create_sub_runtime_with_context(self, runtime_repo, db_with_agent):
        """create_sub_runtime can include initial context."""
        db, agent_id = db_with_agent
        runtime_repo.db = db
        
        main = await runtime_repo.create_main_runtime(agent_id)
        
        initial_context = [
            {"role": "system", "content": "You are a sub-agent."},
            {"role": "user", "content": "Do something."},
        ]
        
        sub = await runtime_repo.create_sub_runtime(
            agent_id=agent_id,
            parent_subagent_id=main.subagent_id,
            initial_context=initial_context,
        )
        
        assert len(sub.context) == 2
        assert sub.context[0]["content"] == "You are a sub-agent."


class TestRuntimeQueries:
    """Tests for querying Runtimes."""
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, runtime_repo, db_with_agent):
        """get_by_id returns the correct Runtime."""
        db, agent_id = db_with_agent
        runtime_repo.db = db
        
        created = await runtime_repo.create_main_runtime(agent_id)
        
        fetched = await runtime_repo.get_by_id(created.subagent_id)
        
        assert fetched is not None
        assert fetched.subagent_id == created.subagent_id
    
    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_nonexistent(self, runtime_repo, db):
        """get_by_id returns None for non-existent Runtime."""
        runtime_repo.db = db
        
        fetched = await runtime_repo.get_by_id("nonexistent-id")
        
        assert fetched is None
    
    @pytest.mark.asyncio
    async def test_has_main_runtime(self, runtime_repo, db_with_agent):
        """has_main_runtime returns correct status."""
        db, agent_id = db_with_agent
        runtime_repo.db = db
        
        # Initially no main runtime
        assert await runtime_repo.has_main_runtime(agent_id) is False
        
        # Create main runtime
        await runtime_repo.create_main_runtime(agent_id)
        
        # Now should have main runtime
        assert await runtime_repo.has_main_runtime(agent_id) is True
    
    @pytest.mark.asyncio
    async def test_get_all_active_runtimes(self, runtime_repo, db_with_agent):
        """get_all_active_runtimes returns all active Runtimes."""
        db, agent_id = db_with_agent
        runtime_repo.db = db
        
        # Create multiple runtimes
        main = await runtime_repo.create_main_runtime(agent_id)
        sub1 = await runtime_repo.create_sub_runtime(agent_id, main.subagent_id)
        sub2 = await runtime_repo.create_sub_runtime(agent_id, main.subagent_id)
        
        # Mark one as completed
        await runtime_repo.mark_completed(sub1.subagent_id)
        
        actives = await runtime_repo.get_all_active_runtimes()
        
        # Should have main and sub2 (not sub1 which is completed)
        active_ids = [r.subagent_id for r in actives]
        assert main.subagent_id in active_ids
        assert sub2.subagent_id in active_ids
        assert sub1.subagent_id not in active_ids
    
    @pytest.mark.asyncio
    async def test_get_main_runtime(self, runtime_repo, db_with_agent):
        """get_main_runtime returns the Main Runtime for an agent."""
        db, agent_id = db_with_agent
        runtime_repo.db = db
        
        main = await runtime_repo.create_main_runtime(agent_id)
        
        fetched = await runtime_repo.get_main_runtime(agent_id)
        
        assert fetched is not None
        assert fetched.subagent_id == main.subagent_id


class TestRuntimeUpdates:
    """Tests for updating Runtime state."""
    
    @pytest.mark.asyncio
    async def test_update_phase(self, runtime_repo, db_with_agent):
        """update_phase changes the Runtime phase."""
        db, agent_id = db_with_agent
        runtime_repo.db = db
        
        runtime = await runtime_repo.create_main_runtime(agent_id)
        assert runtime.phase == "need_think"
        
        await runtime_repo.update_phase(runtime.subagent_id, "waiting_actions")
        
        updated = await runtime_repo.get_by_id(runtime.subagent_id)
        assert updated.phase == "waiting_actions"
    
    @pytest.mark.asyncio
    async def test_update_context(self, runtime_repo, db_with_agent):
        """update_context updates the Runtime context."""
        db, agent_id = db_with_agent
        runtime_repo.db = db
        
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        new_context = [{"role": "user", "content": "New message"}]
        await runtime_repo.update_context(runtime.subagent_id, new_context)
        
        updated = await runtime_repo.get_by_id(runtime.subagent_id)
        assert len(updated.context) == 1
        assert updated.context[0]["content"] == "New message"
    
    @pytest.mark.asyncio
    async def test_set_pending_actions(self, runtime_repo, db_with_agent):
        """set_pending_actions updates pending action list."""
        db, agent_id = db_with_agent
        runtime_repo.db = db
        
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        task_ids = ["task-1", "task-2", "task-3"]
        await runtime_repo.set_pending_actions(runtime.subagent_id, task_ids)
        
        updated = await runtime_repo.get_by_id(runtime.subagent_id)
        assert updated.pending_actions == task_ids
    
    @pytest.mark.asyncio
    async def test_advance_round(self, runtime_repo, db_with_agent):
        """advance_round increments round number."""
        db, agent_id = db_with_agent
        runtime_repo.db = db
        
        runtime = await runtime_repo.create_main_runtime(agent_id)
        assert runtime.current_round_num == 1
        
        await runtime_repo.advance_round(runtime.subagent_id)
        
        updated = await runtime_repo.get_by_id(runtime.subagent_id)
        assert updated.current_round_num == 2
        assert updated.current_round_id == "round-2"


class TestRuntimeCompletion:
    """Tests for Runtime completion/failure."""
    
    @pytest.mark.asyncio
    async def test_mark_completed(self, runtime_repo, db_with_agent):
        """mark_completed sets status to completed."""
        db, agent_id = db_with_agent
        runtime_repo.db = db
        
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        await runtime_repo.mark_completed(runtime.subagent_id)
        
        updated = await runtime_repo.get_by_id(runtime.subagent_id)
        assert updated.status == "completed"
        assert updated.phase == "completed"
    
    @pytest.mark.asyncio
    async def test_mark_failed(self, runtime_repo, db_with_agent):
        """mark_failed sets status to failed with error."""
        db, agent_id = db_with_agent
        runtime_repo.db = db
        
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        await runtime_repo.mark_failed(runtime.subagent_id, "Test error")
        
        updated = await runtime_repo.get_by_id(runtime.subagent_id)
        assert updated.status == "failed"
        assert updated.error == "Test error"
    
    @pytest.mark.asyncio
    async def test_delete(self, runtime_repo, db_with_agent):
        """delete removes the Runtime."""
        db, agent_id = db_with_agent
        runtime_repo.db = db
        
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        await runtime_repo.delete(runtime.subagent_id)
        
        fetched = await runtime_repo.get_by_id(runtime.subagent_id)
        assert fetched is None
