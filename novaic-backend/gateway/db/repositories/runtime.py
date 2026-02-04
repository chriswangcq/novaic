"""
Agent Runtime Repository

Manages agent_runtimes table for Master-driven architecture.
Each SubAgent can have multiple Runtimes (one active at a time).

v12: Initial Master-driven architecture.
v14: SubAgent state refactor - runtime_id rename, subagent_id FK, summary fields.
"""

import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class AgentRuntime:
    """Agent Runtime data model (v14 schema)."""
    runtime_id: str           # Runtime ID (rt-xxx)
    subagent_id: str          # Owner SubAgent ID ("main" or "sub-xxx")
    agent_id: str             # VM Agent ID
    
    # MCP Server
    mcp_url: Optional[str] = None  # e.g. /mcp/aggregate/rt-xxx
    
    # Round state
    current_round_id: Optional[str] = None
    current_round_num: int = 1
    phase: str = 'need_think'  # need_think, waiting_actions, completed
    
    # Context (stored as JSON)
    context: List[Dict[str, Any]] = field(default_factory=list)
    pending_actions: List[str] = field(default_factory=list)  # Task IDs
    
    # Status
    status: str = 'active'  # active, resting, completed
    error: Optional[str] = None
    
    # Summary (v14)
    summary: Optional[str] = None
    is_merged: bool = False
    
    # Saga v2 flags (v20)
    summarized: int = 0
    need_rest: int = 0
    
    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'runtime_id': self.runtime_id,
            'subagent_id': self.subagent_id,
            'agent_id': self.agent_id,
            'mcp_url': self.mcp_url,
            'current_round_id': self.current_round_id,
            'current_round_num': self.current_round_num,
            'phase': self.phase,
            'context': self.context,
            'pending_actions': self.pending_actions,
            'status': self.status,
            'error': self.error,
            'summary': self.summary,
            'is_merged': self.is_merged,
            'summarized': self.summarized,
            'need_rest': self.need_rest,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


