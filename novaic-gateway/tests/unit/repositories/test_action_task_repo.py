"""
Unit Tests for ActionTaskRepository

Tests the action_tasks table operations:
- Task creation
- Task claiming (competitive)
- Result storage
- Status queries
"""

import pytest
import pytest_asyncio

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


class TestTaskCreation:
    """Tests for creating action tasks."""
    
    @pytest.mark.asyncio
    async def test_create_task(self, action_task_repo, db_with_agent):
        """create creates a new action task."""
        db, agent_id = db_with_agent
        action_task_repo.db = db
        
        task = await action_task_repo.create(
            id="task-001",
            agent_id=agent_id,
            subagent_id="main-abc123",
            round_id="round-1",
            mcpcall_id="mc-1",
            type="tool_call",
            action="memory_write",
            args={"key": "test", "value": "data"},
        )
        
        assert task is not None
        assert task["id"] == "task-001"
        assert task["type"] == "tool_call"
        assert task["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_create_generates_idempotency_key(self, action_task_repo, db_with_agent):
        """create generates correct idempotency_key."""
        db, agent_id = db_with_agent
        action_task_repo.db = db
        
        task = await action_task_repo.create(
            id="task-002",
            agent_id=agent_id,
            subagent_id="main-abc",
            round_id="round-2",
            mcpcall_id="mc-3",
            type="tool_call",
        )
        
        expected_key = f"{agent_id}-main-abc-round-2-mc-3"
        assert task["idempotency_key"] == expected_key
    
    @pytest.mark.asyncio
    async def test_create_with_depends_on(self, action_task_repo, db_with_agent):
        """create supports depends_on field."""
        db, agent_id = db_with_agent
        action_task_repo.db = db
        
        # Create first task
        task1 = await action_task_repo.create(
            id="task-first",
            agent_id=agent_id,
            subagent_id="main-abc",
            round_id="round-1",
            mcpcall_id="mc-1",
            type="tool_call",
        )
        
        # Create dependent task
        task2 = await action_task_repo.create(
            id="task-second",
            agent_id=agent_id,
            subagent_id="main-abc",
            round_id="round-1",
            mcpcall_id="mc-2",
            type="tool_call",
            depends_on=[task1["id"]],
            status="blocked",
        )
        
        assert task2["depends_on"] == [task1["id"]]
        assert task2["status"] == "blocked"


class TestTaskRetrieval:
    """Tests for retrieving action tasks."""
    
    @pytest.mark.asyncio
    async def test_get_task(self, action_task_repo, db_with_agent):
        """get retrieves a task by ID."""
        db, agent_id = db_with_agent
        action_task_repo.db = db
        
        created = await action_task_repo.create(
            id="task-get-test",
            agent_id=agent_id,
            subagent_id="main-abc",
            round_id="round-1",
            mcpcall_id="mc-1",
            type="tool_call",
        )
        
        fetched = await action_task_repo.get("task-get-test")
        
        assert fetched is not None
        assert fetched["id"] == created["id"]
    
    @pytest.mark.asyncio
    async def test_get_returns_none_for_nonexistent(self, action_task_repo, db):
        """get returns None for non-existent task."""
        action_task_repo.db = db
        
        fetched = await action_task_repo.get("nonexistent")
        
        assert fetched is None
    
    @pytest.mark.asyncio
    async def test_get_pending_tasks(self, action_task_repo, db_with_agent):
        """get_pending_tasks returns pending tasks."""
        db, agent_id = db_with_agent
        action_task_repo.db = db
        
        subagent_id = "main-test"
        
        # Create pending task
        await action_task_repo.create(
            id="task-pending",
            agent_id=agent_id,
            subagent_id=subagent_id,
            round_id="round-1",
            mcpcall_id="mc-1",
            type="tool_call",
            status="pending",
        )
        
        # Create done task
        done = await action_task_repo.create(
            id="task-done",
            agent_id=agent_id,
            subagent_id=subagent_id,
            round_id="round-1",
            mcpcall_id="mc-2",
            type="tool_call",
            status="pending",
        )
        await action_task_repo.complete(done["id"], {"result": "done"})
        
        pending = await action_task_repo.get_pending_tasks(agent_id=agent_id)
        
        assert len(pending) == 1
        assert pending[0]["id"] == "task-pending"


class TestTaskClaiming:
    """Tests for competitive task claiming."""
    
    @pytest.mark.asyncio
    async def test_claim_task(self, action_task_repo, db_with_agent):
        """claim returns claimed task dict on success."""
        db, agent_id = db_with_agent
        action_task_repo.db = db
        
        task = await action_task_repo.create(
            id="task-claim",
            agent_id=agent_id,
            subagent_id="main-abc",
            round_id="round-1",
            mcpcall_id="mc-1",
            type="tool_call",
        )
        
        claimed = await action_task_repo.claim(task["id"], "worker-001")
        
        # claim returns the task dict on success
        assert claimed is not None
        assert claimed["id"] == task["id"]
        assert claimed["status"] == "executing"
        assert claimed["claimed_by"] == "worker-001"
    
    @pytest.mark.asyncio
    async def test_claim_fails_for_already_claimed(self, action_task_repo, db_with_agent):
        """claim returns None for already claimed task."""
        db, agent_id = db_with_agent
        action_task_repo.db = db
        
        task = await action_task_repo.create(
            id="task-double-claim",
            agent_id=agent_id,
            subagent_id="main-abc",
            round_id="round-1",
            mcpcall_id="mc-1",
            type="tool_call",
        )
        
        # First claim succeeds (returns task dict)
        first = await action_task_repo.claim(task["id"], "worker-001")
        assert first is not None
        
        # Second claim fails (returns None)
        second = await action_task_repo.claim(task["id"], "worker-002")
        assert second is None
        
        # Task still belongs to first worker
        updated = await action_task_repo.get(task["id"])
        assert updated["claimed_by"] == "worker-001"


class TestTaskCompletion:
    """Tests for completing action tasks."""
    
    @pytest.mark.asyncio
    async def test_complete_task(self, action_task_repo, db_with_agent):
        """complete marks task as done with result."""
        db, agent_id = db_with_agent
        action_task_repo.db = db
        
        task = await action_task_repo.create(
            id="task-complete",
            agent_id=agent_id,
            subagent_id="main-abc",
            round_id="round-1",
            mcpcall_id="mc-1",
            type="tool_call",
        )
        
        await action_task_repo.complete(task["id"], {"success": True, "data": "result"})
        
        updated = await action_task_repo.get(task["id"])
        assert updated["status"] == "done"
        assert updated["result"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_fail_task(self, action_task_repo, db_with_agent):
        """fail marks task as failed with error."""
        db, agent_id = db_with_agent
        action_task_repo.db = db
        
        task = await action_task_repo.create(
            id="task-fail",
            agent_id=agent_id,
            subagent_id="main-abc",
            round_id="round-1",
            mcpcall_id="mc-1",
            type="tool_call",
        )
        
        await action_task_repo.fail(task["id"], "Something went wrong")
        
        updated = await action_task_repo.get(task["id"])
        assert updated["status"] == "failed"
        assert updated["error"] == "Something went wrong"
    
    @pytest.mark.asyncio
    async def test_release_task(self, action_task_repo, db_with_agent):
        """release returns task to pending state."""
        db, agent_id = db_with_agent
        action_task_repo.db = db
        
        task = await action_task_repo.create(
            id="task-release",
            agent_id=agent_id,
            subagent_id="main-abc",
            round_id="round-1",
            mcpcall_id="mc-1",
            type="tool_call",
        )
        
        await action_task_repo.claim(task["id"], "worker-001")
        await action_task_repo.release(task["id"])
        
        updated = await action_task_repo.get(task["id"])
        assert updated["status"] == "pending"
        assert updated["claimed_by"] is None


class TestTaskQueries:
    """Tests for task query operations."""
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_round(self, action_task_repo, db_with_agent):
        """get_tasks_by_round returns tasks for specific round."""
        db, agent_id = db_with_agent
        action_task_repo.db = db
        
        # Create 3 tasks in round-1
        for i in range(3):
            await action_task_repo.create(
                id=f"task-round-{i}",
                agent_id=agent_id,
                subagent_id="main-abc",
                round_id="round-1",
                mcpcall_id=f"mc-{i}",
                type="tool_call",
            )
        
        tasks = await action_task_repo.get_tasks_by_round("main-abc", "round-1")
        
        assert len(tasks) == 3
    
    @pytest.mark.asyncio
    async def test_get_by_idempotency_key(self, action_task_repo, db_with_agent):
        """get_by_idempotency_key finds task by key."""
        db, agent_id = db_with_agent
        action_task_repo.db = db
        
        task = await action_task_repo.create(
            id="task-idem",
            agent_id=agent_id,
            subagent_id="main-xyz",
            round_id="round-5",
            mcpcall_id="mc-10",
            type="tool_call",
        )
        
        idem_key = f"{agent_id}-main-xyz-round-5-mc-10"
        found = await action_task_repo.get_by_idempotency_key(idem_key)
        
        assert found is not None
        assert found["id"] == task["id"]
