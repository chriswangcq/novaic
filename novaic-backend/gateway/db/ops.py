"""
Unified Database Operations Interface

All DB operations go through this module.
To change implementation (e.g., to process isolation), only modify this file.
"""

import sqlite3
from typing import Optional, Any, List, Dict, Tuple
from contextlib import contextmanager

from .database import get_database, Database

# ==================== Core Operations ====================


def execute(sql: str, params: Tuple = ()) -> sqlite3.Cursor:
    """Execute a SQL statement."""
    db = get_database()
    return db.execute(sql, params)


def executemany(sql: str, params_list: List[Tuple]) -> sqlite3.Cursor:
    """Execute a SQL statement with multiple parameter sets."""
    db = get_database()
    return db.executemany(sql, params_list)


def fetchone(sql: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
    """Execute query and fetch one row as dict."""
    db = get_database()
    return db.fetchone(sql, params)


def fetchall(sql: str, params: Tuple = ()) -> List[Dict[str, Any]]:
    """Execute query and fetch all rows as list of dicts."""
    db = get_database()
    return db.fetchall(sql, params)


def commit():
    """Commit current transaction."""
    db = get_database()
    db.commit()


def rollback():
    """Rollback current transaction."""
    db = get_database()
    db.rollback()


@contextmanager
def transaction():
    """
    Context manager for database transactions.
    
    Usage:
        with db_ops.transaction():
            db_ops.execute("INSERT ...")
            db_ops.execute("UPDATE ...")
            # Auto-commits on exit, rolls back on exception
    """
    db = get_database()
    with db.transaction():
        yield


@contextmanager
def connection():
    """
    Get a connection context manager.
    
    Usage:
        with db_ops.connection() as conn:
            conn.execute("SELECT ...")
    """
    db = get_database()
    with db.get_connection() as conn:
        yield conn


# ==================== Convenience Operations ====================


def get_config(key: str) -> Optional[str]:
    """Get a config value by key."""
    db = get_database()
    return db.get_config(key)


def set_config(key: str, value: str):
    """Set a config value."""
    db = get_database()
    db.set_config(key, value)


def get_runtime_state(key: str) -> Optional[str]:
    """Get a runtime state value by key."""
    db = get_database()
    return db.get_runtime_state(key)


def set_runtime_state(key: str, value: str):
    """Set a runtime state value."""
    db = get_database()
    db.set_runtime_state(key, value)


# ==================== Database Lifecycle ====================


def init() -> Database:
    """Initialize and connect to database."""
    from .database import init_database
    return init_database()


def close():
    """Close database connection."""
    from .database import close_database
    close_database()


def vacuum():
    """Vacuum the database to reclaim space."""
    db = get_database()
    db.vacuum()
