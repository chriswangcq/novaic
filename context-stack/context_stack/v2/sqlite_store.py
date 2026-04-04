"""
Context Stack v2 — SQLite Scope Store (§5.4)

Persistent scope storage backed by SQLite with WAL mode.

Features:
  - WAL mode for concurrent reads during writes
  - schema_version for safe migrations
  - Thread-safe via connection-per-thread
  - Batch-friendly save with upsert
  - Full MemoryBackend protocol compliance
  - Raw messages stored as JSON (capped by raw_max_chars_per_scope)

Table schema:
  - scopes: core scope record fields
  - scope_messages: raw messages per scope (optional)
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time
from typing import Dict, List, Optional

from .types import Message, MessageRole, ScopeRecord, ScopeState

logger = logging.getLogger("context_stack.v2.sqlite_store")

SCHEMA_VERSION = 2

# ─────────────────────────────────────────────
# SQL Statements
# ─────────────────────────────────────────────

_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS schema_info (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scopes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    skill_name TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT 'open',
    started_at REAL NOT NULL,
    ended_at REAL,
    summary TEXT NOT NULL DEFAULT '',
    decisions TEXT NOT NULL DEFAULT '[]',
    files_changed TEXT NOT NULL DEFAULT '[]',
    errors TEXT NOT NULL DEFAULT '[]',
    tools_used TEXT NOT NULL DEFAULT '{}',
    message_start_idx INTEGER NOT NULL DEFAULT 0,
    message_count INTEGER NOT NULL DEFAULT 0,
    tokens_before INTEGER NOT NULL DEFAULT 0,
    tokens_after INTEGER NOT NULL DEFAULT 0,
    tokens_saved INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 0,
    parent_id TEXT,
    children_ids TEXT NOT NULL DEFAULT '[]',
    created_at REAL NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE TABLE IF NOT EXISTS scope_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope_id TEXT NOT NULL,
    msg_index INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    tool_name TEXT,
    tool_input TEXT,
    tool_call_id TEXT,
    timestamp REAL,
    metadata TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (scope_id) REFERENCES scopes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scope_messages_scope_id
    ON scope_messages(scope_id);

CREATE INDEX IF NOT EXISTS idx_scopes_ended_at
    ON scopes(ended_at);

CREATE INDEX IF NOT EXISTS idx_scopes_state
    ON scopes(state);

CREATE INDEX IF NOT EXISTS idx_scopes_level
    ON scopes(level);
"""


