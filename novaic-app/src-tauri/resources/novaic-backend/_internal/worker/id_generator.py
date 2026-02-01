"""
ID Generator

Generates hierarchical IDs for the multi-process architecture:
- agent_id: Agent configuration ID
- subagent_id: Runtime instance ID (main-xxx or sub-xxx)
- round_id: ReACT round ID (round-1, round-2, ...)
- mcpcall_id: MCP call ID within round (mc-1, mc-2, ...)
- idempotency_key: Combined key for idempotent execution

v11: Created for multi-process architecture.
"""

import uuid
from typing import Optional


class IDGenerator:
    """
    Generates and manages hierarchical IDs.
    
    ID Hierarchy:
        agent_id                    Agent 配置 ID (如 "牛马一号" 的配置)
            │
            └─── subagent_id        运行时实例 ID
                      │             - Main Agent: "main-{uuid}"
                      │             - SubAgent: "sub-{uuid}"
                      │
                      └─── round_id         ReACT 轮次 ID
                               │             - "round-1", "round-2", ...
                               │
                               └─── mcpcall_id    MCP 调用 ID
                                                  - "mc-1", "mc-2", ...
    """
    
    @staticmethod
    def subagent_id(is_main: bool = True) -> str:
        """
        Generate a subagent ID.
        
        Args:
            is_main: True for main agent, False for subagent
        
        Returns:
            ID like "main-abc12345" or "sub-abc12345"
        """
        prefix = "main" if is_main else "sub"
        return f"{prefix}-{uuid.uuid4().hex[:8]}"
    
    @staticmethod
    def round_id(round_number: int) -> str:
        """
        Generate a round ID.
        
        Args:
            round_number: Round number (1, 2, 3, ...)
        
        Returns:
            ID like "round-1"
        """
        return f"round-{round_number}"
    
    @staticmethod
    def mcpcall_id(call_number: int) -> str:
        """
        Generate an MCP call ID.
        
        Args:
            call_number: Call number within round (1, 2, 3, ...)
        
        Returns:
            ID like "mc-1"
        """
        return f"mc-{call_number}"
    
    @staticmethod
    def idempotency_key(
        agent_id: str,
        subagent_id: str,
        round_id: str,
        mcpcall_id: str,
    ) -> str:
        """
        Generate an idempotency key.
        
        Args:
            agent_id: Agent configuration ID
            subagent_id: Runtime instance ID
            round_id: Round ID
            mcpcall_id: MCP call ID
        
        Returns:
            Key like "agent-001-main-abc123-round-1-mc-1"
        """
        return f"{agent_id}-{subagent_id}-{round_id}-{mcpcall_id}"
    
    @staticmethod
    def parse_idempotency_key(key: str) -> Optional[dict]:
        """
        Parse an idempotency key back to its components.
        
        Args:
            key: Idempotency key string
        
        Returns:
            Dict with agent_id, subagent_id, round_id, mcpcall_id
            or None if parsing fails
        """
        try:
            # Format: {agent_id}-{subagent_id}-{round_id}-{mcpcall_id}
            # subagent_id contains a hyphen (main-xxx or sub-xxx)
            # round_id contains a hyphen (round-N)
            # mcpcall_id contains a hyphen (mc-N)
            
            parts = key.split("-")
            if len(parts) < 6:
                return None
            
            # Find the subagent prefix (main or sub)
            subagent_start = None
            for i, part in enumerate(parts):
                if part in ("main", "sub"):
                    subagent_start = i
                    break
            
            if subagent_start is None:
                return None
            
            # agent_id is everything before subagent
            agent_id = "-".join(parts[:subagent_start])
            
            # subagent_id is prefix + uuid
            subagent_id = f"{parts[subagent_start]}-{parts[subagent_start + 1]}"
            
            # Find round
            round_start = None
            for i in range(subagent_start + 2, len(parts)):
                if parts[i] == "round":
                    round_start = i
                    break
            
            if round_start is None:
                return None
            
            round_id = f"{parts[round_start]}-{parts[round_start + 1]}"
            
            # mcpcall_id is the rest
            mcpcall_id = f"{parts[round_start + 2]}-{parts[round_start + 3]}"
            
            return {
                "agent_id": agent_id,
                "subagent_id": subagent_id,
                "round_id": round_id,
                "mcpcall_id": mcpcall_id,
            }
        except (IndexError, ValueError):
            return None
    
    @staticmethod
    def task_id() -> str:
        """Generate a unique task ID."""
        return f"task-{uuid.uuid4().hex[:12]}"
    
    @staticmethod
    def worker_id() -> str:
        """Generate a unique worker ID."""
        return f"worker-{uuid.uuid4().hex[:8]}"


class RoundTracker:
    """
    Tracks round and mcpcall IDs for an agent instance.
    
    Usage:
        tracker = RoundTracker(agent_id, subagent_id)
        
        # Start a new round
        round_id = tracker.next_round()
        
        # Get next mcpcall ID within current round
        mc_id = tracker.next_mcpcall()
        key = tracker.idempotency_key()
    """
    
    def __init__(self, agent_id: str, subagent_id: str):
        """
        Initialize tracker.
        
        Args:
            agent_id: Agent configuration ID
            subagent_id: Runtime instance ID
        """
        self.agent_id = agent_id
        self.subagent_id = subagent_id
        self._round_number = 0
        self._mcpcall_number = 0
    
    @property
    def round_id(self) -> str:
        """Current round ID."""
        return IDGenerator.round_id(self._round_number)
    
    @property
    def mcpcall_id(self) -> str:
        """Current mcpcall ID."""
        return IDGenerator.mcpcall_id(self._mcpcall_number)
    
    def next_round(self) -> str:
        """
        Start a new round.
        
        Returns:
            New round ID
        """
        self._round_number += 1
        self._mcpcall_number = 0
        return self.round_id
    
    def next_mcpcall(self) -> str:
        """
        Get next mcpcall ID.
        
        Returns:
            New mcpcall ID
        """
        self._mcpcall_number += 1
        return self.mcpcall_id
    
    def idempotency_key(self) -> str:
        """
        Get current idempotency key.
        
        Returns:
            Idempotency key for current round and mcpcall
        """
        return IDGenerator.idempotency_key(
            self.agent_id,
            self.subagent_id,
            self.round_id,
            self.mcpcall_id,
        )
    
    def get_state(self) -> dict:
        """Get current tracker state."""
        return {
            "agent_id": self.agent_id,
            "subagent_id": self.subagent_id,
            "round_number": self._round_number,
            "mcpcall_number": self._mcpcall_number,
            "round_id": self.round_id,
            "mcpcall_id": self.mcpcall_id,
        }
    
    def set_state(self, round_number: int, mcpcall_number: int = 0):
        """
        Set tracker state (for recovery).
        
        Args:
            round_number: Round number to set
            mcpcall_number: MCP call number to set
        """
        self._round_number = round_number
        self._mcpcall_number = mcpcall_number
