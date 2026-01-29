"""
Chat Repository

Handles all chat-related database operations including
real-time messages, questions/responses, and execution logs.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..database import Database


class ChatRepository:
    """Repository for chat and real-time state data."""
    
    def __init__(self, db: Database):
        self.db = db
    
    # ==================== Chat Messages ====================
    
    async def list_chat_messages(
        self,
        limit: int = 100,
        before_id: Optional[str] = None,
        message_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List chat messages with optional filters."""
        query = "SELECT * FROM chat_messages WHERE 1=1"
        params = []
        
        if message_type:
            query += " AND type = ?"
            params.append(message_type)
        
        if before_id:
            # Get timestamp of the reference message
            ref = await self.db.fetchone(
                "SELECT timestamp FROM chat_messages WHERE id = ?",
                (before_id,)
            )
            if ref:
                query += " AND timestamp < ?"
                params.append(ref["timestamp"])
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        rows = await self.db.fetchall(query, tuple(params))
        
        # Parse data JSON and reverse to chronological order
        result = []
        for row in reversed(rows):
            try:
                data = json.loads(row.get("data", "{}"))
                result.append({
                    "id": row["id"],
                    "type": row["type"],
                    "timestamp": row["timestamp"],
                    **data
                })
            except json.JSONDecodeError:
                result.append(dict(row))
        
        return result
    
    async def get_chat_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a chat message by ID."""
        row = await self.db.fetchone(
            "SELECT * FROM chat_messages WHERE id = ?",
            (message_id,)
        )
        if row:
            try:
                data = json.loads(row.get("data", "{}"))
                return {
                    "id": row["id"],
                    "type": row["type"],
                    "timestamp": row["timestamp"],
                    **data
                }
            except json.JSONDecodeError:
                return dict(row)
        return None
    
    async def add_chat_message(
        self,
        id: str,
        type: str,
        timestamp: str,
        **data
    ) -> Dict[str, Any]:
        """Add a chat message."""
        await self.db.execute(
            """INSERT INTO chat_messages (id, type, timestamp, data)
               VALUES (?, ?, ?, ?)""",
            (id, type, timestamp, json.dumps(data))
        )
        await self.db.commit()
        
        # Cleanup old messages (keep last 100)
        await self.cleanup_chat_messages(100)
        
        return await self.get_chat_message(id)
    
    async def cleanup_chat_messages(self, keep_count: int = 100):
        """Delete old chat messages, keeping the most recent ones."""
        await self.db.execute(
            """DELETE FROM chat_messages 
               WHERE id NOT IN (
                   SELECT id FROM chat_messages 
                   ORDER BY timestamp DESC 
                   LIMIT ?
               )""",
            (keep_count,)
        )
        await self.db.commit()
    
    # ==================== Pending Questions ====================
    
    async def list_pending_questions(self) -> List[Dict[str, Any]]:
        """List all pending questions."""
        rows = await self.db.fetchall(
            "SELECT * FROM pending_questions ORDER BY timestamp"
        )
        for row in rows:
            if row.get("options"):
                row["options"] = json.loads(row["options"])
        return rows
    
    async def get_pending_question(
        self,
        request_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a pending question by request ID."""
        row = await self.db.fetchone(
            "SELECT * FROM pending_questions WHERE request_id = ?",
            (request_id,)
        )
        if row and row.get("options"):
            row["options"] = json.loads(row["options"])
        return row
    
    async def add_pending_question(
        self,
        request_id: str,
        question: str,
        options: Optional[List[str]] = None,
        message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a pending question."""
        timestamp = datetime.now().isoformat()
        
        await self.db.execute(
            """INSERT INTO pending_questions 
               (request_id, question, options, message_id, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (
                request_id,
                question,
                json.dumps(options) if options else None,
                message_id,
                timestamp
            )
        )
        await self.db.commit()
        
        return await self.get_pending_question(request_id)
    
    async def delete_pending_question(self, request_id: str) -> bool:
        """Delete a pending question."""
        cursor = await self.db.execute(
            "DELETE FROM pending_questions WHERE request_id = ?",
            (request_id,)
        )
        await self.db.commit()
        return cursor.rowcount > 0
    
    # ==================== Question Responses ====================
    
    async def get_question_response(
        self,
        request_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a response to a question."""
        return await self.db.fetchone(
            "SELECT * FROM question_responses WHERE request_id = ?",
            (request_id,)
        )
    
    async def add_question_response(
        self,
        request_id: str,
        response: str,
        selected_option: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a response to a question."""
        timestamp = datetime.now().isoformat()
        
        await self.db.execute(
            """INSERT INTO question_responses 
               (request_id, response, selected_option, timestamp)
               VALUES (?, ?, ?, ?)""",
            (request_id, response, selected_option, timestamp)
        )
        await self.db.commit()
        
        return await self.get_question_response(request_id)
    
    async def pop_question_response(
        self,
        request_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get and delete a question response (atomic)."""
        async with self.db.transaction():
            response = await self.get_question_response(request_id)
            if response:
                await self.db.execute(
                    "DELETE FROM question_responses WHERE request_id = ?",
                    (request_id,)
                )
                # Also delete the pending question
                await self.db.execute(
                    "DELETE FROM pending_questions WHERE request_id = ?",
                    (request_id,)
                )
            return response
    
    # ==================== User Messages ====================
    
    async def list_user_messages(
        self,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List user messages."""
        query = "SELECT * FROM user_messages WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        return await self.db.fetchall(query, tuple(params))
    
    async def get_user_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a user message by ID."""
        return await self.db.fetchone(
            "SELECT * FROM user_messages WHERE id = ?",
            (message_id,)
        )
    
    async def add_user_message(
        self,
        id: str,
        content: str,
        timestamp: str,
        status: str = "delivered",
        model: Optional[str] = None,
        api_key_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a user message."""
        await self.db.execute(
            """INSERT INTO user_messages 
               (id, content, timestamp, status, model, api_key_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (id, content, timestamp, status, model, api_key_id)
        )
        await self.db.commit()
        
        return await self.get_user_message(id)
    
    async def update_user_message_status(
        self,
        message_id: str,
        status: str,
    ) -> bool:
        """
        Update user message status with validation.
        
        Valid transitions:
        - delivered -> read
        - read -> replied
        """
        valid_transitions = {
            "delivered": ["read"],
            "read": ["replied"],
            "replied": [],
        }
        
        async with self.db.transaction():
            # Get current status
            row = await self.db.fetchone(
                "SELECT status FROM user_messages WHERE id = ?",
                (message_id,)
            )
            if not row:
                return False
            
            current_status = row["status"]
            
            # Validate transition
            if status not in valid_transitions.get(current_status, []):
                # Allow setting same status (idempotent)
                if status == current_status:
                    return True
                return False
            
            # Update status
            await self.db.execute(
                "UPDATE user_messages SET status = ? WHERE id = ?",
                (status, message_id)
            )
        
        return True
    
    # ==================== Pending User Messages ====================
    
    async def list_pending_user_messages(self) -> List[Dict[str, Any]]:
        """List pending user messages (inbox)."""
        return await self.db.fetchall(
            "SELECT * FROM pending_user_messages ORDER BY timestamp"
        )
    
    async def add_pending_user_message(
        self,
        id: str,
        content: str,
        timestamp: str,
        model: Optional[str] = None,
        api_key_id: Optional[str] = None,
    ):
        """Add a pending user message."""
        await self.db.execute(
            """INSERT INTO pending_user_messages 
               (id, content, timestamp, model, api_key_id)
               VALUES (?, ?, ?, ?, ?)""",
            (id, content, timestamp, model, api_key_id)
        )
        await self.db.commit()
    
    async def pop_pending_user_message(
        self,
        message_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get and delete a pending user message."""
        async with self.db.transaction():
            row = await self.db.fetchone(
                "SELECT * FROM pending_user_messages WHERE id = ?",
                (message_id,)
            )
            if row:
                await self.db.execute(
                    "DELETE FROM pending_user_messages WHERE id = ?",
                    (message_id,)
                )
            return row
    
    async def pop_all_pending_user_messages(self) -> List[Dict[str, Any]]:
        """Get and delete all pending user messages."""
        async with self.db.transaction():
            rows = await self.db.fetchall(
                "SELECT * FROM pending_user_messages ORDER BY timestamp"
            )
            if rows:
                await self.db.execute("DELETE FROM pending_user_messages")
            return rows
    
    # ==================== Execution Logs ====================
    
    async def list_execution_logs(
        self,
        limit: int = 500,
        message_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List execution logs."""
        query = "SELECT * FROM execution_logs WHERE 1=1"
        params = []
        
        if message_id:
            query += " AND message_id = ?"
            params.append(message_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        rows = await self.db.fetchall(query, tuple(params))
        
        # Parse data JSON and reverse to chronological order
        result = []
        for row in reversed(rows):
            try:
                data = json.loads(row.get("data", "{}")) if row.get("data") else {}
                result.append({
                    "id": row["id"],
                    "type": row["type"],
                    "timestamp": row["timestamp"],
                    "message_id": row["message_id"],
                    "data": data,
                })
            except json.JSONDecodeError:
                result.append(dict(row))
        
        return result
    
    async def add_execution_log(
        self,
        type: str,
        timestamp: str,
        data: Optional[Dict[str, Any]] = None,
        message_id: Optional[str] = None,
    ) -> int:
        """Add an execution log."""
        cursor = await self.db.execute(
            """INSERT INTO execution_logs (type, timestamp, data, message_id)
               VALUES (?, ?, ?, ?)""",
            (type, timestamp, json.dumps(data) if data else None, message_id)
        )
        await self.db.commit()
        
        # Cleanup old logs (keep last 500)
        await self.cleanup_execution_logs(500)
        
        return cursor.lastrowid
    
    async def cleanup_execution_logs(self, keep_count: int = 500):
        """Delete old execution logs, keeping the most recent ones."""
        await self.db.execute(
            """DELETE FROM execution_logs 
               WHERE id NOT IN (
                   SELECT id FROM execution_logs 
                   ORDER BY timestamp DESC 
                   LIMIT ?
               )""",
            (keep_count,)
        )
        await self.db.commit()
    
    async def clear_execution_logs(self):
        """Clear all execution logs."""
        await self.db.execute("DELETE FROM execution_logs")
        await self.db.commit()
    
    # ==================== Agent Runtime State ====================
    
    async def get_agent_rest_state(self) -> Dict[str, Any]:
        """Get agent rest state."""
        rows = await self.db.fetchall(
            "SELECT key, value FROM agent_runtime_state"
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
    
    async def set_agent_rest_state(
        self,
        is_resting: bool,
        reason: Optional[str] = None,
        wake_triggers: Optional[List[Dict]] = None,
        handoff_notes: Optional[str] = None,
        rest_started: Optional[str] = None,
    ):
        """Set agent rest state (transaction)."""
        async with self.db.transaction():
            await self.db.set_runtime_state("is_resting", json.dumps(is_resting))
            await self.db.set_runtime_state("rest_reason", json.dumps(reason))
            await self.db.set_runtime_state("wake_triggers", json.dumps(wake_triggers or []))
            await self.db.set_runtime_state("handoff_notes", json.dumps(handoff_notes))
            await self.db.set_runtime_state("rest_started", json.dumps(rest_started))
    
    async def clear_agent_rest_state(self):
        """Clear agent rest state (wake up)."""
        await self.set_agent_rest_state(
            is_resting=False,
            reason=None,
            wake_triggers=[],
            handoff_notes=None,
            rest_started=None,
        )
    
    async def is_agent_busy(self) -> bool:
        """Check if agent is busy."""
        value = await self.db.get_runtime_state("is_busy")
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return False
        return False
    
    async def set_agent_busy(self, busy: bool):
        """Set agent busy state."""
        await self.db.set_runtime_state("is_busy", json.dumps(busy))
