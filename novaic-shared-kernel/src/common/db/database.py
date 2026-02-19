"""Database connection and management."""

import sqlite3
import threading
import logging
from pathlib import Path
from typing import Optional, Any, List, Dict
from contextlib import contextmanager

from .locks import DatabaseLockManager

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._initialized = False
        self._local = threading.local()
        self._init_schema_func = None
        self.locks = DatabaseLockManager()

    def connect(self, init_schema_func=None):
        if self._initialized:
            return
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema_func = init_schema_func
        conn = self._create_connection()
        if init_schema_func:
            init_schema_func(conn)
        self._initialized = True

    def _create_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA busy_timeout = 10000")
        return conn

    def _get_thread_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = self._create_connection()
        return self._local.conn

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        if not self._initialized:
            raise RuntimeError("Database not connected")
        return self._get_thread_connection().execute(sql, params)

    def executemany(self, sql: str, params_list: List[tuple]) -> sqlite3.Cursor:
        if not self._initialized:
            raise RuntimeError("Database not connected")
        return self._get_thread_connection().executemany(sql, params_list)

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        row = self.execute(sql, params).fetchone()
        return dict(row) if row else None

    def fetchall(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        rows = self.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    fetch_all = fetchall

    @contextmanager
    def transaction(self, lock_type: str = "global", **lock_kwargs):
        if not self._initialized:
            raise RuntimeError("Database not connected")
        conn = self._get_thread_connection()
        with self.locks.acquire(lock_type, **lock_kwargs):
            try:
                yield self
                conn.commit()
            except Exception:
                conn.rollback()
                raise
