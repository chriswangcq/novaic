"""
Unit Tests for Scheduler Component

Tests the ReACT loop scheduling:
- Phase transitions (need_think -> waiting_actions -> completed)
- Think task creation
- Context preparation with inbox messages
- Round advancement and completion logic
"""

import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


class TestSchedulerPhaseNeedThink:
    """Tests for Scheduler._handle_need_think phase."""
    
    @pytest_asyncio.fixture
    async def scheduler_with_runtime(self, db_with_agent):
        """Create Scheduler with a runtime in need_think phase."""
        db, agent_id = db_with_agent
        
        # Create mock Master
        mock_master = MagicMock()
        mock_master.db = db
        mock_master.broadcast_new_task = AsyncMock()
        
        from db.repositories.runtime import RuntimeRepository
        mock_master.runtime_repo = RuntimeRepository(db)
        
        # Create a runtime
        runtime = await mock_master.runtime_repo.create_main_runtime(agent_id)
        
        from master.scheduler import Scheduler
        scheduler = Scheduler(mock_master)
        
        return scheduler, runtime
    
    @pytest.mark.asyncio
    async def test_creates_think_task(self, scheduler_with_runtime):
        """need_think phase creates a think task."""
        scheduler, runtime = scheduler_with_runtime
        
        await scheduler._handle_need_think(runtime)
        
        # Verify task was created in database
        db = scheduler.master.db
        async with db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT id, type, status FROM action_tasks 
                WHERE subagent_id = ?
            """, (runtime.subagent_id,))
            tasks = await cursor.fetchall()
        
        assert len(tasks) == 1
        task_id, task_type, status = tasks[0]
        assert task_id.startswith("think-")
        assert task_type == "think"
        assert status == "pending"
    
    @pytest.mark.asyncio
    async def test_broadcasts_new_task(self, scheduler_with_runtime):
        """need_think phase broadcasts SSE new_task event."""
        scheduler, runtime = scheduler_with_runtime
        
        await scheduler._handle_need_think(runtime)
        
        scheduler.master.broadcast_new_task.assert_called_once()
        call_args = scheduler.master.broadcast_new_task.call_args
        assert call_args.args[1] == 'think'  # task_type
        assert call_args.args[2] == runtime.agent_id  # agent_id
    
    @pytest.mark.asyncio
    async def test_updates_pending_actions(self, scheduler_with_runtime):
        """need_think phase updates runtime's pending_actions."""
        scheduler, runtime = scheduler_with_runtime
        
        await scheduler._handle_need_think(runtime)
        
        # Reload runtime
        updated = await scheduler.master.runtime_repo.get_by_id(runtime.subagent_id)
        
        assert len(updated.pending_actions) == 1
        assert updated.pending_actions[0].startswith("think-")


