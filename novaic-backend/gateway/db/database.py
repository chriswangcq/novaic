"""
Database Connection and Management

Provides synchronous SQLite connection with WAL mode support.
"""

import os
import sqlite3
import threading
import logging
from pathlib import Path
from typing import Optional, Any, List, Dict
from contextlib import contextmanager

from .schema import init_schema_sync
from .locks import DatabaseLockManager

logger = logging.getLogger(__name__)

# Global database instance
_database: Optional["Database"] = None
_lock = threading.Lock()


class Database:
    """
    Synchronous SQLite database wrapper with transaction support.
    
    Features:
    - WAL mode for concurrent access
    - Automatic connection management
    - Transaction support with context manager
    - Row factory for dict-like access
    - Thread-safe with FIFO locks (configurable)
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._initialized = False
        self._local = threading.local()
        
        # Lock manager for coordinating concurrent access
        self.locks = DatabaseLockManager()
    
    def connect(self):
        """Connect to database and initialize schema."""
        if self._conn is not None:
            return
        
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[DB] Connecting to {self.db_path}")
        
        self._conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0
        )
        self._conn.row_factory = sqlite3.Row
        
        # Enable WAL mode and foreign keys
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA synchronous = NORMAL")
        # Set busy timeout to wait for locks instead of failing immediately
        self._conn.execute("PRAGMA busy_timeout = 5000")  # 5 seconds
        
        # Initialize schema
        init_schema_sync(self._conn)
        self._initialized = True
        
        logger.info(f"[DB] Connected and initialized")
    
    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            self._initialized = False
            logger.info("[DB] Connection closed")
    
    def vacuum(self):
        """Vacuum the database to reclaim space."""
        if self._conn:
            self._conn.execute("VACUUM")
            logger.info("[DB] Database vacuumed")
    
    def execute(
        self,
        sql: str,
        params: tuple = ()
    ) -> sqlite3.Cursor:
        """Execute a SQL statement."""
        if not self._conn:
            raise RuntimeError("Database not connected")
        return self._conn.execute(sql, params)
    
    def executemany(
        self,
        sql: str,
        params_list: List[tuple]
    ) -> sqlite3.Cursor:
        """Execute a SQL statement with multiple parameter sets."""
        if not self._conn:
            raise RuntimeError("Database not connected")
        return self._conn.executemany(sql, params_list)
    
    def fetchone(
        self,
        sql: str,
        params: tuple = ()
    ) -> Optional[Dict[str, Any]]:
        """Execute query and fetch one row as dict."""
        cursor = self.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def fetchall(
        self,
        sql: str,
        params: tuple = ()
    ) -> List[Dict[str, Any]]:
        """Execute query and fetch all rows as list of dicts."""
        cursor = self.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def commit(self):
        """Commit current transaction."""
        if self._conn:
            self._conn.commit()
    
    def rollback(self):
        """Rollback current transaction."""
        if self._conn:
            self._conn.rollback()
    
    @contextmanager
    def transaction(self, lock_type: str = "global", **lock_kwargs):
        """
        Context manager for database transactions with FIFO lock.
        
        Args:
            lock_type (str): Lock type ("global", "message", "agent", "task", "saga")
            **lock_kwargs: Lock-specific parameters
                - resource_id (str): Resource identifier (for sharded locks)
                - timeout (float): Maximum wait time
        
        Usage:
            # Global lock (default)
            with db.transaction():
                db.execute("INSERT ...")
                db.execute("UPDATE ...")
            
            # Message lock (sharded by message_id)
            with db.transaction("message", resource_id=message_id):
                db.execute("UPDATE chat_messages ...")
            
            # Agent lock (sharded by agent_id)
            with db.transaction("agent", resource_id=agent_id):
                db.execute("UPDATE subagents ...")
        """
        if not self._conn:
            raise RuntimeError("Database not connected")
        
        with self.locks.acquire(lock_type, **lock_kwargs):
            try:
                yield self
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
    
    @contextmanager
    def get_connection(self, lock_type: str = "global", **lock_kwargs):
        """
        Get a connection context manager with FIFO lock.
        
        Args:
            lock_type (str): Lock type ("global", "message", "agent", "task", "saga")
            **lock_kwargs: Lock-specific parameters
                - resource_id (str): Resource identifier (for sharded locks)
                - timeout (float): Maximum wait time
        
        Usage:
            # Global lock (default)
            with db.get_connection() as conn:
                cursor = conn.execute("SELECT ...")
            
            # Message lock (sharded by message_id)
            with db.get_connection("message", resource_id=message_id) as conn:
                conn.execute("UPDATE chat_messages ...")
                conn.commit()
        """
        if not self._conn:
            raise RuntimeError("Database not connected")
        
        with self.locks.acquire(lock_type, **lock_kwargs):
            yield self
    
    # ==================== Convenience Methods ====================
    
    def get_config(self, key: str) -> Optional[str]:
        """Get a config value by key."""
        row = self.fetchone(
            "SELECT value FROM config WHERE key = ?",
            (key,)
        )
        return row["value"] if row else None
    
    def set_config(self, key: str, value: str):
        """Set a config value."""
        self.execute(
            """INSERT INTO config (key, value, updated_at) 
               VALUES (?, ?, datetime('now'))
               ON CONFLICT(key) DO UPDATE SET 
                   value = excluded.value,
                   updated_at = datetime('now')""",
            (key, value)
        )
        self.commit()
    
    def get_runtime_state(self, key: str) -> Optional[str]:
        """Get a runtime state value by key."""
        row = self.fetchone(
            "SELECT value FROM agent_runtime_state WHERE key = ?",
            (key,)
        )
        return row["value"] if row else None
    
    def set_runtime_state(self, key: str, value: str):
        """Set a runtime state value."""
        self.execute(
            """INSERT INTO agent_runtime_state (key, value, updated_at)
               VALUES (?, ?, datetime('now'))
               ON CONFLICT(key) DO UPDATE SET
                   value = excluded.value,
                   updated_at = datetime('now')""",
            (key, value)
        )
        self.commit()


def get_database() -> Database:
    """Get the global database instance."""
    global _database
    if _database is None:
        # Get data directory from environment
        data_dir = os.environ.get("NOVAIC_DATA_DIR")
        if not data_dir:
            raise RuntimeError("NOVAIC_DATA_DIR environment variable is required")
        
        db_path = Path(data_dir) / "novaic.db"
        _database = Database(db_path)
    
    return _database


def init_database() -> Database:
    """Initialize and return the global database instance."""
    db = get_database()
    db.connect()
    return db


def close_database():
    """Close the global database connection."""
    global _database
    if _database:
        _database.close()
        _database = None
