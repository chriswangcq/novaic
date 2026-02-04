"""
SubAgent Repository

Manages subagents table for SubAgent state management.
Each Agent has one Main SubAgent, can spawn Sub SubAgents.
SubAgents own multiple Runtimes (one active at a time).

v14: New entity for SubAgent state refactor.
v16: Async SubAgent support - added task/progress/result/error/timeout_at fields.
"""

import json
import uuid
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class SubAgent:
    """SubAgent data model."""
    subagent_id: str          # "main" or "sub-xxx"
    agent_id: str
    type: str                 # 'main' or 'sub'
    parent_subagent_id: Optional[str] = None  # For sub type
    
    # Status
    status: str = 'sleeping'  # sleeping / awake / summarizing / running / completed / failed / cancelled
    
    # Context management
    historical_summary: Optional[str] = None  # Merged historical runtime summaries
    
    # Rest/wake related
    wake_triggers: List[Dict[str, Any]] = field(default_factory=lambda: [{"type": "user_response"}])
    handoff_notes: Optional[str] = None
    
    # Async SubAgent fields (v16)
    task: Optional[str] = None           # Task description for sub subagents
    progress: Optional[str] = None       # Current progress description
    result: Optional[str] = None         # Final result (when completed)
    error: Optional[str] = None          # Error message (when failed)
    timeout_at: Optional[str] = None     # Timeout timestamp
    
    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'subagent_id': self.subagent_id,
            'agent_id': self.agent_id,
            'type': self.type,
            'parent_subagent_id': self.parent_subagent_id,
            'status': self.status,
            'historical_summary': self.historical_summary,
            'wake_triggers': self.wake_triggers,
            'handoff_notes': self.handoff_notes,
            'task': self.task,
            'progress': self.progress,
            'result': self.result,
            'error': self.error,
            'timeout_at': self.timeout_at,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


