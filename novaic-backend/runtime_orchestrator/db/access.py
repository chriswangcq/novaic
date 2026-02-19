"""
Runtime Orchestrator database access (RO-native).

Standalone DB management for Runtime Orchestrator; no gateway.db coupling.
"""

from pathlib import Path

from common.db import Database

# RO-specific globals (separate from gateway.db)
_database = None
_database_file = "runtime_orchestrator.db"
_data_dir = ""
_init_schema_func = None


def get_db() -> Database:
    """Get the global Runtime Orchestrator database instance."""
    global _database
    if _database is None:
        if not _data_dir:
            raise RuntimeError(
                "Runtime Orchestrator DB not initialized; "
                "call init_database(data_dir=..., db_file=..., init_schema_func=...) first"
            )
        db_path = Path(_data_dir) / _database_file
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _database = Database(db_path)
        _database.connect(init_schema_func=_init_schema_func)

    return _database


def set_database_target(data_dir: str, db_file: str, init_schema_func=None) -> None:
    """Set target database path before initialization."""
    global _database_file, _data_dir, _database, _init_schema_func
    if _database is not None:
        raise RuntimeError("Database already initialized; set target before init_database()")
    _data_dir = data_dir
    _database_file = db_file
    if init_schema_func is not None:
        _init_schema_func = init_schema_func


def init_database(
    data_dir: str | None = None,
    db_file: str | None = None,
    init_schema_func=None,
) -> Database:
    """Initialize and return the global Runtime Orchestrator database instance."""
    if data_dir is not None or db_file is not None or init_schema_func is not None:
        set_database_target(
            data_dir=data_dir or _data_dir,
            db_file=db_file or _database_file,
            init_schema_func=init_schema_func,
        )
    return get_db()


def close_database():
    """Close the Runtime Orchestrator database connection."""
    global _database
    if _database:
        _database.close()
        _database = None


get_database = get_db

__all__ = ["get_database", "get_db", "init_database", "close_database"]
