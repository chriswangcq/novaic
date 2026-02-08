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
v23: Execution logs - subagent_id, status, kind, event_key, updated_at for upsert support.
v24: Runtime Summary - subagents.hrl/summary_lock, agent_runtimes.simple_summary/hot_summary/cold_summary.
v25: Tools Server persistence - agent_runtimes.tool_ports for Tools Server recovery.
"""

SCHEMA_VERSION = 30

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
    model_id TEXT,  -- Selected LLM model ID (v20)
    cloud_init_complete INTEGER DEFAULT 0  -- Cloud-init initialization status
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
    status TEXT DEFAULT 'sent',      -- 'sending' (pending), 'sent' (delivered/confirmed)
    
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
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
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
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
-- v23: Added subagent_id, status, kind, event_key, updated_at for upsert support

CREATE TABLE IF NOT EXISTS execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL DEFAULT 'default',
    subagent_id TEXT NOT NULL DEFAULT 'main',      -- v23: Owning subagent
    type TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'tool',             -- v23: 'think' | 'tool'
    status TEXT NOT NULL DEFAULT 'complete',       -- v23: 'running' | 'complete'
    event_key TEXT,                                -- v23: Unique business key for upsert
    timestamp TEXT NOT NULL,
    data TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT,                               -- v23: Last update time
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_execution_logs_agent ON execution_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_timestamp ON execution_logs(agent_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_execution_logs_subagent ON execution_logs(agent_id, subagent_id);
-- Note: Using regular UNIQUE INDEX (not partial) because SQLite ON CONFLICT requires non-partial index
CREATE UNIQUE INDEX IF NOT EXISTS idx_execution_logs_event_key ON execution_logs(agent_id, subagent_id, event_key);

-- ========================================
-- 7. Agent Runtime State Tables (per-agent)
-- ========================================

CREATE TABLE IF NOT EXISTS agent_runtime_state (
    agent_id TEXT NOT NULL DEFAULT 'default',
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (agent_id, key),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
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
    notify_on TEXT DEFAULT '["complete", "error"]',  -- JSON: events to notify on
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
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

-- ========================================
-- Agent Notebook - Structured internal workspace
-- ========================================
-- Stores agent's private notes: research, reflections, insights, plans, observations.
-- Unlike agent_memory (simple KV), notebook is a structured document store with
-- types, status lifecycle, relevance scoring, and time-sensitivity.

CREATE TABLE IF NOT EXISTS agent_notebook (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    
    entry_type TEXT NOT NULL,          -- 'research', 'reflection', 'insight', 'plan', 'observation'
    title TEXT NOT NULL,               
    content TEXT NOT NULL,             
    source TEXT,                       -- where this entry came from (runtime_id, tool, etc.)
    
    related_topics TEXT DEFAULT '[]',  -- JSON array of topic tags
    relevance_score REAL DEFAULT 0.5,  -- 0-1 relevance to user
    
    status TEXT DEFAULT 'draft',       -- 'draft', 'ready', 'shared', 'archived'
    
    expires_at TEXT,                   -- ISO timestamp for time-sensitive info (NULL = no expiry)
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_notebook_agent ON agent_notebook(agent_id);
CREATE INDEX IF NOT EXISTS idx_notebook_agent_type ON agent_notebook(agent_id, entry_type);
CREATE INDEX IF NOT EXISTS idx_notebook_agent_status ON agent_notebook(agent_id, status);

-- ========================================
-- Agent Drive - Personality and autonomous behavior config
-- ========================================
-- Per-agent drive configuration: personality, user profile, relationship tracking.
-- Powers the agent's autonomous wake behavior and proactive communication.

CREATE TABLE IF NOT EXISTS agent_drive (
    agent_id TEXT PRIMARY KEY,
    
    -- Personality
    personality TEXT DEFAULT '{}',           -- JSON: personality traits
    communication_style TEXT DEFAULT 'friendly',  -- Communication style hint
    
    -- User profile (learned by agent)
    user_profile TEXT DEFAULT '{}',          -- JSON: user preferences, habits, interests
    user_active_hours TEXT,                  -- e.g. "9:00-18:00"
    
    -- Drive parameters
    proactiveness REAL DEFAULT 0.5,          -- 0-1: how proactive to be
    min_rest_minutes INTEGER DEFAULT 15,     -- minimum rest duration
    max_rest_minutes INTEGER DEFAULT 120,    -- maximum rest duration
    
    -- Relationship tracking
    relationship_level INTEGER DEFAULT 0,    -- 0-100 closeness
    interaction_count INTEGER DEFAULT 0,     -- total interaction count
    no_response_streak INTEGER DEFAULT 0,    -- consecutive proactive messages without user response
    last_proactive_at TEXT,                  -- last proactive message time
    
    -- Tools configuration (Phase 5)
    enabled_tool_categories TEXT DEFAULT '[]',   -- JSON: enabled tool categories
    disabled_tools TEXT DEFAULT '[]',            -- JSON: explicitly disabled tool names
    custom_instructions TEXT DEFAULT '',          -- User-defined extra instructions
    
    -- Timestamps
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

-- ========================================
-- Skills - Reusable capability bundles
-- ========================================

CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    prompt TEXT DEFAULT '',
    tools TEXT DEFAULT '[]',
    workflow TEXT DEFAULT '',
    icon TEXT DEFAULT 'zap',
    enabled INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Agent-Skill assignments (many-to-many)
CREATE TABLE IF NOT EXISTS agent_skills (
    agent_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (agent_id, skill_id),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
);

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
    wake_at TEXT,                      -- ISO timestamp: auto-wake time (NULL = no timer)
    
    -- Async SubAgent fields (v16)
    task TEXT,                         -- Task description for sub subagents
    progress TEXT,                     -- Current progress description
    result TEXT,                       -- Final result (when completed)
    error TEXT,                        -- Error message (when failed)
    timeout_at TEXT,                   -- Timeout timestamp
    
    -- Runtime Summary (v24)
    hrl TEXT DEFAULT '[]',              -- Hot Runtime List (JSON array of runtime_ids)
    summary_lock INTEGER DEFAULT 0,     -- 0=idle, 1=summarizing (CAS lock)
    
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
    
    -- Runtime Summary (v24)
    simple_summary TEXT,               -- Simple summary (plain text)
    hot_summary TEXT,                  -- Hot summary (LLM-generated plain text)
    cold_summary TEXT,                 -- Cold summary (LLM-generated plain text)
    
    -- Tools Server persistence (v25)
    tool_ports TEXT,                    -- JSON: MCP ports for Tools Server discovery (null = not registered)
    
    -- Drive trigger (v29)
    trigger_type TEXT DEFAULT 'user_message',  -- What triggered this runtime (user_message, proactive, scheduled)
    
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
-- Task queue tables removed - now managed by Queue Service (port 19997)
-- tq_tasks and tq_sagas are in queue.db, not novaic.db
"""

