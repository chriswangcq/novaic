"""
Gateway Database Access

提供 Gateway 专用的数据库访问函数。
"""

import os
from pathlib import Path
from common.db import Database
from .schema import init_schema_sync

# Global database instance
_database = None


def get_db() -> Database:
    """Get the global Gateway database instance."""
    global _database
    if _database is None:
        # Get data directory from environment
        data_dir = os.environ.get("NOVAIC_DATA_DIR")
        if not data_dir:
            raise RuntimeError("NOVAIC_DATA_DIR environment variable is required")
        
        # Gateway 使用 novaic.db (原来的主数据库)
        db_path = Path(data_dir) / "novaic.db"
        _database = Database(db_path)
        _database.connect(init_schema_func=init_schema_sync)
    
    return _database


def init_database() -> Database:
    """Initialize and return the global Gateway database instance."""
    return get_db()


def close_database():
    """Close the global Gateway database connection."""
    global _database
    if _database:
        _database.close()
        _database = None


# Alias for compatibility
get_database = get_db