class TestSchedulerContextPreparation:
    """Tests for Scheduler._prepare_context."""
    
    @pytest.mark.asyncio
    async def test_includes_inbox_messages(self, db_with_agent):
        """Context includes unread inbox messages."""
        db, agent_id = db_with_agent
        
        # Add inbox messages
        from tests.conftest import create_test_message
        await create_test_message(db, agent_id, "First message")
        await create_test_message(db, agent_id, "Second message")
        
        # Create runtime
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        # Create scheduler
        mock_master = MagicMock()
        mock_master.db = db
        mock_master.runtime_repo = runtime_repo
        
        from master.scheduler import Scheduler
        scheduler = Scheduler(mock_master)
        
        context = await scheduler._prepare_context(runtime)
        
        # Should have the 2 messages
        user_messages = [m for m in context if m.get('role') == 'user']
        assert len(user_messages) >= 2
    
    @pytest.mark.asyncio
    async def test_marks_messages_as_read(self, db_with_agent):
        """Preparing context marks inbox messages as read."""
        db, agent_id = db_with_agent
        
        from tests.conftest import create_test_message
        msg_id = await create_test_message(db, agent_id, "Test message")
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        mock_master = MagicMock()
        mock_master.db = db
        mock_master.runtime_repo = runtime_repo
        
        from master.scheduler import Scheduler
        scheduler = Scheduler(mock_master)
        
        await scheduler._prepare_context(runtime)
        
        # Check message is now read
        async with db.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT read FROM chat_messages WHERE id = ?", (msg_id,)
            )
            result = await cursor.fetchone()
        
        assert result[0] == 1  # read = True
    
    @pytest.mark.asyncio
    async def test_preserves_existing_context(self, db_with_agent):
        """Context includes existing runtime context."""
        db, agent_id = db_with_agent
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        # Set existing context
        existing = [{"role": "system", "content": "You are helpful."}]
        await runtime_repo.update_context(runtime.subagent_id, existing)
        runtime = await runtime_repo.get_by_id(runtime.subagent_id)
        
        mock_master = MagicMock()
        mock_master.db = db
        mock_master.runtime_repo = runtime_repo
        
        from master.scheduler import Scheduler
        scheduler = Scheduler(mock_master)
        
        context = await scheduler._prepare_context(runtime)
        
        # Should include the system message
        assert any(m.get('content') == "You are helpful." for m in context)


