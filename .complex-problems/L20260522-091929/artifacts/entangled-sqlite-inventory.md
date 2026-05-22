# Entangled SQLite Inventory

Snapshot time: 2026-05-22 10:40-10:45 Asia/Shanghai  
Host: `api.gradievo.com` (`iZt4n5hl0gyf590z3admpmZ`)  
Scope: read-only inventory for P018. No production Entangled data, schema, config, or runtime mode was changed.

## Runtime

Entangled is currently a host process, not a Docker container.

- Process: `python`, pid `3473488`, user `root`
- Command shape: `/opt/novaic/services/novaic-gateway/.venv/bin/python -m entangled.app.main --host 127.0.0.1 --port 19900 --db-path /opt/novaic/data/entangled.db --service-token <redacted>`
- Listener: `127.0.0.1:19900`, pid `3473488`
- Docker containers relevant to this host at snapshot time: `novaic-postgres`, `novaic-llm-factory`; no Entangled container is running.

Health endpoints:

```text
/v1/health: status ok, entities 22
/v1/ready: HTTP 200, status ready, entities 22, missing []
```

Registered entity names reported by health:

```text
skills
api-keys
agents
subagents
files
user-preferences
agent-skills
models
api-key-models
available-models
agent-binding
agent-tools
agent-state
messages
agent-activity-records
agent-activity-participants
environment-events
environment-im-messages
environment-notifications
environment-resource-refs
devices
vm-users
```

## Active SQLite Files

```text
/opt/novaic/data/entangled.db     7106560 bytes  root:root  0644  2026-05-19 16:12:29.619588593 +0800
/opt/novaic/data/entangled.db-wal 4169472 bytes  root:root  0644  2026-05-19 16:12:32.177544892 +0800
/opt/novaic/data/entangled.db-shm   32768 bytes  root:root  0644  2026-05-22 10:05:46.070536699 +0800
```

Open file holders:

- Single holder process: pid `3473488`, command `python`.
- It holds repeated read handles on `entangled.db`, `mem-r` and read handles on `entangled.db-shm`, and write handles on `entangled.db-wal`.

## Table Groups

Registered or sync-facing entity tables:

```text
agent_activity_participants
agent_activity_records
agent_device_bindings
agent_skills
agent_state
agents
api_key_models
api_keys
available_models
chat_messages
devices
environment_events
environment_im_messages
environment_notifications
environment_resource_refs
files
models
skills
subagents
user_preferences
vm_users
```

Supporting identity/config tables present in the live DB but not currently listed by `/v1/health` as registered entities:

```text
users
refresh_tokens
agent_drive
execution_logs
execution_log_payloads
```

Internal Entangled/runtime tables:

```text
entangled_sync_versions
subagent_state_transitions
sqlite_sequence
```

## Row Counts

Point-in-time live counts:

| table | rows |
|---|---:|
| agent_activity_participants | 2 |
| agent_activity_records | 314 |
| agent_device_bindings | 2 |
| agent_drive | 0 |
| agent_skills | 0 |
| agent_state | 1 |
| agents | 3 |
| api_key_models | 408 |
| api_keys | 3 |
| available_models | 2 |
| chat_messages | 270 |
| devices | 1 |
| entangled_sync_versions | 67 |
| environment_events | 270 |
| environment_im_messages | 270 |
| environment_notifications | 210 |
| environment_resource_refs | 0 |
| execution_log_payloads | 302 |
| execution_logs | 302 |
| files | 3 |
| models | 408 |
| refresh_tokens | 1 |
| skills | 1 |
| sqlite_sequence | 1 |
| subagent_state_transitions | 184 |
| subagents | 5 |
| user_preferences | 2 |
| users | 1 |
| vm_users | 0 |

## Sync Versions

`entangled_sync_versions` summary:

```text
rows: 67
min_version: 1
max_version: 5319
negative_versions: 0
```

Grouped by state-key prefix. Parameterized state keys are summarized by prefix to avoid dumping all scoped ids.

