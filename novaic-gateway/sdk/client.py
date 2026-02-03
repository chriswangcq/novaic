"""
Gateway SDK Main Client
"""

from typing import Optional
from .base import HttpClient
from .pipeline import PipelineAPI
from .runtime import RuntimeAPI
from .subagent import SubAgentAPI
from .messages import MessagesAPI
from .mcp import McpAPI
from .llm import LlmAPI
from .health import HealthAPI


class GatewaySDK:
    """
    NovAIC Gateway SDK - Main entry point.
    
    All services communicate ONLY with Gateway.
    MCP management operations are proxied through Gateway.
    
    Usage:
        # As async context manager (recommended)
        async with GatewaySDK() as sdk:
            task = await sdk.pipeline.claim_task(["launcher"])
            runtime = await sdk.runtime.get(task["runtime_id"])
            await sdk.pipeline.mark_done(task["id"], {"status": "ok"})
        
        # Manual lifecycle
        sdk = GatewaySDK()
        try:
            await sdk.pipeline.claim_task(...)
        finally:
            await sdk.close()
    
    Configuration:
        GatewaySDK(
            gateway_url="http://127.0.0.1:19999",
            timeout=30.0,
            max_retries=3,
        )
    """
    
    def __init__(
        self,
        gateway_url: str = "http://127.0.0.1:19999",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize Gateway SDK.
        
        Args:
            gateway_url: Gateway API URL (all operations go through here)
            timeout: Default request timeout in seconds
            max_retries: Max retry attempts for failed requests
            retry_delay: Initial delay between retries (exponential backoff)
        """
        self._http = HttpClient(
            gateway_url=gateway_url,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        
        # API modules
        self.pipeline = PipelineAPI(self._http)
        self.runtime = RuntimeAPI(self._http)
        self.subagent = SubAgentAPI(self._http)
        self.messages = MessagesAPI(self._http)
        self.mcp = McpAPI(self._http)
        self.llm = LlmAPI(self._http)
        self.health = HealthAPI(self._http)  # v18
    
    @property
    def gateway_url(self) -> str:
        """Gateway API URL."""
        return self._http.gateway_url
    
    async def close(self):
        """Close HTTP connections."""
        await self._http.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    # ==================== Convenience Methods ====================
    
    async def health_check(self) -> bool:
        """Check if Gateway is healthy."""
        try:
            await self._http.get(f"{self.gateway_url}/api/health")
            return True
        except Exception:
            return False
    
    async def interrupt(self, agent_id: Optional[str] = None) -> dict:
        """
        Interrupt execution.
        
        Cancels pending tasks and interrupts active runtimes.
        
        Args:
            agent_id: Specific agent to interrupt, or all if None
        
        Returns:
            {"cancelled_tasks": int, "interrupted_runtimes": int}
        """
        return await self._http.post(
            f"{self.gateway_url}/api/interrupt",
            json={"agent_id": agent_id} if agent_id else {}
        )
    
    async def get_agent(self, agent_id: str) -> Optional[dict]:
        """Get agent configuration."""
        from .exceptions import GatewayNotFoundError
        try:
            return await self._http.get(
                f"{self.gateway_url}/api/agents/{agent_id}"
            )
        except GatewayNotFoundError:
            return None
    
    async def get_agents_with_setup_complete(self) -> list:
        """Get all agents that have completed setup."""
        data = await self._http.get(
            f"{self.gateway_url}/internal/agents/setup-complete"
        )
        return data.get("agents", [])
    
    async def set_agent_awake(self, agent_id: str):
        """Mark an agent as awake."""
        await self._http.post(
            f"{self.gateway_url}/internal/agents/{agent_id}/awake"
        )
    
    async def set_agent_sleep(self, agent_id: str):
        """Mark an agent as sleeping."""
        await self._http.post(
            f"{self.gateway_url}/internal/agents/{agent_id}/sleep"
        )
    
    async def broadcast_new_task(self, agent_id: str, task_type: str):
        """Broadcast new task event for SSE."""
        await self._http.post(
            f"{self.gateway_url}/internal/broadcast/new-task",
            json={"agent_id": agent_id, "task_type": task_type}
        )
    
    async def broadcast_chat_message(
        self,
        agent_id: str,
        message: dict,
        event_type: str = "assistant_message"
    ):
        """Broadcast chat message event for SSE."""
        await self._http.post(
            f"{self.gateway_url}/internal/broadcast/chat-message",
            json={
                "agent_id": agent_id,
                "message": message,
                "event_type": event_type,
            }
        )


# Convenience function for quick SDK creation
def create_sdk(
    gateway_url: str = "http://127.0.0.1:19999",
    **kwargs
) -> GatewaySDK:
    """
    Create a GatewaySDK instance.
    
    Usage:
        sdk = create_sdk()
        async with sdk:
            await sdk.pipeline.claim_task(...)
    """
    return GatewaySDK(
        gateway_url=gateway_url,
        **kwargs
    )
