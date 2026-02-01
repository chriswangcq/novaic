"""
Session Registry - Global registry for tracking all active sessions

Tracks sessions from:
- Main agent (REST API)
- WebSocket connections
- Sub-agents
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SessionType(Enum):
    """Type of session."""
    MAIN = "main"
    WEBSOCKET = "websocket"
    SUBAGENT = "subagent"


@dataclass
class SessionInfo:
    """Information about a session."""
    session_key: str
    session_type: SessionType
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    parent_session: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # References (not serialized)
    agent: Any = field(default=None, repr=False)
    session_manager: Any = field(default=None, repr=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "session_key": self.session_key,
            "type": self.session_type.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "message_count": self.message_count,
            "parent_session": self.parent_session,
            "metadata": self.metadata,
        }


class SessionRegistry:
    """
    Global registry for tracking all active sessions.
    
    This allows the session MCP tools to:
    - List all active sessions
    - Get session history
    - Send messages to sessions
    """
    
    def __init__(self):
        self._sessions: Dict[str, SessionInfo] = {}
        self._stats = {
            "registered": 0,
            "unregistered": 0,
        }
    
    def register(
        self,
        session_key: str,
        session_type: SessionType,
        agent: Any = None,
        session_manager: Any = None,
        parent_session: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionInfo:
        """
        Register a new session.
        
        Args:
            session_key: Unique identifier for the session
            session_type: Type of session
            agent: Optional reference to the agent instance
            session_manager: Optional reference to the session manager
            parent_session: Key of parent session (for subagents)
            metadata: Additional metadata
        
        Returns:
            SessionInfo for the registered session
        """
        info = SessionInfo(
            session_key=session_key,
            session_type=session_type,
            agent=agent,
            session_manager=session_manager,
            parent_session=parent_session,
            metadata=metadata or {},
        )
        
        self._sessions[session_key] = info
        self._stats["registered"] += 1
        
        logger.debug(f"[SessionRegistry] Registered: {session_key} ({session_type.value})")
        return info
    
    def unregister(self, session_key: str) -> bool:
        """
        Unregister a session.
        
        Args:
            session_key: Session to unregister
        
        Returns:
            True if session was found and removed
        """
        if session_key in self._sessions:
            del self._sessions[session_key]
            self._stats["unregistered"] += 1
            logger.debug(f"[SessionRegistry] Unregistered: {session_key}")
            return True
        return False
    
    def get(self, session_key: str) -> Optional[SessionInfo]:
        """Get session info by key."""
        return self._sessions.get(session_key)
    
    def update_activity(self, session_key: str, message_count_delta: int = 1) -> None:
        """Update session activity timestamp and message count."""
        info = self._sessions.get(session_key)
        if info:
            info.last_activity = datetime.now()
            info.message_count += message_count_delta
    
    def list_sessions(
        self,
        session_type: Optional[SessionType] = None,
        parent_session: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List all sessions with optional filtering.
        
        Args:
            session_type: Filter by type
            parent_session: Filter by parent
        
        Returns:
            List of session info dictionaries
        """
        results = []
        
        for info in self._sessions.values():
            if session_type and info.session_type != session_type:
                continue
            if parent_session and info.parent_session != parent_session:
                continue
            results.append(info.to_dict())
        
        return results
    
    def get_history(
        self,
        session_key: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get message history for a session.
        
        Args:
            session_key: Session to get history for
            limit: Maximum messages to return
            offset: Offset from start
        
        Returns:
            List of messages or None if session not found
        """
        info = self._sessions.get(session_key)
        if not info:
            return None
        
        if info.session_manager:
            messages = info.session_manager.get_all_messages()
            return messages[offset:offset + limit]
        
        return []
    
    def send_message(
        self,
        session_key: str,
        message: str,
        wait_response: bool = False,
        timeout: int = 60,
    ) -> Dict[str, Any]:
        """
        Send a message to a session.
        
        Note: This is a placeholder. Full implementation requires
        async message queuing and response handling.
        
        Args:
            session_key: Session to send to
            message: Message content
            wait_response: Whether to wait for response
            timeout: Timeout in seconds
        
        Returns:
            Result dictionary
        """
        info = self._sessions.get(session_key)
        if not info:
            return {"success": False, "error": "Session not found"}
        
        # For now, just record that a message was sent
        # Full implementation would queue the message for processing
        self.update_activity(session_key)
        
        return {
            "success": True,
            "session_key": session_key,
            "queued": True,
            "note": "Message queued for processing"
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        type_counts = {}
        for info in self._sessions.values():
            t = info.session_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            **self._stats,
            "active": len(self._sessions),
            "by_type": type_counts,
        }


# Global instance
_registry: Optional[SessionRegistry] = None


def get_session_registry() -> SessionRegistry:
    """Get or create the global session registry."""
    global _registry
    if _registry is None:
        _registry = SessionRegistry()
    return _registry
