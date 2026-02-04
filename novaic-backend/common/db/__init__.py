"""
Database Common Library

提供数据库连接管理和锁机制的公共实现。
供 Gateway 和 Queue Service 共享使用。

Usage:
    from common.db import Database, DatabaseLockManager
"""

from .database import Database
from .locks import (
    LockStrategy,
    FIFOLock,
    ShardedFIFOLock,
    DatabaseLockManager,
)

__all__ = [
    "Database",
    "LockStrategy",
    "FIFOLock",
    "ShardedFIFOLock",
    "DatabaseLockManager",
]