| state key prefix | key rows | min version | max version |
|---|---:|---:|---:|
| agent-activity-participants | 4 | 60 | 1062 |
| agent-activity-records | 4 | 50 | 969 |
| agent-binding | 4 | 1 | 7 |
| agent-state | 1 | 11 | 11 |
| agent-tools | 4 | 1 | 7 |
| agents | 1 | 18 | 18 |
| api-key-models | 2 | 1 | 436 |
| api-keys | 1 | 63 | 63 |
| available-models | 2 | 1 | 8 |
| devices | 2 | 8 | 15 |
| environment-events | 6 | 1 | 152 |
| environment-im-messages | 6 | 1 | 152 |
| environment-notifications | 6 | 2 | 310 |
| execution-logs | 4 | 1 | 1988 |
| files | 1 | 3 | 3 |
| log-payloads | 3 | 8 | 1952 |
| messages | 6 | 2 | 5319 |
| models | 1 | 474 | 474 |
| subagents | 8 | 1 | 1066 |
| user-preferences | 1 | 11 | 11 |

`subagent_state_transitions` summary:

```text
rows: 184
min_id: 15
max_id: 542
min_created_at: 1776772153445
max_created_at: 1779178352178
```

## Index and Trigger Inventory

Index counts from `sqlite_master`:

| table | index rows |
|---|---:|
| agent_activity_participants | 8 |
| agent_activity_records | 8 |
| agent_device_bindings | 2 |
| agent_drive | 1 |
| agent_skills | 2 |
| agent_state | 1 |
| agents | 2 |
| api_key_models | 5 |
| api_keys | 3 |
| available_models | 5 |
| chat_messages | 6 |
| devices | 2 |
| entangled_sync_versions | 1 |
| environment_events | 12 |
| environment_im_messages | 10 |
| environment_notifications | 13 |
| environment_resource_refs | 6 |
| execution_log_payloads | 1 |
| execution_logs | 2 |
| files | 3 |
| models | 1 |
| refresh_tokens | 2 |
| skills | 2 |
| subagent_state_transitions | 1 |
| subagents | 3 |
| user_preferences | 1 |
| users | 3 |
| vm_users | 3 |

Trigger count: `0`.

Explicit indexes are included in the schema dump below. SQLite autoindexes exist for primary-key and unique constraints and must be represented by Postgres primary keys or unique constraints, not recreated as separate named indexes.

## Live Schema Dump

Captured with `sqlite3 -readonly /opt/novaic/data/entangled.db .schema`.