DEFAULT_CONFIG = {
    "version": str(SCHEMA_VERSION),
    "default_model": '"gpt-4o"',
    "max_tokens": "4096",
    "max_iterations": "20",
    "visible_shell": "false",
}

DEFAULT_RUNTIME_STATE = {
    "is_resting": "false",
    "rest_reason": "null",
    "wake_triggers": "[]",
    "handoff_notes": "null",
    "rest_started": "null",
    # Note: is_busy and current_message_id removed in v10 (new architecture)
}


def init_schema_sync(conn):
    """Initialize database schema and default data (synchronous version)."""
    # Check current schema version
    try:
        cursor = conn.execute("SELECT value FROM config WHERE key = 'version'")
        row = cursor.fetchone()
        current_version = int(row[0]) if row else 0
    except Exception:
        current_version = 0
    
    # Split schema SQL into CREATE TABLE and CREATE INDEX statements
    table_statements = []
    index_statements = []
    
    for statement in SCHEMA_SQL.split(';'):
        statement = statement.strip()
        if statement:
            if statement.upper().startswith('CREATE INDEX') or statement.upper().startswith('CREATE UNIQUE INDEX'):
                index_statements.append(statement)
            else:
                table_statements.append(statement)
    
    # Step 1: Execute table creation statements first
    for statement in table_statements:
        try:
            conn.execute(statement)
        except Exception as e:
            # Ignore errors for existing tables/constraints
            if "already exists" not in str(e).lower():
                pass
    
    # Insert default config values (needed for migration check)
    for key, value in DEFAULT_CONFIG.items():
        conn.execute(
            "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
            (key, value)
        )
    
    # Insert default runtime state
    for key, value in DEFAULT_RUNTIME_STATE.items():
        conn.execute(
            "INSERT OR IGNORE INTO agent_runtime_state (key, value) VALUES (?, ?)",
            (key, value)
        )
    
    conn.commit()
    
    # Step 2: Run migrations if needed (adds columns before index creation)
    if current_version < SCHEMA_VERSION:
        print(f"[DB] Migrating from version {current_version} to {SCHEMA_VERSION}")
        run_migration_sync(conn, current_version)
        print(f"[DB] Migration complete")
    
    # Step 3: Create indexes after migration (columns now exist)
    for statement in index_statements:
        try:
            conn.execute(statement)
        except Exception as e:
            # Ignore errors for existing indexes
            if "already exists" not in str(e).lower():
                pass
    
    conn.commit()


