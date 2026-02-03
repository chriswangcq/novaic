"""
NovAIC Gateway - Database Module

SQLite-based state management for stateless Gateway architecture.
All state is stored in SQLite, allowing Gateway to be killed and restarted
with complete state recovery.
"""

from .database import Database, get_database, init_database, close_database
from .schema import init_schema
from .migration import run_migration

__all__ = [
    "Database",
    "get_database",
    "init_database",
    "close_database",
    "init_schema",
    "run_migration",
]