```sql
CREATE TABLE entangled_sync_versions (
                state_key TEXT PRIMARY KEY,
                version INTEGER NOT NULL DEFAULT 0
            );
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    last_login_at TEXT DEFAULT (datetime('now')),
    UNIQUE(email)
);
CREATE TABLE user_preferences (
    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    default_model TEXT DEFAULT 'gpt-4o',
    audio_model TEXT,
    max_tokens INTEGER DEFAULT 4096,
    max_iterations INTEGER DEFAULT 20,
    visible_shell INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE refresh_tokens (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TEXT NOT NULL DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT '' REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    setup_complete INTEGER NOT NULL DEFAULT 0,
    model_id TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE subagents (
    subagent_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    parent_subagent_id TEXT,
    status TEXT DEFAULT 'sleeping',
    wake_triggers TEXT DEFAULT '[{"type":"user_response"}]',
    wake_at TEXT,
    task TEXT,
    progress TEXT,
    result TEXT,
    error TEXT,
    timeout_at TEXT,
    hrl TEXT DEFAULT '[]',
    summary_lock INTEGER DEFAULT 0,
    log_count INTEGER DEFAULT 0,
    need_rest INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE devices (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT '' REFERENCES users(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    name TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now')),
    status TEXT DEFAULT 'created',
    memory INTEGER DEFAULT 4096,
    cpus INTEGER DEFAULT 4,
    data_path TEXT DEFAULT '',
    ports TEXT DEFAULT '{}',
    backend TEXT DEFAULT 'qemu',
    os_type TEXT DEFAULT 'ubuntu',
    os_version TEXT DEFAULT '24.04',
    image_path TEXT DEFAULT '',
    cloud_init_complete INTEGER NOT NULL DEFAULT 0,
    avd_name TEXT DEFAULT '',
    device_serial TEXT DEFAULT '',
    managed INTEGER NOT NULL DEFAULT 1,
    system_image TEXT DEFAULT '',
    pc_client_id TEXT,
    updated_at TEXT DEFAULT (datetime('now')),
    CHECK(type IN ('linux', 'android', 'host_desktop')),
    CHECK(status IN ('created', 'setup', 'ready', 'running', 'stopped', 'error'))
);
CREATE TABLE vm_users (
    id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    password TEXT NOT NULL DEFAULT '',
    display_num INTEGER DEFAULT 11,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(device_id, username)
);
CREATE TABLE skills (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT '' REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    prompt TEXT DEFAULT '',
    tools TEXT DEFAULT '[]',
    workflow TEXT DEFAULT '',
    icon TEXT DEFAULT 'zap',
    enabled INTEGER NOT NULL DEFAULT 1,
    source TEXT DEFAULT 'custom',
    builtin_id TEXT,
    forked_from TEXT,
    auto_match_keywords TEXT DEFAULT '[]',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE agent_skills (
    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    skill_id TEXT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE api_keys (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT '' REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    api_key TEXT,
    has_api_key INTEGER NOT NULL DEFAULT 0,
    api_base TEXT,
    deployment_name TEXT,
    api_version TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE models (
    model_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    is_custom INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
, model_name TEXT DEFAULT '');
CREATE TABLE api_key_models (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    api_key_id TEXT NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
    model_id TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(api_key_id, model_id)
);
CREATE TABLE available_models (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    model_id TEXT NOT NULL,
    api_key_id TEXT NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, model_id)
);
CREATE TABLE agent_device_bindings (
    agent_id TEXT PRIMARY KEY REFERENCES agents(id) ON DELETE CASCADE,
    device_id TEXT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL DEFAULT '',
    mounted_tools TEXT DEFAULT '[]',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE agent_drive (
    agent_id TEXT PRIMARY KEY REFERENCES agents(id) ON DELETE CASCADE,
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
    user_md TEXT DEFAULT '',
    behavior_guide_md TEXT DEFAULT '',
    capability_list_md TEXT DEFAULT '',
    sub_subagent_guide_md TEXT DEFAULT '',
    active_hours_start TEXT DEFAULT '09:00',
    active_hours_end TEXT DEFAULT '22:00',
    active_hours_timezone TEXT DEFAULT 'Asia/Shanghai',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE agent_state (
    agent_id TEXT PRIMARY KEY REFERENCES agents(id) ON DELETE CASCADE,
    state TEXT DEFAULT 'awake',
    wake_triggers TEXT DEFAULT '[]',
    last_active_at TEXT DEFAULT (datetime('now')), sleep_reason TEXT, sleep_started_at TEXT,
    CHECK(state IN ('awake', 'sleep'))
);
CREATE TABLE chat_messages (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    content TEXT,
    read INTEGER DEFAULT 0,
    metadata TEXT DEFAULT '{}',
    timestamp TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
, sender TEXT DEFAULT '', attachments TEXT DEFAULT '[]', lifecycle TEXT DEFAULT 'pending', claimed_by_scope TEXT, lifecycle_updated_at INTEGER);
CREATE TABLE execution_logs (
    id INTEGER PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    subagent_id TEXT DEFAULT 'main',
    type TEXT NOT NULL,
    kind TEXT DEFAULT 'tool',
    status TEXT DEFAULT 'complete',
    event_key TEXT,
    timestamp TEXT NOT NULL,
    data TEXT DEFAULT '{}',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(agent_id, subagent_id, event_key)
);
CREATE TABLE execution_log_payloads (
    log_id INTEGER PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    input TEXT DEFAULT '{}',
    result TEXT DEFAULT '{}',
    error TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(log_id) REFERENCES execution_logs(id) ON DELETE CASCADE
);
CREATE TABLE files (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT '',
    agent_id TEXT,
    category TEXT NOT NULL DEFAULT 'chat_attachments',
    mime_type TEXT NOT NULL DEFAULT 'application/octet-stream',
    size INTEGER DEFAULT 0,
    filename TEXT,
    storage_backend TEXT NOT NULL DEFAULT 'local',
    storage_key TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE subagent_state_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subagent_id TEXT NOT NULL,
    agent_id TEXT,
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    reason TEXT,
    actor TEXT,
    scope_id TEXT,
    metadata_json TEXT,
    created_at INTEGER NOT NULL
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_agents_user_id ON agents(user_id);
CREATE INDEX idx_subagents_agent_id ON subagents(agent_id);
CREATE INDEX idx_subagents_status ON subagents(status);
CREATE INDEX idx_devices_user_id ON devices(user_id);
CREATE INDEX idx_vm_users_device_id ON vm_users(device_id);
CREATE INDEX idx_skills_user_id ON skills(user_id);
CREATE INDEX idx_agent_skills_agent_id ON agent_skills(agent_id);
CREATE INDEX idx_agent_skills_skill_id ON agent_skills(skill_id);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_provider ON api_keys(provider);
CREATE INDEX idx_api_key_models_user_id ON api_key_models(user_id);
CREATE INDEX idx_api_key_models_api_key_id ON api_key_models(api_key_id);
CREATE INDEX idx_api_key_models_model_id ON api_key_models(model_id);
CREATE INDEX idx_available_models_user_id ON available_models(user_id);
CREATE INDEX idx_available_models_model_id ON available_models(model_id);
CREATE INDEX idx_available_models_api_key_id ON available_models(api_key_id);
CREATE INDEX idx_agent_device_bindings_device_id ON agent_device_bindings(device_id);
CREATE INDEX idx_chat_messages_agent_id ON chat_messages(agent_id);
CREATE INDEX idx_chat_messages_read ON chat_messages(read);
CREATE INDEX idx_chat_messages_timestamp ON chat_messages(timestamp);
CREATE INDEX idx_execution_logs_agent_id ON execution_logs(agent_id);
CREATE INDEX idx_execution_log_payloads_agent_id ON execution_log_payloads(agent_id);
CREATE INDEX idx_files_user_id ON files(user_id);
CREATE INDEX idx_files_agent_id ON files(agent_id);
CREATE INDEX idx_chat_messages_lifecycle ON chat_messages(lifecycle);
CREATE INDEX idx_chat_messages_claimed_by_scope ON chat_messages(claimed_by_scope);
CREATE INDEX idx_subagent_state_transitions_sub ON subagent_state_transitions (subagent_id, id);
CREATE TABLE environment_events (
    event_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    event_kind TEXT NOT NULL,
    source_kind TEXT DEFAULT '',
    source_id TEXT DEFAULT '',
    sender_kind TEXT NOT NULL,
    sender_id TEXT DEFAULT '',
    channel_id TEXT NOT NULL DEFAULT 'default',
    thread_id TEXT NOT NULL DEFAULT 'default',
    idempotency_key TEXT NOT NULL,
    resource_refs TEXT DEFAULT '[]',
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    CHECK(event_kind IN ('im_message','system_event','external_event','resource_event')),
    CHECK(sender_kind IN ('user','agent','subagent','system')),
    UNIQUE(agent_id, idempotency_key)
);
CREATE INDEX idx_environment_events_agent_id ON environment_events(agent_id);
CREATE INDEX idx_environment_events_event_kind ON environment_events(event_kind);
CREATE INDEX idx_environment_events_source_kind ON environment_events(source_kind);
CREATE INDEX idx_environment_events_source_id ON environment_events(source_id);
CREATE INDEX idx_environment_events_sender_kind ON environment_events(sender_kind);
CREATE INDEX idx_environment_events_sender_id ON environment_events(sender_id);
CREATE INDEX idx_environment_events_channel_id ON environment_events(channel_id);
CREATE INDEX idx_environment_events_thread_id ON environment_events(thread_id);
CREATE INDEX idx_environment_events_idempotency_key ON environment_events(idempotency_key);
CREATE INDEX idx_environment_events_created_at ON environment_events(created_at);
CREATE TABLE environment_im_messages (
    message_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    event_id TEXT NOT NULL REFERENCES environment_events(event_id) ON DELETE CASCADE,
    sender_kind TEXT NOT NULL,
    sender_id TEXT NOT NULL,
    recipient_kind TEXT NOT NULL,
    recipient_id TEXT NOT NULL,
    channel_id TEXT NOT NULL DEFAULT 'default',
    thread_id TEXT NOT NULL DEFAULT 'default',
    content TEXT DEFAULT '{}',
    attachments TEXT DEFAULT '[]',
    resource_refs TEXT DEFAULT '[]',
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    CHECK(sender_kind IN ('user','agent','subagent','system')),
    CHECK(recipient_kind IN ('user','agent','subagent','system'))
);
CREATE INDEX idx_environment_im_messages_agent_id ON environment_im_messages(agent_id);
CREATE INDEX idx_environment_im_messages_event_id ON environment_im_messages(event_id);
CREATE INDEX idx_environment_im_messages_sender_kind ON environment_im_messages(sender_kind);
CREATE INDEX idx_environment_im_messages_sender_id ON environment_im_messages(sender_id);
CREATE INDEX idx_environment_im_messages_recipient_kind ON environment_im_messages(recipient_kind);
CREATE INDEX idx_environment_im_messages_recipient_id ON environment_im_messages(recipient_id);
CREATE INDEX idx_environment_im_messages_channel_id ON environment_im_messages(channel_id);
CREATE INDEX idx_environment_im_messages_thread_id ON environment_im_messages(thread_id);
CREATE INDEX idx_environment_im_messages_created_at ON environment_im_messages(created_at);
CREATE TABLE environment_notifications (
    notification_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    event_id TEXT NOT NULL REFERENCES environment_events(event_id) ON DELETE CASCADE,
    source_kind TEXT NOT NULL,
    source_id TEXT NOT NULL,
    recipient_kind TEXT NOT NULL,
    recipient_id TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending',
    claim_scope_id TEXT,
    idempotency_key TEXT NOT NULL,
    error TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    claimed_at TEXT DEFAULT (datetime('now')),
    processed_at TEXT DEFAULT (datetime('now')),
    failed_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')), dispatch_claim_id TEXT DEFAULT '', dispatch_claimed_at TEXT DEFAULT '', dispatch_attempts INTEGER DEFAULT 0, dispatch_error TEXT DEFAULT '',
    CHECK(state IN ('pending','claimed','processed','failed')),
    CHECK(recipient_kind IN ('user','agent','subagent','system')),
    UNIQUE(agent_id, idempotency_key)
);
CREATE INDEX idx_environment_notifications_agent_id ON environment_notifications(agent_id);
CREATE INDEX idx_environment_notifications_event_id ON environment_notifications(event_id);
CREATE INDEX idx_environment_notifications_source_kind ON environment_notifications(source_kind);
CREATE INDEX idx_environment_notifications_source_id ON environment_notifications(source_id);
CREATE INDEX idx_environment_notifications_recipient_kind ON environment_notifications(recipient_kind);
CREATE INDEX idx_environment_notifications_recipient_id ON environment_notifications(recipient_id);
CREATE INDEX idx_environment_notifications_state ON environment_notifications(state);
CREATE INDEX idx_environment_notifications_claim_scope_id ON environment_notifications(claim_scope_id);
CREATE INDEX idx_environment_notifications_idempotency_key ON environment_notifications(idempotency_key);
CREATE INDEX idx_environment_notifications_created_at ON environment_notifications(created_at);
CREATE TABLE environment_resource_refs (
    ref_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    event_id TEXT REFERENCES environment_events(event_id) ON DELETE SET NULL,
    owner TEXT NOT NULL,
    kind TEXT NOT NULL,
    locator TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_environment_resource_refs_agent_id ON environment_resource_refs(agent_id);
CREATE INDEX idx_environment_resource_refs_event_id ON environment_resource_refs(event_id);
CREATE INDEX idx_environment_resource_refs_owner ON environment_resource_refs(owner);
CREATE INDEX idx_environment_resource_refs_kind ON environment_resource_refs(kind);
CREATE INDEX idx_environment_resource_refs_created_at ON environment_resource_refs(created_at);
CREATE INDEX idx_environment_notifications_dispatch_claim_id ON environment_notifications(dispatch_claim_id);
CREATE TABLE agent_activity_participants (
    participant_key TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    participant_id TEXT NOT NULL DEFAULT '',
    view_id TEXT NOT NULL DEFAULT 'main',
    kind TEXT NOT NULL DEFAULT 'main',
    label TEXT NOT NULL DEFAULT 'Main Agent',
    status TEXT NOT NULL DEFAULT 'sleeping',
    activity_count INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    last_activity_at TEXT NOT NULL DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    CHECK(kind IN ('main','subagent')),
    UNIQUE(agent_id, view_id)
);
CREATE INDEX idx_agent_activity_participants_agent_id ON agent_activity_participants(agent_id);
CREATE INDEX idx_agent_activity_participants_participant_id ON agent_activity_participants(participant_id);
CREATE INDEX idx_agent_activity_participants_view_id ON agent_activity_participants(view_id);
CREATE INDEX idx_agent_activity_participants_kind ON agent_activity_participants(kind);
CREATE INDEX idx_agent_activity_participants_status ON agent_activity_participants(status);
CREATE INDEX idx_agent_activity_participants_last_activity_at ON agent_activity_participants(last_activity_at);
CREATE TABLE agent_activity_records (
    record_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    participant_id TEXT NOT NULL DEFAULT '',
    participant_view_id TEXT NOT NULL DEFAULT 'main',
    sort_order INTEGER DEFAULT 0,
    phase TEXT NOT NULL,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    text TEXT DEFAULT '',
    truncated INTEGER NOT NULL DEFAULT 0,
    tool TEXT DEFAULT '',
    status TEXT DEFAULT '',
    has_payload INTEGER NOT NULL DEFAULT 0,
    scope_id TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    CHECK(phase IN ('observation','reasoning','action','summary'))
);
CREATE INDEX idx_agent_activity_records_agent_id ON agent_activity_records(agent_id);
CREATE INDEX idx_agent_activity_records_participant_id ON agent_activity_records(participant_id);
CREATE INDEX idx_agent_activity_records_participant_view_id ON agent_activity_records(participant_view_id);
CREATE INDEX idx_agent_activity_records_phase ON agent_activity_records(phase);
CREATE INDEX idx_agent_activity_records_kind ON agent_activity_records(kind);
CREATE INDEX idx_agent_activity_records_scope_id ON agent_activity_records(scope_id);
CREATE INDEX idx_agent_activity_records_created_at ON agent_activity_records(created_at);
```

