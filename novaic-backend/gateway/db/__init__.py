"""
Gateway Database Module

使用 common.db 提供的公共基础设施。
"""

from common.db import Database, DatabaseLockManager
from .access import get_database, get_db, init_database, close_database
from .schema import init_schema_sync
from .migration import run_migration
from . import ops

__all__ = [
    # Database class
    "Database",
    "DatabaseLockManager",
    # Gateway database access
    "get_database",
    "get_db",
    "init_database",
    "close_database",
    # Schema
    "init_schema_sync",
    "run_migration",
    # Modules
    "ops",
]