class SubAgentRepository:
    """Repository for subagents table operations."""
    
    _COLUMNS = """
        subagent_id, agent_id, type, parent_subagent_id,
        status, historical_summary, wake_triggers, handoff_notes,
        task, progress, result, error, timeout_at,
        created_at, updated_at
    """
    
    def __init__(self, db):
        self.db = db
    
    # ========================================
    # Create Operations
    # ========================================
    
    def create_main_subagent(self, agent_id: str) -> SubAgent:
        """Create the main SubAgent for an agent."""
        now = datetime.utcnow().isoformat()
        
        # v14: subagent_id 带编号，方便区分不同 agent 的 main subagent
        subagent_id = f"main-{agent_id[:8]}"
        
        subagent = SubAgent(
            subagent_id=subagent_id,
            agent_id=agent_id,
            type='main',
            status='sleeping',
            created_at=now,
            updated_at=now,
        )
        
        self._insert(subagent)
        return subagent
    
    def create_sub_subagent(
        self, 
        agent_id: str, 
        parent_subagent_id: str = "main",
        task: Optional[str] = None,
        timeout_at: Optional[str] = None,
    ) -> SubAgent:
        """Create a sub SubAgent.
        
        Args:
            agent_id: Parent agent ID
            parent_subagent_id: Parent SubAgent ID
            task: Task description (for async SubAgents)
            timeout_at: Timeout timestamp (for async SubAgents)
        """
        subagent_id = f"sub-{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        subagent = SubAgent(
            subagent_id=subagent_id,
            agent_id=agent_id,
            type='sub',
            parent_subagent_id=parent_subagent_id,
            status='sleeping',
            task=task,
            timeout_at=timeout_at,
            created_at=now,
            updated_at=now,
        )
        
        self._insert(subagent)
        return subagent
    
    def _insert(self, subagent: SubAgent):
        """Insert a SubAgent into the database."""
        with self.db.get_connection("agent", resource_id=subagent.agent_id) as conn:
            conn.execute("""
                INSERT INTO subagents (
                    subagent_id, agent_id, type, parent_subagent_id,
                    status, historical_summary, wake_triggers, handoff_notes,
                    task, progress, result, error, timeout_at,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                subagent.subagent_id,
                subagent.agent_id,
                subagent.type,
                subagent.parent_subagent_id,
                subagent.status,
                subagent.historical_summary,
                json.dumps(subagent.wake_triggers),
                subagent.handoff_notes,
                subagent.task,
                subagent.progress,
                subagent.result,
                subagent.error,
                subagent.timeout_at,
                subagent.created_at,
                subagent.updated_at,
            ))
            conn.commit()
    
    # ========================================
    # Query Operations
    # ========================================
    
    def get_by_id(self, subagent_id: str, agent_id: str) -> Optional[SubAgent]:
        """Get a SubAgent by its ID and agent ID."""
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute(
                f"SELECT {self._COLUMNS} FROM subagents WHERE subagent_id = ? AND agent_id = ?",
                (subagent_id, agent_id)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_subagent(row)
            return None
    
    def get_main_subagent(self, agent_id: str) -> Optional[SubAgent]:
        """Get the main SubAgent for an agent."""
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute(f"""
                SELECT {self._COLUMNS} FROM subagents 
                WHERE agent_id = ? AND type = 'main'
                LIMIT 1
            """, (agent_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_subagent(row)
            return None
    
    def get_or_create_main_subagent(self, agent_id: str) -> SubAgent:
        """Get or create the main SubAgent for an agent."""
        subagent = self.get_main_subagent(agent_id)
        if not subagent:
            try:
                subagent = self.create_main_subagent(agent_id)
            except sqlite3.IntegrityError:
                # Concurrent create; fetch existing main subagent
                subagent = self.get_main_subagent(agent_id)
        return subagent
    
    def get_sub_subagents(self, agent_id: str) -> List[SubAgent]:
        """Get all sub SubAgents for an agent."""
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute(f"""
                SELECT {self._COLUMNS} FROM subagents 
                WHERE agent_id = ? AND type = 'sub'
                ORDER BY created_at ASC
            """, (agent_id,))
            rows = cursor.fetchall()
            return [self._row_to_subagent(row) for row in rows]
    
    # ========================================
    # Status Operations (Atomic)
    # ========================================
    
    def try_wake(
        self, 
        subagent_id: str, 
        agent_id: str, 
        target_status: str = "awake"
    ) -> bool:
        """
        Atomically wake a SubAgent (sleeping/failed -> target_status).
        Uses CAS to ensure only one caller succeeds.
        
        Args:
            target_status: "awaking" (intermediate) or "awake" (final)
        
        Returns True if wake succeeded, False if already awake/awaking.
        """
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            # CAS: sleeping OR failed → target_status
            cursor = conn.execute("""
                UPDATE subagents 
                SET status = ?, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ? AND status IN ('sleeping', 'failed')
            """, (target_status, now, subagent_id, agent_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def set_sleeping(self, subagent_id: str, agent_id: str):
        """Set SubAgent to sleeping status."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents 
                SET status = 'sleeping', updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (now, subagent_id, agent_id))
            conn.commit()
    
    def set_summarizing(self, subagent_id: str, agent_id: str):
        """Set SubAgent to summarizing status."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents 
                SET status = 'summarizing', updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (now, subagent_id, agent_id))
            conn.commit()
    
    def set_awake(self, subagent_id: str, agent_id: str):
        """Set SubAgent to awake status (for direct state changes)."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents 
                SET status = 'awake', updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (now, subagent_id, agent_id))
            conn.commit()
    
    def set_running(self, subagent_id: str, agent_id: str, progress: Optional[str] = None):
        """Set SubAgent to running status (for async SubAgents)."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents 
                SET status = 'running', progress = ?, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (progress, now, subagent_id, agent_id))
            conn.commit()
    
    def set_completed(self, subagent_id: str, agent_id: str, result: Optional[str] = None):
        """Set SubAgent to completed status with result."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents 
                SET status = 'completed', result = ?, progress = NULL, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (result, now, subagent_id, agent_id))
            conn.commit()
    
    def set_failed(self, subagent_id: str, agent_id: str, error: Optional[str] = None):
        """Set SubAgent to failed status with error message."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents 
                SET status = 'failed', error = ?, progress = NULL, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (error, now, subagent_id, agent_id))
            conn.commit()
    
    def set_cancelled(self, subagent_id: str, agent_id: str):
        """Set SubAgent to cancelled status."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents 
                SET status = 'cancelled', progress = NULL, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (now, subagent_id, agent_id))
            conn.commit()
    
    def update_progress(self, subagent_id: str, agent_id: str, progress: str):
        """Update the progress description for a running SubAgent."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents 
                SET progress = ?, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ? AND status = 'running'
            """, (progress, now, subagent_id, agent_id))
            conn.commit()
    
    # ========================================
    # Update Operations
    # ========================================
    
    def update_historical_summary(
        self, 
        subagent_id: str, 
        agent_id: str, 
        summary: str
    ):
        """Update the historical summary for a SubAgent."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents 
                SET historical_summary = ?, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (summary, now, subagent_id, agent_id))
            conn.commit()
    
    def update_wake_triggers(
        self, 
        subagent_id: str, 
        agent_id: str,
        wake_triggers: List[Dict[str, Any]],
        handoff_notes: Optional[str] = None
    ):
        """Update wake triggers and handoff notes for a SubAgent."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents 
                SET wake_triggers = ?, handoff_notes = ?, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (json.dumps(wake_triggers), handoff_notes, now, subagent_id, agent_id))
            conn.commit()
    
    # ========================================
    # Delete Operations
    # ========================================
    
    def delete(self, subagent_id: str, agent_id: str):
        """Delete a SubAgent."""
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute(
                "DELETE FROM subagents WHERE subagent_id = ? AND agent_id = ?",
                (subagent_id, agent_id)
            )
            conn.commit()
    
    def delete_all_for_agent(self, agent_id: str):
        """Delete all SubAgents for an agent."""
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute(
                "DELETE FROM subagents WHERE agent_id = ?",
                (agent_id,)
            )
            conn.commit()
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _row_to_subagent(self, row) -> SubAgent:
        """Convert database row to SubAgent object.
        
        Columns order (v16):
        0: subagent_id, 1: agent_id, 2: type, 3: parent_subagent_id,
        4: status, 5: historical_summary, 6: wake_triggers, 7: handoff_notes,
        8: task, 9: progress, 10: result, 11: error, 12: timeout_at,
        13: created_at, 14: updated_at
        """
        wake_triggers = json.loads(row[6]) if row[6] else [{"type": "user_response"}]
        
        return SubAgent(
            subagent_id=row[0],
            agent_id=row[1],
            type=row[2],
            parent_subagent_id=row[3],
            status=row[4] or 'sleeping',
            historical_summary=row[5],
            wake_triggers=wake_triggers,
            handoff_notes=row[7],
            task=row[8],
            progress=row[9],
            result=row[10],
            error=row[11],
            timeout_at=row[12],
            created_at=row[13],
            updated_at=row[14],
        )
    
    # ========================================
    # Health Monitor Operations (v18)
    # ========================================
    
    def get_stuck_awaking_count(self, timeout_seconds: int = 60) -> int:
        """Get count of SubAgents stuck in 'awaking' state."""
        result = self.db.fetchone(
            """SELECT COUNT(*) as count FROM subagents 
               WHERE status = 'awaking' 
               AND datetime(updated_at, '+' || ? || ' seconds') < datetime('now')""",
            (timeout_seconds,)
        )
        return result["count"] if result else 0
    
    def reset_stuck_awaking(self, timeout_seconds: int = 60) -> int:
        """Reset SubAgents stuck in 'awaking' state to 'sleeping'.
        
        Returns number of SubAgents reset.
        """
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("global") as conn:
            cursor = conn.execute(
                """UPDATE subagents 
                   SET status = 'sleeping', updated_at = ?
                   WHERE status = 'awaking' 
                   AND datetime(updated_at, '+' || ? || ' seconds') < datetime('now')""",
                (now, timeout_seconds)
            )
            conn.commit()
            return cursor.rowcount