## Code Ownership Pointers

Local source pointers inspected for migration requirements:

- `Entangled/packages/server-python/entangled/sql/database.py`: SQLite `Database`, thread-local connections, PRAGMAs, FIFO transaction locks.
- `Entangled/packages/server-python/entangled/sql/field_def.py`: logical field kinds and SQLite storage mapping. JSON and timestamp currently store as `TEXT`; bool stores as `INTEGER`.
- `Entangled/packages/server-python/entangled/sql/entity_def.py`: dynamic table/index DDL generation from schema definitions.
- `Entangled/packages/server-python/entangled/sql/entity_store.py`: schema ensure, CRUD, list/list_stream, rowid cursor behavior, upsert behavior, JSON/bool/timestamp in/out conversion.
- `Entangled/packages/server-python/entangled/sql/persistence.py`: `entangled_sync_versions` DDL, load, and upsert callback.
- `Entangled/packages/server-python/entangled/sql/state_transitions.py`: raw append-only `subagent_state_transitions` DDL and list helpers.
- `Entangled/packages/server-python/entangled/app/factory.py`: startup order for DB, sync versions, transition schema, store, auth, sync engine, and routes.
- `Entangled/packages/server-python/entangled/app/state.py`: global DB/store initialization.
- `Entangled/packages/server-python/entangled/app/schema.py`: dynamic schema registration route calls `store.ensure_schema_unlocked` inside a global transaction.
- `Entangled/packages/server-python/entangled/app/crud.py`: CRUD and stream API route entrypoints.

## Migration-Relevant Observations

- Entangled is live and ready with 22 in-memory registered entities.
- The DB contains more tables than registered entities. Some are supporting or legacy/raw tables and must be classified before migration.
- `entangled_sync_versions` is current state, not residue. Its max version is much higher than many table row counts because scoped subscriptions and repeated changes advance versions independently.
- `subagent_state_transitions` is append-only operational history with an `INTEGER PRIMARY KEY AUTOINCREMENT` id and millisecond integer `created_at`.
- Many JSON-like fields are SQLite `TEXT` with JSON payloads. Postgres design must decide whether to preserve text wire compatibility at the adapter boundary while storing as `jsonb`.
- Timestamp-like fields are mostly SQLite `TEXT`; transition timestamps are integer milliseconds.
- Foreign key clauses are present in DDL, but the SQLite wrapper currently sets `PRAGMA foreign_keys = OFF`; Postgres FK enforcement must therefore be a deliberate compatibility decision, not an accidental stricter cutover.
- The live process uses WAL and multiple thread-local handles to the same DB file.
