"""
Chat Repository

Handles all chat-related database operations including
real-time messages, questions/responses, and execution logs.

Simplified in v3: unified chat_messages table with read field.
All operations are isolated per agent_id.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from common.db.database import Database


# Message types that should not be persisted to database
NON_PERSISTENT_TYPES = {"STATUS_UPDATE", "TYPING", "PING", "HEARTBEAT"}


class ChatRepository:
    """Repository for chat and real-time state data, isolated per agent."""
    
    def __init__(self, db: Database):
        self.db = db
    
    # ==================== Unified Chat Messages ====================
    
    def add_message(
        self,
        agent_id: str,
        id: str,
        type: str,
        content: Optional[str] = None,
        read: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Add a message to the chat.
        
        Args:
            agent_id: Agent ID
            id: Message ID
            type: Message type (USER_MESSAGE, AGENT_REPLY, AGENT_ASK, etc.)
            content: Message content
            read: Whether the message has been read (default False)
            metadata: Additional metadata (model, api_key_id, options, etc.)
            timestamp: Message timestamp (defaults to now)
        
        Returns:
            The created message, or None if type is non-persistent
        """
        # Skip non-persistent message types
        if type in NON_PERSISTENT_TYPES:
            return None
        
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        with self.db.transaction("message", resource_id=id):
            self.db.execute(
                """INSERT OR REPLACE INTO chat_messages 
                   (id, agent_id, type, content, read, metadata, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    id,
                    agent_id,
                    type,
                    content,
                    1 if read else 0,
                    json.dumps(metadata or {}),
                    timestamp
                )
            )
        
        # Cleanup old messages (keep last 200 per agent)
        self.cleanup_messages(agent_id, 200)
        
        return self.get_message(id)
    
    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a message by ID."""
        row = self.db.fetchone(
            "SELECT * FROM chat_messages WHERE id = ?",
            (message_id,)
        )
        if row:
            return self._row_to_message(row)
        return None
    
    def get_messages(
        self,
        agent_id: str,
        read: Optional[bool] = None,
        type_filter: Optional[List[str]] = None,
        limit: int = 100,
        before_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get messages for an agent with optional filters.
        
        Args:
            agent_id: Agent ID
            read: Filter by read status (None = all, True = read only, False = unread only)
            type_filter: Filter by message types
            limit: Maximum number of messages to return
            before_id: Pagination cursor (get messages before this ID)
        
        Returns:
            List of messages in chronological order
        """
        query = "SELECT * FROM chat_messages WHERE agent_id = ?"
        params: List[Any] = [agent_id]
        
        if read is not None:
            query += " AND read = ?"
            params.append(1 if read else 0)
        
        if type_filter:
            placeholders = ",".join(["?" for _ in type_filter])
            query += f" AND type IN ({placeholders})"
            params.extend(type_filter)
        
        if before_id:
            ref = self.db.fetchone(
                "SELECT timestamp FROM chat_messages WHERE id = ?",
                (before_id,)
            )
            if ref:
                query += " AND timestamp < ?"
                params.append(ref["timestamp"])
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        rows = self.db.fetchall(query, tuple(params))
        
        # Return in chronological order
        return [self._row_to_message(row) for row in reversed(rows)]
    
    def get_unread_messages(
        self,
        agent_id: str,
        type_filter: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get unread messages (inbox) for an agent.
        
        Args:
            agent_id: Agent ID
            type_filter: Filter by message types (default: USER_MESSAGE only)
        
        Returns:
            List of unread messages in chronological order
        """
        if type_filter is None:
            type_filter = ["USER_MESSAGE"]
        
        return self.get_messages(
            agent_id=agent_id,
            read=False,
            type_filter=type_filter,
            limit=100,
        )
    
    def mark_as_read(self, message_id: str) -> bool:
        """
        Mark a message as read.
        
        Args:
            message_id: Message ID
        
        Returns:
            True if updated, False if message not found
        """
        with self.db.transaction("message", resource_id=message_id):
            cursor = self.db.execute(
                "UPDATE chat_messages SET read = 1 WHERE id = ?",
                (message_id,)
            )
            return cursor.rowcount > 0
    
    def mark_all_as_read(self, agent_id: str) -> int:
        """
        Mark all messages as read for an agent.
        
        Returns:
            Number of messages marked as read
        """
        with self.db.transaction("agent", resource_id=agent_id):
            cursor = self.db.execute(
                "UPDATE chat_messages SET read = 1 WHERE agent_id = ? AND read = 0",
                (agent_id,)
            )
            return cursor.rowcount
    
    def cleanup_messages(self, agent_id: str, keep_count: int = 200):
        """Delete old messages for an agent, keeping the most recent ones."""
        with self.db.transaction("agent", resource_id=agent_id):
            self.db.execute(
                """DELETE FROM chat_messages 
                   WHERE agent_id = ? AND id NOT IN (
                       SELECT id FROM chat_messages 
                       WHERE agent_id = ?
                       ORDER BY timestamp DESC 
                       LIMIT ?
                   )""",
                (agent_id, agent_id, keep_count)
            )
    
    def get_message_count(self, agent_id: str, read: Optional[bool] = None) -> int:
        """Get message count for an agent."""
        if read is None:
            row = self.db.fetchone(
                "SELECT COUNT(*) as count FROM chat_messages WHERE agent_id = ?",
                (agent_id,)
            )
        else:
            row = self.db.fetchone(
                "SELECT COUNT(*) as count FROM chat_messages WHERE agent_id = ? AND read = ?",
                (agent_id, 1 if read else 0)
            )
        return row["count"] if row else 0
    
    def _row_to_message(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a database row to a message dict.
        
        Returns both 'content' and 'message' fields for SSE compatibility.
        Frontend uses: msg.message || msg.content
        """
        metadata = {}
        if row.get("metadata"):
            try:
                metadata = json.loads(row["metadata"])
            except json.JSONDecodeError:
                pass
        
        content = row.get("content")
        msg_type = row["type"]
        
        result = {
            "id": row["id"],
            "agent_id": row["agent_id"],
            "type": msg_type,
            "content": content,
            "read": bool(row.get("read", 0)),
            "metadata": metadata,
            "timestamp": row["timestamp"],
        }
        
        # Add 'message' field for AGENT_REPLY (frontend compatibility)
        # Frontend expects: msg.message || msg.content
        if msg_type == "AGENT_REPLY":
            result["message"] = content
        elif msg_type == "AGENT_ASK":
            result["question"] = content
        
        return result
    
    # ==================== Backward Compatibility ====================
    # These methods maintain API compatibility with old code
    
    def add_chat_message(
        self,
        agent_id: str,
        id: str,
        type: str,
        timestamp: str,
        **data
    ) -> Optional[Dict[str, Any]]:
        """
        Add a chat message (backward compatible).
        Extracts content from data, stores rest as metadata.
        """
        content = data.pop("content", data.pop("message", None))
        return self.add_message(
            agent_id=agent_id,
            id=id,
            type=type,
            content=content,
            metadata=data if data else None,
            timestamp=timestamp,
        )
    
    def get_chat_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Alias for get_message."""
        return self.get_message(message_id)
    
    def list_chat_messages(
        self,
        agent_id: str,
        limit: int = 100,
        before_id: Optional[str] = None,
        message_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List chat messages (backward compatible)."""
        type_filter = [message_type] if message_type else None
        return self.get_messages(
            agent_id=agent_id,
            limit=limit,
            before_id=before_id,
            type_filter=type_filter,
        )
    
    def get_recent_chat_messages(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent chat messages."""
        return self.get_messages(agent_id, limit=limit)
    
    def get_chat_history(
        self,
        agent_id: str,
        limit: int = 20,
        before_id: Optional[str] = None,
        type_filter: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get chat history."""
        return self.get_messages(
            agent_id=agent_id,
            limit=limit,
            before_id=before_id,
            type_filter=type_filter,
        )
    
    def get_chat_message_count(self, agent_id: str) -> int:
        """Get chat message count."""
        return self.get_message_count(agent_id)
    
    def cleanup_chat_messages(self, agent_id: str, keep_count: int = 100):
        """Cleanup chat messages."""
        self.cleanup_messages(agent_id, keep_count)
    
    # ==================== Pending Questions ====================
    
    def list_pending_questions(self, agent_id: str) -> List[Dict[str, Any]]:
        """List all pending questions for an agent."""
        rows = self.db.fetchall(
            "SELECT * FROM pending_questions WHERE agent_id = ? ORDER BY timestamp",
            (agent_id,)
        )
        result = []
        for row in rows:
            item = dict(row)
            if item.get("options"):
                try:
                    item["options"] = json.loads(item["options"])
                except json.JSONDecodeError:
                    pass
            result.append(item)
        return result
    
    def get_pending_question(
        self,
        request_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a pending question by request ID."""
        row = self.db.fetchone(
            "SELECT * FROM pending_questions WHERE request_id = ?",
            (request_id,)
        )
        if row:
            result = dict(row)
            if result.get("options"):
                try:
                    result["options"] = json.loads(result["options"])
                except json.JSONDecodeError:
                    pass
            return result
        return None
    
    def add_pending_question(
        self,
        agent_id: str,
        request_id: str,
        question: str,
        options: Optional[List[str]] = None,
        message_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Add a pending question for an agent."""
        timestamp = datetime.now().isoformat()
        
        with self.db.transaction("agent", resource_id=agent_id):
            self.db.execute(
                """INSERT INTO pending_questions 
                   (request_id, agent_id, question, options, message_id, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    request_id,
                    agent_id,
                    question,
                    json.dumps(options) if options else None,
                    message_id,
                    timestamp
                )
            )
        
        return self.get_pending_question(request_id)
    
    def delete_pending_question(self, request_id: str) -> bool:
        """Delete a pending question."""
        # First get agent_id to determine resource_id
        question = self.get_pending_question(request_id)
        if not question:
            return False
        
        agent_id = question.get("agent_id")
        with self.db.transaction("agent", resource_id=agent_id):
            cursor = self.db.execute(
                "DELETE FROM pending_questions WHERE request_id = ?",
                (request_id,)
            )
            return cursor.rowcount > 0
    
    def get_all_pending_questions(self, agent_id: str) -> List[Dict[str, Any]]:
        """Alias for list_pending_questions."""
        return self.list_pending_questions(agent_id)
    
    # ==================== Question Responses ====================
    
    def get_question_response(
        self,
        request_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a response to a question."""
        row = self.db.fetchone(
            "SELECT * FROM question_responses WHERE request_id = ?",
            (request_id,)
        )
        return dict(row) if row else None
    
    def add_question_response(
        self,
        agent_id: str,
        request_id: str,
        response: str,
        selected_option: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Add a response to a question."""
        timestamp = datetime.now().isoformat()
        
        with self.db.transaction("agent", resource_id=agent_id):
            self.db.execute(
                """INSERT INTO question_responses 
                   (request_id, agent_id, response, selected_option, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (request_id, agent_id, response, selected_option, timestamp)
            )
        
        return self.get_question_response(request_id)
    
    def pop_question_response(
        self,
        request_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get and delete a question response (atomic)."""
        # First get response to determine agent_id
        response = self.get_question_response(request_id)
        if not response:
            return None
        
        agent_id = response.get("agent_id")
        with self.db.transaction("agent", resource_id=agent_id):
            response = self.get_question_response(request_id)
            if response:
                self.db.execute(
                    "DELETE FROM question_responses WHERE request_id = ?",
                    (request_id,)
                )
                self.db.execute(
                    "DELETE FROM pending_questions WHERE request_id = ?",
                    (request_id,)
                )
            return response
    
    # ==================== Execution Logs ====================
    
    def list_execution_logs(
        self,
        agent_id: str,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """List execution logs for an agent."""
        rows = self.db.fetchall(
            """SELECT * FROM execution_logs 
               WHERE agent_id = ? 
               ORDER BY timestamp DESC LIMIT ?""",
            (agent_id, limit)
        )
        
        result = []
        for row in reversed(rows):
            data = {}
            if row.get("data"):
                try:
                    data = json.loads(row["data"])
                except json.JSONDecodeError:
                    pass
            result.append({
                "id": row["id"],
                "type": row["type"],
                "timestamp": row["timestamp"],
                "data": data,
            })
        
        return result
    
    def add_execution_log(
        self,
        agent_id: str,
        type: str,
        timestamp: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Add an execution log for an agent."""
        with self.db.transaction("agent", resource_id=agent_id):
            cursor = self.db.execute(
                """INSERT INTO execution_logs (agent_id, type, timestamp, data)
                   VALUES (?, ?, ?, ?)""",
                (agent_id, type, timestamp, json.dumps(data) if data else None)
            )
            row_id = cursor.lastrowid
        
        # Cleanup old logs (keep last 500 per agent)
        self.cleanup_execution_logs(agent_id, 500)
        
        return row_id
    
    def cleanup_execution_logs(self, agent_id: str, keep_count: int = 500):
        """Delete old execution logs for an agent."""
        with self.db.transaction("agent", resource_id=agent_id):
            self.db.execute(
                """DELETE FROM execution_logs 
                   WHERE agent_id = ? AND id NOT IN (
                       SELECT id FROM execution_logs 
                       WHERE agent_id = ?
                       ORDER BY timestamp DESC 
                       LIMIT ?
                   )""",
                (agent_id, agent_id, keep_count)
            )
    
    def clear_execution_logs(self, agent_id: str):
        """Clear all execution logs for an agent."""
        with self.db.transaction("agent", resource_id=agent_id):
            self.db.execute(
                "DELETE FROM execution_logs WHERE agent_id = ?",
                (agent_id,)
            )
    
    def get_recent_execution_logs(self, agent_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent execution logs."""
        return self.list_execution_logs(agent_id, limit=limit)
    
    # ==================== Agent Runtime State ====================
    
    def get_agent_rest_state(self, agent_id: str) -> Dict[str, Any]:
        """Get agent rest state."""
        rows = self.db.fetchall(
            "SELECT key, value FROM agent_runtime_state WHERE agent_id = ?",
            (agent_id,)
        )
        state = {}
        for row in rows:
            try:
                state[row["key"]] = json.loads(row["value"])
            except json.JSONDecodeError:
                state[row["key"]] = row["value"]
        
        return {
            "is_resting": state.get("is_resting", False),
            "reason": state.get("rest_reason"),
            "wake_triggers": state.get("wake_triggers", []),
            "handoff_notes": state.get("handoff_notes"),
            "rest_started": state.get("rest_started"),
        }
    
    def set_agent_rest_state(self, agent_id: str, state: Dict[str, Any]):
        """Set agent rest state."""
        with self.db.transaction("agent", resource_id=agent_id):
            self._set_runtime_state(agent_id, "is_resting", json.dumps(state.get("is_resting", False)))
            self._set_runtime_state(agent_id, "rest_reason", json.dumps(state.get("reason")))
            self._set_runtime_state(agent_id, "wake_triggers", json.dumps(state.get("wake_triggers", [])))
            self._set_runtime_state(agent_id, "handoff_notes", json.dumps(state.get("handoff_notes")))
            self._set_runtime_state(agent_id, "rest_started", json.dumps(state.get("rest_started")))
    
    def _set_runtime_state(self, agent_id: str, key: str, value: str):
        """Set a runtime state value."""
        self.db.execute(
            """INSERT OR REPLACE INTO agent_runtime_state (agent_id, key, value, updated_at)
               VALUES (?, ?, ?, datetime('now'))""",
            (agent_id, key, value)
        )
    
    def _get_runtime_state(self, agent_id: str, key: str) -> Optional[str]:
        """Get a runtime state value."""
        row = self.db.fetchone(
            "SELECT value FROM agent_runtime_state WHERE agent_id = ? AND key = ?",
            (agent_id, key)
        )
        return row["value"] if row else None
    
    def get_agent_runtime_state(self, agent_id: str) -> Dict[str, Any]:
        """Get full agent runtime state (v11: is_busy removed)."""
        rest_state = self.get_agent_rest_state(agent_id)
        return rest_state
    
    def clear_agent_rest_state(self, agent_id: str):
        """Clear agent rest state (wake up)."""
        self.set_agent_rest_state(agent_id, {
            "is_resting": False,
            "reason": None,
            "wake_triggers": [],
            "handoff_notes": None,
            "rest_started": None,
        })