class RuntimeRepository:
    """Repository for agent_runtimes table operations (v14 schema)."""
    
    # Explicit column list for v14 schema
    _COLUMNS = """
        runtime_id, subagent_id, agent_id, mcp_url,
        current_round_id, current_round_num, phase,
        context, pending_actions, status, error,
        summary, is_merged, summarized, need_rest, created_at, updated_at
    """
    
    def __init__(self, db):
        self.db = db
    
    # ========================================
    # Create Operations
    # ========================================
    
    def create_runtime(
        self, 
        subagent_id: str, 
        agent_id: str,
        initial_context: Optional[List[Dict[str, Any]]] = None
    ) -> AgentRuntime:
        """Create a new Runtime for a SubAgent.
        
        Args:
            subagent_id: The SubAgent ID ("main" or "sub-xxx")
            agent_id: The VM Agent ID
            initial_context: Optional initial context messages
            
        Returns:
            The created Runtime
        """
        runtime_id = f"rt-{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        runtime = AgentRuntime(
            runtime_id=runtime_id,
            subagent_id=subagent_id,
            agent_id=agent_id,
            current_round_id="round-1",
            current_round_num=1,
            phase='need_think',
            context=initial_context or [],
            created_at=now,
            updated_at=now,
        )
        
        self._insert(runtime)
        return runtime
    
    def _insert(self, runtime: AgentRuntime):
        """Insert a runtime into database."""
        with self.db.get_connection("agent", resource_id=runtime.runtime_id) as conn:
            conn.execute("""
                INSERT INTO agent_runtimes (
                    runtime_id, subagent_id, agent_id, mcp_url,
                    current_round_id, current_round_num, phase,
                    context, pending_actions, status, error,
                    summary, is_merged, summarized, need_rest,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                runtime.runtime_id,
                runtime.subagent_id,
                runtime.agent_id,
                runtime.mcp_url,
                runtime.current_round_id,
                runtime.current_round_num,
                runtime.phase,
                json.dumps(runtime.context),
                json.dumps(runtime.pending_actions),
                runtime.status,
                runtime.error,
                runtime.summary,
                1 if runtime.is_merged else 0,
                runtime.summarized,
                runtime.need_rest,
                runtime.created_at,
                runtime.updated_at,
            ))
            conn.commit()
    
    # ========================================
    # Query Operations
    # ========================================
    
    def get_by_id(self, runtime_id: str) -> Optional[AgentRuntime]:
        """Get a runtime by its ID."""
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            cursor = conn.execute(
                f"SELECT {self._COLUMNS} FROM agent_runtimes WHERE runtime_id = ?",
                (runtime_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_runtime(row)
            return None
    
    def get_active_runtime(self, subagent_id: str, agent_id: str) -> Optional[AgentRuntime]:
        """Get the active runtime for a SubAgent (status in active, resting)."""
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes 
                WHERE subagent_id = ? AND agent_id = ? AND status IN ('active', 'resting')
                ORDER BY created_at DESC
                LIMIT 1
            """, (subagent_id, agent_id))
            row = cursor.fetchone()
            if row:
                return self._row_to_runtime(row)
            return None
    
    def get_active_runtimes_for_agent(self, agent_id: str) -> List[AgentRuntime]:
        """Get all active runtimes for an agent."""
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes 
                WHERE agent_id = ? AND status IN ('active', 'resting')
                ORDER BY created_at ASC
            """, (agent_id,))
            rows = cursor.fetchall()
            return [self._row_to_runtime(row) for row in rows]
    
    def get_all_active_runtimes(self) -> List[AgentRuntime]:
        """Get all active runtimes across all agents."""
        with self.db.get_connection("agent") as conn:
            cursor = conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes 
                WHERE status IN ('active', 'resting')
                ORDER BY created_at ASC
            """)
            rows = cursor.fetchall()
            return [self._row_to_runtime(row) for row in rows]
    
    def has_active_runtime(self, subagent_id: str, agent_id: str) -> bool:
        """Check if SubAgent has an active runtime."""
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute("""
                SELECT 1 FROM agent_runtimes 
                WHERE subagent_id = ? AND agent_id = ? AND status IN ('active', 'resting')
                LIMIT 1
            """, (subagent_id, agent_id))
            row = cursor.fetchone()
            return row is not None
    
    def get_latest_runtimes(
        self, 
        subagent_id: str, 
        agent_id: str, 
        limit: int = 30
    ) -> List[AgentRuntime]:
        """Get the latest runtimes for a SubAgent (for context preparation)."""
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes 
                WHERE subagent_id = ? AND agent_id = ? AND status = 'completed' AND is_merged = 0
                ORDER BY created_at DESC
                LIMIT ?
            """, (subagent_id, agent_id, limit))
            rows = cursor.fetchall()
            # Return in chronological order (oldest first)
            return [self._row_to_runtime(row) for row in reversed(rows)]
    
    def get_unmerged_runtimes(
        self, 
        subagent_id: str, 
        agent_id: str
    ) -> List[AgentRuntime]:
        """Get all unmerged completed runtimes for a SubAgent."""
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes 
                WHERE subagent_id = ? AND agent_id = ? AND status = 'completed' AND is_merged = 0
                ORDER BY created_at ASC
            """, (subagent_id, agent_id))
            rows = cursor.fetchall()
            return [self._row_to_runtime(row) for row in rows]
    
    # ========================================
    # Update Operations
    # ========================================
    
    def set_mcp_url(self, runtime_id: str, mcp_url: str):
        """Set the MCP URL for a runtime."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET mcp_url = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (mcp_url, now, runtime_id))
            conn.commit()
    
    def update_phase(self, runtime_id: str, phase: str):
        """Update runtime phase."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET phase = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (phase, now, runtime_id))
            conn.commit()
    
    def advance_round(self, runtime_id: str, expected_round_num: int = None) -> Optional[str]:
        """Advance to next round (atomic CAS operation).
        
        Args:
            runtime_id: Runtime ID
            expected_round_num: If provided, only advance if current round matches
            
        Returns:
            New round_id if advanced, None if CAS failed or runtime not found.
        """
        now = datetime.utcnow().isoformat()
        
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            if expected_round_num is not None:
                # Atomic CAS: only advance if round_num matches expected
                cursor = conn.execute("""
                    UPDATE agent_runtimes 
                    SET current_round_num = current_round_num + 1,
                        current_round_id = 'round-' || (current_round_num + 1),
                        phase = 'need_think', pending_actions = '[]',
                        updated_at = ?
                    WHERE runtime_id = ? AND current_round_num = ?
                """, (now, runtime_id, expected_round_num))
            else:
                cursor = conn.execute("""
                    UPDATE agent_runtimes 
                    SET current_round_num = current_round_num + 1,
                        current_round_id = 'round-' || (current_round_num + 1),
                        phase = 'need_think', pending_actions = '[]',
                        updated_at = ?
                    WHERE runtime_id = ?
                """, (now, runtime_id))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                runtime = self.get_by_id(runtime_id)
                return runtime.current_round_id if runtime else None
            return None
    
    def update_context(self, runtime_id: str, context: List[Dict[str, Any]]):
        """Update runtime context."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET context = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (json.dumps(context), now, runtime_id))
            conn.commit()
    
    def append_to_context(self, runtime_id: str, messages: List[Dict[str, Any]]):
        """Append messages to runtime context."""
        runtime = self.get_by_id(runtime_id)
        if not runtime:
            raise ValueError(f"Runtime not found: {runtime_id}")
        
        new_context = runtime.context + messages
        self.update_context(runtime_id, new_context)
    
    def set_phase(self, runtime_id: str, phase: str):
        """Set runtime phase only."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET phase = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (phase, now, runtime_id))
            conn.commit()
    
    def set_pending_actions(self, runtime_id: str, task_ids: List[str], phase: str = 'waiting_actions'):
        """Set pending action task IDs for current round."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET pending_actions = ?, phase = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (json.dumps(task_ids), phase, now, runtime_id))
            conn.commit()
    
    def set_status(self, runtime_id: str, status: str):
        """Set runtime status."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET status = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (status, now, runtime_id))
            conn.commit()
    
    def mark_completed(self, runtime_id: str):
        """Mark runtime as completed."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET status = 'completed', phase = 'completed', updated_at = ?
                WHERE runtime_id = ?
            """, (now, runtime_id))
            conn.commit()
    
    def mark_failed(self, runtime_id: str, error: str):
        """Mark runtime as failed."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET status = 'failed', error = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (error, now, runtime_id))
            conn.commit()
    
    def set_resting(self, runtime_id: str):
        """Set runtime to resting state.
        
        v14: Simplified - just sets status='resting'.
        Wake triggers are now stored in SubAgent.
        
        v18: ActionsCollector checks status='resting' to skip further
        think rounds and go directly to summarize.
        """
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET status = 'resting', updated_at = ?
                WHERE runtime_id = ?
            """, (now, runtime_id))
            conn.commit()
    
    # ========================================
    # Summary Operations (v14)
    # ========================================
    
    def set_summary(self, runtime_id: str, summary: str):
        """Set the summary for a completed runtime."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET summary = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (summary, now, runtime_id))
            conn.commit()
    
    def mark_merged(self, runtime_id: str):
        """Mark a runtime's summary as merged into historical_summary."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET is_merged = 1, updated_at = ?
                WHERE runtime_id = ?
            """, (now, runtime_id))
            conn.commit()
    
    def mark_multiple_merged(self, runtime_ids: List[str]):
        """Mark multiple runtimes as merged."""
        if not runtime_ids:
            return
        now = datetime.utcnow().isoformat()
        placeholders = ','.join(['?' for _ in runtime_ids])
        with self.db.get_connection("agent", resource_id=runtime_ids[0] if runtime_ids else None) as conn:
            conn.execute(f"""
                UPDATE agent_runtimes 
                SET is_merged = 1, updated_at = ?
                WHERE runtime_id IN ({placeholders})
            """, [now] + runtime_ids)
            conn.commit()
    
    # ========================================
    # Delete Operations
    # ========================================
    
    def delete(self, runtime_id: str):
        """Delete a runtime."""
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute(
                "DELETE FROM agent_runtimes WHERE runtime_id = ?",
                (runtime_id,)
            )
            conn.commit()
    
    def delete_all_for_agent(self, agent_id: str):
        """Delete all runtimes for an agent."""
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute(
                "DELETE FROM agent_runtimes WHERE agent_id = ?",
                (agent_id,)
            )
            conn.commit()
    
    def delete_all_for_subagent(self, subagent_id: str, agent_id: str):
        """Delete all runtimes for a SubAgent."""
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute(
                "DELETE FROM agent_runtimes WHERE subagent_id = ? AND agent_id = ?",
                (subagent_id, agent_id)
            )
            conn.commit()
    
    def cleanup_completed(self, older_than_hours: int = 24):
        """Clean up completed/failed runtimes older than specified hours."""
        with self.db.get_connection("agent") as conn:
            conn.execute("""
                DELETE FROM agent_runtimes 
                WHERE status IN ('completed', 'failed')
                AND is_merged = 1
                AND updated_at < datetime('now', ? || ' hours')
            """, (f"-{older_than_hours}",))
            conn.commit()
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _row_to_runtime(self, row) -> AgentRuntime:
        """Convert database row to AgentRuntime object (v14 schema)."""
        return AgentRuntime(
            runtime_id=row[0],
            subagent_id=row[1],
            agent_id=row[2],
            mcp_url=row[3],
            current_round_id=row[4],
            current_round_num=row[5] or 1,
            phase=row[6] or 'need_think',
            context=json.loads(row[7]) if row[7] else [],
            pending_actions=json.loads(row[8]) if row[8] else [],
            status=row[9] or 'active',
            error=row[10],
            summary=row[11],
            is_merged=bool(row[12]),
            summarized=row[13] or 0,
            need_rest=row[14] or 0,
            created_at=row[15],
            updated_at=row[16],
        )
    
    # ========================================
    # Backward Compatibility (deprecated)
    # ========================================
    
    def create_main_runtime(self, agent_id: str) -> AgentRuntime:
        """DEPRECATED: Use create_runtime(subagent_id, agent_id) instead."""
        # v14: main subagent_id now has format main-{agent_id[:8]}
        subagent_id = f"main-{agent_id[:8]}"
        return self.create_runtime(subagent_id, agent_id)
    
    def get_main_runtime(self, agent_id: str) -> Optional[AgentRuntime]:
        """DEPRECATED: Get the active main runtime for an agent.
        
        v14: Now queries by subagent type='main' via JOIN, not by subagent_id='main'.
        """
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute("""
                SELECT r.runtime_id, r.subagent_id, r.agent_id, r.mcp_url,
                       r.current_round_id, r.current_round_num, r.phase, r.context,
                       r.pending_actions, r.status, r.error, r.summary, r.is_merged,
                       r.summarized, r.need_rest, r.created_at, r.updated_at
                FROM agent_runtimes r
                JOIN subagents s ON r.subagent_id = s.subagent_id AND r.agent_id = s.agent_id
                WHERE r.agent_id = ? AND s.type = 'main' AND r.status = 'active'
                LIMIT 1
            """, (agent_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_runtime(row)
            return None
    
    def get_active_runtimes(self, agent_id: str) -> List[AgentRuntime]:
        """DEPRECATED: Use get_active_runtimes_for_agent instead."""
        return self.get_active_runtimes_for_agent(agent_id)
    
    def wake_main_runtime(self, runtime_id: str) -> bool:
        """DEPRECATED: Wake logic now handled by SubAgent status."""
        # For backward compatibility, just set status to active
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            cursor = conn.execute("""
                UPDATE agent_runtimes 
                SET status = 'active', phase = 'need_think', 
                    current_round_num = current_round_num + 1,
                    current_round_id = 'round-' || (current_round_num + 1),
                    pending_actions = '[]', updated_at = ?
                WHERE runtime_id = ? AND status = 'completed'
            """, (now, runtime_id))
            conn.commit()
            return cursor.rowcount > 0
