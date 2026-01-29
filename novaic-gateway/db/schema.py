"""
Database Schema Definition

Defines all tables for the NovAIC Gateway SQLite database.
"""

SCHEMA_VERSION = 1

SCHEMA_SQL = """
-- ========================================
-- Database Configuration
-- ========================================
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;
PRAGMA temp_store = MEMORY;

-- ========================================
-- 1. Configuration Tables
-- ========================================

-- General key-value configuration
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- API Keys for LLM providers
CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    api_key TEXT,
    api_base TEXT,
    deployment_name TEXT,
    api_version TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_api_keys_provider ON api_keys(provider);

-- Available models from providers
CREATE TABLE IF NOT EXISTS available_models (
    id TEXT NOT NULL,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    api_key_id TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    is_custom INTEGER DEFAULT 0,
    PRIMARY KEY (id, api_key_id),
    FOREIGN KEY (api_key_id) REFERENCES api_keys(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_models_api_key ON available_models(api_key_id);
CREATE INDEX IF NOT EXISTS idx_models_enabled ON available_models(enabled);

-- ========================================
-- 2. Agent Configuration Tables
-- ========================================

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    vm_config TEXT NOT NULL DEFAULT '{}',
    ports TEXT NOT NULL DEFAULT '{}',
    status TEXT DEFAULT 'stopped'
);

-- ========================================
-- 3. Session Tables
-- ========================================

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    agent_id TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_agent ON sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at);

CREATE TABLE IF NOT EXISTS session_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'message',
    role TEXT,
    content TEXT,
    timestamp TEXT DEFAULT (datetime('now')),
    metadata TEXT DEFAULT '{}',
    compacted_count INTEGER,
    original_tokens INTEGER,
    summary_tokens INTEGER,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_session_messages_session ON session_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_session_messages_timestamp ON session_messages(timestamp);

-- ========================================
-- 4. Chat Message Tables (Real-time)
-- ========================================

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    data TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(timestamp);

-- ========================================
-- 5. Question/Response Tables
-- ========================================

CREATE TABLE IF NOT EXISTS pending_questions (
    request_id TEXT PRIMARY KEY,
    question TEXT,
    options TEXT,
    message_id TEXT,
    timestamp TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS question_responses (
    request_id TEXT PRIMARY KEY,
    response TEXT,
    selected_option TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (request_id) REFERENCES pending_questions(request_id) ON DELETE CASCADE
);

-- ========================================
-- 6. User Message Tables
-- ========================================

CREATE TABLE IF NOT EXISTS user_messages (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL DEFAULT 'USER_MESSAGE',
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    status TEXT DEFAULT 'delivered',
    model TEXT,
    api_key_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_user_messages_status ON user_messages(status);
CREATE INDEX IF NOT EXISTS idx_user_messages_timestamp ON user_messages(timestamp);

CREATE TABLE IF NOT EXISTS pending_user_messages (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    model TEXT,
    api_key_id TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (id) REFERENCES user_messages(id) ON DELETE CASCADE
);

-- ========================================
-- 7. Execution Log Tables
-- ========================================

CREATE TABLE IF NOT EXISTS execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    data TEXT,
    message_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_execution_logs_timestamp ON execution_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_execution_logs_message_id ON execution_logs(message_id);

-- ========================================
-- 8. Agent Runtime State Tables
-- ========================================

CREATE TABLE IF NOT EXISTS agent_runtime_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);
"""

DEFAULT_CONFIG = {
    "version": str(SCHEMA_VERSION),
    "default_model": '"gpt-4o"',
    "max_tokens": "4096",
    "max_iterations": "20",
    "visible_shell": "false",
    "current_agent_id": "null",
}

DEFAULT_RUNTIME_STATE = {
    "is_resting": "false",
    "rest_reason": "null",
    "wake_triggers": "[]",
    "handoff_notes": "null",
    "rest_started": "null",
    "is_busy": "false",
    "current_message_id": "null",
}


async def init_schema(conn):
    """Initialize database schema and default data."""
    # Execute schema SQL (split by statements)
    for statement in SCHEMA_SQL.split(';'):
        statement = statement.strip()
        if statement:
            await conn.execute(statement)
    
    # Insert default config values
    for key, value in DEFAULT_CONFIG.items():
        await conn.execute(
            "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
            (key, value)
        )
    
    # Insert default runtime state
    for key, value in DEFAULT_RUNTIME_STATE.items():
        await conn.execute(
            "INSERT OR IGNORE INTO agent_runtime_state (key, value) VALUES (?, ?)",
            (key, value)
        )
    
    await conn.commit()
