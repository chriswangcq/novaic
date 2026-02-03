"""
Runtime API
"""

from typing import Optional, Dict, Any, List
from .base import BaseAPI


class RuntimeAPI(BaseAPI):
    """
    Runtime operations.
    
    Usage:
        runtime = await sdk.runtime.get(runtime_id)
        await sdk.runtime.update(runtime_id, status="completed", context=[...])
        runtimes = await sdk.runtime.get_latest(agent_id, subagent_id)
    """
    
    async def get(self, runtime_id: str) -> Optional[Dict[str, Any]]:
        """Get a runtime by ID."""
        from .exceptions import GatewayNotFoundError
        try:
            return await self._http.get(
                f"{self.gateway_url}/internal/runtimes/{runtime_id}"
            )
        except GatewayNotFoundError:
            return None
    
    async def get_active(self) -> List[Dict[str, Any]]:
        """Get all active runtimes."""
        data = await self._http.get(
            f"{self.gateway_url}/internal/runtimes/active"
        )
        return data.get("runtimes", [])
    
    async def get_main(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get active main runtime for an agent."""
        from .exceptions import GatewayNotFoundError
        try:
            return await self._http.get(
                f"{self.gateway_url}/internal/runtimes/main/{agent_id}"
            )
        except GatewayNotFoundError:
            return None
    
    async def get_for_subagent(
        self, 
        agent_id: str, 
        subagent_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get active runtime for a SubAgent."""
        from .exceptions import GatewayNotFoundError
        try:
            return await self._http.get(
                f"{self.gateway_url}/internal/runtimes/subagent/{agent_id}/{subagent_id}"
            )
        except GatewayNotFoundError:
            return None
    
    async def get_latest(
        self,
        agent_id: str,
        subagent_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get latest completed runtimes for context preparation."""
        data = await self._http.get(
            f"{self.gateway_url}/internal/runtimes/latest/{agent_id}/{subagent_id}",
            params={"limit": limit}
        )
        return data.get("runtimes", [])
    
    async def has_active(self, agent_id: str, subagent_id: str) -> bool:
        """Check if SubAgent has an active runtime (active/resting status)."""
        data = await self._http.get(
            f"{self.gateway_url}/internal/agents/{agent_id}/subagents/{subagent_id}/has-active-runtime"
        )
        return data.get("has_active_runtime", False)
    
    async def create(
        self,
        agent_id: str,
        subagent_id: Optional[str] = None,
        initial_context: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new runtime.
        
        Args:
            agent_id: Agent identifier
            subagent_id: SubAgent identifier (defaults to main)
            initial_context: Initial conversation context
        
        Returns:
            Created runtime dict
        """
        return await self._http.post(
            f"{self.gateway_url}/internal/runtimes",
            json={
                "agent_id": agent_id,
                "subagent_id": subagent_id or "main",
                "initial_context": initial_context or [],
            }
        )
    
    async def create_main(self, agent_id: str) -> Dict[str, Any]:
        """Create a main runtime for an agent."""
        return await self._http.post(
            f"{self.gateway_url}/internal/runtimes/main",
            json={"agent_id": agent_id}
        )
    
    async def update(self, runtime_id: str, **kwargs) -> bool:
        """
        Update runtime fields.
        
        Supported fields:
            - status: "active", "completed", "interrupted", "failed"
            - context: List of messages
            - summary: Runtime summary
            - metadata: Additional metadata
        """
        await self._http.patch(
            f"{self.gateway_url}/internal/runtimes/{runtime_id}",
            json=kwargs
        )
        return True
    
    async def delete(self, runtime_id: str):
        """Delete a runtime."""
        await self._http.delete(
            f"{self.gateway_url}/internal/runtimes/{runtime_id}"
        )
    
    async def rest(
        self,
        runtime_id: str,
        wake_triggers: List[Dict[str, Any]],
        handoff_notes: Optional[str] = None
    ):
        """
        Put a runtime to rest with wake triggers.
        
        Args:
            runtime_id: Runtime to rest
            wake_triggers: Conditions that will wake the runtime
            handoff_notes: Notes for next activation
        """
        await self._http.post(
            f"{self.gateway_url}/internal/runtimes/{runtime_id}/rest",
            json={
                "wake_triggers": wake_triggers,
                "handoff_notes": handoff_notes,
            }
        )
    
    async def wake(self, runtime_id: str) -> bool:
        """
        Wake a resting runtime.
        
        Returns:
            True if woken, False if already active
        """
        data = await self._http.post(
            f"{self.gateway_url}/internal/runtimes/{runtime_id}/wake"
        )
        return data.get("success", False)
    
    async def advance_round(self, runtime_id: str) -> Dict[str, Any]:
        """
        Advance runtime to next round.
        
        Returns:
            {"round_id": str, "round_number": int}
        """
        return await self._http.post(
            f"{self.gateway_url}/internal/runtimes/{runtime_id}/advance"
        )
    
    async def claim_phase(
        self,
        runtime_id: str,
        phase: str,
        worker_id: str
    ) -> bool:
        """
        Atomically claim a phase in current round.
        
        Returns:
            True if claimed, False if already claimed
        """
        data = await self._http.post(
            f"{self.gateway_url}/internal/runtimes/{runtime_id}/claim-phase",
            json={"phase": phase, "worker_id": worker_id}
        )
        return data.get("success", False)
