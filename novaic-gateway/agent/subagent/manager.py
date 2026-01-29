"""
SubAgentManager - Manages sub-agent execution for parallel tasks

Sub-agents run in separate sessions and can execute tasks independently.
They are useful for long-running or parallel tasks.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class SubAgentStatus(Enum):
    """Status of a sub-agent."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SubAgentConfig:
    """Configuration for spawning a sub-agent."""
    task: str  # Task description
    model: Optional[str] = None  # Model to use (inherit from parent if None)
    timeout_minutes: int = 30  # Maximum execution time
    announce: bool = True  # Announce results to parent session
    context: Optional[str] = None  # Additional context
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task": self.task,
            "model": self.model,
            "timeout_minutes": self.timeout_minutes,
            "announce": self.announce,
            "context": self.context,
        }


@dataclass
class SubAgentResult:
    """Result of a sub-agent execution."""
    subagent_id: str
    status: SubAgentStatus
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.now() - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "subagent_id": self.subagent_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class SubAgent:
    """A running sub-agent instance."""
    id: str
    config: SubAgentConfig
    parent_session_id: str
    session_key: str  # e.g., "subagent:abc123"
    status: SubAgentStatus = SubAgentStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    progress: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    task: Optional[asyncio.Task] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "session_key": self.session_key,
            "parent_session_id": self.parent_session_id,
            "task": self.config.task,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "progress": self.progress,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
        }
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.now() - self.started_at).total_seconds()
        return None