def run_migration_sync(conn, from_version: int):
    """Run migrations synchronously."""
    
    # v21: Add model_id to agents table
    # Always try to add (handles case where version was updated but column wasn't added)
    try:
        conn.execute("ALTER TABLE agents ADD COLUMN model_id TEXT")
        print("[DB] Migration v21: Added model_id to agents")
    except Exception as e:
        if "duplicate column" not in str(e).lower():
            print(f"[DB] Migration v21 warning: {e}")
    
    # v22: Create candidate_models table (handled by CREATE TABLE IF NOT EXISTS)
    
    # v23: Add new columns to execution_logs table
    if from_version < 23:
        # Add subagent_id column
        try:
            conn.execute("ALTER TABLE execution_logs ADD COLUMN subagent_id TEXT NOT NULL DEFAULT 'main'")
            print("[DB] Migration v23: Added subagent_id to execution_logs")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"[DB] Migration v23 warning (subagent_id): {e}")
        
        # Add kind column
        try:
            conn.execute("ALTER TABLE execution_logs ADD COLUMN kind TEXT NOT NULL DEFAULT 'tool'")
            print("[DB] Migration v23: Added kind to execution_logs")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"[DB] Migration v23 warning (kind): {e}")
        
        # Add status column
        try:
            conn.execute("ALTER TABLE execution_logs ADD COLUMN status TEXT NOT NULL DEFAULT 'complete'")
            print("[DB] Migration v23: Added status to execution_logs")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"[DB] Migration v23 warning (status): {e}")
        
        # Add event_key column
        try:
            conn.execute("ALTER TABLE execution_logs ADD COLUMN event_key TEXT")
            print("[DB] Migration v23: Added event_key to execution_logs")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"[DB] Migration v23 warning (event_key): {e}")
        
        # Add updated_at column
        try:
            conn.execute("ALTER TABLE execution_logs ADD COLUMN updated_at TEXT")
            print("[DB] Migration v23: Added updated_at to execution_logs")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"[DB] Migration v23 warning (updated_at): {e}")
    
    # v24: Runtime Summary - add new columns to subagents and agent_runtimes
    if from_version < 24:
        # subagents.hrl (Hot Runtime List)
        try:
            conn.execute("ALTER TABLE subagents ADD COLUMN hrl TEXT DEFAULT '[]'")
            print("[DB] Migration v24: Added hrl to subagents")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"[DB] Migration v24 warning (hrl): {e}")
        
        # subagents.summary_lock
        try:
            conn.execute("ALTER TABLE subagents ADD COLUMN summary_lock INTEGER DEFAULT 0")
            print("[DB] Migration v24: Added summary_lock to subagents")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"[DB] Migration v24 warning (summary_lock): {e}")
        
        # agent_runtimes.simple_summary
        try:
            conn.execute("ALTER TABLE agent_runtimes ADD COLUMN simple_summary TEXT")
            print("[DB] Migration v24: Added simple_summary to agent_runtimes")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"[DB] Migration v24 warning (simple_summary): {e}")
        
        # agent_runtimes.hot_summary
        try:
            conn.execute("ALTER TABLE agent_runtimes ADD COLUMN hot_summary TEXT")
            print("[DB] Migration v24: Added hot_summary to agent_runtimes")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"[DB] Migration v24 warning (hot_summary): {e}")
        
        # agent_runtimes.cold_summary
        try:
            conn.execute("ALTER TABLE agent_runtimes ADD COLUMN cold_summary TEXT")
            print("[DB] Migration v24: Added cold_summary to agent_runtimes")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"[DB] Migration v24 warning (cold_summary): {e}")
    
    # v25: Tools Server persistence - add tool_ports to agent_runtimes
    if from_version < 25:
        try:
            conn.execute("ALTER TABLE agent_runtimes ADD COLUMN tool_ports TEXT")
            print("[DB] Migration v25: Added tool_ports to agent_runtimes")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"[DB] Migration v25 warning (tool_ports): {e}")
    
    # v26: Scheduled wake - add wake_at to subagents
    if from_version < 26:
        try:
            conn.execute("ALTER TABLE subagents ADD COLUMN wake_at TEXT")
            print("[DB] Migration v26: Added wake_at to subagents")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"[DB] Migration v26 warning (wake_at): {e}")

    # v29: Drive Phase 4 - trigger_type on runtimes, no_response_streak on drive
    if from_version < 29:
        try:
            conn.execute("ALTER TABLE agent_runtimes ADD COLUMN trigger_type TEXT DEFAULT 'user_message'")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE agent_drive ADD COLUMN no_response_streak INTEGER DEFAULT 0")
        except Exception:
            pass
        conn.execute("PRAGMA user_version = 29")
        print("[schema] Migrated to v29: trigger_type on runtimes, no_response_streak on drive")

    # v30: Skills & Agent Tools
    if from_version < 30:
        try:
            conn.execute("ALTER TABLE agent_drive ADD COLUMN enabled_tool_categories TEXT DEFAULT '[]'")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE agent_drive ADD COLUMN disabled_tools TEXT DEFAULT '[]'")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE agent_drive ADD COLUMN custom_instructions TEXT DEFAULT ''")
        except Exception:
            pass
        conn.execute("PRAGMA user_version = 30")
        print("[schema] Migrated to v30: skills tables + agent_drive tool config columns")

    # Update version
    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES ('version', ?)",
        (str(SCHEMA_VERSION),)
    )
    conn.commit()
    print(f"[DB] Schema version updated to {SCHEMA_VERSION}")
