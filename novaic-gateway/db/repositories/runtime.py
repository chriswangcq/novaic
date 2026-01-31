"""
Agent Runtime Repository

Manages agent_runtimes table for Master-driven architecture.
Each VM Agent can have:
- One Main Runtime (handles user messages)
- Multiple SubAgent Runtimes (handles sub-tasks)
"""

import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass
class AgentRuntime:
    """Agent Runtime data model."""
    subagent_id: str
    agent_id: str
    type: str  # 'main' or 'sub'
    parent_subagent_id: Optional[str] = None
    
    # MCP Server
    mcp_url: Optional[str] = None  # e.g. /mcp/aggregate/main-xxx
    
    # Round state
    current_round_id: Optional[str] = None
    current_round_num: int = 1
    phase: str = 'need_think'  # need_think, waiting_actions, completed
    
    # Context (stored as JSON)
    context: List[Dict[str, Any]] = field(default_factory=list)
    pending_actions: List[str] = field(default_factory=list)  # Task IDs
    
    # Status
    status: str = 'active'  # active, completed, failed
    error: Optional[str] = None
    
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
            'mcp_url': self.mcp_url,
            'current_round_id': self.current_round_id,
            'current_round_num': self.current_round_num,
            'phase': self.phase,
            'context': self.context,
            'pending_actions': self.pending_actions,
            'status': self.status,
            'error': self.error,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


