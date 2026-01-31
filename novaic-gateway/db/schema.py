"""
Database Schema Definition

Defines all tables for the NovAIC Gateway SQLite database.
v3: unified chat_messages table with read field.
v4: Added unified task system (tasks, task_outputs tables).
v5: Added output_file, ttl_hours, expires_at to tasks.
v6: Changed agents.status to agents.setup_complete (boolean).
v7: Added inbox_messages and agent_state tables for EventBus/Inbox refactor.
v8: Added agent_memory and agent_task_history tables for Memory MCP.
v9: Added ssh_keys and vm_processes tables for VM management.
"""

SCHEMA_VERSION = 9

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
    setup_complete INTEGER DEFAULT 0
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

-- ========================================
-- 8. Unified Task System Tables
-- ========================================
-- Supports async tasks: agent sub-tasks, shell commands, browser automation, etc.

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,                  -- agent, shell, browser, tool, sync_output, custom
    label TEXT,                          -- Human-readable label
    config TEXT,                         -- JSON: task configuration
    status TEXT DEFAULT 'pending',       -- pending, running, completed, failed, cancelled
    
    created_at TEXT DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT,
    
    result TEXT,                         -- JSON: task result (truncated for sync_output)
    result_summary TEXT,                 -- LLM-generated summary
    error TEXT,                          -- Error message if failed
    
    output_file TEXT,                    -- Path to full output file (for large outputs)
    ttl_hours INTEGER DEFAULT 168,       -- Time-to-live in hours (default: 7 days)
    expires_at TEXT,                     -- Expiration timestamp
    
    parent_session_key TEXT,             -- Session that created this task
    agent_id TEXT DEFAULT 'default',     -- Agent that owns this task
    notify_on TEXT DEFAULT '["complete", "error"]'  -- JSON: events to notify on
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at);

CREATE TABLE IF NOT EXISTS task_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    ts TEXT DEFAULT (datetime('now')),
    type TEXT,                           -- tool_call, tool_result, message, stdout, stderr
    content TEXT,                        -- JSON or text content
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_task_outputs_task ON task_outputs(task_id);
CREATE INDEX IF NOT EXISTS idx_task_outputs_ts ON task_outputs(ts);

-- ========================================
-- 9. Inbox Messages Table (for EventBus/Inbox refactor)
-- ========================================
-- Stores all pending input messages that need Agent processing
-- Separate from chat_messages to clearly separate inbox (pending) from chat history

