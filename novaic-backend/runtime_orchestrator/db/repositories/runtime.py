"""
Agent Runtime Repository (RO-native).

Manages agent_runtimes table. No gateway.db coupling.
"""

import json
import uuid
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from common.enums import RuntimeStatus
from common.utils.time import utc_now_iso


@dataclass
class AgentRuntime:
    """Agent Runtime data model (v14 schema, v24 summary fields)."""
    runtime_id: str
    subagent_id: str
    agent_id: str
    mcp_url: Optional[str] = None
    current_round_id: Optional[str] = None
    current_round_num: int = 1
    phase: str = 'need_think'
    context: List[Dict[str, Any]] = None
    pending_actions: List[str] = None
    status: str = 'active'
    error: Optional[str] = None
    summary: Optional[str] = None
    is_merged: bool = False
    summarized: int = 0
    need_rest: int = 0
    simple_summary: Optional[str] = None
    hot_summary: Optional[str] = None
    cold_summary: Optional[str] = None
    tool_ports: Optional[dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        if self.context is None:
            self.context = []
        if self.pending_actions is None:
            self.pending_actions = []

    def to_dict(self) -> Dict[str, Any]:
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
    """Repository for agent_runtimes table operations (RO-native)."""

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

    def create_runtime(
        self,
        subagent_id: str,
        agent_id: str,
        initial_context: Optional[List[Dict[str, Any]]] = None
    ) -> AgentRuntime:
        runtime_id = f"rt-{uuid.uuid4().hex[:12]}"
        now = utc_now_iso()
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
                runtime.runtime_id, runtime.subagent_id, runtime.agent_id,
                runtime.mcp_url, runtime.current_round_id, runtime.current_round_num,
                runtime.phase, json.dumps(runtime.context), json.dumps(runtime.pending_actions),
                runtime.status, runtime.error, runtime.summary,
                1 if runtime.is_merged else 0, runtime.summarized, runtime.need_rest,
                runtime.simple_summary, runtime.hot_summary, runtime.cold_summary,
                json.dumps(runtime.tool_ports) if runtime.tool_ports else None,
                runtime.created_at, runtime.updated_at,
            ))
            conn.commit()

    def get_by_id(self, runtime_id: str) -> Optional[AgentRuntime]:
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
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes
                WHERE subagent_id = ? AND agent_id = ? AND status = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (subagent_id, agent_id, RuntimeStatus.ACTIVE.value))
            row = cursor.fetchone()
            if row:
                return self._row_to_runtime(row)
            return None

    def get_all_active_runtimes(self) -> List[AgentRuntime]:
        with self.db.get_connection("global") as conn:
            cursor = conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes
                WHERE status = ?
                ORDER BY created_at ASC, runtime_id ASC
            """, (RuntimeStatus.ACTIVE.value,))
            rows = cursor.fetchall()
            return [self._row_to_runtime(row) for row in rows]

    def has_active_runtime(self, subagent_id: str, agent_id: str) -> bool:
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute("""
                SELECT 1 FROM agent_runtimes
                WHERE subagent_id = ? AND agent_id = ? AND status = ?
                LIMIT 1
            """, (subagent_id, agent_id, RuntimeStatus.ACTIVE.value))
            row = cursor.fetchone()
            return row is not None

    def get_or_create_active_runtime(
        self,
        subagent_id: str,
        agent_id: str,
        initial_context: Optional[List[Dict[str, Any]]] = None
    ) -> tuple:
        with self.db.get_connection("global") as conn:
            cursor = conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes
                WHERE subagent_id = ? AND agent_id = ? AND status = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (subagent_id, agent_id, RuntimeStatus.ACTIVE.value))
            row = cursor.fetchone()
            if row:
                return self._row_to_runtime(row), False

            runtime_id = f"rt-{uuid.uuid4().hex[:12]}"
            now = utc_now_iso()
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
                runtime.runtime_id, runtime.subagent_id, runtime.agent_id,
                runtime.mcp_url, runtime.current_round_id, runtime.current_round_num,
                runtime.phase, json.dumps(runtime.context), json.dumps(runtime.pending_actions),
                runtime.status, runtime.error, runtime.summary,
                1 if runtime.is_merged else 0, runtime.summarized, runtime.need_rest,
                runtime.simple_summary, runtime.hot_summary, runtime.cold_summary,
                json.dumps(runtime.tool_ports) if runtime.tool_ports else None,
                runtime.created_at, runtime.updated_at,
            ))
            conn.commit()
            return runtime, True

    def get_latest_runtimes(
        self,
        subagent_id: str,
        agent_id: str,
        limit: int = 30
    ) -> List[AgentRuntime]:
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes
                WHERE subagent_id = ? AND agent_id = ? AND status = ? AND is_merged = 0
                ORDER BY created_at DESC
                LIMIT ?
            """, (subagent_id, agent_id, RuntimeStatus.COMPLETED.value, limit))
            rows = cursor.fetchall()
            return [self._row_to_runtime(row) for row in reversed(rows)]

    def get_most_recent_runtime(
        self,
        subagent_id: str,
        agent_id: str,
    ) -> Optional[AgentRuntime]:
        """Get the most recent runtime for subagent (any status; for status display)."""
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes
                WHERE subagent_id = ? AND agent_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (subagent_id, agent_id))
            row = cursor.fetchone()
            return self._row_to_runtime(row) if row else None

    def set_mcp_url(self, runtime_id: str, mcp_url: str):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes SET mcp_url = ?, updated_at = ? WHERE runtime_id = ?
            """, (mcp_url, now, runtime_id))
            conn.commit()

    def advance_round(self, runtime_id: str, expected_round_num: int = None) -> Optional[str]:
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            if expected_round_num is not None:
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
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes SET context = ?, updated_at = ? WHERE runtime_id = ?
            """, (json.dumps(context), now, runtime_id))
            conn.commit()

    def set_phase(self, runtime_id: str, phase: str):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes SET phase = ?, updated_at = ? WHERE runtime_id = ?
            """, (phase, now, runtime_id))
            conn.commit()

    def set_pending_actions(
        self, runtime_id: str, task_ids: List[str], phase: str = 'waiting_actions'
    ):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes
                SET pending_actions = ?, phase = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (json.dumps(task_ids), phase, now, runtime_id))
            conn.commit()

    def set_status(self, runtime_id: str, status: str):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes SET status = ?, updated_at = ? WHERE runtime_id = ?
            """, (status, now, runtime_id))
            conn.commit()

    def mark_completed(self, runtime_id: str):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes SET status = ?, phase = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (RuntimeStatus.COMPLETED.value, RuntimeStatus.COMPLETED.value, now, runtime_id))
            conn.commit()

    def mark_failed(self, runtime_id: str, error: str):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes SET status = ?, error = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (RuntimeStatus.FAILED.value, error, now, runtime_id))
            conn.commit()

    def set_summary(self, runtime_id: str, summary: str):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes SET summary = ?, updated_at = ? WHERE runtime_id = ?
            """, (summary, now, runtime_id))
            conn.commit()

    def set_hot_cold_summary(
        self, runtime_id: str, hot_summary: str, cold_summary: str
    ):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes
                SET hot_summary = ?, cold_summary = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (hot_summary, cold_summary, now, runtime_id))
            conn.commit()

    def set_tool_ports(self, runtime_id: str, tool_ports: dict):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes SET tool_ports = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (json.dumps(tool_ports), now, runtime_id))
            conn.commit()

    def clear_tool_ports(self, runtime_id: str):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes SET tool_ports = NULL, updated_at = ?
                WHERE runtime_id = ?
            """, (now, runtime_id))
            conn.commit()

    def get_runtime_ids_for_subagent(self, subagent_id: str, agent_id: str) -> List[str]:
        """Get all runtime_ids for a subagent (any status)."""
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute(
                "SELECT runtime_id FROM agent_runtimes WHERE subagent_id = ? AND agent_id = ?",
                (subagent_id, agent_id)
            )
            return [row[0] for row in cursor.fetchall()]

    def get_runtimes_by_ids(self, runtime_ids: List[str]) -> List[AgentRuntime]:
        if not runtime_ids:
            return []
        placeholders = ','.join(['?' for _ in runtime_ids])
        with self.db.get_connection(
            "agent", resource_id=runtime_ids[0] if runtime_ids else None
        ) as conn:
            cursor = conn.execute(f"""
                SELECT {self._COLUMNS} FROM agent_runtimes
                WHERE runtime_id IN ({placeholders})
            """, runtime_ids)
            rows = cursor.fetchall()
            runtime_map = {self._row_to_runtime(row).runtime_id: self._row_to_runtime(row) for row in rows}
            return [runtime_map[rid] for rid in runtime_ids if rid in runtime_map]

    def mark_merged(self, runtime_id: str):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes SET is_merged = 1, updated_at = ?
                WHERE runtime_id = ?
            """, (now, runtime_id))
            conn.commit()

    def delete(self, runtime_id: str):
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute(
                "DELETE FROM agent_runtimes WHERE runtime_id = ?",
                (runtime_id,)
            )
            conn.commit()

    def reset_round(
        self, runtime_id: str, round_num: int = 1, round_id: str = None
    ):
        now = utc_now_iso()
        actual_round_id = round_id or f"round-{round_num}"
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute("""
                UPDATE agent_runtimes
                SET current_round_num = ?, current_round_id = ?, updated_at = ?
                WHERE runtime_id = ?
            """, (round_num, actual_round_id, now, runtime_id))
            conn.commit()

    def set_need_rest(self, runtime_id: str, value: int = 1):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            conn.execute(
                "UPDATE agent_runtimes SET need_rest = ?, updated_at = ? WHERE runtime_id = ?",
                (value, now, runtime_id)
            )
            conn.commit()

    def cas_set_summarized(self, runtime_id: str, expected_value: int = 0) -> bool:
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            cursor = conn.execute("""
                UPDATE agent_runtimes SET summarized = 1, updated_at = ?
                WHERE runtime_id = ? AND summarized = ?
            """, (now, runtime_id, expected_value))
            conn.commit()
            return cursor.rowcount > 0

    def cas_set_status(
        self, runtime_id: str, expected_status: List[str], new_status: str
    ) -> bool:
        now = utc_now_iso()
        placeholders = ','.join(['?' for _ in expected_status])
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            cursor = conn.execute(f"""
                UPDATE agent_runtimes SET status = ?, updated_at = ?
                WHERE runtime_id = ? AND status IN ({placeholders})
            """, (new_status, now, runtime_id, *expected_status))
            conn.commit()
            return cursor.rowcount > 0

    def cas_set_status_with_error(
        self,
        runtime_id: str,
        expected_status: List[str],
        new_status: str,
        error: str,
    ) -> bool:
        now = utc_now_iso()
        placeholders = ','.join(['?' for _ in expected_status])
        with self.db.get_connection("agent", resource_id=runtime_id) as conn:
            cursor = conn.execute(f"""
                UPDATE agent_runtimes SET status = ?, error = ?, updated_at = ?
                WHERE runtime_id = ? AND status IN ({placeholders})
            """, (new_status, error, now, runtime_id, *expected_status))
            conn.commit()
            return cursor.rowcount > 0

    def wake_main_runtime(self, runtime_id: str) -> bool:
        now = utc_now_iso()
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

    def _row_to_runtime(self, row) -> AgentRuntime:
        return AgentRuntime(
            runtime_id=row[0], subagent_id=row[1], agent_id=row[2],
            mcp_url=row[3], current_round_id=row[4], current_round_num=row[5] or 1,
            phase=row[6] or 'need_think',
            context=json.loads(row[7]) if row[7] else [],
            pending_actions=json.loads(row[8]) if row[8] else [],
            status=row[9] or 'active', error=row[10], summary=row[11],
            is_merged=bool(row[12]), summarized=row[13] or 0, need_rest=row[14] or 0,
            simple_summary=row[15], hot_summary=row[16], cold_summary=row[17],
            tool_ports=json.loads(row[18]) if row[18] else None,
            created_at=row[19], updated_at=row[20],
        )
