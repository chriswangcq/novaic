"""
Gateway Client for Services

Wrapper around GatewaySDK for backward compatibility.
New code should use GatewaySDK directly from the sdk module.

All services communicate ONLY with Gateway.
MCP operations are proxied through Gateway to MCP Gateway.
"""

from typing import Optional, Dict, Any, List
from sdk import GatewaySDK


class GatewayClient:
    """
    HTTP client for services to interact with Gateway API.
    
    All operations go through Gateway ONLY.
    Services do not communicate with MCP Gateway directly.
    
    This is a compatibility wrapper around GatewaySDK.
    New code should use GatewaySDK directly:
    
        from sdk import GatewaySDK
        async with GatewaySDK() as sdk:
            task = await sdk.pipeline.claim_task(...)
    """
    
    def __init__(
        self, 
        gateway_url: str = "http://127.0.0.1:19999",
        timeout: float = 30.0,
    ):
        self._sdk = GatewaySDK(
            gateway_url=gateway_url,
            timeout=timeout,
        )
        self.gateway_url = self._sdk.gateway_url
    
    async def close(self):
        """Close HTTP session."""
        await self._sdk.close()
    
    # ==================== Pipeline Task Operations ====================
    
    async def claim_task(
        self,
        task_types: List[str],
        task_subtypes: Optional[List[str]] = None,
        worker_id: str = "unknown",
        collector_ready_only: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Atomically claim a pending pipeline task."""
        return await self._sdk.pipeline.claim_task(
            task_types, task_subtypes, worker_id, collector_ready_only
        )
    
    async def create_task(
        self,
        task_type: str,
        task_subtype: str,
        runtime_id: str,
        stage_id: str,
        agent_id: str,
        args: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        expected_tasks: int = 0,
    ) -> Optional[str]:
        """Create a new pipeline task."""
        return await self._sdk.pipeline.create_task(
            task_type, task_subtype, runtime_id, stage_id, agent_id,
            args, idempotency_key, expected_tasks
        )
    
    async def mark_task_done(self, task_id: str, result: Any = None):
        """Mark a task as done with result."""
        await self._sdk.pipeline.mark_done(task_id, result)
    
    async def mark_task_failed(self, task_id: str, error: str):
        """Mark a task as failed with error."""
        await self._sdk.pipeline.mark_failed(task_id, error)
    
    async def release_task(self, task_id: str):
        """Release a claimed task back to pending for retry."""
        await self._sdk.pipeline.release_task(task_id)
    
    async def update_heartbeat(self, task_id: str):
        """Update heartbeat for a claimed task."""
        await self._sdk.pipeline.heartbeat(task_id)
    
    async def recover_stale_tasks(
        self, 
        task_type: Optional[str] = None, 
        timeout_seconds: int = 60
    ) -> int:
        """Recover stale tasks. Returns count recovered."""
        return await self._sdk.pipeline.recover_stale_tasks(task_type, timeout_seconds)
    
    async def increment_collector_count(self, stage_id: str) -> Dict[str, Any]:
        """Increment completed_tasks count for a stage's collector."""
        return await self._sdk.pipeline.increment_collector_count(stage_id)
    
    async def get_tasks_by_stage(self, stage_id: str) -> List[Dict[str, Any]]:
        """Get all tasks for a stage."""
        return await self._sdk.pipeline.get_tasks_by_stage(stage_id)
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a single task by ID."""
        return await self._sdk.pipeline.get_task(task_id)
    
    # ==================== Runtime Operations ====================
    
    async def get_runtime(self, runtime_id: str) -> Optional[Dict[str, Any]]:
        """Get a runtime by ID."""
        return await self._sdk.runtime.get(runtime_id)
    
    async def create_runtime(
        self,
        runtime_id: str,
        subagent_id: str,
        agent_id: str,
    ) -> str:
        """Create a new runtime. Returns the created runtime_id."""
        result = await self._sdk.runtime.create(agent_id, subagent_id)
        return result.get("runtime_id", runtime_id)
    
    async def update_runtime(self, runtime_id: str, **kwargs) -> bool:
        """Update runtime fields."""
        return await self._sdk.runtime.update(runtime_id, **kwargs)
    
    async def delete_runtime(self, runtime_id: str):
        """Delete a runtime record (for rollback on creation failure)."""
        await self._sdk.runtime.delete(runtime_id)
    
    # ==================== SubAgent Operations ====================
    
    async def get_main_subagent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get or create main SubAgent."""
        return await self._sdk.subagent.get_main(agent_id)
    
    async def get_subagent(
        self, 
        agent_id: str, 
        subagent_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a SubAgent by ID."""
        return await self._sdk.subagent.get(agent_id, subagent_id)
    
    async def try_wake_subagent(
        self, 
        agent_id: str, 
        subagent_id: str,
        target_status: str = "awake"
    ) -> bool:
        """Atomically wake a SubAgent (sleeping -> target_status)."""
        return await self._sdk.subagent.try_wake(agent_id, subagent_id, target_status=target_status)
    
    async def set_subagent_sleeping(self, agent_id: str, subagent_id: str):
        """Set SubAgent to sleeping."""
        await self._sdk.subagent.set_sleeping(agent_id, subagent_id)
    
    async def set_subagent_awake(self, agent_id: str, subagent_id: str):
        """Set SubAgent to awake (after runtime created successfully)."""
        await self._sdk.subagent.set_awake(agent_id, subagent_id)
    
    async def set_subagent_completed(self, agent_id: str, subagent_id: str, result: Optional[str] = None):
        """Set SubAgent to completed (for async spawn)."""
        await self._sdk.subagent.set_completed(agent_id, subagent_id, result=result)
    
    async def set_subagent_failed(self, agent_id: str, subagent_id: str, error: Optional[str] = None):
        """Set SubAgent to failed (for async spawn)."""
        await self._sdk.subagent.set_failed(agent_id, subagent_id, error=error)
    
    async def update_subagent(
        self, 
        agent_id: str, 
        subagent_id: str, 
        **kwargs
    ):
        """Update SubAgent fields."""
        await self._sdk.subagent.update(agent_id, subagent_id, **kwargs)
    
    # ==================== Message Operations ====================
    
    async def get_unread_messages_grouped(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get unread messages grouped by agent_id."""
        return await self._sdk.messages.get_unread_grouped()
    
    async def get_unread_messages(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get unread messages for an agent."""
        return await self._sdk.messages.get_unread(agent_id)
    
    async def mark_messages_processed(self, message_ids: List[str]):
        """Mark messages as processed."""
        await self._sdk.messages.mark_processed(message_ids)
    
    async def has_unread_messages(self, agent_id: str) -> bool:
        """Check if agent has unread messages."""
        return await self._sdk.messages.has_unread(agent_id)
    
    async def claim_sending_message(self) -> Optional[Dict[str, Any]]:
        """CAS claim a sending message (sending → sent). For Monitor queue."""
        return await self._sdk.messages.claim_sending()
    
    # ==================== Agent Operations ====================
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent config."""
        return await self._sdk.get_agent(agent_id)
    
    async def get_latest_runtimes(
        self, 
        agent_id: str, 
        subagent_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get latest completed runtimes."""
        return await self._sdk.runtime.get_latest(agent_id, subagent_id, limit)
    
    async def has_active_runtime(self, agent_id: str, subagent_id: str) -> bool:
        """Check if SubAgent has an active runtime (active/resting status)."""
        return await self._sdk.runtime.has_active(agent_id, subagent_id)
    
    # ==================== MCP Operations (via Gateway proxy) ====================
    
    async def has_agent_shared_mcp(self, agent_id: str) -> bool:
        """Check if agent has shared MCP (via Gateway)."""
        return await self._sdk.mcp.has_agent_shared(agent_id)
    
    async def create_agent_shared_mcp(self, agent_id: str, agent_index: int = 0):
        """Create agent shared MCP (via Gateway)."""
        await self._sdk.mcp.create_agent_shared(agent_id, agent_index)
    
    async def delete_agent_shared_mcp(self, agent_id: str):
        """Delete agent shared MCP (via Gateway)."""
        await self._sdk.mcp.delete_agent_shared(agent_id)
    
    async def create_runtime_mcp(
        self, 
        agent_id: str, 
        runtime_id: str, 
        subagent_id: str,
        agent_index: int = 0
    ):
        """Create runtime MCP (via Gateway)."""
        await self._sdk.mcp.create_runtime(agent_id, runtime_id, subagent_id, agent_index)
    
    async def delete_runtime_mcp(self, agent_id: str, runtime_id: str):
        """Delete runtime MCP (via Gateway)."""
        await self._sdk.mcp.delete_runtime(agent_id, runtime_id)
    
    async def create_aggregate_mcp(
        self, 
        agent_id: str, 
        runtime_id: str, 
        subagent_id: str,
        agent_index: int = 0
    ) -> str:
        """Create aggregate MCP (via Gateway). Returns MCP URL."""
        return await self._sdk.mcp.create_aggregate(agent_id, runtime_id, subagent_id, agent_index)
    
    async def delete_aggregate_mcp(self, agent_id: str, runtime_id: str):
        """Delete aggregate MCP (via Gateway)."""
        await self._sdk.mcp.delete_aggregate(agent_id, runtime_id)
    
    # ==================== LLM Operations ====================
    
    async def compact_context(
        self, 
        agent_id: str, 
        messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compact context using LLM."""
        return await self._sdk.llm.compact_context(agent_id, messages)
    
    # ==================== Health Monitor Operations (v18) ====================
    
    async def get_stuck_sending_count(self, timeout_seconds: int = 30) -> int:
        """Get count of messages stuck in 'sending' state."""
        return await self._sdk.health.get_stuck_sending_count(timeout_seconds)
    
    async def get_stuck_awaking_count(self, timeout_seconds: int = 60) -> int:
        """Get count of SubAgents stuck in 'awaking' state."""
        return await self._sdk.health.get_stuck_awaking_count(timeout_seconds)
    
    async def reset_stuck_awaking(self, timeout_seconds: int = 60) -> int:
        """Reset SubAgents stuck in 'awaking' state to 'sleeping'."""
        return await self._sdk.health.reset_stuck_awaking(timeout_seconds)