CREATE TABLE IF NOT EXISTS inbox_messages (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    type TEXT NOT NULL,               -- USER_MESSAGE, SYSTEM_MESSAGE, WEBHOOK, CRON_TRIGGER, SUBAGENT_RESULT
    content TEXT,
    priority INTEGER DEFAULT 2,       -- 0=CRITICAL, 1=HIGH, 2=NORMAL, 3=LOW
    source TEXT,                      -- user, system:bootstrap, webhook:xxx, cron:xxx, subagent:xxx
    metadata TEXT DEFAULT '{}',       -- JSON: additional data
    status TEXT DEFAULT 'pending',    -- pending, processing, done, failed
    created_at TEXT NOT NULL,
    processed_at TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_inbox_agent_status ON inbox_messages(agent_id, status);
CREATE INDEX IF NOT EXISTS idx_inbox_priority ON inbox_messages(agent_id, priority, created_at);

-- ========================================
-- 10. Agent State Table (for EventBus/Inbox refactor)
-- ========================================
-- Stores Agent runtime state persistently (sleep/awake, wake triggers, etc.)

CREATE TABLE IF NOT EXISTS agent_state (
    agent_id TEXT PRIMARY KEY,
    state TEXT DEFAULT 'awake',       -- sleep, awake
    wake_triggers TEXT DEFAULT '[]',  -- JSON: conditions to wake from sleep
    rest_reason TEXT,                 -- Why agent is resting
    rest_started_at TEXT,
    last_active_at TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

-- ========================================
-- 11. Agent Memory Tables (for Memory MCP)
-- ========================================
-- Persistent key-value storage per agent/namespace

CREATE TABLE IF NOT EXISTS agent_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    namespace TEXT NOT NULL DEFAULT 'default',
    key TEXT NOT NULL,
    value TEXT,                       -- JSON serialized value
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(agent_id, namespace, key),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_agent_memory_agent ON agent_memory(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_memory_namespace ON agent_memory(agent_id, namespace);

-- Task history for Memory MCP (persistent task logs)
CREATE TABLE IF NOT EXISTS agent_task_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    status TEXT DEFAULT 'completed',  -- completed, failed, in_progress
    timestamp TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_agent_task_history_agent ON agent_task_history(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_task_history_timestamp ON agent_task_history(agent_id, timestamp);

-- ========================================
-- 12. SSH Keys Table (for VM access)
-- ========================================
-- Stores SSH key pairs for VM authentication

CREATE TABLE IF NOT EXISTS ssh_keys (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    public_key TEXT NOT NULL,
    private_key TEXT NOT NULL,
    is_default INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_ssh_keys_default ON ssh_keys(is_default);

-- ========================================
-- 13. VM Processes Table (for VM lifecycle)
-- ========================================
-- Tracks running QEMU processes for each agent

CREATE TABLE IF NOT EXISTS vm_processes (
    agent_id TEXT PRIMARY KEY,
    pid INTEGER,
    status TEXT DEFAULT 'stopped',
    started_at TEXT,
    ports TEXT DEFAULT '{}',
    qemu_cmd TEXT,
    error_message TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_vm_processes_status ON vm_processes(status);
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
        
        # Update schema version to 3
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', ?)",
            ("3",)
        )
        
        await conn.commit()
        print("[DB] Migration to v3 complete")
    
    if from_version < 4:
        print("[DB] Running migration from v3 to v4...")
        
        # Migration from v3 to v4:
        # Add unified task system tables (tasks, task_outputs)
        # These are created by SCHEMA_SQL, but we need to ensure indexes exist
        
        # Create tasks table if not exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                label TEXT,
                config TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now')),
                started_at TEXT,
                completed_at TEXT,
                result TEXT,
                result_summary TEXT,
                error TEXT,
                parent_session_key TEXT,
                agent_id TEXT DEFAULT 'default',
                notify_on TEXT DEFAULT '["complete", "error"]'
            )
        """)
        
        # Create task_outputs table if not exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS task_outputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                ts TEXT DEFAULT (datetime('now')),
                type TEXT,
                content TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(agent_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_task_outputs_task ON task_outputs(task_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_task_outputs_ts ON task_outputs(ts)")
        
        # Update schema version to 4
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', ?)",
            (str(SCHEMA_VERSION),)
        )
        
        await conn.commit()
        print("[DB] Migration to v4 complete")
    
    if from_version < 5:
        print("[DB] Running migration from v4 to v5...")
        
        # Migration from v4 to v5:
        # Add output_file, ttl_hours, expires_at columns to tasks table
        # for unified task/result system
        
        # Check if columns already exist
        cursor = await conn.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in await cursor.fetchall()]
        
        if 'output_file' not in columns:
            print("[DB] Adding 'output_file' column to tasks")
            await conn.execute("ALTER TABLE tasks ADD COLUMN output_file TEXT")
        
        if 'ttl_hours' not in columns:
            print("[DB] Adding 'ttl_hours' column to tasks")
            await conn.execute("ALTER TABLE tasks ADD COLUMN ttl_hours INTEGER DEFAULT 168")
        
        if 'expires_at' not in columns:
            print("[DB] Adding 'expires_at' column to tasks")
            await conn.execute("ALTER TABLE tasks ADD COLUMN expires_at TEXT")
        
        # Set default expires_at for existing tasks (7 days from created_at)
        await conn.execute("""
            UPDATE tasks 
            SET expires_at = datetime(created_at, '+' || COALESCE(ttl_hours, 168) || ' hours')
            WHERE expires_at IS NULL
        """)
        
        # Create index for expires_at for efficient cleanup
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_expires ON tasks(expires_at)"
        )
        
        # Update schema version to 5
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', ?)",
            (str(SCHEMA_VERSION),)
        )
        
        await conn.commit()
        print("[DB] Migration to v5 complete")
    
    if from_version < 6:
        print("[DB] Running migration from v5 to v6...")
        
        # Migration from v5 to v6:
        # Change agents.status (text) to agents.setup_complete (boolean)
        # - pending/downloading/creating/deploying -> 0 (not complete)
        # - ready/stopped/running/error -> 1 (complete)
        
        # Check if setup_complete column already exists
        cursor = await conn.execute("PRAGMA table_info(agents)")
        columns = [row[1] for row in await cursor.fetchall()]
        
        if 'setup_complete' not in columns:
            print("[DB] Adding 'setup_complete' column to agents")
            await conn.execute("ALTER TABLE agents ADD COLUMN setup_complete INTEGER DEFAULT 0")
            
            # Migrate data: ready/stopped/running means setup is complete
            await conn.execute("""
                UPDATE agents 
                SET setup_complete = CASE 
                    WHEN status IN ('ready', 'stopped', 'running') THEN 1 
                    ELSE 0 
                END
            """)
            print("[DB] Migrated status to setup_complete")
        
        # Update schema version to 6
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', '6')"
        )
        
        await conn.commit()
        print("[DB] Migration to v6 complete")
    
    if from_version < 7:
        print("[DB] Running migration from v6 to v7...")
        
        # Migration from v6 to v7:
        # Add inbox_messages and agent_state tables for EventBus/Inbox refactor
        
        # Create inbox_messages table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS inbox_messages (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT,
                priority INTEGER DEFAULT 2,
                source TEXT,
                metadata TEXT DEFAULT '{}',
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL,
                processed_at TEXT,
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for inbox_messages
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_inbox_agent_status ON inbox_messages(agent_id, status)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_inbox_priority ON inbox_messages(agent_id, priority, created_at)"
        )
        
        print("[DB] Created inbox_messages table")
        
        # Create agent_state table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_state (
                agent_id TEXT PRIMARY KEY,
                state TEXT DEFAULT 'awake',
                wake_triggers TEXT DEFAULT '[]',
                rest_reason TEXT,
                rest_started_at TEXT,
                last_active_at TEXT,
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
            )
        """)
        
        print("[DB] Created agent_state table")
        
        # Migrate existing agent rest state from agent_runtime_state to agent_state
        try:
            # Get all agents
            cursor = await conn.execute("SELECT id FROM agents")
            agents = await cursor.fetchall()
            
            import json
            
            for agent_row in agents:
                agent_id = agent_row[0]
                
                # Get existing runtime state
                cursor = await conn.execute(
                    "SELECT key, value FROM agent_runtime_state WHERE agent_id = ?",
                    (agent_id,)
                )
                runtime_state = {row[0]: row[1] for row in await cursor.fetchall()}
                
                # Determine state
                is_resting = runtime_state.get("is_resting", "false") == "true"
                state = "sleep" if is_resting else "awake"
                
                # Parse wake_triggers
                wake_triggers_str = runtime_state.get("wake_triggers", "[]")
                try:
                    wake_triggers = json.loads(wake_triggers_str) if wake_triggers_str else []
                except:
                    wake_triggers = []
                
                rest_reason = runtime_state.get("rest_reason")
                if rest_reason == "null":
                    rest_reason = None
                
                rest_started = runtime_state.get("rest_started")
                if rest_started == "null":
                    rest_started = None
                
                # Insert into agent_state
                await conn.execute("""
                    INSERT OR REPLACE INTO agent_state 
                    (agent_id, state, wake_triggers, rest_reason, rest_started_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (agent_id, state, json.dumps(wake_triggers), rest_reason, rest_started))
            
            print(f"[DB] Migrated state for {len(agents)} agents")
        except Exception as e:
            print(f"[DB] Warning: Could not migrate agent runtime state: {e}")
        
        # Update schema version to 7
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', '7')"
        )
        
        await conn.commit()
        print("[DB] Migration to v7 complete")
    
    if from_version < 8:
        print("[DB] Running migration from v7 to v8...")
        
        # Migration from v7 to v8:
        # Add agent_memory and agent_task_history tables for Memory MCP
        # These are created by SCHEMA_SQL via CREATE TABLE IF NOT EXISTS
        
        # Update schema version to 8
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', '8')"
        )
        
        await conn.commit()
        print("[DB] Migration to v8 complete")
    
    if from_version < 9:
        print("[DB] Running migration from v8 to v9...")
        
        # Migration from v8 to v9:
        # Add ssh_keys and vm_processes tables for VM management
        
        # Create ssh_keys table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS ssh_keys (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                public_key TEXT NOT NULL,
                private_key TEXT NOT NULL,
                is_default INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ssh_keys_default ON ssh_keys(is_default)"
        )
        print("[DB] Created ssh_keys table")
        
        # Create vm_processes table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS vm_processes (
                agent_id TEXT PRIMARY KEY,
                pid INTEGER,
                status TEXT DEFAULT 'stopped',
                started_at TEXT,
                ports TEXT DEFAULT '{}',
                qemu_cmd TEXT,
                error_message TEXT,
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
            )
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_vm_processes_status ON vm_processes(status)"
        )
        print("[DB] Created vm_processes table")
        
        # Update schema version to 9
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', '9')"
        )
        
        await conn.commit()
        print("[DB] Migration to v9 complete")
