"""
Database Connection and Management

Provides async SQLite connection with WAL mode support.
"""

import os
import asyncio
import contextvars
import aiosqlite
import logging
from pathlib import Path
from typing import Optional, Any, List, Dict, Callable, Awaitable, Tuple
from contextlib import asynccontextmanager

from .schema import init_schema

logger = logging.getLogger(__name__)

# Global database instance
_database: Optional["Database"] = None


class QueuedCursor:
    def __init__(self, db: "Database", cursor: aiosqlite.Cursor):
        self._db = db
        self._cursor = cursor

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    @property
    def lastrowid(self) -> int:
        return self._cursor.lastrowid

    async def fetchone(self):
        # 直接在同一个 worker 线程中执行，不重新排队
        # cursor 已经在 worker 中创建，所以可以直接操作
        return await self._cursor.fetchone()

    async def fetchall(self):
        # 直接在同一个 worker 线程中执行，不重新排队
        return await self._cursor.fetchall()


class _ConnectionProxy:
    def __init__(self, db: "Database"):
        self._db = db

    async def execute(self, sql: str, params: tuple = ()):
        return await self._db.execute(sql, params)

    async def executemany(self, sql: str, params_list: List[tuple]):
        return await self._db.executemany(sql, params_list)

    async def commit(self):
        return await self._db.commit()

    async def rollback(self):
        return await self._db.rollback()


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
        self._queue: Optional[asyncio.Queue] = None
        self._worker_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._closing = False
        self._in_worker = contextvars.ContextVar("db_in_worker", default=False)
        self._in_transaction = contextvars.ContextVar("db_in_transaction", default=False)
    
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
        # Set busy timeout to wait for locks instead of failing immediately
        await self._conn.execute("PRAGMA busy_timeout = 5000")  # 5 seconds
        
        # Initialize schema
        await init_schema(self._conn)
        self._initialized = True

        if self._queue is None:
            self._queue = asyncio.Queue()
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker_loop())
        
        logger.info(f"[DB] Connected and initialized")
    
    async def close(self):
        """Close database connection."""
        self._closing = True
        if self._queue and self._worker_task:
            await self._queue.put(None)
            await self._worker_task
            self._worker_task = None
        if self._conn:
            await self._conn.close()
            self._conn = None
            self._initialized = False
            logger.info("[DB] Connection closed")
    
    async def vacuum(self):
        """Vacuum the database to reclaim space."""
        if self._conn:
            async def _do(conn):
                await conn.execute("VACUUM")
            await self._run(_do)
            logger.info("[DB] Database vacuumed")

    async def _worker_loop(self):
        assert self._queue is not None
        while True:
            item = await self._queue.get()
            if item is None:
                self._queue.task_done()
                break
            func, fut = item
            try:
                async with self._lock:
                    token = self._in_worker.set(True)
                    try:
                        result = await func(self._conn)
                    finally:
                        self._in_worker.reset(token)
                if not fut.cancelled():
                    fut.set_result(result)
            except Exception as e:
                if not fut.cancelled():
                    fut.set_exception(e)
            finally:
                self._queue.task_done()

    async def _run(self, func: Callable[[aiosqlite.Connection], Awaitable[Any]]):
        if not self._conn:
            raise RuntimeError("Database not connected")
        if self._in_worker.get() or self._in_transaction.get():
            return await func(self._conn)
        if not self._queue or self._closing:
            raise RuntimeError("Database queue is not available")
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        await self._queue.put((func, fut))
        return await fut
    
    async def execute(
        self,
        sql: str,
        params: tuple = ()
    ) -> aiosqlite.Cursor:
        """Execute a SQL statement."""
        async def _do(conn):
            return await conn.execute(sql, params)
        cursor = await self._run(_do)
        return QueuedCursor(self, cursor)
    
    async def executemany(
        self,
        sql: str,
        params_list: List[tuple]
    ) -> aiosqlite.Cursor:
        """Execute a SQL statement with multiple parameter sets."""
        async def _do(conn):
            return await conn.executemany(sql, params_list)
        cursor = await self._run(_do)
        return QueuedCursor(self, cursor)
    
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
        async def _do(conn):
            await conn.commit()
        await self._run(_do)
    
    async def rollback(self):
        """Rollback current transaction."""
        async def _do(conn):
            await conn.rollback()
        await self._run(_do)
    
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
        async with self._lock:
            token = self._in_transaction.set(True)
            try:
                yield self
                await self.commit()  # 通过队列提交
            except Exception:
                await self.rollback()  # 通过队列回滚
                raise
            finally:
                self._in_transaction.reset(token)
    
    @asynccontextmanager
    async def get_connection(self):
        """
        Get a connection context manager.
        
        This is an alias for accessing the raw connection for operations
        that need direct connection access (like BEGIN/COMMIT manually).
        
        Usage:
            async with db.get_connection() as conn:
                cursor = await conn.execute("SELECT ...")
        """
        if not self._conn:
            raise RuntimeError("Database not connected")
        async with self._lock:
            token = self._in_transaction.set(True)
            try:
                yield _ConnectionProxy(self)
            finally:
                self._in_transaction.reset(token)
    
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
