"""
Notebook Repository (RO-native).
Minimal parity for /internal/agents/{agent_id}/notebook-summary.
"""

from typing import Dict, Any

from common.utils.time import utc_now_iso


class NotebookRepository:
    """Repository for agent_notebook table (RO-native)."""

    def __init__(self, db):
        self.db = db

    def get_summary(self, agent_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get compact summary of recent entries for Drive Prompt injection."""
        now = utc_now_iso()
        rows = self.db.fetchall(
            """SELECT id, entry_type, title, status, relevance_score, created_at
               FROM agent_notebook
               WHERE agent_id = ?
                 AND status != 'archived'
                 AND (expires_at IS NULL OR expires_at > ?)
               ORDER BY created_at DESC
               LIMIT ?""",
            (agent_id, now, min(limit, 50))
        )
        entries = [
            {
                "id": row["id"],
                "type": row["entry_type"],
                "title": row["title"],
                "status": row["status"],
                "relevance": row["relevance_score"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
        return {
            "success": True,
            "entries": entries,
            "count": len(entries),
        }
