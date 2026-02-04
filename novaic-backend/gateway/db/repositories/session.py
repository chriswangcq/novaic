"""
Session Repository

Handles all session-related database operations.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from common.db.database import Database


class SessionRepository:
    """Repository for session data."""
    
    def __init__(self, db: Database):
        self.db = db
    
    # ==================== Sessions ====================
    
    def list_sessions(
        self,
        agent_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List sessions, optionally filtered by agent."""
        if agent_id:
            rows = self.db.fetchall(
                """SELECT * FROM sessions 
                   WHERE agent_id = ? 
                   ORDER BY updated_at DESC 
                   LIMIT ?""",
                (agent_id, limit)
            )
        else:
            rows = self.db.fetchall(
                "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?",
                (limit,)
            )
        
        for row in rows:
            row["metadata"] = json.loads(row.get("metadata", "{}"))
        return rows
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID."""
        row = self.db.fetchone(
            "SELECT * FROM sessions WHERE id = ?",
            (session_id,)
        )
        if row:
            row["metadata"] = json.loads(row.get("metadata", "{}"))
        return row
    
    def create_session(
        self,
        session_id: str,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new session."""
        now = datetime.now().isoformat()
        
        # Use agent_id if available, otherwise use session_id
        resource_id = agent_id if agent_id else session_id
        with self.db.transaction(lock_type="agent", resource_id=resource_id):
            self.db.execute(
                """INSERT INTO sessions (id, agent_id, created_at, updated_at, metadata)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, agent_id, now, now, json.dumps(metadata or {}))
            )
        
        return self.get_session(session_id)
    
    def update_session_timestamp(self, session_id: str):
        """Update session's updated_at timestamp."""
        with self.db.transaction(lock_type="agent", resource_id=session_id):
            self.db.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), session_id)
            )
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages."""
        with self.db.transaction(lock_type="agent", resource_id=session_id):
            cursor = self.db.execute(
                "DELETE FROM sessions WHERE id = ?",
                (session_id,)
            )
            return cursor.rowcount > 0
    
    def ensure_session(
        self,
        session_id: str,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get or create a session."""
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id, agent_id)
        return session
    
    # ==================== Session Messages ====================
    
    def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
        message_type: str = "message",
    ) -> List[Dict[str, Any]]:
        """Get messages from a session."""
        query = """SELECT * FROM session_messages 
                   WHERE session_id = ? AND type = ?
                   ORDER BY timestamp ASC"""
        params = [session_id, message_type]
        
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        rows = self.db.fetchall(query, tuple(params))
        
        for row in rows:
            row["metadata"] = json.loads(row.get("metadata", "{}"))
        return rows
    
    def get_all_entries(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get all entries (messages + compaction summaries) from a session."""
        query = """SELECT * FROM session_messages 
                   WHERE session_id = ?
                   ORDER BY timestamp ASC"""
        params = [session_id]
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        rows = self.db.fetchall(query, tuple(params))
        
        for row in rows:
            row["metadata"] = json.loads(row.get("metadata", "{}"))
        return rows
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Add a message to a session."""
        timestamp = datetime.now().isoformat()
        
        # Ensure session exists
        self.ensure_session(session_id)
        
        with self.db.transaction(lock_type="agent", resource_id=session_id):
            cursor = self.db.execute(
                """INSERT INTO session_messages 
                   (session_id, type, role, content, timestamp, metadata)
                   VALUES (?, 'message', ?, ?, ?, ?)""",
                (
                    session_id,
                    role,
                    json.dumps(content) if not isinstance(content, str) else content,
                    timestamp,
                    json.dumps(metadata or {})
                )
            )
            
            # Update session timestamp
            self.db.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (timestamp, session_id)
            )
            
            return cursor.lastrowid
    
    def add_compaction_summary(
        self,
        session_id: str,
        summary: str,
        compacted_count: int,
        original_tokens: int,
        summary_tokens: int,
    ) -> int:
        """Add a compaction summary to a session."""
        timestamp = datetime.now().isoformat()
        
        with self.db.transaction(lock_type="agent", resource_id=session_id):
            cursor = self.db.execute(
                """INSERT INTO session_messages 
                   (session_id, type, content, timestamp, compacted_count, original_tokens, summary_tokens)
                   VALUES (?, 'compaction_summary', ?, ?, ?, ?, ?)""",
                (session_id, summary, timestamp, compacted_count, original_tokens, summary_tokens)
            )
            return cursor.lastrowid
    
    def get_latest_compaction(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get the most recent compaction summary for a session."""
        return self.db.fetchone(
            """SELECT * FROM session_messages 
               WHERE session_id = ? AND type = 'compaction_summary'
               ORDER BY timestamp DESC LIMIT 1""",
            (session_id,)
        )
    
    def get_message_count(self, session_id: str) -> int:
        """Get the number of messages in a session."""
        row = self.db.fetchone(
            "SELECT COUNT(*) as count FROM session_messages WHERE session_id = ? AND type = 'message'",
            (session_id,)
        )
        return row["count"] if row else 0
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session."""
        session = self.get_session(session_id)
        if not session:
            return {"exists": False}
        
        message_count = self.db.fetchone(
            "SELECT COUNT(*) as count FROM session_messages WHERE session_id = ? AND type = 'message'",
            (session_id,)
        )
        compaction_count = self.db.fetchone(
            "SELECT COUNT(*) as count FROM session_messages WHERE session_id = ? AND type = 'compaction_summary'",
            (session_id,)
        )
        
        timestamps = self.db.fetchall(
            "SELECT MIN(timestamp) as first, MAX(timestamp) as last FROM session_messages WHERE session_id = ?",
            (session_id,)
        )
        
        return {
            "exists": True,
            "message_count": message_count["count"] if message_count else 0,
            "compaction_count": compaction_count["count"] if compaction_count else 0,
            "first_message": timestamps[0]["first"] if timestamps else None,
            "last_message": timestamps[0]["last"] if timestamps else None,
        }
