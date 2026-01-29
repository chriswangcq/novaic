"""
BaseTrigger - Abstract base class for wake triggers
"""

from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class TriggerConfig:
    """Base configuration for triggers."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
        }


class BaseTrigger(ABC):
    """
    Abstract base class for wake triggers.
    
    Triggers are event sources that can wake the agent.
    Each trigger type implements its own logic for when to fire.
    """
    
    def __init__(self, config: TriggerConfig):
        """
        Initialize the trigger.
        
        Args:
            config: Trigger configuration
        """
        self.config = config
        self._on_trigger: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]] = None
        self._running = False
    
    @property
    def id(self) -> str:
        """Get trigger ID."""
        return self.config.id
    
    @property
    def name(self) -> str:
        """Get trigger name."""
        return self.config.name
    
    @property
    def enabled(self) -> bool:
        """Check if trigger is enabled."""
        return self.config.enabled
    
    @property
    def is_running(self) -> bool:
        """Check if trigger is running."""
        return self._running
    
    def set_callback(
        self,
        callback: Callable[[str, Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        Set the callback to invoke when trigger fires.
        
        Args:
            callback: Async function(trigger_id, data) to call
        """
        self._on_trigger = callback
    
    async def _fire(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Fire the trigger.
        
        Args:
            message: Wake message for the agent
            data: Additional trigger data
        """
        if not self._on_trigger:
            return
        
        await self._on_trigger(self.id, {
            "message": message,
            "trigger_name": self.name,
            **(data or {})
        })
    
    @abstractmethod
    async def start(self) -> None:
        """Start the trigger."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the trigger."""
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Get trigger information."""
        pass
    
    def enable(self) -> None:
        """Enable the trigger."""
        self.config.enabled = True
    
    def disable(self) -> None:
        """Disable the trigger."""
        self.config.enabled = False
