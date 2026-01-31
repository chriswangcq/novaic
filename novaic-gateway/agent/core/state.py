"""
Agent State Management

Manages the agent's operational state (SLEEP, AWAKE).

Note: The BUSY state is deprecated in the new Inbox-based architecture.
Agent state is now managed by AgentStateRepository (persistent) and 
processing is handled by AgentRunner. The BUSY state is kept for 
backward compatibility but should not be used in new code.
"""

import asyncio
import logging
from enum import Enum
from datetime import datetime
from typing import Optional, Callable, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """
    Agent operational states.
    
    Note: In the new Inbox-based architecture, only SLEEP and AWAKE are used.
    BUSY is deprecated and kept for backward compatibility only.
    """
    
    SLEEP = "sleep"    # Agent is dormant, not processing events
    AWAKE = "awake"    # Agent is ready to receive and process events
    BUSY = "busy"      # DEPRECATED: Agent is currently processing an event


@dataclass
class StateTransition:
    """Record of a state transition."""
    
    from_state: AgentState
    to_state: AgentState
    timestamp: datetime = field(default_factory=datetime.now)
    reason: Optional[str] = None


class StateManager:
    """
    Manages the agent's operational state.
    
    Features:
    - State transitions with callbacks
    - Auto-sleep after idle timeout
    - State history tracking
    - Async wait for state changes
    """
    
    def __init__(
        self,
        initial_state: AgentState = AgentState.AWAKE,
        idle_timeout: Optional[float] = None,  # Seconds before auto-sleep
        max_history: int = 100,
    ):
        """
        Initialize the state manager.
        
        Args:
            initial_state: Starting state
            idle_timeout: Auto-sleep after this many seconds of idle (None = disabled)
            max_history: Maximum state transitions to keep in history
        """
        self._state = initial_state
        self._idle_timeout = idle_timeout
        self._max_history = max_history
        
        # Callbacks
        self._on_state_change: List[Callable[[AgentState, AgentState], None]] = []
        
        # History
        self._history: List[StateTransition] = []
        
        # Timestamps
        self._last_state_change = datetime.now()
        self._last_activity = datetime.now()
        
        # Idle timeout task
        self._idle_task: Optional[asyncio.Task] = None
        
        # Event for waiting on state changes
        self._state_changed = asyncio.Event()
    
    def get_state(self) -> AgentState:
        """Get the current state."""
        return self._state
    
    def set_state(self, new_state: AgentState, reason: Optional[str] = None) -> bool:
        """
        Set the agent state.
        
        Args:
            new_state: The new state to transition to
            reason: Optional reason for the transition
        
        Returns:
            True if state changed, False if already in that state
        """
        if self._state == new_state:
            return False
        
        old_state = self._state
        self._state = new_state
        
        # Record transition
        transition = StateTransition(
            from_state=old_state,
            to_state=new_state,
            reason=reason,
        )
        self._history.append(transition)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        # Update timestamps
        self._last_state_change = datetime.now()
        self._last_activity = datetime.now()
        
        # Notify waiters
        self._state_changed.set()
        self._state_changed.clear()
        
        # Call callbacks
        for callback in self._on_state_change:
            try:
                callback(old_state, new_state)
            except Exception as e:
                logger.error(f"[StateManager] Callback error: {e}")
        
        # Reset idle timer
        self._reset_idle_timer()
        
        logger.info(f"[StateManager] State changed: {old_state.value} -> {new_state.value}"
                   + (f" ({reason})" if reason else ""))
        
        return True
    
    def record_activity(self) -> None:
        """Record activity to reset idle timer."""
        self._last_activity = datetime.now()
        self._reset_idle_timer()
    
    def _reset_idle_timer(self) -> None:
        """Reset the idle timeout timer."""
        # Cancel existing timer
        if self._idle_task:
            self._idle_task.cancel()
            self._idle_task = None
        
        # Start new timer if we have a timeout and are awake
        if self._idle_timeout and self._state == AgentState.AWAKE:
            self._idle_task = asyncio.create_task(self._idle_timeout_handler())
    
    async def _idle_timeout_handler(self) -> None:
        """Handle idle timeout - transition to sleep."""
        try:
            await asyncio.sleep(self._idle_timeout)
            
            # Only sleep if still awake (not busy)
            if self._state == AgentState.AWAKE:
                self.set_state(AgentState.SLEEP, reason="idle timeout")
                
        except asyncio.CancelledError:
            pass
    
    def on_state_change(self, callback: Callable[[AgentState, AgentState], None]) -> None:
        """
        Register a callback for state changes.
        
        Args:
            callback: Function(old_state, new_state) to call on state change
        """
        self._on_state_change.append(callback)
    
    async def wait_for_state(
        self,
        target_state: AgentState,
        timeout: Optional[float] = None
    ) -> bool:
        """
        Wait for the agent to reach a specific state.
        
        Args:
            target_state: The state to wait for
            timeout: Maximum time to wait (None = wait forever)
        
        Returns:
            True if state reached, False if timeout
        """
        if self._state == target_state:
            return True
        
        try:
            while self._state != target_state:
                if timeout:
                    await asyncio.wait_for(self._state_changed.wait(), timeout=timeout)
                else:
                    await self._state_changed.wait()
                
                if self._state == target_state:
                    return True
            
            return True
            
        except asyncio.TimeoutError:
            return False
    
    async def wait_until_available(self, timeout: Optional[float] = None) -> bool:
        """
        Wait until agent is not busy.
        
        Args:
            timeout: Maximum time to wait
        
        Returns:
            True if available, False if timeout
        """
        if self._state != AgentState.BUSY:
            return True
        
        try:
            while self._state == AgentState.BUSY:
                if timeout:
                    await asyncio.wait_for(self._state_changed.wait(), timeout=timeout)
                else:
                    await self._state_changed.wait()
            
            return True
            
        except asyncio.TimeoutError:
            return False
    
    def can_accept_event(self) -> bool:
        """Check if agent can accept new events."""
        return self._state != AgentState.BUSY
    
    def is_sleeping(self) -> bool:
        """Check if agent is sleeping."""
        return self._state == AgentState.SLEEP
    
    def get_history(self, limit: int = 10) -> List[dict]:
        """Get recent state transition history."""
        return [
            {
                "from": t.from_state.value,
                "to": t.to_state.value,
                "timestamp": t.timestamp.isoformat(),
                "reason": t.reason,
            }
            for t in self._history[-limit:]
        ]
    
    def get_info(self) -> dict:
        """Get current state info."""
        return {
            "state": self._state.value,
            "last_state_change": self._last_state_change.isoformat(),
            "last_activity": self._last_activity.isoformat(),
            "idle_timeout": self._idle_timeout,
            "history_count": len(self._history),
        }
