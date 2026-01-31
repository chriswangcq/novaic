"""
Unit Tests for Monitor Component

Tests the inbox monitoring functionality:
- Detecting unread messages
- Creating Runtime when agent has no Main Runtime
- Skipping agents that already have a Main Runtime
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


class TestMonitorCheckAgent:
    """Tests for Monitor._check_agent logic."""
    
    @pytest_asyncio.fixture
    async def monitor_with_mocks(self, db_with_agent):
        """Create a Monitor with mocked Master."""
        db, agent_id = db_with_agent
        
        # Create mock Master
        mock_master = MagicMock()
        mock_master.db = db
        mock_master.create_main_runtime = AsyncMock()
        
        # Add runtime repo
        from db.repositories.runtime import RuntimeRepository
        mock_master.runtime_repo = RuntimeRepository(db)
        
        from master.monitor import Monitor
        monitor = Monitor(mock_master)
        
        return monitor, agent_id
    
    @pytest.mark.asyncio
    async def test_detects_unread_messages(self, monitor_with_mocks):
        """Monitor detects agents with unread messages."""
        monitor, agent_id = monitor_with_mocks
        
        # Add an unread message
        from tests.conftest import create_test_message
        await create_test_message(monitor.master.db, agent_id, "Test message")
        
        # Check the agent
        await monitor._check_agent(agent_id)
        
        # Should have triggered Runtime creation
        monitor.master.create_main_runtime.assert_called_once_with(agent_id)
    
    @pytest.mark.asyncio
    async def test_skips_agent_with_no_unread_messages(self, monitor_with_mocks):
        """Monitor skips agents with no unread messages."""
        monitor, agent_id = monitor_with_mocks
        
        # No messages added
        
        await monitor._check_agent(agent_id)
        
        # Should NOT have triggered Runtime creation
        monitor.master.create_main_runtime.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_skips_agent_with_existing_main_runtime(self, monitor_with_mocks):
        """Monitor skips agents that already have a Main Runtime."""
        monitor, agent_id = monitor_with_mocks
        
        # Add unread message
        from tests.conftest import create_test_message
        await create_test_message(monitor.master.db, agent_id, "Test message")
        
        # Create existing Main Runtime
        await monitor.master.runtime_repo.create_main_runtime(agent_id)
        
        await monitor._check_agent(agent_id)
        
        # Should NOT trigger another Runtime creation
        monitor.master.create_main_runtime.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_creates_runtime_when_only_sub_exists(self, monitor_with_mocks):
        """Monitor creates Main Runtime even if SubAgent exists."""
        monitor, agent_id = monitor_with_mocks
        
        # Add unread message
        from tests.conftest import create_test_message
        await create_test_message(monitor.master.db, agent_id, "Test message")
        
        # First create a main runtime to act as parent, then complete it
        main = await monitor.master.runtime_repo.create_main_runtime(agent_id)
        await monitor.master.runtime_repo.mark_completed(main.subagent_id)
        
        # Create only a SubAgent Runtime (not Main - main is completed)
        await monitor.master.runtime_repo.create_sub_runtime(
            agent_id, parent_subagent_id=main.subagent_id
        )
        
        await monitor._check_agent(agent_id)
        
        # Should trigger Runtime creation because no active Main exists
        monitor.master.create_main_runtime.assert_called_once_with(agent_id)


class TestMonitorCheckAgents:
    """Tests for Monitor._check_agents (checking all agents)."""
    
    @pytest.mark.asyncio
    async def test_checks_all_setup_complete_agents(self, db):
        """Monitor checks all agents with setup_complete=1."""
        # Create multiple agents (using correct schema)
        await db.execute("""
            INSERT INTO agents (id, name, setup_complete, vm_config, ports, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, ("agent-1", "Agent 1", 1, "{}", "{}"))
        await db.execute("""
            INSERT INTO agents (id, name, setup_complete, vm_config, ports, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, ("agent-2", "Agent 2", 1, "{}", "{}"))
        await db.execute("""
            INSERT INTO agents (id, name, setup_complete, vm_config, ports, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, ("agent-3", "Agent 3", 0, "{}", "{}"))  # Not setup complete
        await db.commit()
        
        # Create mock Master
        mock_master = MagicMock()
        mock_master.db = db
        mock_master.create_main_runtime = AsyncMock()
        
        from db.repositories.runtime import RuntimeRepository
        mock_master.runtime_repo = RuntimeRepository(db)
        
        from master.monitor import Monitor
        monitor = Monitor(mock_master)
        
        # Add messages for all agents
        from tests.conftest import create_test_message
        await create_test_message(db, "agent-1", "Msg 1")
        await create_test_message(db, "agent-2", "Msg 2")
        await create_test_message(db, "agent-3", "Msg 3")  # Won't be checked
        
        await monitor._check_agents()
        
        # Should only check agents with setup_complete=1
        assert mock_master.create_main_runtime.call_count == 2
        called_agents = [call.args[0] for call in mock_master.create_main_runtime.call_args_list]
        assert "agent-1" in called_agents
        assert "agent-2" in called_agents
        assert "agent-3" not in called_agents


class TestMonitorLifecycle:
    """Tests for Monitor start/stop lifecycle."""
    
    @pytest.mark.asyncio
    async def test_start_sets_running_flag(self, db):
        """Monitor.start() sets running to True."""
        mock_master = MagicMock()
        mock_master.db = db
        
        from master.monitor import Monitor
        monitor = Monitor(mock_master)
        
        await monitor.start()
        
        assert monitor.running is True
        
        # Clean up
        await monitor.stop()
    
    @pytest.mark.asyncio
    async def test_stop_sets_running_flag(self, db):
        """Monitor.stop() sets running to False."""
        mock_master = MagicMock()
        mock_master.db = db
        
        from master.monitor import Monitor
        monitor = Monitor(mock_master)
        
        await monitor.start()
        await monitor.stop()
        
        assert monitor.running is False
    
    @pytest.mark.asyncio
    async def test_start_is_idempotent(self, db):
        """Calling start() multiple times is safe."""
        mock_master = MagicMock()
        mock_master.db = db
        
        from master.monitor import Monitor
        monitor = Monitor(mock_master)
        
        await monitor.start()
        task1 = monitor._task
        
        await monitor.start()  # Second call
        task2 = monitor._task
        
        # Should be the same task
        assert task1 is task2
        
        await monitor.stop()
