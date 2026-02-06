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

from common.enums import RuntimeStatus
from common.config import ServiceConfig


@dataclass
class AgentRuntime:
    """Agent Runtime data model (v14 schema, v24 summary fields)."""
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
    
    # Runtime Summary (v24)
    simple_summary: Optional[str] = None
    hot_summary: Optional[str] = None
    cold_summary: Optional[str] = None
    
    # Tools Server persistence (v25)
    tool_ports: Optional[dict] = None  # MCP ports for Tools Server discovery
    
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
            'simple_summary': self.simple_summary,
            'hot_summary': self.hot_summary,
            'cold_summary': self.cold_summary,
            'tool_ports': self.tool_ports,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


class RuntimeRepository:
    """Repository for agent_runtimes table operations (v14 schema, v24 summary fields)."""
    
    # Explicit column list for v14 schema + v24 summary fields
    _COLUMNS = """
        runtime_id, subagent_id, agent_id, mcp_url,
        current_round_id, current_round_num, phase,
        context, pending_actions, status, error,
        summary, is_merged, summarized, need_rest,
        simple_summary, hot_summary, cold_summary,
        tool_ports, created_at, updated_at
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
                    simple_summary, hot_summary, cold_summary,
                    tool_ports, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                runtime.simple_summary,
                runtime.hot_summary,
                runtime.cold_summary,
                json.dumps(runtime.tool_ports) if runtime.tool_ports else None,
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
                WHERE subagent_id = ? AND agent_id = ? AND status IN (?, ?)
                ORDER BY created_at DESC
                LIMIT 1
            """, (subagent_id, agent_id, RuntimeStatus.ACTIVE.value, RuntimeStatus.RESTING.value))
            row = cursor.fetchone()
            if row:
                return self._row_to_runtime(row)
            return None
    
    def get_active_runtimes_for_agent(self, agent_id: str) -> List[AgentRuntime]:
        """Get all active runtimes for an agent."""
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes 
                WHERE agent_id = ? AND status IN (?, ?)
                ORDER BY created_at ASC
            """, (agent_id, RuntimeStatus.ACTIVE.value, RuntimeStatus.RESTING.value))
            rows = cursor.fetchall()
            return [self._row_to_runtime(row) for row in rows]
    
    def get_all_active_runtimes(self) -> List[AgentRuntime]:
        """Get all active runtimes across all agents."""
        with self.db.get_connection("global") as conn:
            cursor = conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes 
                WHERE status IN (?, ?)
                ORDER BY created_at ASC
            """, (RuntimeStatus.ACTIVE.value, RuntimeStatus.RESTING.value))
            rows = cursor.fetchall()
            return [self._row_to_runtime(row) for row in rows]
    
    def has_active_runtime(self, subagent_id: str, agent_id: str) -> bool:
        """Check if SubAgent has an active runtime."""
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute("""
                SELECT 1 FROM agent_runtimes 
                WHERE subagent_id = ? AND agent_id = ? AND status IN (?, ?)
                LIMIT 1
            """, (subagent_id, agent_id, RuntimeStatus.ACTIVE.value, RuntimeStatus.RESTING.value))
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
                WHERE subagent_id = ? AND agent_id = ? AND status = ? AND is_merged = 0
                ORDER BY created_at DESC
                LIMIT ?
            """, (subagent_id, agent_id, RuntimeStatus.COMPLETED.value, limit))
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
                WHERE subagent_id = ? AND agent_id = ? AND status = ? AND is_merged = 0
                ORDER BY created_at ASC
            """, (subagent_id, agent_id, RuntimeStatus.COMPLETED.value))
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
        """Set runtime status.
        
        Args:
            runtime_id: Runtime ID
            status: Status value (should use RuntimeStatus enum values)
        """
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
                SET status = ?, phase = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (RuntimeStatus.COMPLETED.value, RuntimeStatus.COMPLETED.value, now, runtime_id))
            conn.commit()
    
    def mark_failed(self, runtime_id: str, error: str):
        """Mark runtime as failed."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET status = ?, error = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (RuntimeStatus.FAILED.value, error, now, runtime_id))
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
                SET status = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (RuntimeStatus.RESTING.value, now, runtime_id))
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
    
    def set_simple_summary(self, runtime_id: str, simple_summary: str):
        """Set the simple summary for a runtime.
        
        Simple summary: Plain text summary of the runtime's purpose/outcome.
        """
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET simple_summary = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (simple_summary, now, runtime_id))
            conn.commit()
    
    def set_hot_summary(self, runtime_id: str, hot_summary: str):
        """Set the hot summary for a completed runtime.
        
        Hot summary: 
        - Earlier rounds: LLM-generated summary paragraph
        - Last N rounds: Full content with think + tools + results
        """
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET hot_summary = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (hot_summary, now, runtime_id))
            conn.commit()
    
    def set_cold_summary(self, runtime_id: str, cold_summary: str):
        """Set the cold summary for a completed runtime.
        
        Cold summary: LLM-generated summary of all rounds.
        """
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET cold_summary = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (cold_summary, now, runtime_id))
            conn.commit()
    
    def set_hot_cold_summary(self, runtime_id: str, hot_summary: str, cold_summary: str):
        """Set both hot and cold summaries atomically."""
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET hot_summary = ?, cold_summary = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (hot_summary, cold_summary, now, runtime_id))
            conn.commit()
    
    # ========================================
    # Tools Server Persistence (v25)
    # ========================================
    
    def set_tool_ports(self, runtime_id: str, tool_ports: dict):
        """Save Tools Server MCP ports for a runtime.
        
        Called by Tools Server when registering a runtime's tools.
        Enables recovery after Tools Server restart.
        
        Args:
            runtime_id: Runtime ID
            tool_ports: MCP ports dict (e.g. {"vmuse": 8080})
        """
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET tool_ports = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (json.dumps(tool_ports), now, runtime_id))
            conn.commit()
    
    def clear_tool_ports(self, runtime_id: str):
        """Clear Tools Server MCP ports for a runtime.
        
        Called by Tools Server when unregistering a runtime's tools.
        """
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET tool_ports = NULL, updated_at = ?
                WHERE runtime_id = ?
            """, (now, runtime_id))
            conn.commit()
    
    def get_summaries(self, runtime_id: str) -> Optional[Dict[str, Optional[str]]]:
        """Get all three summary types for a runtime.
        
        Returns:
            Dict with keys: simple_summary, hot_summary, cold_summary
            Returns None if runtime not found.
        """
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            cursor = conn.execute("""
                SELECT simple_summary, hot_summary, cold_summary 
                FROM agent_runtimes WHERE runtime_id = ?
            """, (runtime_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'simple_summary': row[0],
                    'hot_summary': row[1],
                    'cold_summary': row[2],
                }
            return None
    
    def get_runtimes_by_ids(self, runtime_ids: List[str]) -> List[AgentRuntime]:
        """Get multiple runtimes by their IDs.
        
        Args:
            runtime_ids: List of runtime IDs to fetch
            
        Returns:
            List of AgentRuntime objects (in order of input IDs where found)
        """
        if not runtime_ids:
            return []
        
        placeholders = ','.join(['?' for _ in runtime_ids])
        with self.db.get_connection("agent", resource_id=runtime_ids[0] if runtime_ids else None) as conn:
            cursor = conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes 
                WHERE runtime_id IN ({placeholders})
            """, runtime_ids)
            rows = cursor.fetchall()
            
            # Build a map for ordering
            runtime_map = {self._row_to_runtime(row).runtime_id: self._row_to_runtime(row) for row in rows}
            
            # Return in input order (preserving order)
            return [runtime_map[rid] for rid in runtime_ids if rid in runtime_map]
    
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
                WHERE status IN (?, ?)
                AND is_merged = 1
                AND datetime(updated_at) < datetime('now', ? || ' hours')
            """, (RuntimeStatus.COMPLETED.value, RuntimeStatus.FAILED.value, f"-{older_than_hours}"))
            conn.commit()
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _row_to_runtime(self, row) -> AgentRuntime:
        """Convert database row to AgentRuntime object (v14 schema + v25 fields)."""
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
            simple_summary=row[15],
            hot_summary=row[16],
            cold_summary=row[17],
            tool_ports=json.loads(row[18]) if row[18] else None,
            created_at=row[19],
            updated_at=row[20],
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
        v24: Updated to include new summary fields.
        """
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute("""
                SELECT r.runtime_id, r.subagent_id, r.agent_id, r.mcp_url,
                       r.current_round_id, r.current_round_num, r.phase, r.context,
                       r.pending_actions, r.status, r.error, r.summary, r.is_merged,
                       r.summarized, r.need_rest, r.simple_summary, r.hot_summary, 
                       r.cold_summary, r.created_at, r.updated_at
                FROM agent_runtimes r
                JOIN subagents s ON r.subagent_id = s.subagent_id AND r.agent_id = s.agent_id
                WHERE r.agent_id = ? AND s.type = 'main' AND r.status = ?
                LIMIT 1
            """, (agent_id, RuntimeStatus.ACTIVE.value))
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
                SET status = ?, phase = 'need_think', 
                    current_round_num = current_round_num + 1,
                    current_round_id = 'round-' || (current_round_num + 1),
                    pending_actions = '[]', updated_at = ?
                WHERE runtime_id = ? AND status = ?
            """, (RuntimeStatus.ACTIVE.value, now, runtime_id, RuntimeStatus.COMPLETED.value))
            conn.commit()
            return cursor.rowcount > 0
    
    # ========================================
    # New Methods (v25)
    # ========================================
    
    def get_runtime_ids_for_subagent(self, subagent_id: str, agent_id: str) -> List[str]:
        """获取 subagent 的所有 runtime_ids。
        
        Args:
            subagent_id: SubAgent ID
            agent_id: Agent ID
            
        Returns:
            List of runtime IDs belonging to the SubAgent
        """
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute(
                "SELECT runtime_id FROM agent_runtimes WHERE subagent_id = ? AND agent_id = ?",
                (subagent_id, agent_id)
            )
            return [row[0] for row in cursor.fetchall()]
    
    def reset_round(self, runtime_id: str, round_num: int = 1, round_id: str = None):
        """重置 round（用于 runtime reset）。
        
        Args:
            runtime_id: Runtime ID
            round_num: Round number to reset to (default 1)
            round_id: Round ID to set (default "round-{round_num}")
        """
        now = datetime.utcnow().isoformat()
        actual_round_id = round_id or f"round-{round_num}"
        
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes 
                SET current_round_num = ?, current_round_id = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (round_num, actual_round_id, now, runtime_id))
            conn.commit()
    
    def set_need_rest(self, runtime_id: str, value: int = 1):
        """设置 need_rest 标志。
        
        Args:
            runtime_id: Runtime ID
            value: Value to set (default 1)
        """
        now = datetime.utcnow().isoformat()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute(
                "UPDATE agent_runtimes SET need_rest = ?, updated_at = ? WHERE runtime_id = ?",
                (value, now, runtime_id)
            )
            conn.commit()
    
    def cas_update_phase(self, runtime_id: str, new_phase: str, expected_phase: str, round_id: str = None) -> bool:
        """CAS 更新 phase，返回是否成功。
        
        Args:
            runtime_id: Runtime ID
            new_phase: New phase to set
            expected_phase: Expected current phase (CAS condition)
            round_id: Optional round_id to set along with phase
            
        Returns:
            True if update succeeded (phase matched expected), False otherwise
        """
        now = datetime.utcnow().isoformat()
        
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            if round_id:
                cursor = conn.execute("""
                    UPDATE agent_runtimes 
                    SET phase = ?, current_round_id = ?, updated_at = ?
                    WHERE runtime_id = ? AND phase = ?
                """, (new_phase, round_id, now, runtime_id, expected_phase))
            else:
                cursor = conn.execute("""
                    UPDATE agent_runtimes 
                    SET phase = ?, updated_at = ?
                    WHERE runtime_id = ? AND phase = ?
                """, (new_phase, now, runtime_id, expected_phase))
            conn.commit()
            return cursor.rowcount > 0
    
    def cas_set_summarized(self, runtime_id: str, expected_value: int = 0) -> bool:
        """CAS 设置 summarized=1，返回是否成功。
        
        Args:
            runtime_id: Runtime ID
            expected_value: Expected current value (default 0)
            
        Returns:
            True if update succeeded (summarized matched expected), False otherwise
        """
        now = datetime.utcnow().isoformat()
        
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            cursor = conn.execute("""
                UPDATE agent_runtimes
                SET summarized = 1, updated_at = ?
                WHERE runtime_id = ? AND summarized = ?
            """, (now, runtime_id, expected_value))
            conn.commit()
            return cursor.rowcount > 0
    
    def cas_set_need_rest(self, runtime_id: str, target: int, expected: int) -> bool:
        """CAS 设置 need_rest，返回是否成功。
        
        Args:
            runtime_id: Runtime ID
            target: Target value to set
            expected: Expected current value (CAS condition)
            
        Returns:
            True if update succeeded (need_rest matched expected), False otherwise
        """
        now = datetime.utcnow().isoformat()
        
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            cursor = conn.execute("""
                UPDATE agent_runtimes
                SET need_rest = ?, updated_at = ?
                WHERE runtime_id = ? AND need_rest = ?
            """, (target, now, runtime_id, expected))
            conn.commit()
            return cursor.rowcount > 0
    
    def cas_set_status(self, runtime_id: str, expected_status: List[str], new_status: str) -> bool:
        """CAS set status - only update if current status is in expected_status list.
        
        Args:
            runtime_id: Runtime ID
            expected_status: List of expected current statuses
            new_status: New status to set
            
        Returns:
            True if update succeeded, False otherwise
        """
        now = datetime.utcnow().isoformat()
        placeholders = ','.join(['?' for _ in expected_status])
        
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            cursor = conn.execute(f"""
                UPDATE agent_runtimes 
                SET status = ?, updated_at = ?
                WHERE runtime_id = ? AND status IN ({placeholders})
            """, (new_status, now, runtime_id, *expected_status))
            conn.commit()
            return cursor.rowcount > 0
    
    def cas_set_status_with_error(self, runtime_id: str, expected_status: List[str], new_status: str, error: str) -> bool:
        """CAS set status with error - only update if current status is in expected_status list.
        
        Args:
            runtime_id: Runtime ID
            expected_status: List of expected current statuses
            new_status: New status to set
            error: Error message to set
            
        Returns:
            True if update succeeded, False otherwise
        """
        now = datetime.utcnow().isoformat()
        placeholders = ','.join(['?' for _ in expected_status])
        
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            cursor = conn.execute(f"""
                UPDATE agent_runtimes 
                SET status = ?, error = ?, updated_at = ?
                WHERE runtime_id = ? AND status IN ({placeholders})
            """, (new_status, error, now, runtime_id, *expected_status))
            conn.commit()
            return cursor.rowcount > 0
