"""
NovAIC Gateway - Database Module

SQLite-based state management for stateless Gateway architecture.
All state is stored in SQLite, allowing Gateway to be killed and restarted
with complete state recovery.

Usage:
    # Use the unified ops interface (recommended)
    from gateway.db import ops as db_ops
    
    row = db_ops.fetchone("SELECT * FROM config WHERE key = ?", ("default_model",))
    db_ops.execute("INSERT INTO ...", (...))
    db_ops.commit()
    
    with db_ops.transaction():
        db_ops.execute(...)
        db_ops.execute(...)
"""

from .database import Database, get_database, init_database, close_database
from .schema import init_schema_sync
from .migration import run_migration
from .locks import (
    LockStrategy,
    FIFOLock,
    ShardedFIFOLock,
    DatabaseLockManager,
)
from . import ops

__all__ = [
    # Database class and lifecycle
    "Database",
    "get_database",
    "init_database",
    "close_database",
    "init_schema_sync",
    "run_migration",
    # Lock management
    "LockStrategy",
    "FIFOLock",
    "ShardedFIFOLock",
    "DatabaseLockManager",
    # Unified operations interface
    "ops",
]