class SubAgentManager:
    """
    Manages sub-agent lifecycle and execution.
    
    Responsibilities:
    - Spawn sub-agents with separate sessions
    - Track sub-agent status and results
    - Handle timeouts and cancellation
    - Announce results to parent sessions
    """
    
    def __init__(
        self,
        agent_factory: Callable[[str], Awaitable[Any]],  # Creates new agent for session
        on_result: Optional[Callable[[str, SubAgentResult], Awaitable[None]]] = None,
        max_concurrent: int = 5,
    ):
        """
        Initialize the manager.
        
        Args:
            agent_factory: Factory function to create agents for sub-sessions
            on_result: Callback when sub-agent completes
            max_concurrent: Maximum concurrent sub-agents
        """
        self.agent_factory = agent_factory
        self.on_result = on_result
        self.max_concurrent = max_concurrent
        
        # Active sub-agents
        self._subagents: Dict[str, SubAgent] = {}
        
        # Statistics
        self._stats = {
            "spawned": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        }
    
    async def spawn(
        self,
        config: SubAgentConfig,
        parent_session_id: str,
        wait: bool = False,
    ) -> Dict[str, Any]:
        """
        Spawn a new sub-agent.
        
        Args:
            config: Sub-agent configuration
            parent_session_id: Parent session ID
            wait: If True, wait for completion and return result
        
        Returns:
            Dictionary with subagent_id, session_key, and optionally result
        """
        # Check concurrency limit
        running = sum(1 for s in self._subagents.values() if s.status == SubAgentStatus.RUNNING)
        if running >= self.max_concurrent:
            return {
                "success": False,
                "error": f"Maximum concurrent sub-agents ({self.max_concurrent}) reached",
            }
        
        # Create sub-agent
        subagent_id = str(uuid.uuid4())[:8]
        session_key = f"subagent:{subagent_id}"
        
        subagent = SubAgent(
            id=subagent_id,
            config=config,
            parent_session_id=parent_session_id,
            session_key=session_key,
        )
        
        self._subagents[subagent_id] = subagent
        self._stats["spawned"] += 1
        
        logger.info(f"[SubAgentManager] Spawned: {subagent_id} for task: {config.task[:50]}...")
        
        # Start execution
        subagent.task = asyncio.create_task(self._execute(subagent))
        
        if wait:
            # Wait for completion
            try:
                await asyncio.wait_for(
                    subagent.task,
                    timeout=config.timeout_minutes * 60
                )
            except asyncio.TimeoutError:
                subagent.status = SubAgentStatus.FAILED
                subagent.error = "Timeout"
            except asyncio.CancelledError:
                subagent.status = SubAgentStatus.CANCELLED
            
            return {
                "success": subagent.status == SubAgentStatus.COMPLETED,
                "subagent_id": subagent_id,
                "session_key": session_key,
                "status": subagent.status.value,
                "result": subagent.result,
                "error": subagent.error,
            }
        else:
            return {
                "success": True,
                "subagent_id": subagent_id,
                "session_key": session_key,
                "status": subagent.status.value,
            }
    
    async def _execute(self, subagent: SubAgent) -> None:
        """Execute a sub-agent task."""
        subagent.status = SubAgentStatus.RUNNING
        subagent.started_at = datetime.now()
        
        try:
            # Create agent for this sub-session
            agent = await self.agent_factory(subagent.session_key)
            
            # Build the task message
            task_message = subagent.config.task
            if subagent.config.context:
                task_message = f"Context: {subagent.config.context}\n\nTask: {task_message}"
            
            # Run the task
            final_result = None
            async for event in agent.chat(
                task_message,
                model=subagent.config.model,
            ):
                event_type = event.get("type")
                
                if event_type == "thinking":
                    subagent.progress = event.get("data", "")
                elif event_type == "final":
                    final_result = event.get("data", "")
                elif event_type == "error":
                    raise Exception(event.get("data", {}).get("error", "Unknown error"))
            
            # Mark completed
            subagent.status = SubAgentStatus.COMPLETED
            subagent.result = final_result
            subagent.completed_at = datetime.now()
            self._stats["completed"] += 1
            
            logger.info(f"[SubAgentManager] Completed: {subagent.id}")
            
        except asyncio.CancelledError:
            subagent.status = SubAgentStatus.CANCELLED
            subagent.completed_at = datetime.now()
            self._stats["cancelled"] += 1
            logger.info(f"[SubAgentManager] Cancelled: {subagent.id}")
            raise
            
        except Exception as e:
            subagent.status = SubAgentStatus.FAILED
            subagent.error = str(e)
            subagent.completed_at = datetime.now()
            self._stats["failed"] += 1
            logger.error(f"[SubAgentManager] Failed: {subagent.id} - {e}")
        
        finally:
            # Notify completion
            if self.on_result and subagent.config.announce:
                try:
                    result = SubAgentResult(
                        subagent_id=subagent.id,
                        status=subagent.status,
                        result=subagent.result,
                        error=subagent.error,
                        started_at=subagent.started_at,
                        completed_at=subagent.completed_at,
                    )
                    await self.on_result(subagent.parent_session_id, result)
                except Exception as e:
                    logger.error(f"[SubAgentManager] Failed to announce result: {e}")
    
    async def cancel(self, subagent_id: str) -> Dict[str, Any]:
        """
        Cancel a running sub-agent.
        
        Args:
            subagent_id: ID of the sub-agent to cancel
        
        Returns:
            Result dictionary
        """
        subagent = self._subagents.get(subagent_id)
        if not subagent:
            return {"success": False, "error": "Sub-agent not found"}
        
        if subagent.status != SubAgentStatus.RUNNING:
            return {
                "success": False,
                "error": f"Sub-agent is not running (status: {subagent.status.value})"
            }
        
        if subagent.task:
            subagent.task.cancel()
            try:
                await subagent.task
            except asyncio.CancelledError:
                pass
        
        return {
            "success": True,
            "subagent_id": subagent_id,
            "status": subagent.status.value,
        }
    
    def get_status(self, subagent_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a sub-agent."""
        subagent = self._subagents.get(subagent_id)
        if not subagent:
            return None
        return subagent.to_dict()
    
    def list_subagents(
        self,
        parent_session_id: Optional[str] = None,
        status: Optional[SubAgentStatus] = None,
    ) -> List[Dict[str, Any]]:
        """
        List sub-agents with optional filtering.
        
        Args:
            parent_session_id: Filter by parent session
            status: Filter by status
        
        Returns:
            List of sub-agent info dictionaries
        """
        results = []
        
        for subagent in self._subagents.values():
            if parent_session_id and subagent.parent_session_id != parent_session_id:
                continue
            if status and subagent.status != status:
                continue
            results.append(subagent.to_dict())
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        running = sum(1 for s in self._subagents.values() if s.status == SubAgentStatus.RUNNING)
        
        return {
            **self._stats,
            "total": len(self._subagents),
            "running": running,
            "max_concurrent": self.max_concurrent,
        }
    
    async def cleanup_completed(self, max_age_hours: int = 24) -> int:
        """
        Clean up completed sub-agents older than max_age.
        
        Args:
            max_age_hours: Maximum age in hours
        
        Returns:
            Number of sub-agents cleaned up
        """
        cutoff = datetime.now()
        cleaned = 0
        
        to_remove = []
        for subagent_id, subagent in self._subagents.items():
            if subagent.status in (SubAgentStatus.COMPLETED, SubAgentStatus.FAILED, SubAgentStatus.CANCELLED):
                if subagent.completed_at:
                    age_hours = (cutoff - subagent.completed_at).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        to_remove.append(subagent_id)
        
        for subagent_id in to_remove:
            del self._subagents[subagent_id]
            cleaned += 1
        
        if cleaned > 0:
            logger.info(f"[SubAgentManager] Cleaned up {cleaned} old sub-agents")
        
        return cleaned
