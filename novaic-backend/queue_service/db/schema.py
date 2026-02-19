"""
Queue Service Database Schema

仅包含 Task Queue 相关的表：
- tq_tasks: 任务队列表
- tq_sagas: Saga 流程表
- config: 配置表（版本管理）
"""

SCHEMA_VERSION = 4

SCHEMA_SQL = """
-- ========================================
-- Database Configuration
-- ========================================
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = OFF;  -- Queue 表无外键依赖
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;
PRAGMA cache_size = -64000;
PRAGMA temp_store = MEMORY;

-- ========================================
-- Configuration Table
-- ========================================
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ========================================
-- Task Queue Tables
-- ========================================

-- tq_tasks: Pure task queue table
CREATE TABLE IF NOT EXISTS tq_tasks (
    -- Identification
    id TEXT PRIMARY KEY,
    idempotency_key TEXT UNIQUE,      -- Prevents duplicate task creation
    
    -- Task content (business-agnostic)
    topic TEXT NOT NULL,              -- Task topic/queue name
    payload TEXT NOT NULL,            -- JSON: task parameters
    
    -- State machine
    status TEXT DEFAULT 'pending',    -- pending, claimed, done, failed
    
    -- Claim information
    claimed_by TEXT,                  -- Worker ID
    claimed_at TEXT,
    heartbeat_at TEXT,
    
    -- Retry control
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TEXT,               -- When task becomes claimable again
    
    -- Result
    result TEXT,                      -- JSON: execution result
    error TEXT,                       -- Error message
    
    -- Timestamps
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    
    -- Version (optimistic locking)
    version INTEGER DEFAULT 0
);

-- Task queue indexes
CREATE INDEX IF NOT EXISTS idx_tq_tasks_pending ON tq_tasks(topic, status, created_at) 
    WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_tq_tasks_pending_retry_at ON tq_tasks(status, next_retry_at)
    WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_tq_tasks_heartbeat ON tq_tasks(status, heartbeat_at) 
    WHERE status = 'claimed';
CREATE UNIQUE INDEX IF NOT EXISTS idx_tq_tasks_idempotency ON tq_tasks(idempotency_key);
CREATE INDEX IF NOT EXISTS idx_tq_tasks_topic ON tq_tasks(topic, status);

-- tq_sagas: Saga state tracking table (also serves as task queue)
CREATE TABLE IF NOT EXISTS tq_sagas (
    -- Identification
    id TEXT PRIMARY KEY,
    idempotency_key TEXT UNIQUE,      -- Prevents duplicate saga creation
    
    -- Saga definition
    saga_type TEXT NOT NULL,          -- Saga type name
    context TEXT NOT NULL,            -- JSON: business context
    
    -- Progress tracking
    current_step INTEGER DEFAULT 0,   -- Current step index
    
    -- Status (pending → running → completed/failed)
    status TEXT DEFAULT 'pending',    -- pending, running, completed, failed
    
    -- Claim information (same as tq_tasks)
    claimed_by TEXT,                  -- Worker ID
    claimed_at TEXT,
    heartbeat_at TEXT,
    
    -- Step results
    step_results TEXT DEFAULT '{}',   -- JSON: results from each step
    
    -- Error
    error TEXT,                       -- Error message if failed
    
    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT,
    completed_at TEXT
);

-- Saga indexes
CREATE INDEX IF NOT EXISTS idx_tq_sagas_pending ON tq_sagas(status, created_at)
    WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_tq_sagas_heartbeat ON tq_sagas(status, heartbeat_at)
    WHERE status = 'running';
CREATE INDEX IF NOT EXISTS idx_tq_sagas_type ON tq_sagas(saga_type, status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tq_sagas_idempotency ON tq_sagas(idempotency_key);

-- idempotency execution ledger: cross-process side-effect guard
CREATE TABLE IF NOT EXISTS tq_idempotency_ledger (
    idempotency_key TEXT PRIMARY KEY,
    status TEXT NOT NULL,             -- in_progress, completed
    owner_token TEXT,
    task_id TEXT,
    result TEXT,                      -- JSON snapshot for completed execution
    contention_count INTEGER DEFAULT 0,
    last_contended_at TEXT,
    lease_until TEXT,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tq_idempotency_lease ON tq_idempotency_ledger(status, lease_until)
    WHERE status = 'in_progress';
"""

DEFAULT_CONFIG = {
    "version": str(SCHEMA_VERSION),
}


def init_schema(conn):
    """Initialize database schema and default data."""
    # Check current schema version
    try:
        cursor = conn.execute("SELECT value FROM config WHERE key = 'version'")
        row = cursor.fetchone()
        current_version = int(row[0]) if row else 0
    except Exception:
        current_version = 0
    
    # Execute schema SQL (split by statements)
    for statement in SCHEMA_SQL.split(';'):
        statement = statement.strip()
        if statement:
            conn.execute(statement)
    
    # Insert default config values
    for key, value in DEFAULT_CONFIG.items():
        conn.execute(
            "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
            (key, value)
        )
    
    conn.commit()
    
    # Run migrations if needed
    if current_version < SCHEMA_VERSION:
        print(f"[Queue DB] Migrating from version {current_version} to {SCHEMA_VERSION}")
        run_migration(conn, current_version)
        print(f"[Queue DB] Migration complete")


def run_migration(conn, from_version: int):
    """Run migrations."""
    if from_version < 2:
        # v2: add retry scheduling visibility for pending tasks
        try:
            conn.execute("ALTER TABLE tq_tasks ADD COLUMN next_retry_at TEXT")
        except Exception:
            # Column may already exist in some environments.
            pass
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tq_tasks_pending_retry_at ON tq_tasks(status, next_retry_at) "
            "WHERE status = 'pending'"
        )
    if from_version < 3:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tq_idempotency_ledger (
                idempotency_key TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                owner_token TEXT,
                task_id TEXT,
                result TEXT,
                contention_count INTEGER DEFAULT 0,
                last_contended_at TEXT,
                lease_until TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tq_idempotency_lease ON tq_idempotency_ledger(status, lease_until) "
            "WHERE status = 'in_progress'"
        )
    if from_version < 4:
        try:
            conn.execute(
                "ALTER TABLE tq_idempotency_ledger ADD COLUMN contention_count INTEGER DEFAULT 0"
            )
        except Exception:
            pass
        try:
            conn.execute(
                "ALTER TABLE tq_idempotency_ledger ADD COLUMN last_contended_at TEXT"
            )
        except Exception:
            pass

    # Update version
    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES ('version', ?)",
        (str(SCHEMA_VERSION),)
    )
    conn.commit()
    print(f"[Queue DB] Schema version updated to {SCHEMA_VERSION}")