class SqliteScopeStore:
    """
    Thread-safe SQLite-backed scope store with WAL mode.

    Implements MemoryBackend protocol.

    Usage:
        store = SqliteScopeStore("./scopes.db")
        engine = ContextEngine(store=store)
        # ... use engine ...
        store.close()  # or use context manager

    Multi-tenant: use separate DB files or key prefix per tenant.
    """

    def __init__(
        self,
        path: str = ":memory:",
        store_raw_messages: bool = True,
        raw_max_chars: int = 50_000,
    ):
        """
        Args:
            path: SQLite database path. ":memory:" for in-memory (testing).
            store_raw_messages: whether to persist raw scope messages
            raw_max_chars: max total chars for raw messages per scope
        """
        self._path = path
        self._store_raw = store_raw_messages
        self._raw_max_chars = raw_max_chars
        self._closed = False

        # Thread-local connections (SQLite is not thread-safe with one conn)
        self._local = threading.local()

        # Initialize schema on main thread
        conn = self._get_connection()
        self._init_schema(conn)

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create a thread-local connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            conn = sqlite3.connect(self._path)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn

    def _init_schema(self, conn: sqlite3.Connection) -> None:
        """Create tables if needed and verify/update schema version."""
        conn.executescript(_CREATE_TABLES)

        # Check/set schema version
        cur = conn.execute(
            "SELECT value FROM schema_info WHERE key = 'schema_version'"
        )
        row = cur.fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO schema_info (key, value) VALUES ('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )
            conn.commit()
        else:
            stored_version = int(row[0])
            if stored_version > SCHEMA_VERSION:
                raise RuntimeError(
                    f"Database schema version {stored_version} is newer than "
                    f"supported version {SCHEMA_VERSION}. Upgrade context-stack."
                )
            if stored_version < SCHEMA_VERSION:
                self._migrate(conn, stored_version, SCHEMA_VERSION)

        logger.info(
            "SqliteScopeStore initialized: path=%s schema_v=%d",
            self._path, SCHEMA_VERSION,
        )

    def _migrate(
        self,
        conn: sqlite3.Connection,
        from_version: int,
        to_version: int,
    ) -> None:
        """Run schema migrations."""
        logger.info(
            "Migrating schema from v%d to v%d", from_version, to_version,
        )
        if from_version < 2:
            # v1 → v2: add gem fusion columns
            try:
                conn.execute("ALTER TABLE scopes ADD COLUMN level INTEGER NOT NULL DEFAULT 0")
                conn.execute("ALTER TABLE scopes ADD COLUMN parent_id TEXT")
                conn.execute("ALTER TABLE scopes ADD COLUMN children_ids TEXT NOT NULL DEFAULT '[]'")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_scopes_level ON scopes(level)")
            except sqlite3.OperationalError:
                pass  # columns already exist
        conn.execute(
            "UPDATE schema_info SET value = ? WHERE key = 'schema_version'",
            (str(to_version),),
        )
        conn.commit()

    # ─────────────────────────────────────────
    # MemoryBackend Protocol
    # ─────────────────────────────────────────

    def save(self, record: ScopeRecord) -> None:
        """Save or update a scope record."""
        self._check_closed()
        conn = self._get_connection()

        conn.execute(
            """INSERT OR REPLACE INTO scopes
            (id, name, skill_name, state, started_at, ended_at,
             summary, decisions, files_changed, errors, tools_used,
             message_start_idx, message_count,
             tokens_before, tokens_after, tokens_saved,
             level, parent_id, children_ids)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.id,
                record.name,
                record.skill_name,
                record.state.value,
                record.started_at,
                record.ended_at,
                record.summary,
                json.dumps(record.decisions),
                json.dumps(record.files_changed),
                json.dumps(record.errors),
                json.dumps(record.tools_used),
                record.message_start_idx,
                record.message_count,
                record.tokens_before,
                record.tokens_after,
                record.tokens_saved,
                record.level,
                record.parent_id,
                json.dumps(record.children_ids),
            ),
        )

        # Save raw messages (if configured and available)
        if self._store_raw and record.raw_messages:
            # Delete old messages for this scope
            conn.execute(
                "DELETE FROM scope_messages WHERE scope_id = ?",
                (record.id,),
            )
            total_chars = 0
            for i, msg in enumerate(record.raw_messages):
                msg_chars = len(msg.content)
                if total_chars + msg_chars > self._raw_max_chars:
                    break
                conn.execute(
                    """INSERT INTO scope_messages
                    (scope_id, msg_index, role, content, tool_name,
                     tool_input, tool_call_id, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        record.id,
                        i,
                        msg.role.value,
                        msg.content,
                        msg.tool_name,
                        msg.tool_input,
                        msg.tool_call_id,
                        msg.timestamp,
                        json.dumps(msg.metadata),
                    ),
                )
                total_chars += msg_chars

        conn.commit()
        logger.debug("Saved scope: %s (%s)", record.id, record.name)

    def load(self, scope_id: str) -> Optional[ScopeRecord]:
        """Load a scope record by ID."""
        self._check_closed()
        conn = self._get_connection()

        cur = conn.execute("SELECT * FROM scopes WHERE id = ?", (scope_id,))
        row = cur.fetchone()
        if not row:
            return None

        record = self._row_to_record(row)

        # Load raw messages
        msg_cur = conn.execute(
            "SELECT * FROM scope_messages WHERE scope_id = ? ORDER BY msg_index",
            (scope_id,),
        )
        record.raw_messages = [self._row_to_message(r) for r in msg_cur]

        return record

    def search(self, query: str, limit: int = 5) -> List[ScopeRecord]:
        """Search scopes by keyword in name and summary."""
        self._check_closed()
        conn = self._get_connection()

        if not query:
            return self.list_all(limit)

        # SQLite LIKE for basic search
        pattern = f"%{query}%"
        cur = conn.execute(
            """SELECT * FROM scopes
            WHERE state = 'compacted'
              AND (name LIKE ? OR summary LIKE ? OR files_changed LIKE ?)
            ORDER BY ended_at DESC
            LIMIT ?""",
            (pattern, pattern, pattern, limit),
        )
        return [self._row_to_record(row) for row in cur]

    def list_all(self, limit: int = 50) -> List[ScopeRecord]:
        """List all compacted scopes, most recent first."""
        self._check_closed()
        conn = self._get_connection()

        cur = conn.execute(
            """SELECT * FROM scopes
            WHERE state = 'compacted'
            ORDER BY ended_at DESC
            LIMIT ?""",
            (limit,),
        )
        return [self._row_to_record(row) for row in cur]

    def get_recallable_names(self) -> List[str]:
        """Get names of scopes that have raw messages stored."""
        self._check_closed()
        conn = self._get_connection()

        cur = conn.execute(
            """SELECT DISTINCT s.name FROM scopes s
            INNER JOIN scope_messages sm ON s.id = sm.scope_id
            WHERE s.state = 'compacted'
            ORDER BY s.ended_at DESC
            LIMIT 50""",
        )
        return [row[0] for row in cur]

    # ─────────────────────────────────────────
    # Extended operations
    # ─────────────────────────────────────────

    def delete(self, scope_id: str) -> bool:
        """Delete a scope and its messages. Returns True if deleted."""
        self._check_closed()
        conn = self._get_connection()
        conn.execute("DELETE FROM scope_messages WHERE scope_id = ?", (scope_id,))
        cur = conn.execute("DELETE FROM scopes WHERE id = ?", (scope_id,))
        conn.commit()
        return cur.rowcount > 0

    def vacuum(self) -> None:
        """Reclaim disk space after deletions."""
        self._check_closed()
        conn = self._get_connection()
        conn.execute("VACUUM")

    @property
    def count(self) -> int:
        """Total number of scope records."""
        self._check_closed()
        conn = self._get_connection()
        cur = conn.execute("SELECT COUNT(*) FROM scopes")
        return cur.fetchone()[0]

    @property
    def compacted_count(self) -> int:
        """Number of compacted scope records."""
        self._check_closed()
        conn = self._get_connection()
        cur = conn.execute(
            "SELECT COUNT(*) FROM scopes WHERE state = 'compacted'"
        )
        return cur.fetchone()[0]

    @property
    def db_size_bytes(self) -> int:
        """Current database file size in bytes."""
        if self._path == ":memory:":
            return 0
        try:
            return os.path.getsize(self._path)
        except OSError:
            return 0

    # ─────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────

    def close(self) -> None:
        """Close the store and all thread-local connections."""
        if self._closed:
            return
        self._closed = True
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
        logger.info("SqliteScopeStore closed: %s", self._path)

    def __enter__(self) -> "SqliteScopeStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _check_closed(self) -> None:
        if self._closed:
            raise RuntimeError("SqliteScopeStore has been closed.")

    # ─────────────────────────────────────────
    # Row conversions
    # ─────────────────────────────────────────

    def _row_to_record(self, row: sqlite3.Row) -> ScopeRecord:
        """Convert a SQLite row to a ScopeRecord."""
        return ScopeRecord(
            id=row["id"],
            name=row["name"],
            skill_name=row["skill_name"],
            state=ScopeState(row["state"]),
            started_at=row["started_at"],
            ended_at=row["ended_at"],
            summary=row["summary"],
            decisions=json.loads(row["decisions"]),
            files_changed=json.loads(row["files_changed"]),
            errors=json.loads(row["errors"]),
            tools_used=json.loads(row["tools_used"]),
            message_start_idx=row["message_start_idx"],
            message_count=row["message_count"],
            tokens_before=row["tokens_before"],
            tokens_after=row["tokens_after"],
            tokens_saved=row["tokens_saved"],
            level=row["level"] if "level" in row.keys() else 0,
            parent_id=row["parent_id"] if "parent_id" in row.keys() else None,
            children_ids=json.loads(row["children_ids"]) if "children_ids" in row.keys() else [],
        )

    def _row_to_message(self, row: sqlite3.Row) -> Message:
        """Convert a SQLite row to a Message."""
        return Message(
            role=MessageRole(row["role"]),
            content=row["content"],
            tool_name=row["tool_name"],
            tool_input=row["tool_input"],
            tool_call_id=row["tool_call_id"],
            timestamp=row["timestamp"] or time.time(),
            metadata=json.loads(row["metadata"]),
        )
