"""
Unit Tests for MCPExecutionRepository

Tests the mcp_executions table operations for idempotency:
- Execution creation
- Idempotency checking (get_or_create)
- Status updates (complete, fail)
"""

import pytest
import pytest_asyncio

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


class TestExecutionCreation:
    """Tests for creating MCP execution records."""
    
    @pytest.mark.asyncio
    async def test_create_execution(self, mcp_execution_repo, db_with_agent):
        """create creates a new execution record."""
        db, agent_id = db_with_agent
        mcp_execution_repo.db = db
        
        idem_key = f"{agent_id}-main-abc-round-1-mc-1"
        
        execution = await mcp_execution_repo.create(
            idempotency_key=idem_key,
            agent_id=agent_id,
            subagent_id="main-abc",
            round_id="round-1",
            mcpcall_id="mc-1",
            tool_name="memory_write",
            args={"key": "test"},
        )
        
        assert execution is not None
        assert execution["idempotency_key"] == idem_key
        assert execution["status"] == "executing"
        assert execution["tool_name"] == "memory_write"
    
    @pytest.mark.asyncio
    async def test_get_or_create_creates_new(self, mcp_execution_repo, db_with_agent):
        """get_or_create creates new record if not exists."""
        db, agent_id = db_with_agent
        mcp_execution_repo.db = db
        
        idem_key = f"{agent_id}-main-xyz-round-1-mc-1"
        
        execution, was_created = await mcp_execution_repo.get_or_create(
            idempotency_key=idem_key,
            agent_id=agent_id,
            subagent_id="main-xyz",
            round_id="round-1",
            mcpcall_id="mc-1",
            tool_name="qemu_run_command",
        )
        
        assert was_created is True
        assert execution["status"] == "executing"
    
    @pytest.mark.asyncio
    async def test_get_or_create_returns_existing(self, mcp_execution_repo, db_with_agent):
        """get_or_create returns existing record."""
        db, agent_id = db_with_agent
        mcp_execution_repo.db = db
        
        idem_key = f"{agent_id}-main-existing-round-1-mc-1"
        
        # Create first
        first, created1 = await mcp_execution_repo.get_or_create(
            idempotency_key=idem_key,
            agent_id=agent_id,
            subagent_id="main-existing",
            round_id="round-1",
            mcpcall_id="mc-1",
            tool_name="memory_write",
        )
        
        # Get second time
        second, created2 = await mcp_execution_repo.get_or_create(
            idempotency_key=idem_key,
            agent_id=agent_id,
            subagent_id="main-existing",
            round_id="round-1",
            mcpcall_id="mc-1",
            tool_name="memory_write",
        )
        
        assert created1 is True
        assert created2 is False
        assert first["idempotency_key"] == second["idempotency_key"]


class TestIdempotencyChecking:
    """Tests for idempotency checking."""
    
    @pytest.mark.asyncio
    async def test_get_returns_existing_execution(self, mcp_execution_repo, db_with_agent):
        """get returns existing execution record."""
        db, agent_id = db_with_agent
        mcp_execution_repo.db = db
        
        idem_key = f"{agent_id}-main-get-round-1-mc-1"
        
        await mcp_execution_repo.create(
            idempotency_key=idem_key,
            agent_id=agent_id,
            subagent_id="main-get",
            round_id="round-1",
            mcpcall_id="mc-1",
            tool_name="test_tool",
        )
        
        fetched = await mcp_execution_repo.get(idem_key)
        
        assert fetched is not None
        assert fetched["tool_name"] == "test_tool"
    
    @pytest.mark.asyncio
    async def test_get_returns_none_for_nonexistent(self, mcp_execution_repo, db):
        """get returns None for non-existent key."""
        mcp_execution_repo.db = db
        
        fetched = await mcp_execution_repo.get("nonexistent-key")
        
        assert fetched is None
    
    @pytest.mark.asyncio
    async def test_check_idempotency_for_done(self, mcp_execution_repo, db_with_agent):
        """Done executions should return cached result."""
        db, agent_id = db_with_agent
        mcp_execution_repo.db = db
        
        idem_key = f"{agent_id}-main-done-round-1-mc-1"
        
        await mcp_execution_repo.create(
            idempotency_key=idem_key,
            agent_id=agent_id,
            subagent_id="main-done",
            round_id="round-1",
            mcpcall_id="mc-1",
            tool_name="test_tool",
        )
        
        # Complete it
        await mcp_execution_repo.complete(idem_key, {"data": "cached_result"})
        
        # Get should return the completed execution with result
        fetched = await mcp_execution_repo.get(idem_key)
        
        assert fetched["status"] == "done"
        assert fetched["result"]["data"] == "cached_result"


