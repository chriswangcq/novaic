"""
Memory Repository

Handles all Agent Memory database operations.
Replaces file-based memory storage with SQLite.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..database import Database


class MemoryRepository:
    """Repository for Agent memory data (key-value storage)."""
    
    def __init__(self, db: Database):
        self.db = db
    
    # ========================================
    # Key-Value Memory Operations
    # ========================================
    
    def save(
        self,
        agent_id: str,
        key: str,
        value: Any,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """Save a memory value (upsert)."""
        now = datetime.now().isoformat()
        value_json = json.dumps(value, ensure_ascii=False)
        
        # Use INSERT OR REPLACE for upsert
        self.db.execute(
            """INSERT INTO agent_memory (agent_id, namespace, key, value, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(agent_id, namespace, key) 
               DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at""",
            (agent_id, namespace, key, value_json, now, now)
        )
        self.db.commit()
        
        return {
            "success": True,
            "key": key,
            "namespace": namespace
        }
    
    def recall(
        self,
        agent_id: str,
        key: Optional[str] = None,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """Recall memory value(s)."""
        if key:
            # Get single key
            row = self.db.fetchone(
                """SELECT value, updated_at FROM agent_memory 
                   WHERE agent_id = ? AND namespace = ? AND key = ?""",
                (agent_id, namespace, key)
            )
            if row:
                return {
                    "success": True,
                    "key": key,
                    "value": json.loads(row["value"]),
                    "updated_at": row["updated_at"],
                    "found": True
                }
            else:
                return {
                    "success": True,
                    "key": key,
                    "value": None,
                    "found": False
                }
        else:
            # Get all in namespace
            rows = self.db.fetchall(
                """SELECT key, value FROM agent_memory 
                   WHERE agent_id = ? AND namespace = ?""",
                (agent_id, namespace)
            )
            memories = {row["key"]: json.loads(row["value"]) for row in rows}
            return {
                "success": True,
                "namespace": namespace,
                "memories": memories,
                "count": len(memories)
            }
    
    def delete(
        self,
        agent_id: str,
        key: str,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """Delete a memory value."""
        result = self.db.execute(
            """DELETE FROM agent_memory 
               WHERE agent_id = ? AND namespace = ? AND key = ?""",
            (agent_id, namespace, key)
        )
        self.db.commit()
        
        return {
            "success": True,
            "key": key,
            "deleted": result.rowcount > 0
        }
    
    def list_namespaces(self, agent_id: str) -> List[str]:
        """List all namespaces for an agent."""
        rows = self.db.fetchall(
            """SELECT DISTINCT namespace FROM agent_memory WHERE agent_id = ?""",
            (agent_id,)
        )
        return [row["namespace"] for row in rows]
    
    def delete_all_for_agent(self, agent_id: str) -> int:
        """Delete all memory for an agent. Returns count deleted."""
        result = self.db.execute(
            "DELETE FROM agent_memory WHERE agent_id = ?",
            (agent_id,)
        )
        self.db.commit()
        return result.rowcount
    
    # ========================================
    # Task History Operations
    # ========================================
    
    def log_task(
        self,
        agent_id: str,
        action: str,
        details: Optional[str] = None,
        status: str = "completed"
    ) -> Dict[str, Any]:
        """Log a task action."""
        now = datetime.now().isoformat()
        
        self.db.execute(
            """INSERT INTO agent_task_history (agent_id, action, details, status, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (agent_id, action, details, status, now)
        )
        self.db.commit()
        
        # Get count
        row = self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM agent_task_history WHERE agent_id = ?",
            (agent_id,)
        )
        
        return {
            "success": True,
            "logged": {
                "action": action,
                "details": details,
                "status": status,
                "timestamp": now
            },
            "history_count": row["cnt"] if row else 0
        }
    
    def get_task_history(
        self,
        agent_id: str,
        limit: int = 20,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get task history."""
        # Get total count
        total_row = self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM agent_task_history WHERE agent_id = ?",
            (agent_id,)
        )
        total_count = total_row["cnt"] if total_row else 0
        
        # Build query
        if status_filter:
            rows = self.db.fetchall(
                """SELECT action, details, status, timestamp FROM agent_task_history 
                   WHERE agent_id = ? AND status = ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (agent_id, status_filter, limit)
            )
            # Get filtered count
            filter_row = self.db.fetchone(
                "SELECT COUNT(*) as cnt FROM agent_task_history WHERE agent_id = ? AND status = ?",
                (agent_id, status_filter)
            )
            filtered_count = filter_row["cnt"] if filter_row else 0
        else:
            rows = self.db.fetchall(
                """SELECT action, details, status, timestamp FROM agent_task_history 
                   WHERE agent_id = ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (agent_id, limit)
            )
            filtered_count = total_count
        
        history = [dict(row) for row in rows]
        history.reverse()  # Oldest first
        
        return {
            "success": True,
            "history": history,
            "total_count": total_count,
            "filtered_count": filtered_count
        }
    
    def cleanup_old_tasks(self, agent_id: str, keep_count: int = 100) -> int:
        """Keep only the most recent N task history entries."""
        # Get IDs to keep
        rows = self.db.fetchall(
            """SELECT id FROM agent_task_history 
               WHERE agent_id = ? 
               ORDER BY timestamp DESC LIMIT ?""",
            (agent_id, keep_count)
        )
        keep_ids = [row["id"] for row in rows]
        
        if not keep_ids:
            return 0
        
        # Delete others
        placeholders = ",".join(["?"] * len(keep_ids))
        result = self.db.execute(
            f"""DELETE FROM agent_task_history 
                WHERE agent_id = ? AND id NOT IN ({placeholders})""",
            (agent_id, *keep_ids)
        )
        self.db.commit()
        return result.rowcount
    
    def delete_task_history_for_agent(self, agent_id: str) -> int:
        """Delete all task history for an agent."""
        result = self.db.execute(
            "DELETE FROM agent_task_history WHERE agent_id = ?",
            (agent_id,)
        )
        self.db.commit()
        return result.rowcount
