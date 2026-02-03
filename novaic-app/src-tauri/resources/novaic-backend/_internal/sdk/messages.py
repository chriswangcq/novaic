"""
Messages API
"""

from typing import Optional, Dict, Any, List
from .base import BaseAPI


class MessagesAPI(BaseAPI):
    """
    Message operations.
    
    Usage:
        messages = await sdk.messages.get_unread(agent_id)
        await sdk.messages.mark_processed(message_ids)
        has_new = await sdk.messages.has_unread(agent_id)
    """
    
    async def get_unread(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get unread messages for an agent."""
        data = await self._http.get(
            f"{self.gateway_url}/internal/messages/unread/{agent_id}"
        )
        return data.get("messages", [])
    
    async def get_unread_grouped(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get unread messages grouped by agent_id.
        
        Returns:
            {"agent_id_1": [messages], "agent_id_2": [messages], ...}
        """
        data = await self._http.get(
            f"{self.gateway_url}/internal/messages/unread-grouped"
        )
        return data.get("messages_by_agent", {})
    
    async def get_unread_count(self, agent_id: str) -> int:
        """Get count of unread messages for an agent."""
        data = await self._http.get(
            f"{self.gateway_url}/internal/messages/unread-count/{agent_id}"
        )
        return data.get("count", 0)
    
    async def has_unread(self, agent_id: str) -> bool:
        """Check if agent has unread messages."""
        count = await self.get_unread_count(agent_id)
        return count > 0
    
    async def mark_read(self, message_ids: List[str]):
        """Mark messages as read."""
        await self._http.patch(
            f"{self.gateway_url}/internal/messages/mark-read",
            json={"message_ids": message_ids}
        )
    
    async def mark_processed(self, message_ids: List[str]):
        """Mark messages as processed (by worker)."""
        await self._http.patch(
            f"{self.gateway_url}/internal/messages/mark-processed",
            json={"message_ids": message_ids}
        )
    
    async def send(
        self,
        agent_id: str,
        content: str,
        message_type: str = "user",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a new message.
        
        Args:
            agent_id: Target agent
            content: Message content
            message_type: "user", "system", "tool_result"
            metadata: Optional metadata
        
        Returns:
            Created message dict
        """
        return await self._http.post(
            f"{self.gateway_url}/internal/messages",
            json={
                "agent_id": agent_id,
                "content": content,
                "type": message_type,
                "metadata": metadata,
            }
        )
    
    # ==================== Monitor Queue (v18) ====================
    
    async def claim_sending(self) -> Optional[Dict[str, Any]]:
        """
        CAS claim a sending message (sending → sent).
        
        Used by Monitor service to consume the message queue.
        
        Returns:
            Claimed message dict, or None if queue is empty
        """
        data = await self._http.post(
            f"{self.gateway_url}/internal/messages/claim-sending"
        )
        return data.get("message")
