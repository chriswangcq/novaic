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
from common.config import ServiceConfig
from common.utils.time import utc_now_iso


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
            timestamp = utc_now_iso()
        
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
        
        # Cleanup old messages (keep last N per agent)
        self.cleanup_messages(agent_id, ServiceConfig.CLEANUP_KEEP_MESSAGES)
        
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
        limit: int = None,
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
        if limit is None:
            limit = ServiceConfig.MAX_MESSAGES_PER_PAGE
        
        # Always exclude internal messages from UI queries
        # These are system/internal messages that should not appear in the chat UI:
        # - SYSTEM_WAKE: 系统唤醒消息
        # - SUBAGENT_COMPLETED: 子任务完成通知
        # - SPAWN_SUBAGENT: 子代理创建任务
        # - SYSTEM_MESSAGE: 系统消息（如 setup bootstrap）
        query = "SELECT * FROM chat_messages WHERE agent_id = ? AND type NOT IN ('SYSTEM_WAKE', 'SUBAGENT_COMPLETED', 'SPAWN_SUBAGENT', 'SYSTEM_MESSAGE')"
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
            limit=ServiceConfig.MAX_MESSAGES_PER_PAGE,
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
    
    def cleanup_messages(self, agent_id: str, keep_count: int = None):
        """Delete old messages for an agent, keeping the most recent ones."""
        if keep_count is None:
            keep_count = ServiceConfig.CLEANUP_KEEP_MESSAGES
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
        timestamp = utc_now_iso()
        
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
        timestamp = utc_now_iso()
        
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
    
    # Maximum size for data fields in logs (50KB) - larger images will be saved to file
    MAX_LOG_DATA_SIZE = 50 * 1024
    
    # Known image field names
    IMAGE_FIELD_NAMES = ('screenshot', 'image', 'image_data', 'base64', 'data')
    
    # Base64 image prefixes
    BASE64_IMAGE_PREFIXES = ('iVBOR', '/9j/', 'R0lGOD', 'data:image')
    
    def _is_base64_image(self, value: str) -> bool:
        """Check if a string looks like base64 encoded image data."""
        if not isinstance(value, str):
            return False
        return value.startswith(self.BASE64_IMAGE_PREFIXES)
    
    def _save_image_to_file(self, base64_data: str, agent_id: str, subagent_id: str = "main") -> str:
        """
        Save base64 image to file and return URL.
        
        Args:
            base64_data: Base64 encoded image data
            agent_id: Agent ID for organizing images
            subagent_id: Subagent ID
            
        Returns:
            URL path to access the image (e.g., "/api/images/agent_id/abc123.png")
        """
        try:
            from task_queue.utils.image_storage import get_image_storage
            storage = get_image_storage()
            url = storage.save_image(agent_id, base64_data, subagent_id)
            return url
        except Exception as e:
            # If saving fails, return truncated placeholder
            logger.warning(f"[ChatRepository] Failed to save image to file: {e}")
            return "[IMAGE_SAVE_FAILED]"
    
    def _convert_large_images_to_urls(
        self,
        data: Any,
        agent_id: str,
        subagent_id: str = "main",
        max_size: int = None,
    ) -> Any:
        """
        Recursively convert large base64 images to file URLs.
        
        Instead of truncating, saves large images to files and replaces with URLs.
        This allows images to be viewed on demand without bloating the database.
        
        Args:
            data: Data to process
            agent_id: Agent ID for organizing images
            subagent_id: Subagent ID
            max_size: Size threshold in bytes
            
        Returns:
            Processed data with large images replaced by URLs
        """
        if max_size is None:
            max_size = self.MAX_LOG_DATA_SIZE
            
        if data is None:
            return None
            
        if isinstance(data, str):
            if len(data) > max_size and self._is_base64_image(data):
                # Save to file and return URL
                return self._save_image_to_file(data, agent_id, subagent_id)
            elif len(data) > max_size:
                # Non-image large data: truncate
                return data[:1000] + f"... [TRUNCATED: {len(data)} bytes]"
            return data
            
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Check if this is a known image field with large data
                if key in self.IMAGE_FIELD_NAMES and isinstance(value, str) and len(value) > max_size:
                    if self._is_base64_image(value):
                        result[key] = self._save_image_to_file(value, agent_id, subagent_id)
                    else:
                        result[key] = value[:1000] + f"... [TRUNCATED: {len(value)} bytes]"
                else:
                    result[key] = self._convert_large_images_to_urls(value, agent_id, subagent_id, max_size)
            return result
            
        if isinstance(data, list):
            return [self._convert_large_images_to_urls(item, agent_id, subagent_id, max_size) for item in data]
            
        return data
    
    def _truncate_large_data(self, data: Any, max_size: int = None) -> Any:
        """
        Recursively truncate large data fields (for reading from DB).
        
        This is used when reading logs to prevent memory issues.
        Note: New logs should use _convert_large_images_to_urls instead.
        """
        if max_size is None:
            max_size = self.MAX_LOG_DATA_SIZE
            
        if data is None:
            return None
            
        if isinstance(data, str):
            # If it's already a URL, keep it
            if data.startswith('/api/images/'):
                return data
            if len(data) > max_size:
                if self._is_base64_image(data):
                    return "[IMAGE_DATA_TRUNCATED]"
                return data[:1000] + f"... [TRUNCATED: {len(data)} bytes]"
            return data
            
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key in self.IMAGE_FIELD_NAMES and isinstance(value, str) and len(value) > max_size:
                    if self._is_base64_image(value):
                        result[key] = "[IMAGE_DATA_TRUNCATED]"
                    else:
                        result[key] = value[:1000] + f"... [TRUNCATED: {len(value)} bytes]"
                else:
                    result[key] = self._truncate_large_data(value, max_size)
            return result
            
        if isinstance(data, list):
            return [self._truncate_large_data(item, max_size) for item in data]
            
        return data
    
    def _row_to_execution_log(
        self,
        row: Dict[str, Any],
        truncate_large: bool = True,
        exclude_input: bool = False,
    ) -> Dict[str, Any]:
        """Convert a database row to an execution log dict.
        
        Args:
            row: Database row
            truncate_large: If True, truncate large data fields (screenshots, etc.)
            exclude_input: If True, don't return full input, only input_summary for think types
        """
        data = {}
        if row.get("data"):
            try:
                data = json.loads(row["data"])
            except json.JSONDecodeError:
                pass
        
        # Truncate large data to prevent memory issues
        if truncate_large:
            data = self._truncate_large_data(data)
        
        # Extract input and result from data if present (for backward compatibility)
        # These are stored in data by upsert_execution_log, but should be returned as top-level fields
        input_data = data.pop("input", None) if isinstance(data, dict) else None
        result_data = data.pop("result", None) if isinstance(data, dict) else None
        
        # Also truncate input and result
        if truncate_large:
            input_data = self._truncate_large_data(input_data)
            result_data = self._truncate_large_data(result_data)
        
        # Generate input_summary for think types when exclude_input is True
        # Only exclude input for think types, tool types should always have input
        input_summary = None
        kind = row.get("kind", "tool")
        should_exclude_input = exclude_input and kind == "think"
        
        if should_exclude_input and input_data and isinstance(input_data, dict):
            input_summary = {
                "message_count": len(input_data.get("messages", [])),
                "tool_count": len(input_data.get("tools", [])),
                "model": input_data.get("model"),
                "provider": input_data.get("provider"),
            }
        
        return {
            "id": row["id"],
            "agent_id": row.get("agent_id"),
            "subagent_id": row.get("subagent_id", "main"),
            "type": row["type"],
            "kind": kind,
            "status": row.get("status", "complete"),
            "event_key": row.get("event_key"),
            "timestamp": row["timestamp"],
            "data": data,
            "input": None if should_exclude_input else input_data,  # Only exclude for think types
            "input_summary": input_summary,
            "result": result_data,
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        }
    
    def get_execution_log_input(self, log_id: int) -> Optional[Dict[str, Any]]:
        """Get the input data for a specific execution log.
        
        Args:
            log_id: The execution log ID
            
        Returns:
            The input data dict, or None if not found
        """
        row = self.db.fetchone(
            "SELECT data FROM execution_logs WHERE id = ?",
            (log_id,)
        )
        if not row or not row.get("data"):
            return None
        
        try:
            data = json.loads(row["data"])
            return data.get("input") if isinstance(data, dict) else None
        except json.JSONDecodeError:
            return None
    
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
        
        return [self._row_to_execution_log(row) for row in reversed(rows)]
    
    def add_execution_log(
        self,
        agent_id: str,
        type: str,
        timestamp: str,
        data: Optional[Dict[str, Any]] = None,
        subagent_id: str = "main",
        kind: str = "tool",
        status: str = "complete",
        event_key: Optional[str] = None,
    ) -> int:
        """Add an execution log for an agent.
        
        Note: Large images (>50KB) will be saved to files and replaced with URLs.
        """
        now = utc_now_iso()
        
        # Convert large images to file URLs to prevent database bloat
        processed_data = self._convert_large_images_to_urls(data, agent_id, subagent_id) if data else None
        
        with self.db.transaction("agent", resource_id=agent_id):
            cursor = self.db.execute(
                """INSERT INTO execution_logs 
                   (agent_id, subagent_id, type, kind, status, event_key, timestamp, data, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (agent_id, subagent_id, type, kind, status, event_key, 
                 timestamp, json.dumps(processed_data) if processed_data else None, now)
            )
            row_id = cursor.lastrowid
        
        # Cleanup old logs (keep last N per agent)
        self.cleanup_execution_logs(agent_id, ServiceConfig.CLEANUP_KEEP_EXECUTION_LOGS)
        
        return row_id
    
    def upsert_execution_log(
        self,
        agent_id: str,
        subagent_id: str,
        kind: str,
        status: str,
        event_key: str,
        data: Optional[Dict[str, Any]] = None,
        input_data: Optional[Dict[str, Any]] = None,
        result_data: Optional[Dict[str, Any]] = None,
        type: Optional[str] = None,
    ) -> int:
        """
        Upsert an execution log by (agent_id, subagent_id, event_key).
        
        If not exists: INSERT with new data
        If exists: UPDATE status, data, updated_at
        
        Args:
            agent_id: Agent ID
            subagent_id: SubAgent ID (e.g., 'main', 'sub-xxx')
            kind: Log kind ('think' | 'tool')
            status: Log status ('running' | 'complete')
            event_key: Unique business key (e.g., 'think:{runtime_id}:{round_id}')
            data: Main data payload
            input_data: Input data (merged into data)
            result_data: Result data (merged into data)
            type: Log type (defaults to kind if not provided)
        
        Returns:
            The row ID of the upserted log
        """
        now = utc_now_iso()
        log_type = type or kind
        
        # Merge data fields
        merged_data = data or {}
        if input_data:
            merged_data["input"] = input_data
        if result_data:
            merged_data["result"] = result_data
        
        # Convert large images to file URLs to prevent database bloat
        processed_data = self._convert_large_images_to_urls(merged_data, agent_id, subagent_id) if merged_data else None
        data_json = json.dumps(processed_data) if processed_data else None
        
        with self.db.transaction("agent", resource_id=agent_id):
            # Check if record exists to merge data properly
            existing = self.db.fetchone(
                "SELECT id, data FROM execution_logs WHERE agent_id = ? AND subagent_id = ? AND event_key = ?",
                (agent_id, subagent_id, event_key)
            )
            
            if existing:
                # Merge existing data with new data (preserve input when updating with result)
                existing_data = {}
                if existing["data"]:
                    try:
                        existing_data = json.loads(existing["data"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                # Deep merge: keep existing fields, add/update new fields
                final_data = {**existing_data, **processed_data} if processed_data else existing_data
                # Ensure input is preserved if it existed
                if "input" in existing_data and (not processed_data or "input" not in processed_data):
                    final_data["input"] = existing_data["input"]
                
                final_data_json = json.dumps(final_data) if final_data else None
                
                cursor = self.db.execute(
                    """UPDATE execution_logs SET
                       status = ?, data = ?, updated_at = ?
                       WHERE id = ?""",
                    (status, final_data_json, now, existing["id"])
                )
                row_id = existing["id"]
            else:
                # Insert new record
                cursor = self.db.execute(
                    """INSERT INTO execution_logs 
                       (agent_id, subagent_id, type, kind, status, event_key, timestamp, data, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (agent_id, subagent_id, log_type, kind, status, event_key, now, data_json, now)
                )
                row_id = cursor.lastrowid
        
        return row_id
    
    def get_execution_logs(
        self,
        agent_id: str,
        subagent_id: Optional[str] = None,
        after_id: Optional[int] = None,
        before_id: Optional[int] = None,
        limit: int = None,
        exclude_input: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get execution logs with optional filters.
        
        Args:
            agent_id: Agent ID
            subagent_id: Optional SubAgent ID filter
            after_id: Optional ID to fetch logs after (for incremental fetch)
            before_id: Optional ID to fetch logs before (for pagination)
            limit: Maximum number of logs to return
            exclude_input: If True, don't return full input, only input_summary
        
        Returns:
            List of execution logs with all fields
        """
        if limit is None:
            limit = ServiceConfig.MAX_EXECUTION_LOGS_PER_PAGE
        
        query = "SELECT * FROM execution_logs WHERE agent_id = ?"
        params: List[Any] = [agent_id]
        
        if subagent_id is not None:
            query += " AND subagent_id = ?"
            params.append(subagent_id)
        
        if after_id is not None:
            query += " AND id > ?"
            params.append(after_id)
        
        if before_id is not None:
            query += " AND id < ?"
            params.append(before_id)
        
        # For before_id (pagination), order DESC then reverse; for after_id, order ASC
        if before_id is not None:
            query += " ORDER BY id DESC LIMIT ?"
        else:
            query += " ORDER BY id ASC LIMIT ?"
        params.append(limit)
        
        rows = self.db.fetchall(query, tuple(params))
        
        # Reverse if using before_id to return in chronological order (oldest to newest)
        if before_id is not None:
            rows = list(reversed(rows))
        
        return [self._row_to_execution_log(row, exclude_input=exclude_input) for row in rows]
    
    def get_log_subagents(self, agent_id: str) -> List[str]:
        """
        Get list of subagent_ids that have logs for this agent.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            List of unique subagent_ids
        """
        rows = self.db.fetchall(
            "SELECT DISTINCT subagent_id FROM execution_logs WHERE agent_id = ?",
            (agent_id,)
        )
        return [row["subagent_id"] for row in rows]
    
    def cleanup_execution_logs(self, agent_id: str, keep_count: int = None):
        """Delete old execution logs for an agent."""
        if keep_count is None:
            keep_count = ServiceConfig.CLEANUP_KEEP_EXECUTION_LOGS
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
    
    def get_recent_execution_logs(
        self,
        agent_id: str,
        limit: int = 20,
        subagent_id: Optional[str] = None,
        exclude_input: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get recent execution logs (newest first), optionally filtered by subagent_id.
        
        Args:
            agent_id: Agent ID
            limit: Maximum number of logs to return
            subagent_id: Optional SubAgent ID filter
            exclude_input: If True, don't return full input, only input_summary
        
        Returns logs in chronological order (oldest to newest).
        """
        query = "SELECT * FROM execution_logs WHERE agent_id = ?"
        params: List[Any] = [agent_id]
        
        if subagent_id is not None:
            query += " AND subagent_id = ?"
            params.append(subagent_id)
        
        # Get newest logs first, then reverse for chronological order
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        
        rows = self.db.fetchall(query, tuple(params))
        # Reverse to return in chronological order (oldest to newest)
        return [self._row_to_execution_log(row, exclude_input=exclude_input) for row in reversed(rows)]

    def get_execution_logs_after(
        self,
        agent_id: str,
        after_id: int,
        limit: int = 50,
        subagent_id: Optional[str] = None,
        exclude_input: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get execution logs with id > after_id (for incremental fetch).
        
        Args:
            agent_id: Agent ID
            after_id: Return logs with id > after_id
            limit: Maximum number of logs to return
            subagent_id: Optional SubAgent ID filter
            exclude_input: If True, don't return full input, only input_summary
        """
        return self.get_execution_logs(agent_id, subagent_id=subagent_id, after_id=after_id, limit=limit, exclude_input=exclude_input)

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
