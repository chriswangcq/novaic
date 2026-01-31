"""
Integration Tests for Message Flow

Tests the complete message flow from user input to agent reply:
1. User sends message → Gateway stores in inbox
2. Monitor detects unread message → Creates Runtime
3. Scheduler drives Runtime → Creates think task
4. Worker executes think → Returns actions
5. Scheduler creates action tasks → Workers execute
6. Reply sent to user
"""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestMessageToRuntimeFlow:
    """Tests message triggering Runtime creation."""
    
    @pytest_asyncio.fixture
    async def integrated_system(self, db_with_agent):
        """Set up integrated Master/Monitor/Scheduler system."""
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
            
            mock_broadcaster = MagicMock()
            mock_broadcaster.broadcast_new_task = AsyncMock()
            
            master = Master(db, mock_broadcaster, MasterConfig(
                monitor_interval=0.1,
                scheduler_interval=0.1,
            ))
            
            yield master, agent_id
    
    @pytest.mark.asyncio
    async def test_unread_message_triggers_runtime_creation(self, integrated_system):
        """An unread message triggers Monitor to create a Runtime."""
        master, agent_id = integrated_system
        
        # Add an unread message
        from tests.conftest import create_test_message
        await create_test_message(master.db, agent_id, "Hello, agent!")
        
        # Run monitor check once (not starting the full loop)
        await master.monitor._check_agents()
        
        # Should have created a Main Runtime
        runtime = await master.runtime_repo.get_main_runtime(agent_id)
        assert runtime is not None
        assert runtime.type == "main"
    
    @pytest.mark.asyncio
    async def test_runtime_starts_in_need_think_phase(self, integrated_system):
        """New Runtime starts in need_think phase."""
        master, agent_id = integrated_system
        
        await create_test_message(master.db, agent_id, "Test message")
        await master.monitor._check_agents()
        
        runtime = await master.runtime_repo.get_main_runtime(agent_id)
        
        assert runtime.phase == "need_think"
    
    @pytest.mark.asyncio
    async def test_scheduler_creates_think_task(self, integrated_system):
        """Scheduler creates think task for need_think Runtime."""
        master, agent_id = integrated_system
        
        # Create runtime directly
        runtime = await master.create_main_runtime(agent_id)
        
        # Add a message to context
        from tests.conftest import create_test_message
        await create_test_message(master.db, agent_id, "Think about this")
        
        # Run scheduler once
        await master.scheduler._schedule_runtimes()
        await asyncio.sleep(0.1)  # Give time for async task
        
        # Should have created a think task
        db = master.db
        async with db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT id, type FROM action_tasks 
                WHERE subagent_id = ? AND type = 'think'
            """, (runtime.subagent_id,))
            tasks = await cursor.fetchall()
        
        assert len(tasks) >= 1


class TestThinkToActionFlow:
    """Tests the flow from thinking to action execution."""
    
    @pytest.mark.asyncio
    async def test_think_result_creates_action_tasks(self, db_with_agent):
        """Think result with actions creates action_tasks."""
        db, agent_id = db_with_agent
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        with patch('master.master.get_mcp_gateway_manager'), \
             patch('master.master.get_sub_mcp_manager') as mock_sub:
            mock_sub.return_value = MagicMock(
                create_runtime_server=AsyncMock(),
                remove_runtime_server=AsyncMock(),
            )
            
            from master import Master, MasterConfig
            
            broadcaster = MagicMock()
            broadcaster.broadcast_new_task = AsyncMock()
            
            master = Master(db, broadcaster, MasterConfig())
            
            # Simulate think result with actions
            results = [{
                'task_id': 'think-123',
                'type': 'think',
                'status': 'done',
                'result': {
                    'success': True,
                    'actions': [
                        {'type': 'tool_call', 'tool': 'memory_write', 'args': {'key': 'test'}},
                        {'type': 'reply', 'content': 'I stored the data.'},
                    ],
                    'is_final': False,
                },
                'error': None,
            }]
            
            await master.scheduler._advance_or_complete(runtime, results)
            
            # Should have created action tasks
            async with db.get_connection() as conn:
                cursor = await conn.execute("""
                    SELECT type FROM action_tasks 
                    WHERE subagent_id = ? AND type IN ('tool_call', 'reply')
                """, (runtime.subagent_id,))
                tasks = await cursor.fetchall()
            
            task_types = [t[0] for t in tasks]
            assert 'tool_call' in task_types
            assert 'reply' in task_types


class TestRuntimeCompletionFlow:
    """Tests Runtime completion scenarios."""
    
    @pytest.mark.asyncio
    async def test_is_final_completes_runtime(self, db_with_agent):
        """is_final=True in think result completes Runtime."""
        db, agent_id = db_with_agent
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        with patch('master.master.get_mcp_gateway_manager'), \
             patch('master.master.get_sub_mcp_manager') as mock_sub:
            mock_sub.return_value = MagicMock(remove_runtime_server=AsyncMock())
            
            from master import Master, MasterConfig
            
            broadcaster = MagicMock()
            master = Master(db, broadcaster, MasterConfig())
            
            # Simulate final think result
            results = [{
                'task_id': 'think-final',
                'type': 'think',
                'status': 'done',
                'result': {
                    'success': True,
                    'actions': [],
                    'is_final': True,
                },
                'error': None,
            }]
            
            await master.scheduler._advance_or_complete(runtime, results)
            
            updated = await runtime_repo.get_by_id(runtime.subagent_id)
            assert updated.status == "completed"
    
    @pytest.mark.asyncio
    async def test_think_error_fails_runtime(self, db_with_agent):
        """Think error fails the Runtime."""
        db, agent_id = db_with_agent
        
        from db.repositories.runtime import RuntimeRepository
        runtime_repo = RuntimeRepository(db)
        
        runtime = await runtime_repo.create_main_runtime(agent_id)
        
        with patch('master.master.get_mcp_gateway_manager'), \
             patch('master.master.get_sub_mcp_manager') as mock_sub:
            mock_sub.return_value = MagicMock(remove_runtime_server=AsyncMock())
            
            from master import Master, MasterConfig
            
            broadcaster = MagicMock()
            master = Master(db, broadcaster, MasterConfig())
            
            # Simulate failed think
            results = [{
                'task_id': 'think-error',
                'type': 'think',
                'status': 'done',
                'result': {
                    'success': False,
                    'error': 'LLM API error',
                    'actions': [],
                },
                'error': None,
            }]
            
            await master.scheduler._advance_or_complete(runtime, results)
            
            updated = await runtime_repo.get_by_id(runtime.subagent_id)
            assert updated.status == "failed"


# Helper function
async def create_test_message(db, agent_id, content):
    """Helper to create test message."""
    from datetime import datetime
    import uuid
    
    msg_id = f"msg-{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    
    await db.execute("""
        INSERT INTO chat_messages (id, agent_id, type, content, read, processed, timestamp)
        VALUES (?, ?, ?, ?, 0, 0, ?)
    """, (msg_id, agent_id, "USER_MESSAGE", content, now))
    await db.commit()
    
    return msg_id
