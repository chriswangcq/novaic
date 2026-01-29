"""
Session Storage - JSONL persistence for sessions

Provides persistent storage for session message history.
"""

import json
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class SessionStorage:
    """
    Persistent storage for session data using JSONL format.
    
    Each session is stored as a JSONL file where each line is a JSON object
    representing a message or event in the session.
    
    File format:
    - Each line is a valid JSON object
    - Messages have: role, content, timestamp, metadata
    - Special entries: compaction_summary, session_metadata
    """
    
    def __init__(self, storage_dir: str = "storage/sessions"):
        """
        Initialize the storage.
        
        Args:
            storage_dir: Directory to store session files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_session_path(self, session_key: str) -> Path:
        """Get the file path for a session."""
        # Sanitize session key for filesystem
        safe_key = session_key.replace("/", "_").replace(":", "_")
        return self.storage_dir / f"{safe_key}.jsonl"
    
    def _get_metadata_path(self, session_key: str) -> Path:
        """Get the metadata file path for a session."""
        safe_key = session_key.replace("/", "_").replace(":", "_")
        return self.storage_dir / f"{safe_key}.meta.json"
    
    def session_exists(self, session_key: str) -> bool:
        """Check if a session file exists."""
        return self._get_session_path(session_key).exists()
    
    def list_sessions(self) -> List[str]:
        """List all stored sessions."""
        sessions = []
        for path in self.storage_dir.glob("*.jsonl"):
            # Convert filename back to session key
            session_key = path.stem.replace("_", ":")
            sessions.append(session_key)
        return sessions
    
    def save_message(
        self,
        session_key: str,
        role: str,
        content: Any,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Append a message to the session file.
        
        Args:
            session_key: Session identifier
            role: Message role (user, assistant, system, tool)
            content: Message content
            timestamp: Message timestamp (default: now)
            metadata: Additional metadata
        """
        path = self._get_session_path(session_key)
        
        entry = {
            "type": "message",
            "role": role,
            "content": content,
            "timestamp": (timestamp or datetime.now()).isoformat(),
            "metadata": metadata or {},
        }
        
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def save_compaction_summary(
        self,
        session_key: str,
        summary: str,
        compacted_count: int,
        original_tokens: int,
        summary_tokens: int,
    ) -> None:
        """
        Save a compaction summary entry.
        
        Args:
            session_key: Session identifier
            summary: The compaction summary text
            compacted_count: Number of messages compacted
            original_tokens: Token count before compaction
            summary_tokens: Token count after compaction
        """
        path = self._get_session_path(session_key)
        
        entry = {
            "type": "compaction_summary",
            "summary": summary,
            "compacted_count": compacted_count,
            "original_tokens": original_tokens,
            "summary_tokens": summary_tokens,
            "timestamp": datetime.now().isoformat(),
        }
        
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def load_messages(
        self,
        session_key: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Load messages from a session file.
        
        Args:
            session_key: Session identifier
            limit: Maximum number of messages to return
            offset: Number of messages to skip from start
        
        Returns:
            List of message dictionaries
        """
        path = self._get_session_path(session_key)
        
        if not path.exists():
            return []
        
        messages = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("type") == "message":
                            messages.append(entry)
                    except json.JSONDecodeError:
                        logger.warning(f"[Storage] Invalid JSON in {session_key}: {line[:50]}")
        except Exception as e:
            logger.error(f"[Storage] Error reading {session_key}: {e}")
        
        # Apply offset and limit
        if offset:
            messages = messages[offset:]
        if limit:
            messages = messages[:limit]
        
        return messages
    
    def load_full_session(self, session_key: str) -> List[Dict[str, Any]]:
        """
        Load all entries from a session file (messages + compaction summaries).
        
        Returns:
            List of all entries in order
        """
        path = self._get_session_path(session_key)
        
        if not path.exists():
            return []
        
        entries = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.error(f"[Storage] Error reading {session_key}: {e}")
        
        return entries
    
    def get_latest_compaction(self, session_key: str) -> Optional[Dict[str, Any]]:
        """Get the most recent compaction summary for a session."""
        entries = self.load_full_session(session_key)
        
        for entry in reversed(entries):
            if entry.get("type") == "compaction_summary":
                return entry
        
        return None
    
    def save_metadata(self, session_key: str, metadata: Dict[str, Any]) -> None:
        """Save session metadata to a separate file."""
        path = self._get_metadata_path(session_key)
        
        metadata["updated_at"] = datetime.now().isoformat()
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def load_metadata(self, session_key: str) -> Optional[Dict[str, Any]]:
        """Load session metadata."""
        path = self._get_metadata_path(session_key)
        
        if not path.exists():
            return None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[Storage] Error reading metadata for {session_key}: {e}")
            return None
    
    def delete_session(self, session_key: str) -> bool:
        """
        Delete a session and its metadata.
        
        Returns:
            True if deleted, False if not found
        """
        session_path = self._get_session_path(session_key)
        metadata_path = self._get_metadata_path(session_key)
        
        deleted = False
        
        if session_path.exists():
            session_path.unlink()
            deleted = True
        
        if metadata_path.exists():
            metadata_path.unlink()
        
        return deleted
    
    def archive_session(self, session_key: str, archive_dir: str = "storage/sessions/archive") -> bool:
        """
        Move a session to archive.
        
        Returns:
            True if archived successfully
        """
        archive_path = Path(archive_dir)
        archive_path.mkdir(parents=True, exist_ok=True)
        
        session_path = self._get_session_path(session_key)
        metadata_path = self._get_metadata_path(session_key)
        
        if not session_path.exists():
            return False
        
        # Add timestamp to archived filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_key = session_key.replace("/", "_").replace(":", "_")
        
        # Move files
        session_path.rename(archive_path / f"{safe_key}_{timestamp}.jsonl")
        
        if metadata_path.exists():
            metadata_path.rename(archive_path / f"{safe_key}_{timestamp}.meta.json")
        
        logger.info(f"[Storage] Archived session: {session_key}")
        return True
    
    def get_session_stats(self, session_key: str) -> Dict[str, Any]:
        """Get statistics for a session."""
        path = self._get_session_path(session_key)
        
        if not path.exists():
            return {"exists": False}
        
        entries = self.load_full_session(session_key)
        
        message_count = sum(1 for e in entries if e.get("type") == "message")
        compaction_count = sum(1 for e in entries if e.get("type") == "compaction_summary")
        
        # Get file size
        file_size = path.stat().st_size
        
        # Get timestamp range
        timestamps = [
            e.get("timestamp")
            for e in entries
            if e.get("timestamp")
        ]
        
        return {
            "exists": True,
            "message_count": message_count,
            "compaction_count": compaction_count,
            "file_size_bytes": file_size,
            "first_message": min(timestamps) if timestamps else None,
            "last_message": max(timestamps) if timestamps else None,
        }