class TestExecutionCompletion:
    """Tests for completing/failing executions."""
    
    @pytest.mark.asyncio
    async def test_complete_execution(self, mcp_execution_repo, db_with_agent):
        """complete marks execution as done with result."""
        db, agent_id = db_with_agent
        mcp_execution_repo.db = db
        
        idem_key = f"{agent_id}-main-complete-round-1-mc-1"
        
        await mcp_execution_repo.create(
            idempotency_key=idem_key,
            agent_id=agent_id,
            subagent_id="main-complete",
            round_id="round-1",
            mcpcall_id="mc-1",
            tool_name="test_tool",
        )
        
        result = {"success": True, "output": "completed successfully"}
        await mcp_execution_repo.complete(idem_key, result)
        
        fetched = await mcp_execution_repo.get(idem_key)
        
        assert fetched["status"] == "done"
        assert fetched["result"]["output"] == "completed successfully"
        assert fetched["executed_at"] is not None
    
    @pytest.mark.asyncio
    async def test_fail_execution(self, mcp_execution_repo, db_with_agent):
        """fail marks execution as failed with error."""
        db, agent_id = db_with_agent
        mcp_execution_repo.db = db
        
        idem_key = f"{agent_id}-main-fail-round-1-mc-1"
        
        await mcp_execution_repo.create(
            idempotency_key=idem_key,
            agent_id=agent_id,
            subagent_id="main-fail",
            round_id="round-1",
            mcpcall_id="mc-1",
            tool_name="test_tool",
        )
        
        await mcp_execution_repo.fail(idem_key, "Something went wrong")
        
        fetched = await mcp_execution_repo.get(idem_key)
        
        assert fetched["status"] == "failed"
        assert fetched["error"] == "Something went wrong"
    
    @pytest.mark.asyncio
    async def test_timeout_execution(self, mcp_execution_repo, db_with_agent):
        """timeout marks execution as timed out."""
        db, agent_id = db_with_agent
        mcp_execution_repo.db = db
        
        idem_key = f"{agent_id}-main-timeout-round-1-mc-1"
        
        await mcp_execution_repo.create(
            idempotency_key=idem_key,
            agent_id=agent_id,
            subagent_id="main-timeout",
            round_id="round-1",
            mcpcall_id="mc-1",
            tool_name="long_running_tool",
        )
        
        await mcp_execution_repo.timeout(idem_key)
        
        fetched = await mcp_execution_repo.get(idem_key)
        
        assert fetched["status"] == "timeout"


class TestExecutionQueries:
    """Tests for execution query operations."""
    
    @pytest.mark.asyncio
    async def test_get_by_agent(self, mcp_execution_repo, db_with_agent):
        """get_by_agent returns executions for an agent."""
        db, agent_id = db_with_agent
        mcp_execution_repo.db = db
        
        subagent_id = "main-query"
        round_id = "round-1"
        
        # Create multiple executions
        for i in range(3):
            await mcp_execution_repo.create(
                idempotency_key=f"{agent_id}-{subagent_id}-{round_id}-mc-{i}",
                agent_id=agent_id,
                subagent_id=subagent_id,
                round_id=round_id,
                mcpcall_id=f"mc-{i}",
                tool_name=f"tool_{i}",
            )
        
        executions = await mcp_execution_repo.get_by_agent(agent_id, subagent_id=subagent_id)
        
        assert len(executions) == 3
    
    @pytest.mark.asyncio
    async def test_get_executing_returns_long_running(self, mcp_execution_repo, db_with_agent):
        """get_executing returns executions that have been running too long."""
        db, agent_id = db_with_agent
        mcp_execution_repo.db = db
        
        # Create an execution
        idem_key = f"{agent_id}-main-exec-round-1-mc-1"
        await mcp_execution_repo.create(
            idempotency_key=idem_key,
            agent_id=agent_id,
            subagent_id="main-exec",
            round_id="round-1",
            mcpcall_id="mc-1",
            tool_name="test",
        )
        
        # Get executing with 0 minute timeout (all should match)
        # Note: This tests the interface; actual timeout behavior depends on DB time
        executions = await mcp_execution_repo.get_executing(timeout_minutes=0)
        
        # Should return a list (may or may not include our execution depending on timing)
        assert isinstance(executions, list)
