"""
SubAgent Repository

Manages subagents table for SubAgent state management.
Each Agent has one Main SubAgent, can spawn Sub SubAgents.
SubAgents own multiple Runtimes (one active at a time).

v14: New entity for SubAgent state refactor.
"""

import json
import uuid
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
    status: str = 'sleeping'  # sleeping / awake / summarizing
    
    # Context management
    historical_summary: Optional[str] = None  # Merged historical runtime summaries
    
    # Rest/wake related
    wake_triggers: List[Dict[str, Any]] = field(default_factory=lambda: [{"type": "user_response"}])
    handoff_notes: Optional[str] = None
    
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
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


class SubAgentRepository:
    """Repository for subagents table operations."""
    
    _COLUMNS = """
        subagent_id, agent_id, type, parent_subagent_id,
        status, historical_summary, wake_triggers, handoff_notes,
        created_at, updated_at
    """
    
    def __init__(self, db):
        self.db = db
    
    # ========================================
    # Create Operations
    # ========================================
    
    async def create_main_subagent(self, agent_id: str) -> SubAgent:
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
        
        await self._insert(subagent)
        return subagent
    
    async def create_sub_subagent(
        self, 
        agent_id: str, 
        parent_subagent_id: str = "main"
    ) -> SubAgent:
        """Create a sub SubAgent."""
        subagent_id = f"sub-{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        subagent = SubAgent(
            subagent_id=subagent_id,
            agent_id=agent_id,
            type='sub',
            parent_subagent_id=parent_subagent_id,
            status='sleeping',
            created_at=now,
            updated_at=now,
        )
        
        await self._insert(subagent)
        return subagent
    
    async def _insert(self, subagent: SubAgent):
        """Insert a SubAgent into the database."""
        async with self.db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO subagents (
                    subagent_id, agent_id, type, parent_subagent_id,
                    status, historical_summary, wake_triggers, handoff_notes,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                subagent.subagent_id,
                subagent.agent_id,
                subagent.type,
                subagent.parent_subagent_id,
                subagent.status,
                subagent.historical_summary,
                json.dumps(subagent.wake_triggers),
                subagent.handoff_notes,
                subagent.created_at,
                subagent.updated_at,
            ))
            await conn.commit()
    
    # ========================================
    # Query Operations
    # ========================================
    
    async def get_by_id(self, subagent_id: str, agent_id: str) -> Optional[SubAgent]:
        """Get a SubAgent by its ID and agent ID."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                f"SELECT {self._COLUMNS} FROM subagents WHERE subagent_id = ? AND agent_id = ?",
                (subagent_id, agent_id)
            )
            row = await cursor.fetchone()
            if row:
                return self._row_to_subagent(row)
            return None
    
    async def get_main_subagent(self, agent_id: str) -> Optional[SubAgent]:
        """Get the main SubAgent for an agent."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(f"""
                SELECT {self._COLUMNS} FROM subagents 
                WHERE agent_id = ? AND type = 'main'
                LIMIT 1
            """, (agent_id,))
            row = await cursor.fetchone()
            if row:
                return self._row_to_subagent(row)
            return None
    
    async def get_or_create_main_subagent(self, agent_id: str) -> SubAgent:
        """Get or create the main SubAgent for an agent."""
        subagent = await self.get_main_subagent(agent_id)
        if not subagent:
            subagent = await self.create_main_subagent(agent_id)
        return subagent
    
    async def get_sub_subagents(self, agent_id: str) -> List[SubAgent]:
        """Get all sub SubAgents for an agent."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(f"""
                SELECT {self._COLUMNS} FROM subagents 
                WHERE agent_id = ? AND type = 'sub'
                ORDER BY created_at ASC
            """, (agent_id,))
            rows = await cursor.fetchall()
            return [self._row_to_subagent(row) for row in rows]
    
    # ========================================
    # Status Operations (Atomic)
    # ========================================
    
    async def try_wake(self, subagent_id: str, agent_id: str) -> bool:
        """
        Atomically wake a SubAgent (sleeping -> awake).
        Uses CAS to ensure only one caller succeeds.
        
        Returns True if wake succeeded, False if already awake.
        """
        now = datetime.utcnow().isoformat()
        async with self.db.get_connection() as conn:
            cursor = await conn.execute("""
                UPDATE subagents 
                SET status = 'awake', updated_at = ?
                WHERE subagent_id = ? AND agent_id = ? AND status = 'sleeping'
            """, (now, subagent_id, agent_id))
            await conn.commit()
            return cursor.rowcount > 0
    
    async def set_sleeping(self, subagent_id: str, agent_id: str):
        """Set SubAgent to sleeping status."""
        now = datetime.utcnow().isoformat()
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE subagents 
                SET status = 'sleeping', updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (now, subagent_id, agent_id))
            await conn.commit()
    
    async def set_summarizing(self, subagent_id: str, agent_id: str):
        """Set SubAgent to summarizing status."""
        now = datetime.utcnow().isoformat()
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE subagents 
                SET status = 'summarizing', updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (now, subagent_id, agent_id))
            await conn.commit()
    
    async def set_awake(self, subagent_id: str, agent_id: str):
        """Set SubAgent to awake status (for direct state changes)."""
        now = datetime.utcnow().isoformat()
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE subagents 
                SET status = 'awake', updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (now, subagent_id, agent_id))
            await conn.commit()
    
    # ========================================
    # Update Operations
    # ========================================
    
    async def update_historical_summary(
        self, 
        subagent_id: str, 
        agent_id: str, 
        summary: str
    ):
        """Update the historical summary for a SubAgent."""
        now = datetime.utcnow().isoformat()
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE subagents 
                SET historical_summary = ?, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (summary, now, subagent_id, agent_id))
            await conn.commit()
    
    async def update_wake_triggers(
        self, 
        subagent_id: str, 
        agent_id: str,
        wake_triggers: List[Dict[str, Any]],
        handoff_notes: Optional[str] = None
    ):
        """Update wake triggers and handoff notes for a SubAgent."""
        now = datetime.utcnow().isoformat()
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE subagents 
                SET wake_triggers = ?, handoff_notes = ?, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (json.dumps(wake_triggers), handoff_notes, now, subagent_id, agent_id))
            await conn.commit()
    
    # ========================================
    # Delete Operations
    # ========================================
    
    async def delete(self, subagent_id: str, agent_id: str):
        """Delete a SubAgent."""
        async with self.db.get_connection() as conn:
            await conn.execute(
                "DELETE FROM subagents WHERE subagent_id = ? AND agent_id = ?",
                (subagent_id, agent_id)
            )
            await conn.commit()
    
    async def delete_all_for_agent(self, agent_id: str):
        """Delete all SubAgents for an agent."""
        async with self.db.get_connection() as conn:
            await conn.execute(
                "DELETE FROM subagents WHERE agent_id = ?",
                (agent_id,)
            )
            await conn.commit()
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _row_to_subagent(self, row) -> SubAgent:
        """Convert database row to SubAgent object."""
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
            created_at=row[8],
            updated_at=row[9],
        )
