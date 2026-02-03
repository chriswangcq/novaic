"""
SubAgent API

v16: Async SubAgent support - spawn returns immediately, use query to poll.
"""

from typing import Optional, Dict, Any, List
from .base import BaseAPI


class SubAgentAPI(BaseAPI):
    """
    SubAgent operations.
    
    Usage:
        # Main SubAgent
        subagent = await sdk.subagent.get_main(agent_id)
        success = await sdk.subagent.try_wake(agent_id, subagent_id)
        await sdk.subagent.set_sleeping(agent_id, subagent_id)
        
        # Async SubAgent spawn
        result = await sdk.subagent.spawn(agent_id, task="...")
        status = await sdk.subagent.query(agent_id, result["subagent_id"])
        await sdk.subagent.cancel(agent_id, subagent_id)
    """
    
    async def get_main(self, agent_id: str) -> Dict[str, Any]:
        """Get or create the main SubAgent for an agent."""
        return await self._http.get(
            f"{self.gateway_url}/internal/subagents/{agent_id}/main"
        )
    
    async def get(self, agent_id: str, subagent_id: str) -> Optional[Dict[str, Any]]:
        """Get a SubAgent by ID."""
        from .exceptions import GatewayNotFoundError
        try:
            return await self._http.get(
                f"{self.gateway_url}/internal/subagents/{agent_id}/{subagent_id}"
            )
        except GatewayNotFoundError:
            return None
    
    async def try_wake(
        self, 
        agent_id: str, 
        subagent_id: str,
        target_status: str = "awake"
    ) -> bool:
        """
        Atomically wake a sleeping SubAgent.
        
        Uses CAS to ensure only one caller succeeds.
        
        Args:
            target_status: "awaking" (intermediate) or "awake" (final)
        
        Returns:
            True if woken, False if already awake/awaking
        """
        data = await self._http.post(
            f"{self.gateway_url}/internal/subagents/{agent_id}/{subagent_id}/wake",
            params={"target_status": target_status}
        )
        return data.get("success", False)
    
    async def set_sleeping(self, agent_id: str, subagent_id: str):
        """Set SubAgent to sleeping status."""
        await self._http.post(
            f"{self.gateway_url}/internal/subagents/{agent_id}/{subagent_id}/sleeping"
        )
    
    async def set_awake(self, agent_id: str, subagent_id: str):
        """Set SubAgent to awake status (after runtime created successfully)."""
        await self._http.post(
            f"{self.gateway_url}/internal/subagents/{agent_id}/{subagent_id}/awake"
        )
    
    async def set_summarizing(self, agent_id: str, subagent_id: str):
        """Set SubAgent to summarizing status."""
        await self._http.post(
            f"{self.gateway_url}/internal/subagents/{agent_id}/{subagent_id}/summarizing"
        )
    
    async def set_completed(self, agent_id: str, subagent_id: str, result: Optional[str] = None):
        """Set SubAgent to completed status with result."""
        await self._http.post(
            f"{self.gateway_url}/internal/subagents/{agent_id}/{subagent_id}/completed",
            json={"result": result}
        )
    
    async def set_failed(self, agent_id: str, subagent_id: str, error: Optional[str] = None):
        """Set SubAgent to failed status with error message."""
        await self._http.post(
            f"{self.gateway_url}/internal/subagents/{agent_id}/{subagent_id}/failed",
            json={"error": error}
        )
    
    async def update(
        self,
        agent_id: str,
        subagent_id: str,
        **kwargs
    ):
        """
        Update SubAgent fields.
        
        Supported fields:
            - historical_summary: str
            - wake_triggers: List[Dict]
            - handoff_notes: str
        """
        await self._http.patch(
            f"{self.gateway_url}/internal/subagents/{agent_id}/{subagent_id}",
            json=kwargs
        )
    
    async def spawn(
        self,
        agent_id: str,
        task: str,
        share_context: bool = False,
        parent_subagent_id: Optional[str] = None,
        timeout_minutes: int = 30,
    ) -> Dict[str, Any]:
        """
        Spawn a new SubAgent with its Runtime (async mode).
        
        Returns immediately. Use query() to poll for completion.
        
        Args:
            agent_id: Parent agent
            task: Task description for the SubAgent
            share_context: Copy context from parent runtime
            parent_subagent_id: Parent SubAgent (defaults to main)
            timeout_minutes: Timeout in minutes (default 30)
        
        Returns:
            {"subagent_id": str, "runtime_id": str}
        """
        return await self._http.post(
            f"{self.gateway_url}/internal/subagents/{agent_id}/spawn",
            json={
                "task": task,
                "share_context": share_context,
                "parent_subagent_id": parent_subagent_id,
                "timeout_minutes": timeout_minutes,
            }
        )
    
    async def query(self, agent_id: str, subagent_id: str) -> Dict[str, Any]:
        """
        Query SubAgent status for async spawn polling.
        
        Returns:
            {
                "subagent_id": str,
                "status": str,        # running | completed | failed | cancelled
                "completed": bool,    # True if finished
                "progress": str,      # Current progress (if running)
                "result": str,        # Final result (if completed)
                "error": str,         # Error message (if failed)
                "runtime_id": str,
            }
        """
        return await self._http.get(
            f"{self.gateway_url}/internal/subagents/{agent_id}/{subagent_id}/status"
        )
    
    async def cancel(self, agent_id: str, subagent_id: str) -> Dict[str, Any]:
        """
        Cancel a running SubAgent.
        
        Returns:
            {"success": bool, "reason": str (if failed)}
        """
        return await self._http.post(
            f"{self.gateway_url}/internal/subagents/{agent_id}/{subagent_id}/cancel"
        )
    
    # Legacy alias for compatibility
    async def get_status(self, agent_id: str, subagent_id: str) -> Dict[str, Any]:
        """Alias for query() - for backwards compatibility."""
        return await self.query(agent_id, subagent_id)
    
    async def delete(self, agent_id: str, subagent_id: str):
        """Delete a SubAgent and its runtimes."""
        await self._http.delete(
            f"{self.gateway_url}/internal/subagents/{agent_id}/{subagent_id}"
        )
