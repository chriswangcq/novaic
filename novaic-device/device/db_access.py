"""Device Service database access — self-contained SQLite for VM/SSH tables.

Device Service owns `vm_processes` and `ssh_keys` tables in its own DB file.
No dependency on gateway.db.access.
"""

import logging
from pathlib import Path
from common.db import Database

logger = logging.getLogger(__name__)

_database = None

DEVICE_SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;

CREATE TABLE IF NOT EXISTS vm_processes (
    agent_id TEXT PRIMARY KEY,
    pid INTEGER,
    status TEXT DEFAULT 'stopped',
    started_at TEXT,
    ports TEXT DEFAULT '{}',
    qemu_cmd TEXT DEFAULT '',
    error_message TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS ssh_keys (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    public_key TEXT NOT NULL,
    private_key TEXT NOT NULL,
    created_at TEXT NOT NULL,
    is_default INTEGER DEFAULT 0
);
"""


def _init_schema(db):
    db.executescript(DEVICE_SCHEMA_SQL)


def init_database(data_dir: str, db_file: str = "device.db") -> Database:
    """Initialize the Device Service database."""
    global _database
    db_path = Path(data_dir) / db_file
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _database = Database(db_path)
    _database.connect(init_schema_func=_init_schema)
    logger.info("Device DB initialized: %s", db_path)
    return _database


def get_db() -> Database:
    """Get the Device Service database instance."""
    if _database is None:
        raise RuntimeError("Device database not initialized. Call init_database() first.")
    return _database


def close_database():
    """Close the Device Service database."""
    global _database
    if _database:
        _database.close()
        _database = None
