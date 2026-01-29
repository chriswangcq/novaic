"""
Database Schema Definition

Defines all tables for the NovAIC Gateway SQLite database.
Simplified in v3: unified chat_messages table with read field.
"""

SCHEMA_VERSION = 3

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
-- 3. Session Tables (for LLM context)
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
-- 4. Unified Chat Messages Table
-- ========================================
-- Stores all messages: user messages, agent replies, questions, etc.
-- Uses 'read' field for inbox management (unread = inbox items)

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL DEFAULT 'default',
    type TEXT NOT NULL,              -- 'USER_MESSAGE', 'AGENT_REPLY', 'AGENT_ASK', etc.
    content TEXT,                    -- Message content
    read INTEGER DEFAULT 0,          -- 0=unread, 1=read (for inbox)
    metadata TEXT DEFAULT '{}',      -- model, api_key_id, options, etc.
    timestamp TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_agent ON chat_messages(agent_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_read ON chat_messages(agent_id, read);
CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(agent_id, timestamp);

-- ========================================
-- 5. Question/Response Tables (per-agent)
-- ========================================

CREATE TABLE IF NOT EXISTS pending_questions (
    request_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL DEFAULT 'default',
    question TEXT,
    options TEXT,
    message_id TEXT,
    timestamp TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_pending_questions_agent ON pending_questions(agent_id);

CREATE TABLE IF NOT EXISTS question_responses (
    request_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL DEFAULT 'default',
    response TEXT,
    selected_option TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (request_id) REFERENCES pending_questions(request_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_question_responses_agent ON question_responses(agent_id);

-- ========================================
-- 6. Execution Log Tables (per-agent)
-- ========================================
-- Pure flow logs, not associated with messages

CREATE TABLE IF NOT EXISTS execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL DEFAULT 'default',
    type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    data TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_execution_logs_agent ON execution_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_timestamp ON execution_logs(agent_id, timestamp);

-- ========================================
-- 7. Agent Runtime State Tables (per-agent)
-- ========================================

CREATE TABLE IF NOT EXISTS agent_runtime_state (
    agent_id TEXT NOT NULL DEFAULT 'default',
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (agent_id, key)
);

CREATE INDEX IF NOT EXISTS idx_agent_runtime_state_agent ON agent_runtime_state(agent_id);
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
    # Check current schema version
    try:
        cursor = await conn.execute("SELECT value FROM config WHERE key = 'version'")
        row = await cursor.fetchone()
        current_version = int(row[0]) if row else 0
    except Exception:
        current_version = 0
    
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
    
    # Run migrations if needed
    if current_version < SCHEMA_VERSION:
        print(f"[DB] Migrating from version {current_version} to {SCHEMA_VERSION}")
        await run_migration(conn, current_version)
        print(f"[DB] Migration complete")


async def run_migration(conn, from_version: int):
    """Run migrations from old schema version to current."""
    if from_version < 3:
        print("[DB] Running migration from v2 to v3...")
        
        # Migration from v2 to v3:
        # 1. Add 'content' and 'read' columns to chat_messages if not exist
        # 2. Migrate data from user_messages to chat_messages
        # 3. Migrate data from pending_user_messages to chat_messages (with read=0)
        # 4. Drop user_messages and pending_user_messages tables
        
        # Check if columns exist
        cursor = await conn.execute("PRAGMA table_info(chat_messages)")
        columns = [row[1] for row in await cursor.fetchall()]
        
        if 'read' not in columns:
            print("[DB] Adding 'read' column to chat_messages")
            await conn.execute("ALTER TABLE chat_messages ADD COLUMN read INTEGER DEFAULT 0")
        
        if 'content' not in columns:
            print("[DB] Adding 'content' column to chat_messages")
            await conn.execute("ALTER TABLE chat_messages ADD COLUMN content TEXT")
        
        if 'metadata' not in columns:
            print("[DB] Adding 'metadata' column to chat_messages")
            await conn.execute("ALTER TABLE chat_messages ADD COLUMN metadata TEXT DEFAULT '{}'")
        
        # Migrate data from user_messages if table exists
        try:
            cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_messages'")
            if await cursor.fetchone():
                print("[DB] Migrating data from user_messages...")
                
                # Get all user messages
                cursor = await conn.execute("""
                    SELECT id, agent_id, type, content, timestamp, status, model, api_key_id, created_at
                    FROM user_messages
                """)
                user_messages = await cursor.fetchall()
                
                import json
                migrated = 0
                for row in user_messages:
                    msg_id = row[0]
                    agent_id = row[1]
                    msg_type = row[2] or "USER_MESSAGE"
                    content = row[3]
                    timestamp = row[4]
                    status = row[5] or "delivered"
                    model = row[6]
                    api_key_id = row[7]
                    created_at = row[8]
                    
                    # Map status to read flag: delivered=0, read=1
                    read = 1 if status == "read" else 0
                    
                    # Build metadata
                    metadata = {}
                    if model:
                        metadata["model"] = model
                    if api_key_id:
                        metadata["api_key_id"] = api_key_id
                    if status:
                        metadata["status"] = status
                    
                    # Insert into chat_messages (or update if exists)
                    await conn.execute("""
                        INSERT OR REPLACE INTO chat_messages 
                        (id, agent_id, type, content, read, metadata, timestamp, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (msg_id, agent_id, msg_type, content, read, json.dumps(metadata), timestamp, created_at))
                    migrated += 1
                
                print(f"[DB] Migrated {migrated} messages from user_messages")
        except Exception as e:
            print(f"[DB] Warning: Could not migrate user_messages: {e}")
        
        # Migrate data from pending_user_messages if table exists
        try:
            cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pending_user_messages'")
            if await cursor.fetchone():
                print("[DB] Migrating data from pending_user_messages...")
                
                # Get all pending messages
                cursor = await conn.execute("""
                    SELECT id, agent_id, content, timestamp, model, api_key_id, created_at
                    FROM pending_user_messages
                """)
                pending_messages = await cursor.fetchall()
                
                import json
                migrated = 0
                for row in pending_messages:
                    msg_id = row[0]
                    agent_id = row[1]
                    content = row[2]
                    timestamp = row[3]
                    model = row[4]
                    api_key_id = row[5]
                    created_at = row[6]
                    
                    # Pending messages are unread
                    read = 0
                    
                    # Build metadata
                    metadata = {}
                    if model:
                        metadata["model"] = model
                    if api_key_id:
                        metadata["api_key_id"] = api_key_id
                    
                    # Check if message already exists in chat_messages
                    check_cursor = await conn.execute("SELECT id FROM chat_messages WHERE id = ?", (msg_id,))
                    exists = await check_cursor.fetchone()
                    
                    if exists:
                        # Update to mark as unread
                        await conn.execute("UPDATE chat_messages SET read = 0 WHERE id = ?", (msg_id,))
                    else:
                        # Insert as new message
                        await conn.execute("""
                            INSERT INTO chat_messages 
                            (id, agent_id, type, content, read, metadata, timestamp, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (msg_id, agent_id, "USER_MESSAGE", content, read, json.dumps(metadata), timestamp, created_at))
                    migrated += 1
                
                print(f"[DB] Migrated {migrated} messages from pending_user_messages")
        except Exception as e:
            print(f"[DB] Warning: Could not migrate pending_user_messages: {e}")
        
        # Create new indexes
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_read ON chat_messages(agent_id, read)"
        )
        
        # Drop old tables
        print("[DB] Dropping old tables...")
        await conn.execute("DROP TABLE IF EXISTS pending_user_messages")
        await conn.execute("DROP TABLE IF EXISTS user_messages")
        
        # Drop old index on execution_logs
        await conn.execute("DROP INDEX IF EXISTS idx_execution_logs_message_id")
        
        # Update schema version
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', ?)",
            (str(SCHEMA_VERSION),)
        )
        
        await conn.commit()
        print("[DB] Migration to v3 complete")
