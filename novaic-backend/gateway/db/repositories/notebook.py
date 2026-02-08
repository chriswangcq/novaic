"""
Notebook Repository

Data access layer for agent_notebook table.
Handles structured document storage for agent's private workspace.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any


class NotebookRepository:
    """Repository for agent_notebook table."""
    
    def __init__(self, db):
        self.db = db
    
    def write(
        self,
        agent_id: str,
        entry_type: str,
        title: str,
        content: str,
        source: Optional[str] = None,
        related_topics: Optional[List[str]] = None,
        relevance_score: float = 0.5,
        expires_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new notebook entry."""
        now = datetime.utcnow().isoformat()
        topics_json = json.dumps(related_topics or [], ensure_ascii=False)
        relevance_score = max(0.0, min(1.0, relevance_score))
        
        with self.db.transaction(lock_type="agent", resource_id=agent_id):
            cursor = self.db.execute(
                """INSERT INTO agent_notebook 
                   (agent_id, entry_type, title, content, source, 
                    related_topics, relevance_score, status, expires_at,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?)""",
                (agent_id, entry_type, title, content, source,
                 topics_json, relevance_score, expires_at, now, now)
            )
            entry_id = cursor.lastrowid
        
        return {
            "success": True,
            "id": entry_id,
            "entry_type": entry_type,
            "title": title,
            "status": "draft",
        }
    
    def read(
        self,
        agent_id: str,
        entry_id: int,
    ) -> Dict[str, Any]:
        """Read a single notebook entry by ID."""
        row = self.db.fetchone(
            """SELECT id, entry_type, title, content, source,
                      related_topics, relevance_score, status,
                      expires_at, created_at, updated_at
               FROM agent_notebook 
               WHERE id = ? AND agent_id = ?""",
            (entry_id, agent_id)
        )
        
        if not row:
            return {"success": True, "found": False, "entry": None}
        
        return {
            "success": True,
            "found": True,
            "entry": self._row_to_dict(row),
        }
    
    def list_entries(
        self,
        agent_id: str,
        entry_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        include_expired: bool = False,
    ) -> Dict[str, Any]:
        """List notebook entries with optional filters."""
        conditions = ["agent_id = ?"]
        params: list = [agent_id]
        
        if entry_type:
            conditions.append("entry_type = ?")
            params.append(entry_type)
        
        if status:
            conditions.append("status = ?")
            params.append(status)
        
        if not include_expired:
            conditions.append("(expires_at IS NULL OR expires_at > ?)")
            params.append(datetime.utcnow().isoformat())
        
        where = " AND ".join(conditions)
        params.append(min(limit, 100))  # cap at 100
        
        rows = self.db.fetchall(
            f"""SELECT id, entry_type, title, content, source,
                       related_topics, relevance_score, status,
                       expires_at, created_at, updated_at
                FROM agent_notebook
                WHERE {where}
                ORDER BY created_at DESC
                LIMIT ?""",
            tuple(params)
        )
        
        entries = [self._row_to_dict(row) for row in rows]
        
        return {
            "success": True,
            "entries": entries,
            "count": len(entries),
        }
    
    def update(
        self,
        agent_id: str,
        entry_id: int,
        status: Optional[str] = None,
        content: Optional[str] = None,
        title: Optional[str] = None,
        relevance_score: Optional[float] = None,
        expires_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing notebook entry."""
        now = datetime.utcnow().isoformat()
        
        updates = ["updated_at = ?"]
        params: list = [now]
        
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        
        if relevance_score is not None:
            updates.append("relevance_score = ?")
            params.append(max(0.0, min(1.0, relevance_score)))
        
        if expires_at is not None:
            updates.append("expires_at = ?")
            params.append(expires_at)
        
        if len(updates) == 1:  # only updated_at
            return {"success": True, "message": "No fields to update"}
        
        set_clause = ", ".join(updates)
        params.extend([entry_id, agent_id])
        
        with self.db.transaction(lock_type="agent", resource_id=agent_id):
            self.db.execute(
                f"""UPDATE agent_notebook 
                    SET {set_clause}
                    WHERE id = ? AND agent_id = ?""",
                tuple(params)
            )
        
        return {"success": True, "id": entry_id}
    
    def delete(
        self,
        agent_id: str,
        entry_id: int,
    ) -> Dict[str, Any]:
        """Delete a notebook entry."""
        with self.db.transaction(lock_type="agent", resource_id=agent_id):
            self.db.execute(
                "DELETE FROM agent_notebook WHERE id = ? AND agent_id = ?",
                (entry_id, agent_id)
            )
        
        return {"success": True, "id": entry_id}
    
    def get_summary(
        self,
        agent_id: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Get compact summary of recent entries for Drive Prompt injection.
        
        Returns only metadata (no full content) to keep context size small.
        Excludes expired and archived entries.
        """
        now = datetime.utcnow().isoformat()
        
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
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        return {
            "id": row["id"],
            "entry_type": row["entry_type"],
            "title": row["title"],
            "content": row["content"],
            "source": row["source"],
            "related_topics": json.loads(row["related_topics"] or "[]"),
            "relevance_score": row["relevance_score"],
            "status": row["status"],
            "expires_at": row["expires_at"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
