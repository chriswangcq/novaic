"""
SubAgent Repository (RO-native).

Manages subagents table. No gateway.db coupling.
"""

import json
import sqlite3
import uuid
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from common.enums import SubagentStatus
from common.utils.time import utc_now_iso


@dataclass
class SubAgent:
    """SubAgent data model."""
    subagent_id: str
    agent_id: str
    type: str
    parent_subagent_id: Optional[str] = None
    status: str = 'sleeping'
    historical_summary: Optional[str] = None
    wake_triggers: List[Dict[str, Any]] = field(default_factory=lambda: [{"type": "user_response"}])
    handoff_notes: Optional[str] = None
    wake_at: Optional[str] = None
    task: Optional[str] = None
    progress: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    timeout_at: Optional[str] = None
    hrl: List[str] = field(default_factory=list)
    summary_lock: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SubAgentRepository:
    """Repository for subagents table operations (RO-native)."""

    _COLUMNS = """
        subagent_id, agent_id, type, parent_subagent_id,
        status, historical_summary, wake_triggers, handoff_notes, wake_at,
        task, progress, result, error, timeout_at,
        hrl, summary_lock,
        created_at, updated_at
    """

    def __init__(self, db):
        self.db = db

    def _ensure_agent_exists(self, agent_id: str) -> None:
        """Ensure agent row exists for subagent FK (RO schema: id, name, created_at only)."""
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO agents (id, name, created_at)
                VALUES (?, ?, datetime('now'))
                """,
                (agent_id, f"agent-{agent_id[:8]}"),
            )
            conn.commit()

    def create_main_subagent(self, agent_id: str) -> SubAgent:
        now = utc_now_iso()
        self._ensure_agent_exists(agent_id)
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

    def _insert(self, subagent: SubAgent):
        with self.db.get_connection("agent", resource_id=subagent.agent_id) as conn:
            conn.execute("""
                INSERT INTO subagents (
                    subagent_id, agent_id, type, parent_subagent_id,
                    status, historical_summary, wake_triggers, handoff_notes, wake_at,
                    task, progress, result, error, timeout_at,
                    hrl, summary_lock,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                subagent.subagent_id, subagent.agent_id, subagent.type,
                subagent.parent_subagent_id, subagent.status,
                subagent.historical_summary, json.dumps(subagent.wake_triggers),
                subagent.handoff_notes, subagent.wake_at,
                subagent.task, subagent.progress, subagent.result,
                subagent.error, subagent.timeout_at,
                json.dumps(subagent.hrl), subagent.summary_lock,
                subagent.created_at, subagent.updated_at,
            ))
            conn.commit()

    def get_by_id(self, subagent_id: str, agent_id: str) -> Optional[SubAgent]:
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute(
                f"SELECT {self._COLUMNS} FROM subagents WHERE subagent_id = ? AND agent_id = ?",
                (subagent_id, agent_id)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_subagent(row)
            return None

    def get_by_subagent_id(self, subagent_id: str) -> Optional[SubAgent]:
        """Get SubAgent by subagent_id only (subagent_id is globally unique).

        Uses global connection since agent_id is unknown. For Gateway business APIs
        that need to resolve agent_id from subagent_id via RO API.
        """
        with self.db.get_connection("global") as conn:
            cursor = conn.execute(
                f"SELECT {self._COLUMNS} FROM subagents WHERE subagent_id = ?",
                (subagent_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_subagent(row)
            return None

    def get_main_subagent(self, agent_id: str) -> Optional[SubAgent]:
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
        subagent = self.get_main_subagent(agent_id)
        if not subagent:
            try:
                subagent = self.create_main_subagent(agent_id)
            except sqlite3.IntegrityError:
                subagent = self.get_main_subagent(agent_id)
        return subagent

    def update_wake_info(
        self,
        subagent_id: str,
        agent_id: str,
        wake_triggers: List[Dict[str, Any]],
        wake_at: Optional[str] = None,
        handoff_notes: Optional[str] = None
    ):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents
                SET wake_triggers = ?, wake_at = ?, handoff_notes = ?, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (json.dumps(wake_triggers), wake_at, handoff_notes, now, subagent_id, agent_id))
            conn.commit()

    def create_sub_subagent(
        self,
        agent_id: str,
        parent_subagent_id: str,
        task: Optional[str] = None,
        timeout_at: Optional[str] = None,
    ) -> SubAgent:
        """Create a sub SubAgent."""
        subagent_id = f"sub-{uuid.uuid4().hex[:12]}"
        now = utc_now_iso()
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

    def set_sleeping(self, subagent_id: str, agent_id: str):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents SET status = ?, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (SubagentStatus.SLEEPING.value, now, subagent_id, agent_id))
            conn.commit()

    def set_awake(self, subagent_id: str, agent_id: str):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents SET status = ?, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (SubagentStatus.AWAKE.value, now, subagent_id, agent_id))
            conn.commit()

    def set_summarizing(self, subagent_id: str, agent_id: str):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents SET status = ?, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (SubagentStatus.SUMMARIZING.value, now, subagent_id, agent_id))
            conn.commit()

    def set_completed(self, subagent_id: str, agent_id: str, result: Optional[str] = None):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents SET status = ?, result = ?, progress = NULL, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (SubagentStatus.COMPLETED.value, result, now, subagent_id, agent_id))
            conn.commit()

    def set_failed(self, subagent_id: str, agent_id: str, error: Optional[str] = None):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents SET status = ?, error = ?, progress = NULL, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (SubagentStatus.FAILED.value, error, now, subagent_id, agent_id))
            conn.commit()

    def set_cancelled(self, subagent_id: str, agent_id: str):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents SET status = ?, progress = NULL, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (SubagentStatus.CANCELLED.value, now, subagent_id, agent_id))
            conn.commit()

    def update_historical_summary(self, subagent_id: str, agent_id: str, summary: str):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents SET historical_summary = ?, updated_at = ?
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
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents SET wake_triggers = ?, handoff_notes = ?, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (json.dumps(wake_triggers), handoff_notes, now, subagent_id, agent_id))
            conn.commit()

    def delete(self, subagent_id: str, agent_id: str):
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("DELETE FROM subagents WHERE subagent_id = ? AND agent_id = ?", (subagent_id, agent_id))
            conn.commit()

    def get_due_for_wake(self) -> List[SubAgent]:
        """Find sleeping SubAgents whose wake_at has passed."""
        now = utc_now_iso()
        with self.db.get_connection("global") as conn:
            cursor = conn.execute(f"""
                SELECT {self._COLUMNS} FROM subagents
                WHERE status = 'sleeping' AND wake_at IS NOT NULL AND wake_at <= ?
                ORDER BY wake_at ASC
            """, (now,))
            rows = cursor.fetchall()
            return [self._row_to_subagent(row) for row in rows]

    def get_hrl(self, subagent_id: str, agent_id: str) -> List[str]:
        subagent = self.get_by_id(subagent_id, agent_id)
        return subagent.hrl if subagent else []

    def add_to_hrl(self, subagent_id: str, agent_id: str, runtime_id: str) -> bool:
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute(
                "SELECT hrl FROM subagents WHERE subagent_id = ? AND agent_id = ?",
                (subagent_id, agent_id)
            )
            row = cursor.fetchone()
            if not row:
                return False
            current_hrl = json.loads(row[0]) if row[0] else []
            if runtime_id in current_hrl:
                return False
            current_hrl.append(runtime_id)
            conn.execute("""
                UPDATE subagents SET hrl = ?, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (json.dumps(current_hrl), now, subagent_id, agent_id))
            conn.commit()
            return True

    def get_summary_lock(self, subagent_id: str, agent_id: str) -> int:
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute(
                "SELECT summary_lock FROM subagents WHERE subagent_id = ? AND agent_id = ?",
                (subagent_id, agent_id)
            )
            row = cursor.fetchone()
            return row[0] if row and row[0] is not None else 0

    def acquire_summary_lock(self, subagent_id: str, agent_id: str) -> bool:
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute("""
                UPDATE subagents SET summary_lock = 1, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ? AND summary_lock = 0
            """, (now, subagent_id, agent_id))
            updated = cursor.rowcount > 0
            conn.commit()
            return updated

    def release_summary_lock(self, subagent_id: str, agent_id: str):
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            conn.execute("""
                UPDATE subagents SET summary_lock = 0, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (now, subagent_id, agent_id))
            conn.commit()

    def atomic_update_history_and_hrl(
        self,
        subagent_id: str,
        agent_id: str,
        new_history: str,
        remove_runtime_ids: List[str]
    ) -> bool:
        now = utc_now_iso()
        with self.db.get_connection("agent", resource_id=agent_id) as conn:
            cursor = conn.execute(
                "SELECT hrl FROM subagents WHERE subagent_id = ? AND agent_id = ?",
                (subagent_id, agent_id)
            )
            row = cursor.fetchone()
            if not row:
                return False
            current_hrl = json.loads(row[0]) if row[0] else []
            new_hrl = [r for r in current_hrl if r not in remove_runtime_ids]
            conn.execute("""
                UPDATE subagents SET historical_summary = ?, hrl = ?, updated_at = ?
                WHERE subagent_id = ? AND agent_id = ?
            """, (new_history, json.dumps(new_hrl), now, subagent_id, agent_id))
            conn.commit()
            return True

    def _row_to_subagent(self, row) -> SubAgent:
        wake_triggers = json.loads(row[6]) if row[6] else [{"type": "user_response"}]
        hrl = json.loads(row[14]) if row[14] else []
        return SubAgent(
            subagent_id=row[0], agent_id=row[1], type=row[2],
            parent_subagent_id=row[3], status=row[4] or 'sleeping',
            historical_summary=row[5], wake_triggers=wake_triggers,
            handoff_notes=row[7], wake_at=row[8],
            task=row[9], progress=row[10], result=row[11],
            error=row[12], timeout_at=row[13],
            hrl=hrl, summary_lock=row[15] or 0,
            created_at=row[16], updated_at=row[17],
        )
