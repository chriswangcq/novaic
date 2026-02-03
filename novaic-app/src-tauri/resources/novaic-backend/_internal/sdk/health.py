"""
Health API (v18)

Health monitoring operations for detecting stuck states.
"""

from .base import BaseAPI


class HealthAPI(BaseAPI):
    """
    Health monitoring operations.
    
    Usage:
        count = await sdk.health.get_stuck_sending_count(30)
        count = await sdk.health.get_stuck_awaking_count(60)
        reset = await sdk.health.reset_stuck_awaking(60)
    """
    
    async def get_stuck_sending_count(self, timeout_seconds: int = 30) -> int:
        """Get count of messages stuck in 'sending' state."""
        data = await self._http.get(
            f"{self.gateway_url}/internal/health/stuck-sending",
            params={"timeout_seconds": timeout_seconds}
        )
        return data.get("count", 0)
    
    async def get_stuck_awaking_count(self, timeout_seconds: int = 60) -> int:
        """Get count of SubAgents stuck in 'awaking' state."""
        data = await self._http.get(
            f"{self.gateway_url}/internal/health/stuck-awaking",
            params={"timeout_seconds": timeout_seconds}
        )
        return data.get("count", 0)
    
    async def reset_stuck_awaking(self, timeout_seconds: int = 60) -> int:
        """Reset SubAgents stuck in 'awaking' state to 'sleeping'.
        
        Returns number of SubAgents reset.
        """
        data = await self._http.post(
            f"{self.gateway_url}/internal/health/reset-stuck-awaking",
            params={"timeout_seconds": timeout_seconds}
        )
        return data.get("reset_count", 0)