class TestSchedulerPhaseWaitingActions:
    """Tests for Scheduler._handle_waiting_actions phase."""
    
    @pytest.mark.asyncio
    async def test_waits_for_pending_tasks(self, db_with_agent):
        """waiting_actions phase waits for pending tasks."""
        db, agent_id = db_with_agent
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        # Create a pending task
        task_id = "think-test123"
        await db.execute("""
            INSERT INTO action_tasks (id, agent_id, subagent_id, round_id, mcpcall_id, type, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (task_id, agent_id, runtime.subagent_id, "round-1", "think", "think", "pending"))
        await db.commit()
        
        # Set pending actions
        await runtime_repo.set_pending_actions(runtime.subagent_id, [task_id])
        runtime = await runtime_repo.get_by_id(runtime.subagent_id)
        
        mock_master = MagicMock()
        mock_master.db = db
        mock_master.runtime_repo = runtime_repo
        
        from master.scheduler import Scheduler
        scheduler = Scheduler(mock_master)
        
        # Should not advance (task still pending)
        await scheduler._handle_waiting_actions(runtime)
        
        # Runtime should still be active
        updated = await runtime_repo.get_by_id(runtime.subagent_id)
        assert updated.status == "active"
    
    @pytest.mark.asyncio
    async def test_advances_when_all_done(self, db_with_agent):
        """waiting_actions phase advances when all tasks complete."""
        db, agent_id = db_with_agent
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        # Create a completed think task with done action
        task_id = "think-test123"
        result = json.dumps({
            "success": True,
            "actions": [],  # No actions means done
            "is_final": True,
        })
        await db.execute("""
            INSERT INTO action_tasks (id, agent_id, subagent_id, round_id, mcpcall_id, type, status, result, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (task_id, agent_id, runtime.subagent_id, "round-1", "think", "think", "done", result))
        await db.commit()
        
        await runtime_repo.set_pending_actions(runtime.subagent_id, [task_id])
        runtime = await runtime_repo.get_by_id(runtime.subagent_id)
        
        mock_master = MagicMock()
        mock_master.db = db
        mock_master.runtime_repo = runtime_repo
        mock_master.destroy_runtime = AsyncMock()
        mock_master.set_agent_sleep = AsyncMock()
        mock_master.broadcast_new_task = AsyncMock()
        
        from master.scheduler import Scheduler
        scheduler = Scheduler(mock_master)
        
        await scheduler._handle_waiting_actions(runtime)
        
        # Runtime should be completed
        updated = await runtime_repo.get_by_id(runtime.subagent_id)
        assert updated.status == "completed"


class TestSchedulerAdvanceOrComplete:
    """Tests for Scheduler._advance_or_complete decision logic."""
    
    @pytest.mark.asyncio
    async def test_completes_on_done_action(self, db_with_agent):
        """Runtime completes when is_final=True in think result."""
        db, agent_id = db_with_agent
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        mock_master = MagicMock()
        mock_master.db = db
        mock_master.runtime_repo = runtime_repo
        mock_master.destroy_runtime = AsyncMock()
        mock_master.set_agent_sleep = AsyncMock()
        mock_master.broadcast_new_task = AsyncMock()
        
        from master.scheduler import Scheduler
        scheduler = Scheduler(mock_master)
        
        # Simulate done action
        results = [{
            'task_id': 'think-123',
            'type': 'think',
            'status': 'done',
            'result': {
                'success': True,
                'actions': [],
                'is_final': True,
            },
            'error': None,
        }]
        
        await scheduler._advance_or_complete(runtime, results)
        
        # Runtime should be completed
        updated = await runtime_repo.get_by_id(runtime.subagent_id)
        assert updated.status == "completed"
    
    @pytest.mark.asyncio
    async def test_advances_round_on_actions(self, db_with_agent):
        """Runtime advances to next round when actions are returned."""
        db, agent_id = db_with_agent
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        mock_master = MagicMock()
        mock_master.db = db
        mock_master.runtime_repo = runtime_repo
        mock_master.broadcast_new_task = AsyncMock()
        
        from master.scheduler import Scheduler
        scheduler = Scheduler(mock_master)
        
        # Simulate actions returned
        results = [{
            'task_id': 'think-123',
            'type': 'think',
            'status': 'done',
            'result': {
                'success': True,
                'actions': [
                    {'type': 'tool_call', 'name': 'memory_write', 'args': {}}
                ],
                'is_final': False,
            },
            'error': None,
        }]
        
        await scheduler._advance_or_complete(runtime, results)
        
        # Should have created action tasks
        async with db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT type FROM action_tasks 
                WHERE subagent_id = ? AND type = 'tool_call'
            """, (runtime.subagent_id,))
            tasks = await cursor.fetchall()
        
        assert len(tasks) >= 1
    
    @pytest.mark.asyncio
    async def test_marks_failed_on_think_error(self, db_with_agent):
        """Runtime fails when think returns error."""
        db, agent_id = db_with_agent
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        mock_master = MagicMock()
        mock_master.db = db
        mock_master.runtime_repo = runtime_repo
        mock_master.destroy_runtime = AsyncMock()
        mock_master.set_agent_sleep = AsyncMock()
        
        from master.scheduler import Scheduler
        scheduler = Scheduler(mock_master)
        
        # Simulate think error
        results = [{
            'task_id': 'think-123',
            'type': 'think',
            'status': 'done',
            'result': {
                'success': False,
                'error': 'LLM API error',
                'actions': [],
            },
            'error': None,
        }]
        
        await scheduler._advance_or_complete(runtime, results)
        
        # Runtime should be failed
        updated = await runtime_repo.get_by_id(runtime.subagent_id)
        assert updated.status == "failed"


class TestSchedulerLifecycle:
    """Tests for Scheduler start/stop lifecycle."""
    
    @pytest.mark.asyncio
    async def test_start_sets_running_flag(self, db):
        """Scheduler.start() sets running to True."""
        mock_master = MagicMock()
        mock_master.db = db
        
        from master.scheduler import Scheduler
        scheduler = Scheduler(mock_master)
        
        await scheduler.start()
        
        assert scheduler.running is True
        
        await scheduler.stop()
    
    @pytest.mark.asyncio
    async def test_stop_sets_running_flag(self, db):
        """Scheduler.stop() sets running to False."""
        mock_master = MagicMock()
        mock_master.db = db
        
        from master.scheduler import Scheduler
        scheduler = Scheduler(mock_master)
        
        await scheduler.start()
        await scheduler.stop()
        
        assert scheduler.running is False
