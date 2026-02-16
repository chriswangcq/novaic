"""Gateway database access helpers."""

from pathlib import Path
from common.config import ServiceConfig
from common.db import Database
from .schema import init_schema_sync

# Global database instance
_database = None
_database_file = ServiceConfig.GATEWAY_DB_FILE
_data_dir = ServiceConfig.DATA_DIR


def get_db() -> Database:
    """Get the global Gateway database instance."""
    global _database
    if _database is None:
        db_path = Path(_data_dir) / _database_file
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _database = Database(db_path)
        _database.connect(init_schema_func=init_schema_sync)
    
    return _database


def set_database_target(data_dir: str, db_file: str) -> None:
    """Set target database path before initialization."""
    global _database_file, _data_dir, _database
    if _database is not None:
        raise RuntimeError("Database already initialized; set target before init_database()")
    _data_dir = data_dir
    _database_file = db_file


def init_database(data_dir: str | None = None, db_file: str | None = None) -> Database:
    """Initialize and return the global Gateway database instance."""
    if data_dir is not None or db_file is not None:
        set_database_target(
            data_dir=data_dir or _data_dir,
            db_file=db_file or _database_file,
        )
    return get_db()


def close_database():
    """Close the global Gateway database connection."""
    global _database
    if _database:
        _database.close()
        _database = None


# Alias for compatibility
get_database = get_db
