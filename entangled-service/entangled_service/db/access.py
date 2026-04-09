"""Database singleton for Entangled Service."""

from pathlib import Path
from .database import Database

_database: Database | None = None


def init_database(db_path: str) -> Database:
    global _database
    if _database is not None:
        return _database
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    _database = Database(p)
    _database.connect()
    return _database


def get_db() -> Database:
    if _database is None:
        raise RuntimeError("Database not initialized — call init_database() first")
    return _database


def close_database():
    global _database
    if _database:
        _database.close()
        _database = None
