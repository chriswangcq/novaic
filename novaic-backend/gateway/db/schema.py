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
v10: Removed inbox_messages table and is_busy field (new architecture).
v11: Multi-process architecture - action_tasks, mcp_executions, worker_processes tables.
v12: Master-driven architecture - agent_runtimes table for Runtime management.
v13: Added mcp_url field to agent_runtimes for Runtime MCP Server URL.
v14: SubAgent state refactor - subagents table, runtime_id rename, summary fields.
v15: Three-Task Architecture - pipeline_tasks table for launcher/collector/async pattern.
v16: Async SubAgent - added progress/result/error/timeout_at fields to subagents.
v17: Removed v11 legacy (action_tasks, mcp_executions, worker_processes tables).
v18: Event-driven Monitor - chat_messages.status field (sending/sent).
v19: Task Queue v2 - tq_tasks and tq_sagas tables for new architecture.
v20: Saga v2 - agent_runtimes.summarized and need_rest fields.
v21: Agent model selection - agents.model_id field.
v22: Candidate models - candidate_models table with available flag.
"""

SCHEMA_VERSION = 22

SCHEMA_SQL = """
-- ========================================
-- Database Configuration
-- ========================================
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;  -- Wait 5s for locks instead of failing immediately
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

-- Candidate models from providers
CREATE TABLE IF NOT EXISTS candidate_models (
    id TEXT NOT NULL,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    api_key_id TEXT NOT NULL,
    available INTEGER DEFAULT 1,
    is_custom INTEGER DEFAULT 0,
    PRIMARY KEY (id, api_key_id),
    FOREIGN KEY (api_key_id) REFERENCES api_keys(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_models_api_key ON candidate_models(api_key_id);
CREATE INDEX IF NOT EXISTS idx_models_available ON candidate_models(available);

-- ========================================
-- 2. Agent Configuration Tables
-- ========================================

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    vm_config TEXT NOT NULL DEFAULT '{}',
    ports TEXT NOT NULL DEFAULT '{}',
    setup_complete INTEGER DEFAULT 0,
    model_id TEXT  -- Selected LLM model ID (v20)
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
-- v11: Added claimed_by, claimed_at, processed for Worker claiming

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL DEFAULT 'default',
    type TEXT NOT NULL,              -- 'USER_MESSAGE', 'AGENT_REPLY', 'AGENT_ASK', etc.
    content TEXT,                    -- Message content
    read INTEGER DEFAULT 0,          -- 0=unread, 1=read (for inbox)
    metadata TEXT DEFAULT '{}',      -- model, api_key_id, options, etc.
    timestamp TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    
    -- v11: Worker claiming fields
    claimed_by TEXT,                 -- Worker ID that claimed this message
    claimed_at TEXT,                 -- When the message was claimed
    processed INTEGER DEFAULT 0,     -- 0=not processed, 1=processed
    
    -- v18: Event-driven Monitor - message delivery status
    status TEXT DEFAULT 'sent'       -- 'sending' (pending), 'sent' (delivered/confirmed)
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_agent ON chat_messages(agent_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_read ON chat_messages(agent_id, read);
CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(agent_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_chat_messages_pending ON chat_messages(agent_id, processed, claimed_by);
CREATE INDEX IF NOT EXISTS idx_chat_messages_status ON chat_messages(status, created_at);  -- v18: for Monitor queue

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
-- 9. Agent State Table
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

-- ========================================
-- 14. SubAgents Table (v14 - SubAgent state refactor)
-- ========================================
-- Persistent SubAgent entities that own multiple Runtimes
-- Each Agent has one Main SubAgent, can spawn Sub SubAgents

CREATE TABLE IF NOT EXISTS subagents (
    subagent_id TEXT PRIMARY KEY,      -- "main" or "sub-xxx"
    agent_id TEXT NOT NULL,
    type TEXT NOT NULL,                -- 'main' / 'sub'
    parent_subagent_id TEXT,           -- Parent SubAgent (for sub type)
    
    -- Status
    status TEXT DEFAULT 'sleeping',    -- sleeping / awake / summarizing / running / completed / failed / cancelled
    
    -- Context management
    historical_summary TEXT,           -- Merged historical runtime summaries
    
    -- Rest/wake related
    wake_triggers TEXT DEFAULT '[{"type": "user_response"}]',
    handoff_notes TEXT,
    
    -- Async SubAgent fields (v16)
    task TEXT,                         -- Task description for sub subagents
    progress TEXT,                     -- Current progress description
    result TEXT,                       -- Final result (when completed)
    error TEXT,                        -- Error message (when failed)
    timeout_at TEXT,                   -- Timeout timestamp
    
    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT,
    
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_subagents_agent ON subagents(agent_id, type);
CREATE INDEX IF NOT EXISTS idx_subagents_status ON subagents(status);

-- ========================================
-- 15. Agent Runtimes Table (v12 - Master-driven, v14 - refactored)
-- ========================================
-- Tracks Agent Runtime instances managed by Master
-- Each SubAgent can have multiple Runtimes (one active at a time)

CREATE TABLE IF NOT EXISTS agent_runtimes (
    runtime_id TEXT PRIMARY KEY,       -- Runtime ID (rt-xxx)
    subagent_id TEXT NOT NULL,         -- Owner SubAgent ID
    agent_id TEXT NOT NULL,            -- VM Agent ID (denormalized for query efficiency)
    
    -- MCP Server
    mcp_url TEXT,                      -- Aggregate MCP mount path (e.g. /mcp/aggregate/rt-xxx)
    
    -- Round state
    current_round_id TEXT,
    current_round_num INTEGER DEFAULT 1,
    phase TEXT DEFAULT 'need_think',   -- need_think, waiting_actions, completed
    
    -- Context (JSON)
    context TEXT DEFAULT '[]',         -- Conversation history
    pending_actions TEXT DEFAULT '[]', -- Current round's pending action task IDs
    
    -- Status
    status TEXT DEFAULT 'active',      -- active, resting, completed
    error TEXT,
    
    -- Summary (v14, v20)
    summary TEXT,                      -- Runtime summary after completion
    is_merged INTEGER DEFAULT 0,       -- Whether merged into historical_summary
    summarized INTEGER DEFAULT 0,      -- v20: Whether summary has been generated (async)
    need_rest INTEGER DEFAULT 0,       -- v20: Whether agent needs to rest (set by done/reset)
    
    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT,
    
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (subagent_id) REFERENCES subagents(subagent_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_runtimes_agent ON agent_runtimes(agent_id, status);
CREATE INDEX IF NOT EXISTS idx_runtimes_subagent ON agent_runtimes(subagent_id, status);
CREATE INDEX IF NOT EXISTS idx_runtimes_phase ON agent_runtimes(status, phase);

-- ========================================
-- 16. Pipeline Tasks Table (v15 - Three-Task Architecture)
-- ========================================
-- Unified task queue for the three-task architecture:
-- - launcher: creates async tasks + collector
-- - collector: collects results + triggers next launcher
-- - async: pure execution (LLM calls, tool execution)

CREATE TABLE IF NOT EXISTS pipeline_tasks (
    id TEXT PRIMARY KEY,
    
    -- Task classification
    task_type TEXT NOT NULL,         -- 'launcher', 'collector', 'async'
    task_subtype TEXT NOT NULL,      -- 'think_launcher', 'think', 'tool_call', etc.
    
    -- Context
    runtime_id TEXT NOT NULL,        -- Associated runtime
    stage_id TEXT NOT NULL,          -- Stage grouping (same for launcher + async tasks + collector)
    agent_id TEXT NOT NULL,          -- VM Agent ID (denormalized)
    
    -- Input/Output
    args TEXT DEFAULT '{}',          -- JSON: task arguments
    result TEXT,                     -- JSON: execution result
    error TEXT,                      -- Error message if failed
    
    -- Status
    status TEXT DEFAULT 'pending',   -- pending, claimed, done, failed
    
    -- Claim information
    claimed_by TEXT,                 -- Worker ID that claimed this task
    claimed_at TEXT,                 -- When it was claimed
    heartbeat_at TEXT,               -- Last heartbeat (for liveness detection)
    
    -- Idempotency
    idempotency_key TEXT UNIQUE,     -- Prevents duplicate task creation
    
    -- Collector specific
    expected_tasks INTEGER DEFAULT 0,  -- Number of async tasks to wait for (collector only)
    completed_tasks INTEGER DEFAULT 0, -- Number of completed async tasks (collector only)
    
    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT
    
    -- Note: No foreign keys to allow system-level tasks (agent_id="system", runtime_id="system")
);

CREATE INDEX IF NOT EXISTS idx_pipeline_tasks_pending ON pipeline_tasks(status, task_type, created_at);
CREATE INDEX IF NOT EXISTS idx_pipeline_tasks_runtime ON pipeline_tasks(runtime_id, stage_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_tasks_stage ON pipeline_tasks(stage_id, task_type);
CREATE INDEX IF NOT EXISTS idx_pipeline_tasks_heartbeat ON pipeline_tasks(status, heartbeat_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_pipeline_tasks_idempotency ON pipeline_tasks(idempotency_key);

-- ========================================
-- 17. Task Queue v2 Tables (v19)
-- ========================================
-- Generic task queue infrastructure, decoupled from business logic.
-- Part of the new three-layer architecture:
-- Layer 1: TaskQueue (tq_tasks) - Pure task queue
-- Layer 2: Idempotent Tasks - Business handlers
-- Layer 3: Saga (tq_sagas) - Business flow orchestration

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
    # Note: is_busy and current_message_id removed in v10 (new architecture)
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
    
    if from_version < 10:
        print("[DB] Running migration from v9 to v10...")
        
        # Migration from v9 to v10:
        # Remove inbox_messages table and is_busy field (new architecture)
        # Messages are now only in chat_messages with read=0/1
        
        # Drop inbox_messages table
        await conn.execute("DROP TABLE IF EXISTS inbox_messages")
        print("[DB] Dropped inbox_messages table")
        
        # Remove is_busy and current_message_id from agent_runtime_state
        await conn.execute(
            "DELETE FROM agent_runtime_state WHERE key IN ('is_busy', 'current_message_id')"
        )
        print("[DB] Removed is_busy and current_message_id from agent_runtime_state")
        
        # Update schema version to 10
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', '10')"
        )
        
        await conn.commit()
        print("[DB] Migration to v10 complete")
    
    if from_version < 11:
        print("[DB] Running migration from v10 to v11...")
        
        # Migration from v10 to v11:
        # Multi-process architecture with Worker model
        # - Add claimed_by, claimed_at, processed columns to chat_messages
        # - Create action_tasks table (task queue)
        # - Create mcp_executions table (idempotency)
        # - Create worker_processes table (process management)
        
        # 1. Add columns to chat_messages
        cursor = await conn.execute("PRAGMA table_info(chat_messages)")
        columns = [row[1] for row in await cursor.fetchall()]
        
        if 'claimed_by' not in columns:
            print("[DB] Adding 'claimed_by' column to chat_messages")
            await conn.execute("ALTER TABLE chat_messages ADD COLUMN claimed_by TEXT")
        
        if 'claimed_at' not in columns:
            print("[DB] Adding 'claimed_at' column to chat_messages")
            await conn.execute("ALTER TABLE chat_messages ADD COLUMN claimed_at TEXT")
        
        if 'processed' not in columns:
            print("[DB] Adding 'processed' column to chat_messages")
            await conn.execute("ALTER TABLE chat_messages ADD COLUMN processed INTEGER DEFAULT 0")
        
        # Create new index for pending messages
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_pending ON chat_messages(agent_id, processed, claimed_by)"
        )
        print("[DB] Updated chat_messages table")
        
        # 2. Create action_tasks table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS action_tasks (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                subagent_id TEXT NOT NULL,
                round_id TEXT NOT NULL,
                mcpcall_id TEXT NOT NULL,
                idempotency_key TEXT UNIQUE,
                type TEXT NOT NULL,
                action TEXT,
                args TEXT DEFAULT '{}',
                parent_task_id TEXT,
                depends_on TEXT DEFAULT '[]',
                message_id TEXT,
                status TEXT DEFAULT 'pending',
                claimed_by TEXT,
                claimed_at TEXT,
                executed_at TEXT,
                result TEXT,
                error TEXT,
                async_task_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_action_tasks_pending ON action_tasks(status, created_at)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_action_tasks_agent ON action_tasks(agent_id, status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_action_tasks_parent ON action_tasks(parent_task_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_action_tasks_round ON action_tasks(subagent_id, round_id)")
        await conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_action_tasks_idempotency ON action_tasks(idempotency_key)")
        print("[DB] Created action_tasks table")
        
        # 3. Create mcp_executions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS mcp_executions (
                idempotency_key TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                subagent_id TEXT NOT NULL,
                round_id TEXT NOT NULL,
                mcpcall_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                args TEXT,
                status TEXT DEFAULT 'executing',
                result TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                executed_at TEXT,
                FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_mcp_exec_status ON mcp_executions(status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_mcp_exec_agent ON mcp_executions(agent_id, subagent_id)")
        print("[DB] Created mcp_executions table")
        
        # 4. Create worker_processes table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS worker_processes (
                id TEXT PRIMARY KEY,
                pid INTEGER,
                status TEXT DEFAULT 'stopped',
                max_concurrent INTEGER DEFAULT 10,
                started_at TEXT,
                last_heartbeat TEXT,
                current_tasks TEXT DEFAULT '[]',
                tasks_completed INTEGER DEFAULT 0,
                tasks_failed INTEGER DEFAULT 0,
                last_error TEXT
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_worker_status ON worker_processes(status)")
        print("[DB] Created worker_processes table")
        
        # Update schema version to 11
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', '11')"
        )
        
        await conn.commit()
        print("[DB] Migration to v11 complete")
    
    if from_version < 12:
        print("[DB] Running migration from v11 to v12...")
        
        # Migration from v11 to v12:
        # Master-driven architecture with Agent Runtimes
        # - Create agent_runtimes table for Master to manage Runtime instances
        
        # Check if agent_runtimes table already exists (from v14+ SCHEMA_SQL)
        cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_runtimes'")
        table_exists = await cursor.fetchone()
        
        if not table_exists:
            # Create old v12 schema (will be migrated to v14 later)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_runtimes (
                    subagent_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    parent_subagent_id TEXT,
                    current_round_id TEXT,
                    current_round_num INTEGER DEFAULT 1,
                    phase TEXT DEFAULT 'need_think',
                    context TEXT DEFAULT '[]',
                    pending_actions TEXT DEFAULT '[]',
                    status TEXT DEFAULT 'active',
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_subagent_id) REFERENCES agent_runtimes(subagent_id) ON DELETE SET NULL
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_runtimes_agent ON agent_runtimes(agent_id, status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_runtimes_parent ON agent_runtimes(parent_subagent_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_runtimes_phase ON agent_runtimes(status, phase)")
            print("[DB] Created agent_runtimes table")
        else:
            print("[DB] agent_runtimes table already exists (v14+ schema), skipping v12 creation")
        
        # Update schema version to 12
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', '12')"
        )
        
        await conn.commit()
        print("[DB] Migration to v12 complete")
    
    if from_version < 13:
        print("[DB] Running migration from v12 to v13...")
        
        # Migration from v12 to v13:
        # Add mcp_url field to agent_runtimes for Runtime MCP Server URL
        
        # Check if column already exists (v14+ schema already has it)
        cursor = await conn.execute("PRAGMA table_info(agent_runtimes)")
        columns = [row[1] for row in await cursor.fetchall()]
        
        if 'mcp_url' not in columns:
            print("[DB] Adding 'mcp_url' column to agent_runtimes")
            await conn.execute("ALTER TABLE agent_runtimes ADD COLUMN mcp_url TEXT")
        else:
            print("[DB] mcp_url column already exists (v14+ schema)")
        
        # Update schema version to 13
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', '13')"
        )
        
        await conn.commit()
        print("[DB] Migration to v13 complete")
    
    if from_version < 14:
        print("[DB] Running migration from v13 to v14...")
        
        # Migration from v13 to v14:
        # SubAgent state refactor
        # 1. Create subagents table
        # 2. Rename subagent_id to runtime_id in agent_runtimes
        # 3. Add subagent_id foreign key to agent_runtimes
        # 4. Add summary and is_merged fields to agent_runtimes
        # 5. Migrate existing data
        
        import json
        from datetime import datetime
        
        # Check if agent_runtimes already has v14 schema (runtime_id column)
        cursor = await conn.execute("PRAGMA table_info(agent_runtimes)")
        columns = [row[1] for row in await cursor.fetchall()]
        is_v14_schema = 'runtime_id' in columns
        
        if is_v14_schema:
            print("[DB] agent_runtimes already has v14 schema (created by SCHEMA_SQL)")
            # Just ensure subagents table and indexes exist
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_subagents_agent ON subagents(agent_id, type)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_subagents_status ON subagents(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_runtimes_agent ON agent_runtimes(agent_id, status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_runtimes_subagent ON agent_runtimes(subagent_id, status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_runtimes_phase ON agent_runtimes(status, phase)")
            
            # Create main subagent for existing agents (if any)
            cursor = await conn.execute("SELECT id FROM agents")
            agents = await cursor.fetchall()
            now = datetime.utcnow().isoformat()
            
            for agent_row in agents:
                agent_id = agent_row[0]
                wake_triggers = '[{"type": "user_response"}]'
                try:
                    cursor = await conn.execute(
                        "SELECT wake_triggers FROM agent_state WHERE agent_id = ?",
                        (agent_id,)
                    )
                    row = await cursor.fetchone()
                    if row and row[0]:
                        wake_triggers = row[0]
                except:
                    pass
                
                await conn.execute("""
                    INSERT OR IGNORE INTO subagents 
                    (subagent_id, agent_id, type, status, wake_triggers, created_at, updated_at)
                    VALUES (?, ?, 'main', 'sleeping', ?, ?, ?)
                """, ("main", agent_id, wake_triggers, now, now))
            
            if agents:
                print(f"[DB] Created main subagent for {len(agents)} existing agents")
        else:
            # Full migration from v12/v13 schema
            now = datetime.utcnow().isoformat()
            
            # 1. Create subagents table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS subagents (
                    subagent_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    parent_subagent_id TEXT,
                    status TEXT DEFAULT 'sleeping',
                    historical_summary TEXT,
                    wake_triggers TEXT DEFAULT '[{"type": "user_response"}]',
                    handoff_notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_subagents_agent ON subagents(agent_id, type)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_subagents_status ON subagents(status)")
            print("[DB] Created subagents table")
            
            # 2. Create new agent_runtimes table with renamed columns
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_runtimes_new (
                    runtime_id TEXT PRIMARY KEY,
                    subagent_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    mcp_url TEXT,
                    current_round_id TEXT,
                    current_round_num INTEGER DEFAULT 1,
                    phase TEXT DEFAULT 'need_think',
                    context TEXT DEFAULT '[]',
                    pending_actions TEXT DEFAULT '[]',
                    status TEXT DEFAULT 'active',
                    error TEXT,
                    summary TEXT,
                    is_merged INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT,
                    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
                    FOREIGN KEY (subagent_id) REFERENCES subagents(subagent_id) ON DELETE CASCADE
                )
            """)
            
            # 3. Get all existing agents and create main subagent for each
            cursor = await conn.execute("SELECT id FROM agents")
            agents = await cursor.fetchall()
            
            for agent_row in agents:
                agent_id = agent_row[0]
                # v14: subagent_id 带编号，格式 main-{agent_id[:8]}
                subagent_id = f"main-{agent_id[:8]}"
                
                wake_triggers = '[{"type": "user_response"}]'
                try:
                    cursor = await conn.execute(
                        "SELECT wake_triggers FROM agent_state WHERE agent_id = ?",
                        (agent_id,)
                    )
                    row = await cursor.fetchone()
                    if row and row[0]:
                        wake_triggers = row[0]
                except:
                    pass
                
                await conn.execute("""
                    INSERT OR IGNORE INTO subagents 
                    (subagent_id, agent_id, type, status, wake_triggers, created_at, updated_at)
                    VALUES (?, ?, 'main', 'sleeping', ?, ?, ?)
                """, (subagent_id, agent_id, wake_triggers, now, now))
            
            print(f"[DB] Created main subagent for {len(agents)} agents")
            
            # 4. Migrate existing runtimes to new table
            cursor = await conn.execute("""
                SELECT subagent_id, agent_id, type, parent_subagent_id, mcp_url,
                       current_round_id, current_round_num, phase,
                       context, pending_actions, status, error,
                       created_at, updated_at
                FROM agent_runtimes
            """)
            runtimes = await cursor.fetchall()
            
            for runtime in runtimes:
                old_subagent_id = runtime[0]
                agent_id = runtime[1]
                runtime_type = runtime[2]
                
                if runtime_type == 'main':
                    # v14: subagent_id 带编号，格式 main-{agent_id[:8]}
                    new_subagent_id = f"main-{agent_id[:8]}"
                    new_runtime_id = old_subagent_id.replace("main-", "rt-")
                else:
                    new_subagent_id = old_subagent_id
                    new_runtime_id = old_subagent_id.replace("sub-", "rt-sub-")
                    # v14: parent_subagent_id 也使用新格式
                    parent_id = f"main-{agent_id[:8]}"
                    
                    await conn.execute("""
                        INSERT OR IGNORE INTO subagents 
                        (subagent_id, agent_id, type, parent_subagent_id, status, created_at, updated_at)
                        VALUES (?, ?, 'sub', ?, 'sleeping', ?, ?)
                    """, (new_subagent_id, agent_id, parent_id, now, now))
                
                await conn.execute("""
                    INSERT OR IGNORE INTO agent_runtimes_new 
                    (runtime_id, subagent_id, agent_id, mcp_url,
                     current_round_id, current_round_num, phase,
                     context, pending_actions, status, error,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_runtime_id, new_subagent_id, agent_id, runtime[4],
                    runtime[5], runtime[6], runtime[7],
                    runtime[8], runtime[9], runtime[10], runtime[11],
                    runtime[12], runtime[13]
                ))
            
            print(f"[DB] Migrated {len(runtimes)} runtimes")
            
            # 5. Update action_tasks to use new runtime_id
            for runtime in runtimes:
                old_id = runtime[0]
                runtime_type = runtime[2]
                if runtime_type == 'main':
                    new_id = old_id.replace("main-", "rt-")
                else:
                    new_id = old_id.replace("sub-", "rt-sub-")
                
                await conn.execute("""
                    UPDATE action_tasks SET subagent_id = ? WHERE subagent_id = ?
                """, (new_id, old_id))
                
                await conn.execute("""
                    UPDATE mcp_executions SET subagent_id = ? WHERE subagent_id = ?
                """, (new_id, old_id))
            
            print("[DB] Updated action_tasks and mcp_executions references")
            
            # 6. Drop old table and rename new one
            await conn.execute("DROP TABLE IF EXISTS agent_runtimes")
            await conn.execute("ALTER TABLE agent_runtimes_new RENAME TO agent_runtimes")
            
            # 7. Recreate indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_runtimes_agent ON agent_runtimes(agent_id, status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_runtimes_subagent ON agent_runtimes(subagent_id, status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_runtimes_phase ON agent_runtimes(status, phase)")
            
            print("[DB] Recreated agent_runtimes table with new schema")
        
        # Update schema version to 14
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', '14')"
        )
        
        await conn.commit()
        print("[DB] Migration to v14 complete")
    
    if from_version < 15:
        print("[DB] Running migration from v14 to v15...")
        
        # Migration from v14 to v15:
        # Three-Task Architecture - pipeline_tasks table
        # Table is created by SCHEMA_SQL via CREATE TABLE IF NOT EXISTS
        
        # Update schema version to 15
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', '15')"
        )
        
        await conn.commit()
        print("[DB] Migration to v15 complete")
    
    if from_version < 16:
        print("[DB] Running migration from v15 to v16...")
        
        # Migration from v15 to v16:
        # Async SubAgent - add progress/result/error/timeout_at/task fields to subagents
        
        cursor = await conn.execute("PRAGMA table_info(subagents)")
        columns = [row[1] for row in await cursor.fetchall()]
        
        if 'task' not in columns:
            print("[DB] Adding 'task' column to subagents")
            await conn.execute("ALTER TABLE subagents ADD COLUMN task TEXT")
        
        if 'progress' not in columns:
            print("[DB] Adding 'progress' column to subagents")
            await conn.execute("ALTER TABLE subagents ADD COLUMN progress TEXT")
        
        if 'result' not in columns:
            print("[DB] Adding 'result' column to subagents")
            await conn.execute("ALTER TABLE subagents ADD COLUMN result TEXT")
        
        if 'error' not in columns:
            print("[DB] Adding 'error' column to subagents")
            await conn.execute("ALTER TABLE subagents ADD COLUMN error TEXT")
        
        if 'timeout_at' not in columns:
            print("[DB] Adding 'timeout_at' column to subagents")
            await conn.execute("ALTER TABLE subagents ADD COLUMN timeout_at TEXT")
        
        # Update schema version to 16
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', '16')"
        )
        
        await conn.commit()
        print("[DB] Migration to v16 complete")
    
    if from_version < 17:
        print("[DB] Running migration from v16 to v17...")
        
        # Migration from v16 to v17:
        # Remove v11 legacy tables (action_tasks, mcp_executions, worker_processes)
        # These were replaced by pipeline_tasks in v15 Three-Task Architecture
        
        # Drop legacy tables and indexes
        await conn.execute("DROP TABLE IF EXISTS action_tasks")
        print("[DB] Dropped action_tasks table")
        
        await conn.execute("DROP TABLE IF EXISTS mcp_executions")
        print("[DB] Dropped mcp_executions table")
        
        await conn.execute("DROP TABLE IF EXISTS worker_processes")
        print("[DB] Dropped worker_processes table")
        
        # Update schema version to 17
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', '17')"
        )
        
        await conn.commit()
        print("[DB] Migration to v17 complete")
    
    if from_version < 18:
        print("[DB] Running migration from v17 to v18...")
        
        # Migration from v17 to v18:
        # Event-driven Monitor - add status field to chat_messages
        
        cursor = await conn.execute("PRAGMA table_info(chat_messages)")
        columns = [row[1] for row in await cursor.fetchall()]
        
        if 'status' not in columns:
            print("[DB] Adding 'status' column to chat_messages")
            await conn.execute("ALTER TABLE chat_messages ADD COLUMN status TEXT DEFAULT 'sent'")
            # All existing messages are already delivered, so default to 'sent'
        
        # Create index for Monitor queue
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_status ON chat_messages(status, created_at)"
        )
        print("[DB] Created index for chat_messages.status")
        
        # Update schema version to 18
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', '18')"
        )
        
        await conn.commit()
        print("[DB] Migration to v18 complete")
    
    if from_version < 19:
        print("[DB] Running migration from v18 to v19...")
        
        # Migration from v18 to v19:
        # Task Queue v2 - tq_tasks and tq_sagas tables
        # Tables are created by SCHEMA_SQL via CREATE TABLE IF NOT EXISTS
        
        # Ensure indexes exist
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tq_tasks_pending 
            ON tq_tasks(topic, status, created_at) WHERE status = 'pending'
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tq_tasks_heartbeat 
            ON tq_tasks(status, heartbeat_at) WHERE status = 'claimed'
        """)
        await conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_tq_tasks_idempotency 
            ON tq_tasks(idempotency_key)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tq_tasks_topic 
            ON tq_tasks(topic, status)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tq_sagas_status 
            ON tq_sagas(status, created_at)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tq_sagas_type 
            ON tq_sagas(saga_type, status)
        """)
        await conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_tq_sagas_idempotency 
            ON tq_sagas(idempotency_key)
        """)
        print("[DB] Created Task Queue v2 tables and indexes")
        
        # Update schema version to 19
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', '19')"
        )
        
        await conn.commit()
        print("[DB] Migration to v19 complete")
    
    if from_version < 20:
        print("[DB] Running migration from v19 to v20...")
        
        # Migration from v19 to v20:
        # Saga v2 - add summarized and need_rest fields to agent_runtimes
        
        cursor = await conn.execute("PRAGMA table_info(agent_runtimes)")
        columns = [row[1] for row in await cursor.fetchall()]
        
        if 'summarized' not in columns:
            print("[DB] Adding 'summarized' column to agent_runtimes")
            await conn.execute("ALTER TABLE agent_runtimes ADD COLUMN summarized INTEGER DEFAULT 0")
            
            # Mark completed runtimes with summary as already summarized
            await conn.execute("""
                UPDATE agent_runtimes 
                SET summarized = 1 
                WHERE status = 'completed' AND summary IS NOT NULL AND summary != ''
            """)
            print("[DB] Updated existing runtimes with summaries")
        
        if 'need_rest' not in columns:
            print("[DB] Adding 'need_rest' column to agent_runtimes")
            await conn.execute("ALTER TABLE agent_runtimes ADD COLUMN need_rest INTEGER DEFAULT 0")
            
            # Mark completed runtimes as need_rest=1
            await conn.execute("""
                UPDATE agent_runtimes 
                SET need_rest = 1 
                WHERE status = 'completed'
            """)
            print("[DB] Updated existing completed runtimes with need_rest=1")
        
        # Update schema version to 20
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', '20')"
        )
        
        await conn.commit()
        print("[DB] Migration to v20 complete")
    
    if from_version < 21:
        print("[DB] Running migration from v20 to v21...")
        
        # Migration from v20 to v21:
        # Agent model selection - add model_id field to agents table
        
        cursor = await conn.execute("PRAGMA table_info(agents)")
        columns = [row[1] for row in await cursor.fetchall()]
        
        if 'model_id' not in columns:
            print("[DB] Adding 'model_id' column to agents")
            await conn.execute("ALTER TABLE agents ADD COLUMN model_id TEXT")
        
        # Update schema version to 21
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', '21')"
        )
        
        await conn.commit()
        print("[DB] Migration to v21 complete")
    
    if from_version < 22:
        print("[DB] Running migration from v21 to v22...")
        
        # Migration from v21 to v22:
        # Rename available_models -> candidate_models
        # Rename enabled -> available
        
        # Check if candidate_models already exists
        cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='candidate_models'")
        exists = await cursor.fetchone()
        
        if not exists:
            # Create new table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS candidate_models (
                    id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    api_key_id TEXT NOT NULL,
                    available INTEGER DEFAULT 1,
                    is_custom INTEGER DEFAULT 0,
                    PRIMARY KEY (id, api_key_id),
                    FOREIGN KEY (api_key_id) REFERENCES api_keys(id) ON DELETE CASCADE
                )
            """)
            
            # Copy data from available_models if exists
            cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='available_models'")
            if await cursor.fetchone():
                await conn.execute("""
                    INSERT OR REPLACE INTO candidate_models (id, name, provider, api_key_id, available, is_custom)
                    SELECT id, name, provider, api_key_id, enabled, is_custom FROM available_models
                """)
                
                # Drop old table
                await conn.execute("DROP TABLE available_models")
        
        # Recreate indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_models_api_key ON candidate_models(api_key_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_models_available ON candidate_models(available)")
        
        # Update schema version to 22
        await conn.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES ('version', '22')"
        )
        
        await conn.commit()
        print("[DB] Migration to v22 complete")