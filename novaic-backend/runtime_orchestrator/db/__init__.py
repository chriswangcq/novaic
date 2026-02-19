"""
Runtime Orchestrator DB facade.

This package is the canonical import path for RO data access.
"""

from .access import close_database, get_database, get_db, init_database
from .schema import init_runtime_schema_sync

__all__ = [
    "get_database",
    "get_db",
    "init_database",
    "close_database",
    "init_runtime_schema_sync",
]

