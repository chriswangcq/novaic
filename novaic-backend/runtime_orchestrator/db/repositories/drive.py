"""
Drive Repository (RO-native).
Minimal parity for /internal/agents/{agent_id}/drive.
"""

import json
from typing import Dict, Any

from common.utils.time import utc_now_iso


class DriveRepository:
    """Repository for agent_drive table (RO-native)."""

    def __init__(self, db):
        self.db = db

    def get_or_create(self, agent_id: str) -> Dict[str, Any]:
        """Get drive record, creating default if missing."""
        try:
            with self.db.transaction(lock_type="agent", resource_id=agent_id):
                self.db.execute(
                    "INSERT OR IGNORE INTO agent_drive (agent_id) VALUES (?)",
                    (agent_id,)
                )
        except Exception:
            pass

        row = self.db.fetchone(
            "SELECT * FROM agent_drive WHERE agent_id = ?",
            (agent_id,)
        )
        if not row:
            return self._default_drive(agent_id)

        return {
            "agent_id": row["agent_id"],
            "personality": json.loads(row["personality"] or "{}"),
            "communication_style": row["communication_style"] or "friendly",
            "user_profile": json.loads(row["user_profile"] or "{}"),
            "interaction_count": row["interaction_count"] or 0,
            "no_response_streak": row["no_response_streak"] or 0,
        }

    def increment_interaction(self, agent_id: str) -> Dict[str, Any]:
        """Atomically increment interaction_count and reset no_response_streak."""
        now = utc_now_iso()
        self.get_or_create(agent_id)
        try:
            with self.db.transaction(lock_type="agent", resource_id=agent_id):
                self.db.execute(
                    """UPDATE agent_drive
                       SET interaction_count = interaction_count + 1,
                           no_response_streak = 0,
                           updated_at = ?
                       WHERE agent_id = ?""",
                    (now, agent_id)
                )
        except Exception as e:
            return {"success": False, "error": str(e)}
        return {"success": True}

    def _default_drive(self, agent_id: str) -> Dict[str, Any]:
        return {
            "agent_id": agent_id,
            "personality": {},
            "communication_style": "friendly",
            "user_profile": {},
            "interaction_count": 0,
            "no_response_streak": 0,
        }
