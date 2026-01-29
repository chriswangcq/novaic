"""
Session Storage - Database Version

Provides persistent storage for session message history using SQLite.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from db.database import get_database, Database
from db.repositories.session import SessionRepository

logger = logging.getLogger(__name__)


class SessionStorageDB:
    """
    Database-backed session storage.
    
    All operations go directly to SQLite.
    Replaces the JSONL file-based storage.
    """
    
    def __init__(self, db: Optional[Database] = None):
        self._db = db
        self._repo: Optional[SessionRepository] = None
    
    @property
    def db(self) -> Database:
        if self._db is None:
            self._db = get_database()
        return self._db
    
    @property
    def repo(self) -> SessionRepository:
        if self._repo is None:
            self._repo = SessionRepository(self.db)
        return self._repo
    
    async def session_exists(self, session_key: str) -> bool:
        """Check if a session exists."""
        session = await self.repo.get_session(session_key)
        return session is not None
    
    async def list_sessions(self) -> List[str]:
        """List all stored sessions."""
        sessions = await self.repo.list_sessions()
        return [s["id"] for s in sessions]
    
    async def save_message(
        self,
        session_key: str,
        role: str,
        content: Any,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Save a message to the session.
        
        Args:
            session_key: Session identifier
            role: Message role (user, assistant, system, tool)
            content: Message content
            timestamp: Message timestamp (default: now)
            metadata: Additional metadata
        
        Returns:
            Message ID
        """
        return await self.repo.add_message(
            session_id=session_key,
            role=role,
            content=content,
            metadata=metadata,
        )
    
    async def save_compaction_summary(
        self,
        session_key: str,
        summary: str,
        compacted_count: int,
        original_tokens: int,
        summary_tokens: int,
    ) -> int:
        """
        Save a compaction summary entry.
        
        Args:
            session_key: Session identifier
            summary: The compaction summary text
            compacted_count: Number of messages compacted
            original_tokens: Token count before compaction
            summary_tokens: Token count after compaction
        
        Returns:
            Entry ID
        """
        return await self.repo.add_compaction_summary(
            session_id=session_key,
            summary=summary,
            compacted_count=compacted_count,
            original_tokens=original_tokens,
            summary_tokens=summary_tokens,
        )
    
    async def load_messages(
        self,
        session_key: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Load messages from a session.
        
        Args:
            session_key: Session identifier
            limit: Maximum number of messages to return
            offset: Number of messages to skip from start
        
        Returns:
            List of message dictionaries
        """
        messages = await self.repo.get_messages(
            session_id=session_key,
            limit=limit,
            offset=offset,
            message_type="message",
        )
        
        # Convert to expected format
        return [
            {
                "type": "message",
                "role": m["role"],
                "content": m["content"],
                "timestamp": m["timestamp"],
                "metadata": m.get("metadata", {}),
            }
            for m in messages
        ]
    
    async def load_full_session(
        self,
        session_key: str
    ) -> List[Dict[str, Any]]:
        """
        Load all entries from a session (messages + compaction summaries).
        
        Returns:
            List of all entries in order
        """
        entries = await self.repo.get_all_entries(session_id=session_key)
        
        result = []
        for entry in entries:
            if entry["type"] == "message":
                result.append({
                    "type": "message",
                    "role": entry["role"],
                    "content": entry["content"],
                    "timestamp": entry["timestamp"],
                    "metadata": entry.get("metadata", {}),
                })
            elif entry["type"] == "compaction_summary":
                result.append({
                    "type": "compaction_summary",
                    "summary": entry["content"],
                    "compacted_count": entry.get("compacted_count"),
                    "original_tokens": entry.get("original_tokens"),
                    "summary_tokens": entry.get("summary_tokens"),
                    "timestamp": entry["timestamp"],
                })
        
        return result
    
    async def get_latest_compaction(
        self,
        session_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get the most recent compaction summary for a session."""
        entry = await self.repo.get_latest_compaction(session_key)
        if entry:
            return {
                "type": "compaction_summary",
                "summary": entry["content"],
                "compacted_count": entry.get("compacted_count"),
                "original_tokens": entry.get("original_tokens"),
                "summary_tokens": entry.get("summary_tokens"),
                "timestamp": entry["timestamp"],
            }
        return None
    
    async def save_metadata(
        self,
        session_key: str,
        metadata: Dict[str, Any]
    ):
        """Save session metadata."""
        await self.repo.ensure_session(session_key)
        # Update session with metadata in the sessions table
        await self.db.execute(
            """UPDATE sessions SET metadata = ?, updated_at = ?
               WHERE id = ?""",
            (json.dumps(metadata), datetime.now().isoformat(), session_key)
        )
        await self.db.commit()
    
    async def load_metadata(
        self,
        session_key: str
    ) -> Optional[Dict[str, Any]]:
        """Load session metadata."""
        session = await self.repo.get_session(session_key)
        if session:
            return session.get("metadata", {})
        return None
    
    async def delete_session(self, session_key: str) -> bool:
        """Delete a session and its messages."""
        return await self.repo.delete_session(session_key)
    
    async def get_session_stats(
        self,
        session_key: str
    ) -> Dict[str, Any]:
        """Get statistics for a session."""
        return await self.repo.get_session_stats(session_key)


# ==================== Sync Wrapper for Backward Compatibility ====================

import asyncio


class SessionStorage:
    """
    Synchronous wrapper around SessionStorageDB.
    
    Maintains the same API as the original file-based SessionStorage.
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        # storage_dir is ignored for DB version
        self._async_storage = SessionStorageDB()
    
    def _run_async(self, coro):
        """Run an async coroutine synchronously."""
        try:
            loop = asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        except RuntimeError:
            return asyncio.run(coro)
    
    def session_exists(self, session_key: str) -> bool:
        """Check if a session exists."""
        return self._run_async(self._async_storage.session_exists(session_key))
    
    def list_sessions(self) -> List[str]:
        """List all stored sessions."""
        return self._run_async(self._async_storage.list_sessions())
    
    def save_message(
        self,
        session_key: str,
        role: str,
        content: Any,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save a message to the session."""
        self._run_async(self._async_storage.save_message(
            session_key, role, content, timestamp, metadata
        ))
    
    def save_compaction_summary(
        self,
        session_key: str,
        summary: str,
        compacted_count: int,
        original_tokens: int,
        summary_tokens: int,
    ) -> None:
        """Save a compaction summary entry."""
        self._run_async(self._async_storage.save_compaction_summary(
            session_key, summary, compacted_count, original_tokens, summary_tokens
        ))
    
    def load_messages(
        self,
        session_key: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Load messages from a session."""
        return self._run_async(self._async_storage.load_messages(
            session_key, limit, offset
        ))
    
    def load_full_session(self, session_key: str) -> List[Dict[str, Any]]:
        """Load all entries from a session."""
        return self._run_async(self._async_storage.load_full_session(session_key))
    
    def get_latest_compaction(
        self,
        session_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get the most recent compaction summary."""
        return self._run_async(self._async_storage.get_latest_compaction(session_key))
    
    def save_metadata(
        self,
        session_key: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Save session metadata."""
        self._run_async(self._async_storage.save_metadata(session_key, metadata))
    
    def load_metadata(self, session_key: str) -> Optional[Dict[str, Any]]:
        """Load session metadata."""
        return self._run_async(self._async_storage.load_metadata(session_key))
    
    def delete_session(self, session_key: str) -> bool:
        """Delete a session."""
        return self._run_async(self._async_storage.delete_session(session_key))
    
    def archive_session(
        self,
        session_key: str,
        archive_dir: str = "storage/sessions/archive"
    ) -> bool:
        """Archive a session (deletes in DB version)."""
        # In DB version, we just delete (data is in DB)
        return self.delete_session(session_key)
    
    def get_session_stats(self, session_key: str) -> Dict[str, Any]:
        """Get statistics for a session."""
        return self._run_async(self._async_storage.get_session_stats(session_key))
