"""
Agent State Repository

Data access layer for agent_state table.
Handles Agent runtime state persistence (sleep/awake, wake triggers, etc.).
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any


class AgentStateRepository:
    """Repository for agent_state table."""
    
    def __init__(self, db):
        self.db = db
    
    def get_state(self, agent_id: str) -> Dict[str, Any]:
        """
        Get Agent state.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            State dict with keys: agent_id, state, wake_triggers, rest_reason, rest_started_at, last_active_at
        """
        row = self.db.fetchone(
            "SELECT * FROM agent_state WHERE agent_id = ?",
            (agent_id,)
        )
        
        if row:
            return {
                "agent_id": row["agent_id"],
                "state": row["state"],
                "wake_triggers": json.loads(row["wake_triggers"] or "[]"),
                "rest_reason": row["rest_reason"],
                "rest_started_at": row["rest_started_at"],
                "last_active_at": row["last_active_at"],
            }
        
        # Return default state if not found
        return {
            "agent_id": agent_id,
            "state": "awake",
            "wake_triggers": [],
            "rest_reason": None,
            "rest_started_at": None,
            "last_active_at": None,
        }
    
    def set_state(self, agent_id: str, state: str):
        """
        Set Agent state.
        
        Args:
            agent_id: Agent ID
            state: State value ('sleep' or 'awake')
        """
        now = datetime.utcnow().isoformat()
        
        with self.db.transaction("agent", resource_id=agent_id):
            self.db.execute(
                """INSERT INTO agent_state (agent_id, state, last_active_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(agent_id) DO UPDATE SET 
                   state = excluded.state, 
                   last_active_at = excluded.last_active_at""",
                (agent_id, state, now)
            )
    
    def set_sleep(
        self,
        agent_id: str,
        reason: str,
        wake_triggers: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Set Agent to sleep state.
        
        Args:
            agent_id: Agent ID
            reason: Reason for sleeping
            wake_triggers: List of wake trigger conditions
        """
        now = datetime.utcnow().isoformat()
        
        with self.db.transaction("agent", resource_id=agent_id):
            self.db.execute(
                """INSERT INTO agent_state (agent_id, state, rest_reason, wake_triggers, rest_started_at, last_active_at)
                   VALUES (?, 'sleep', ?, ?, ?, ?)
                   ON CONFLICT(agent_id) DO UPDATE SET 
                   state = 'sleep',
                   rest_reason = excluded.rest_reason,
                   wake_triggers = excluded.wake_triggers,
                   rest_started_at = excluded.rest_started_at,
                   last_active_at = excluded.last_active_at""",
                (agent_id, reason, json.dumps(wake_triggers or []), now, now)
            )
    
    def set_awake(self, agent_id: str):
        """
        Set Agent to awake state.
        
        Clears rest_reason, wake_triggers, and rest_started_at.
        
        Args:
            agent_id: Agent ID
        """
        now = datetime.utcnow().isoformat()
        
        with self.db.transaction("agent", resource_id=agent_id):
            self.db.execute(
                """INSERT INTO agent_state (agent_id, state, rest_reason, wake_triggers, rest_started_at, last_active_at)
                   VALUES (?, 'awake', NULL, '[]', NULL, ?)
                   ON CONFLICT(agent_id) DO UPDATE SET 
                   state = 'awake',
                   rest_reason = NULL,
                   wake_triggers = '[]',
                   rest_started_at = NULL,
                   last_active_at = excluded.last_active_at""",
                (agent_id, now)
            )
    
    def update_last_active(self, agent_id: str):
        """
        Update last_active_at timestamp.
        
        Args:
            agent_id: Agent ID
        """
        now = datetime.utcnow().isoformat()
        
        with self.db.transaction("agent", resource_id=agent_id):
            self.db.execute(
                """UPDATE agent_state SET last_active_at = ? WHERE agent_id = ?""",
                (now, agent_id)
            )
    
    def is_sleeping(self, agent_id: str) -> bool:
        """
        Check if Agent is sleeping.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            True if Agent is in sleep state
        """
        state = self.get_state(agent_id)
        return state["state"] == "sleep"
    
    def is_awake(self, agent_id: str) -> bool:
        """
        Check if Agent is awake.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            True if Agent is in awake state
        """
        state = self.get_state(agent_id)
        return state["state"] == "awake"
    
    def get_wake_triggers(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get wake triggers for an Agent.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            List of wake trigger conditions
        """
        state = self.get_state(agent_id)
        return state["wake_triggers"]
    
    def ensure_exists(self, agent_id: str):
        """
        Ensure agent_state record exists for an Agent.
        
        Creates a default awake state if not exists.
        
        Args:
            agent_id: Agent ID
        """
        now = datetime.utcnow().isoformat()
        
        with self.db.transaction("agent", resource_id=agent_id):
            self.db.execute(
                """INSERT OR IGNORE INTO agent_state (agent_id, state, wake_triggers, last_active_at)
                   VALUES (?, 'awake', '[]', ?)""",
                (agent_id, now)
            )
    
    def delete_state(self, agent_id: str):
        """
        Delete Agent state record.
        
        Args:
            agent_id: Agent ID
        """
        with self.db.transaction("agent", resource_id=agent_id):
            self.db.execute(
                "DELETE FROM agent_state WHERE agent_id = ?",
                (agent_id,)
            )