class RuntimeRepository:
    """Repository for agent_runtimes table operations."""
    
    # Explicit column list to ensure consistent ordering regardless of ALTER TABLE order
    _COLUMNS = """
        subagent_id, agent_id, type, parent_subagent_id, mcp_url,
        current_round_id, current_round_num, phase,
        context, pending_actions, status, error,
        created_at, updated_at
    """
    
    def __init__(self, db):
        self.db = db
    
    # ========================================
    # Create Operations
    # ========================================
    
    async def create_main_runtime(self, agent_id: str) -> AgentRuntime:
        """Create a new Main Runtime for an agent."""
        subagent_id = f"main-{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        runtime = AgentRuntime(
            subagent_id=subagent_id,
            agent_id=agent_id,
            type='main',
            current_round_id=f"round-1",
            current_round_num=1,
            phase='need_think',
            created_at=now,
            updated_at=now,
        )
        
        await self._insert(runtime)
        return runtime
    
    async def create_sub_runtime(
        self, 
        agent_id: str, 
        parent_subagent_id: str,
        initial_context: Optional[List[Dict[str, Any]]] = None
    ) -> AgentRuntime:
        """Create a new SubAgent Runtime."""
        subagent_id = f"sub-{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        runtime = AgentRuntime(
            subagent_id=subagent_id,
            agent_id=agent_id,
            type='sub',
            parent_subagent_id=parent_subagent_id,
            current_round_id=f"round-1",
            current_round_num=1,
            phase='need_think',
            context=initial_context or [],
            created_at=now,
            updated_at=now,
        )
        
        await self._insert(runtime)
        return runtime
    
    async def _insert(self, runtime: AgentRuntime):
        """Insert a runtime into database."""
        async with self.db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO agent_runtimes (
                    subagent_id, agent_id, type, parent_subagent_id, mcp_url,
                    current_round_id, current_round_num, phase,
                    context, pending_actions, status, error,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                runtime.subagent_id,
                runtime.agent_id,
                runtime.type,
                runtime.parent_subagent_id,
                runtime.mcp_url,
                runtime.current_round_id,
                runtime.current_round_num,
                runtime.phase,
                json.dumps(runtime.context),
                json.dumps(runtime.pending_actions),
                runtime.status,
                runtime.error,
                runtime.created_at,
                runtime.updated_at,
            ))
            await conn.commit()
    
    # ========================================
    # Query Operations
    # ========================================
    
    async def get_by_id(self, subagent_id: str) -> Optional[AgentRuntime]:
        """Get a runtime by its ID."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                f"SELECT {self._COLUMNS} FROM agent_runtimes WHERE subagent_id = ?",
                (subagent_id,)
            )
            row = await cursor.fetchone()
            if row:
                return self._row_to_runtime(row)
            return None
    
    async def get_main_runtime(self, agent_id: str) -> Optional[AgentRuntime]:
        """Get the Main Runtime for an agent (any status).
        
        Main Runtime is unique per agent and persists across sleep/wake cycles.
        Returns the most recent Main Runtime regardless of status.
        """
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes 
                WHERE agent_id = ? AND type = 'main'
                ORDER BY created_at DESC
                LIMIT 1
            """, (agent_id,))
            row = await cursor.fetchone()
            if row:
                return self._row_to_runtime(row)
            return None
    
    async def get_active_runtimes(self, agent_id: str) -> List[AgentRuntime]:
        """Get all active runtimes for an agent."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes 
                WHERE agent_id = ? AND status = 'active'
                ORDER BY created_at ASC
            """, (agent_id,))
            rows = await cursor.fetchall()
            return [self._row_to_runtime(row) for row in rows]
    
    async def get_all_active_runtimes(self) -> List[AgentRuntime]:
        """Get all active runtimes across all agents."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes 
                WHERE status = 'active'
                ORDER BY created_at ASC
            """)
            rows = await cursor.fetchall()
            return [self._row_to_runtime(row) for row in rows]
    
    async def get_sub_runtimes(self, parent_subagent_id: str) -> List[AgentRuntime]:
        """Get all active sub-runtimes for a parent runtime."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes 
                WHERE parent_subagent_id = ? AND status = 'active'
                ORDER BY created_at ASC
            """, (parent_subagent_id,))
            rows = await cursor.fetchall()
            return [self._row_to_runtime(row) for row in rows]
    
    async def has_active_main_runtime(self, agent_id: str) -> bool:
        """Check if agent has an active (running) Main Runtime."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT 1 FROM agent_runtimes 
                WHERE agent_id = ? AND type = 'main' AND status = 'active'
                LIMIT 1
            """, (agent_id,))
            row = await cursor.fetchone()
            return row is not None
    
    async def wake_main_runtime(self, subagent_id: str):
        """Wake up a sleeping Main Runtime.
        
        Resets status to 'active' and phase to 'need_think' so scheduler
        will pick it up and process any pending messages.
        
        v2.10: Also increment round_num to avoid idempotency_key conflicts.
        When a Runtime wakes up, it starts a new round - using the old round_num
        would cause UNIQUE constraint failures on action_tasks.
        """
        # First get current round_num
        runtime = await self.get_by_id(subagent_id)
        if not runtime:
            return
        
        new_round_num = runtime.current_round_num + 1
        new_round_id = f"round-{new_round_num}"
        now = datetime.utcnow().isoformat()
        
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE agent_runtimes 
                SET status = 'active', phase = 'need_think', 
                    current_round_num = ?, current_round_id = ?,
                    pending_actions = '[]', updated_at = ?
                WHERE subagent_id = ?
            """, (new_round_num, new_round_id, now, subagent_id))
            await conn.commit()
    
    # ========================================
    # Update Operations
    # ========================================
    
    async def set_mcp_url(self, subagent_id: str, mcp_url: str):
        """Set the MCP URL for a runtime."""
        now = datetime.utcnow().isoformat()
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE agent_runtimes 
                SET mcp_url = ?, updated_at = ?
                WHERE subagent_id = ?
            """, (mcp_url, now, subagent_id))
            await conn.commit()
    
    async def update_phase(self, subagent_id: str, phase: str):
        """Update runtime phase."""
        now = datetime.utcnow().isoformat()
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE agent_runtimes 
                SET phase = ?, updated_at = ?
                WHERE subagent_id = ?
            """, (phase, now, subagent_id))
            await conn.commit()
    
    async def advance_round(self, subagent_id: str) -> str:
        """Advance to next round, return new round_id."""
        runtime = await self.get_by_id(subagent_id)
        if not runtime:
            raise ValueError(f"Runtime not found: {subagent_id}")
        
        new_round_num = runtime.current_round_num + 1
        new_round_id = f"round-{new_round_num}"
        now = datetime.utcnow().isoformat()
        
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE agent_runtimes 
                SET current_round_id = ?, current_round_num = ?, 
                    phase = 'need_think', pending_actions = '[]',
                    updated_at = ?
                WHERE subagent_id = ?
            """, (new_round_id, new_round_num, now, subagent_id))
            await conn.commit()
        
        return new_round_id
    
    async def update_context(self, subagent_id: str, context: List[Dict[str, Any]]):
        """Update runtime context."""
        now = datetime.utcnow().isoformat()
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE agent_runtimes 
                SET context = ?, updated_at = ?
                WHERE subagent_id = ?
            """, (json.dumps(context), now, subagent_id))
            await conn.commit()
    
    async def append_to_context(self, subagent_id: str, messages: List[Dict[str, Any]]):
        """Append messages to runtime context."""
        runtime = await self.get_by_id(subagent_id)
        if not runtime:
            raise ValueError(f"Runtime not found: {subagent_id}")
        
        new_context = runtime.context + messages
        await self.update_context(subagent_id, new_context)
    
    async def set_phase(self, subagent_id: str, phase: str):
        """Set runtime phase only (without changing pending_actions).
        
        v2.10: Used to set 'processing_results' phase as a lock to prevent
        race conditions where _advance_or_complete could be called twice.
        
        Args:
            subagent_id: Runtime ID
            phase: New phase to set
        """
        now = datetime.utcnow().isoformat()
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE agent_runtimes 
                SET phase = ?, updated_at = ?
                WHERE subagent_id = ?
            """, (phase, now, subagent_id))
            await conn.commit()
    
    async def set_pending_actions(self, subagent_id: str, task_ids: List[str], phase: str = 'waiting_actions'):
        """Set pending action task IDs for current round.
        
        Args:
            subagent_id: Runtime ID
            task_ids: List of action task IDs
            phase: Phase to set ('waiting_actions' or 'waiting_actions_final')
                   'waiting_actions_final' means runtime should complete after actions done
        """
        now = datetime.utcnow().isoformat()
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE agent_runtimes 
                SET pending_actions = ?, phase = ?, updated_at = ?
                WHERE subagent_id = ?
            """, (json.dumps(task_ids), phase, now, subagent_id))
            await conn.commit()
    
    async def mark_completed(self, subagent_id: str):
        """Mark runtime as completed."""
        now = datetime.utcnow().isoformat()
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE agent_runtimes 
                SET status = 'completed', phase = 'completed', updated_at = ?
                WHERE subagent_id = ?
            """, (now, subagent_id))
            await conn.commit()
    
    async def mark_failed(self, subagent_id: str, error: str):
        """Mark runtime as failed."""
        now = datetime.utcnow().isoformat()
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE agent_runtimes 
                SET status = 'failed', error = ?, updated_at = ?
                WHERE subagent_id = ?
            """, (error, now, subagent_id))
            await conn.commit()
    
    # ========================================
    # Delete Operations
    # ========================================
    
    async def delete(self, subagent_id: str):
        """Delete a runtime."""
        async with self.db.get_connection() as conn:
            await conn.execute(
                "DELETE FROM agent_runtimes WHERE subagent_id = ?",
                (subagent_id,)
            )
            await conn.commit()
    
    async def delete_all_for_agent(self, agent_id: str):
        """Delete all runtimes for an agent."""
        async with self.db.get_connection() as conn:
            await conn.execute(
                "DELETE FROM agent_runtimes WHERE agent_id = ?",
                (agent_id,)
            )
            await conn.commit()
    
    async def cleanup_completed(self, older_than_hours: int = 24):
        """Clean up completed/failed runtimes older than specified hours."""
        async with self.db.get_connection() as conn:
            await conn.execute("""
                DELETE FROM agent_runtimes 
                WHERE status IN ('completed', 'failed')
                AND updated_at < datetime('now', ? || ' hours')
            """, (f"-{older_than_hours}",))
            await conn.commit()
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _row_to_runtime(self, row) -> AgentRuntime:
        """Convert database row to AgentRuntime object."""
        return AgentRuntime(
            subagent_id=row[0],
            agent_id=row[1],
            type=row[2],
            parent_subagent_id=row[3],
            mcp_url=row[4],
            current_round_id=row[5],
            current_round_num=row[6] or 1,
            phase=row[7] or 'need_think',
            context=json.loads(row[8]) if row[8] else [],
            pending_actions=json.loads(row[9]) if row[9] else [],
            status=row[10] or 'active',
            error=row[11],
            created_at=row[12],
            updated_at=row[13],
        )
