"""
Inbox Repository

Data access layer for inbox_messages table.
Handles all pending input messages that need Agent processing.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4


class InboxRepository:
    """Repository for inbox_messages table."""
    
    def __init__(self, db):
        self.db = db
    
    async def add_message(
        self,
        agent_id: str,
        msg_type: str,
        content: str,
        priority: int = 2,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add a message to the inbox.
        
        Args:
            agent_id: Agent ID
            msg_type: Message type (USER_MESSAGE, SYSTEM_MESSAGE, etc.)
            content: Message content
            priority: Priority (0=CRITICAL, 1=HIGH, 2=NORMAL, 3=LOW)
            source: Message source (user, system:bootstrap, webhook:xxx, etc.)
            metadata: Additional metadata
        
        Returns:
            The created message dict
        """
        msg_id = str(uuid4())[:12]
        now = datetime.now().isoformat()
        
        await self.db.execute(
            """INSERT INTO inbox_messages 
               (id, agent_id, type, content, priority, source, metadata, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
            (msg_id, agent_id, msg_type, content, priority, source, 
             json.dumps(metadata or {}), now)
        )
        await self.db.commit()
        
        return {
            "id": msg_id,
            "agent_id": agent_id,
            "type": msg_type,
            "content": content,
            "priority": priority,
            "source": source,
            "metadata": metadata or {},
            "status": "pending",
            "created_at": now,
            "processed_at": None,
        }
    
    async def pop_message(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get and claim the next pending message (by priority, then time).
        
        Atomically updates status to 'processing'.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            Message dict or None if no pending messages
        """
        # Get the next pending message
        row = await self.db.fetchone(
            """SELECT * FROM inbox_messages 
               WHERE agent_id = ? AND status = 'pending'
               ORDER BY priority ASC, created_at ASC
               LIMIT 1""",
            (agent_id,)
        )
        
        if not row:
            return None
        
        msg_id = row["id"]
        
        # Update status to processing
        await self.db.execute(
            "UPDATE inbox_messages SET status = 'processing' WHERE id = ?",
            (msg_id,)
        )
        await self.db.commit()
        
        # Parse and return
        return {
            "id": row["id"],
            "agent_id": row["agent_id"],
            "type": row["type"],
            "content": row["content"],
            "priority": row["priority"],
            "source": row["source"],
            "metadata": json.loads(row["metadata"] or "{}"),
            "status": "processing",
            "created_at": row["created_at"],
            "processed_at": row["processed_at"],
        }
    
    async def mark_done(self, msg_id: str):
        """Mark a message as done."""
        await self.db.execute(
            "UPDATE inbox_messages SET status = 'done', processed_at = ? WHERE id = ?",
            (datetime.now().isoformat(), msg_id)
        )
        await self.db.commit()
    
    async def mark_failed(self, msg_id: str, error: Optional[str] = None):
        """Mark a message as failed."""
        if error:
            # Store error in metadata
            row = await self.db.fetchone(
                "SELECT metadata FROM inbox_messages WHERE id = ?",
                (msg_id,)
            )
            if row:
                metadata = json.loads(row["metadata"] or "{}")
                metadata["error"] = error
                await self.db.execute(
                    "UPDATE inbox_messages SET status = 'failed', processed_at = ?, metadata = ? WHERE id = ?",
                    (datetime.now().isoformat(), json.dumps(metadata), msg_id)
                )
            else:
                await self.db.execute(
                    "UPDATE inbox_messages SET status = 'failed', processed_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), msg_id)
                )
        else:
            await self.db.execute(
                "UPDATE inbox_messages SET status = 'failed', processed_at = ? WHERE id = ?",
                (datetime.now().isoformat(), msg_id)
            )
        await self.db.commit()
    
    async def get_pending_count(self, agent_id: str) -> int:
        """Get count of pending messages."""
        result = await self.db.fetchone(
            "SELECT COUNT(*) as count FROM inbox_messages WHERE agent_id = ? AND status = 'pending'",
            (agent_id,)
        )
        return result["count"] if result else 0
    
    async def get_pending_messages(
        self,
        agent_id: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get pending messages list.
        
        Args:
            agent_id: Agent ID
            limit: Maximum number of messages to return
        
        Returns:
            List of message dicts
        """
        rows = await self.db.fetchall(
            """SELECT * FROM inbox_messages 
               WHERE agent_id = ? AND status = 'pending'
               ORDER BY priority ASC, created_at ASC
               LIMIT ?""",
            (agent_id, limit)
        )
        
        return [
            {
                "id": row["id"],
                "agent_id": row["agent_id"],
                "type": row["type"],
                "content": row["content"],
                "priority": row["priority"],
                "source": row["source"],
                "metadata": json.loads(row["metadata"] or "{}"),
                "status": row["status"],
                "created_at": row["created_at"],
                "processed_at": row["processed_at"],
            }
            for row in rows
        ]
    
    async def recover_processing(self, agent_id: str) -> int:
        """
        Recover messages stuck in 'processing' state.
        
        Called on service restart to reset processing messages back to pending.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            Number of messages recovered
        """
        result = await self.db.execute(
            "UPDATE inbox_messages SET status = 'pending' WHERE agent_id = ? AND status = 'processing'",
            (agent_id,)
        )
        await self.db.commit()
        return result.rowcount if hasattr(result, 'rowcount') else 0
    
    async def get_message(self, msg_id: str) -> Optional[Dict[str, Any]]:
        """Get a message by ID."""
        row = await self.db.fetchone(
            "SELECT * FROM inbox_messages WHERE id = ?",
            (msg_id,)
        )
        
        if not row:
            return None
        
        return {
            "id": row["id"],
            "agent_id": row["agent_id"],
            "type": row["type"],
            "content": row["content"],
            "priority": row["priority"],
            "source": row["source"],
            "metadata": json.loads(row["metadata"] or "{}"),
            "status": row["status"],
            "created_at": row["created_at"],
            "processed_at": row["processed_at"],
        }
    
    async def delete_old_messages(
        self,
        agent_id: str,
        days: int = 7,
        statuses: Optional[List[str]] = None,
    ) -> int:
        """
        Delete old messages.
        
        Args:
            agent_id: Agent ID
            days: Delete messages older than this many days
            statuses: Only delete messages with these statuses (default: done, failed)
        
        Returns:
            Number of messages deleted
        """
        if statuses is None:
            statuses = ["done", "failed"]
        
        placeholders = ",".join("?" * len(statuses))
        cutoff = datetime.now().isoformat()
        
        result = await self.db.execute(
            f"""DELETE FROM inbox_messages 
                WHERE agent_id = ? 
                AND status IN ({placeholders})
                AND created_at < datetime('now', '-{days} days')""",
            (agent_id, *statuses)
        )
        await self.db.commit()
        return result.rowcount if hasattr(result, 'rowcount') else 0
