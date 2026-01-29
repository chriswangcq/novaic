"""
Database Connection and Management

Provides async SQLite connection with WAL mode support.
"""

import os
import aiosqlite
import logging
from pathlib import Path
from typing import Optional, Any, List, Dict
from contextlib import asynccontextmanager

from .schema import init_schema

logger = logging.getLogger(__name__)

# Global database instance
_database: Optional["Database"] = None


class Database:
    """
    Async SQLite database wrapper with transaction support.
    
    Features:
    - WAL mode for concurrent access
    - Automatic connection management
    - Transaction support with context manager
    - Row factory for dict-like access
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None
        self._initialized = False
    
    async def connect(self):
        """Connect to database and initialize schema."""
        if self._conn is not None:
            return
        
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[DB] Connecting to {self.db_path}")
        
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        
        # Enable WAL mode and foreign keys
        await self._conn.execute("PRAGMA journal_mode = WAL")
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.execute("PRAGMA synchronous = NORMAL")
        
        # Initialize schema
        await init_schema(self._conn)
        self._initialized = True
        
        logger.info(f"[DB] Connected and initialized")
    
    async def close(self):
        """Close database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None
            self._initialized = False
            logger.info("[DB] Connection closed")
    
    async def execute(
        self,
        sql: str,
        params: tuple = ()
    ) -> aiosqlite.Cursor:
        """Execute a SQL statement."""
        if not self._conn:
            raise RuntimeError("Database not connected")
        return await self._conn.execute(sql, params)
    
    async def executemany(
        self,
        sql: str,
        params_list: List[tuple]
    ) -> aiosqlite.Cursor:
        """Execute a SQL statement with multiple parameter sets."""
        if not self._conn:
            raise RuntimeError("Database not connected")
        return await self._conn.executemany(sql, params_list)
    
    async def fetchone(
        self,
        sql: str,
        params: tuple = ()
    ) -> Optional[Dict[str, Any]]:
        """Execute query and fetch one row as dict."""
        cursor = await self.execute(sql, params)
        row = await cursor.fetchone()
        return dict(row) if row else None
    
    async def fetchall(
        self,
        sql: str,
        params: tuple = ()
    ) -> List[Dict[str, Any]]:
        """Execute query and fetch all rows as list of dicts."""
        cursor = await self.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def commit(self):
        """Commit current transaction."""
        if self._conn:
            await self._conn.commit()
    
    async def rollback(self):
        """Rollback current transaction."""
        if self._conn:
            await self._conn.rollback()
    
    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for database transactions.
        
        Usage:
            async with db.transaction():
                await db.execute("INSERT ...")
                await db.execute("UPDATE ...")
                # Commits on exit, rolls back on exception
        """
        if not self._conn:
            raise RuntimeError("Database not connected")
        
        try:
            yield self
            await self._conn.commit()
        except Exception:
            await self._conn.rollback()
            raise
    
    # ==================== Convenience Methods ====================
    
    async def get_config(self, key: str) -> Optional[str]:
        """Get a config value by key."""
        row = await self.fetchone(
            "SELECT value FROM config WHERE key = ?",
            (key,)
        )
        return row["value"] if row else None
    
    async def set_config(self, key: str, value: str):
        """Set a config value."""
        await self.execute(
            """INSERT INTO config (key, value, updated_at) 
               VALUES (?, ?, datetime('now'))
               ON CONFLICT(key) DO UPDATE SET 
                   value = excluded.value,
                   updated_at = datetime('now')""",
            (key, value)
        )
        await self.commit()
    
    async def get_runtime_state(self, key: str) -> Optional[str]:
        """Get a runtime state value by key."""
        row = await self.fetchone(
            "SELECT value FROM agent_runtime_state WHERE key = ?",
            (key,)
        )
        return row["value"] if row else None
    
    async def set_runtime_state(self, key: str, value: str):
        """Set a runtime state value."""
        await self.execute(
            """INSERT INTO agent_runtime_state (key, value, updated_at)
               VALUES (?, ?, datetime('now'))
               ON CONFLICT(key) DO UPDATE SET
                   value = excluded.value,
                   updated_at = datetime('now')""",
            (key, value)
        )
        await self.commit()


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


async def init_database() -> Database:
    """Initialize and return the global database instance."""
    db = get_database()
    await db.connect()
    return db


async def close_database():
    """Close the global database connection."""
    global _database
    if _database:
        await _database.close()
        _database = None
