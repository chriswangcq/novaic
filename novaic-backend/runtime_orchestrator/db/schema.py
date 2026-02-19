"""
Runtime Orchestrator database schema (RO-native).

This schema is intentionally narrower than Gateway schema:
- keeps agent orchestration/runtime state
- excludes business-domain chat/config/session tables
"""

RUNTIME_SCHEMA_VERSION = 1

RUNTIME_BUSINESS_TABLES = (
    "api_keys",
    "candidate_models",
    "sessions",
    "session_messages",
    "chat_messages",
    "pending_questions",
    "question_responses",
    "execution_logs",
    "tasks",
    "task_outputs",
    "agent_state",
    "skills",
    "agent_skills",
    "ssh_keys",
    "vm_processes",
    "devices",
)

RUNTIME_SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;

CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS subagents (
    subagent_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    type TEXT NOT NULL,
    parent_subagent_id TEXT,
    status TEXT DEFAULT 'sleeping',
    historical_summary TEXT,
    wake_triggers TEXT DEFAULT '[{"type": "user_response"}]',
    handoff_notes TEXT,
    wake_at TEXT,
    task TEXT,
    progress TEXT,
    result TEXT,
    error TEXT,
    timeout_at TEXT,
    hrl TEXT DEFAULT '[]',
    summary_lock INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_ro_subagents_agent ON subagents(agent_id, type);
CREATE INDEX IF NOT EXISTS idx_ro_subagents_status ON subagents(status);

CREATE TABLE IF NOT EXISTS agent_runtimes (
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
    summarized INTEGER DEFAULT 0,
    need_rest INTEGER DEFAULT 0,
    simple_summary TEXT,
    hot_summary TEXT,
    cold_summary TEXT,
    tool_ports TEXT,
    trigger_type TEXT DEFAULT 'user_message',
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (subagent_id) REFERENCES subagents(subagent_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_ro_runtimes_agent ON agent_runtimes(agent_id, status);
CREATE INDEX IF NOT EXISTS idx_ro_runtimes_subagent ON agent_runtimes(subagent_id, status);
CREATE INDEX IF NOT EXISTS idx_ro_runtimes_phase ON agent_runtimes(status, phase);

CREATE TABLE IF NOT EXISTS pipeline_tasks (
    id TEXT PRIMARY KEY,
    task_type TEXT NOT NULL,
    task_subtype TEXT NOT NULL,
    runtime_id TEXT NOT NULL,
    stage_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    args TEXT DEFAULT '{}',
    result TEXT,
    error TEXT,
    status TEXT DEFAULT 'pending',
    claimed_by TEXT,
    claimed_at TEXT,
    heartbeat_at TEXT,
    idempotency_key TEXT UNIQUE,
    expected_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_ro_pipeline_pending ON pipeline_tasks(status, task_type, created_at);
CREATE INDEX IF NOT EXISTS idx_ro_pipeline_runtime ON pipeline_tasks(runtime_id, stage_id);
CREATE INDEX IF NOT EXISTS idx_ro_pipeline_stage ON pipeline_tasks(stage_id, task_type);

CREATE TABLE IF NOT EXISTS agent_runtime_state (
    agent_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (agent_id, key)
);

CREATE TABLE IF NOT EXISTS agent_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    namespace TEXT NOT NULL DEFAULT 'default',
    key TEXT NOT NULL,
    value TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(agent_id, namespace, key)
);
CREATE INDEX IF NOT EXISTS idx_ro_memory_agent ON agent_memory(agent_id);
CREATE INDEX IF NOT EXISTS idx_ro_memory_ns ON agent_memory(agent_id, namespace);

CREATE TABLE IF NOT EXISTS agent_notebook (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    entry_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT,
    related_topics TEXT DEFAULT '[]',
    relevance_score REAL DEFAULT 0.5,
    status TEXT DEFAULT 'draft',
    expires_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_ro_notebook_agent ON agent_notebook(agent_id);

CREATE TABLE IF NOT EXISTS agent_task_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    status TEXT DEFAULT 'completed',
    timestamp TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_ro_task_history_agent ON agent_task_history(agent_id);

CREATE TABLE IF NOT EXISTS agent_drive (
    agent_id TEXT PRIMARY KEY,
    personality TEXT DEFAULT '{}',
    communication_style TEXT DEFAULT 'friendly',
    user_profile TEXT DEFAULT '{}',
    user_active_hours TEXT,
    proactiveness REAL DEFAULT 0.5,
    min_rest_minutes INTEGER DEFAULT 15,
    max_rest_minutes INTEGER DEFAULT 120,
    relationship_level INTEGER DEFAULT 0,
    interaction_count INTEGER DEFAULT 0,
    no_response_streak INTEGER DEFAULT 0,
    last_proactive_at TEXT,
    enabled_tool_categories TEXT DEFAULT '[]',
    disabled_tools TEXT DEFAULT '[]',
    custom_instructions TEXT DEFAULT '',
    soul_md TEXT DEFAULT '',
    heartbeat_md TEXT DEFAULT '',
    memory_md TEXT DEFAULT '',
    user_md TEXT DEFAULT '',
    active_hours_start TEXT DEFAULT '09:00',
    active_hours_end TEXT DEFAULT '22:00',
    active_hours_timezone TEXT DEFAULT 'Asia/Shanghai',
    growth_log TEXT DEFAULT '[]',
    drive_config TEXT DEFAULT '{}',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agent_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    quadrant TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    task_type TEXT DEFAULT 'one_time',
    progress_notes TEXT DEFAULT '[]',
    source TEXT NOT NULL,
    reasoning TEXT,
    due_date TEXT,
    reminder_at TEXT,
    context TEXT,
    related_profile_keys TEXT DEFAULT '[]',
    completed_at TEXT,
    completion_notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_ro_agent_tasks_agent ON agent_tasks(agent_id);
CREATE INDEX IF NOT EXISTS idx_ro_agent_tasks_status ON agent_tasks(agent_id, status);
"""


def init_runtime_schema_sync(conn):
    """Initialize Runtime Orchestrator schema."""
    for table in RUNTIME_BUSINESS_TABLES:
        try:
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        except Exception:
            pass

    for statement in RUNTIME_SCHEMA_SQL.split(";"):
        stmt = statement.strip()
        if not stmt:
            continue
        try:
            conn.execute(stmt)
        except Exception:
            pass

    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES ('runtime_schema_version', ?)",
        (str(RUNTIME_SCHEMA_VERSION),),
    )
    conn.commit()


__all__ = [
    "RUNTIME_SCHEMA_VERSION",
    "RUNTIME_BUSINESS_TABLES",
    "RUNTIME_SCHEMA_SQL",
    "init_runtime_schema_sync",
]
