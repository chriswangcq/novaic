# Gateway SQLite Boundary Classification

Snapshot time: 2026-05-22 11:08-11:15 Asia/Shanghai  
Host: `api.gradievo.com`  
Scope: P021 Gateway-only read inventory and classification. No Gateway production cutover was attempted.

## Runtime Evidence

Gateway process:

```text
pid 3473503 root python /opt/novaic/services/novaic-gateway/main_gateway.py --host 127.0.0.1 --port 19999 --data-dir /opt/novaic/data ...
```

Listener:

```text
127.0.0.1:19999 pid=3473503
```

Health:

```json
{"status":"healthy","version":"0.3.0","agent_initialized":true,"mcp_healthy":false,"tools_count":0,"vmcontrol_healthy":false}
```

## Live File Evidence

Active file:

```text
/opt/novaic/data/gateway.db|176128|root:root|644|2026-05-22 10:05:46.718525455 +0800
```

No `gateway.db-wal` or `gateway.db-shm` was present in the `stat` check.

`lsof` did not show an open holder for `gateway.db*` at the inventory moment, even though Gateway has an initialized DB path. Treat this as "not actively held at the sampled instant", not as proof that Gateway never opens it.

Archived evidence:

```text
/opt/novaic/residue-archive/sqlite-20260522T013250Z/services/novaic-gateway/development.db
```

That archived `development.db` is 0 bytes and is already residue from the earlier cleanup pass.

## Live Schema and Row Counts

| table | rows | classification |
|---|---:|---|
| users | 1 | auth state, migrate to `novaic_gateway` |
| refresh_tokens | 26 | auth/session state, migrate to `novaic_gateway` or expire before cutover |
| config | 5 | local ops config, migrate to `novaic_gateway` unless replaced by strict config |
| entangled_sync_versions | 0 | obsolete embedded Entangled residue, no migration |
| sessions | 0 | obsolete product/session residue, no migration |
| session_messages | 0 | obsolete product/session residue, no migration |
| ssh_keys | 0 | obsolete Gateway/device residue, no migration |
| vm_processes | 0 | obsolete VM lifecycle residue, no migration |
| pipeline_tasks | 0 | obsolete pre-Queue task residue, no migration |
| pc_clients | 0 | obsolete/deferred device-client residue, no migration unless future code reclaims it |
| sqlite_sequence | 0 | SQLite internal, no migration |

Trigger count was not separately present in schema output; `sqlite_master` inventory showed only tables and indexes.

Schema dump:

```sql
CREATE TABLE config (
    user_id TEXT NOT NULL DEFAULT '',
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, key)
);
CREATE TABLE entangled_sync_versions (
    state_key TEXT PRIMARY KEY,
    current_version INTEGER NOT NULL CHECK (current_version >= 0)
);
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    agent_id TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL
);
CREATE TABLE session_messages (
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
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE ssh_keys (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT '',
    name TEXT NOT NULL,
    public_key TEXT NOT NULL,
    private_key TEXT NOT NULL,
    is_default INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE vm_processes (
    agent_id TEXT PRIMARY KEY,
    pid INTEGER,
    status TEXT DEFAULT 'stopped',
    started_at TEXT,
    ports TEXT DEFAULT '{}',
    qemu_cmd TEXT,
    error_message TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);
CREATE TABLE pipeline_tasks (
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
CREATE TABLE pc_clients (
    pc_client_id TEXT PRIMARY KEY,
    user_id      TEXT NOT NULL DEFAULT 'local',
    name         TEXT DEFAULT '',
    online       INTEGER DEFAULT 0,
    first_seen   TEXT DEFAULT (datetime('now')),
    last_seen    TEXT DEFAULT (datetime('now'))
);
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    last_login_at TEXT
);
CREATE TABLE refresh_tokens (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_sessions_agent ON sessions(agent_id);
CREATE INDEX idx_sessions_updated ON sessions(updated_at);
CREATE INDEX idx_session_messages_session ON session_messages(session_id);
CREATE INDEX idx_session_messages_timestamp ON session_messages(timestamp);
CREATE INDEX idx_ssh_keys_default ON ssh_keys(is_default);
CREATE INDEX idx_ssh_keys_user ON ssh_keys(user_id);
CREATE INDEX idx_vm_processes_status ON vm_processes(status);
CREATE INDEX idx_pipeline_tasks_pending ON pipeline_tasks(status, task_type, created_at);
CREATE INDEX idx_pipeline_tasks_runtime ON pipeline_tasks(runtime_id, stage_id);
CREATE INDEX idx_pipeline_tasks_stage ON pipeline_tasks(stage_id, task_type);
CREATE INDEX idx_pipeline_tasks_heartbeat ON pipeline_tasks(status, heartbeat_at);
CREATE UNIQUE INDEX idx_pipeline_tasks_idempotency ON pipeline_tasks(idempotency_key);
CREATE INDEX idx_pc_clients_user ON pc_clients(user_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at);
```

## Code Ownership Evidence

Relevant local source:

- `novaic-gateway/main_gateway.py`: sets `ServiceConfig.GATEWAY_DB_FILE` to `<data-dir>/gateway.db`, initializes DB during lifespan, and describes Gateway as thin auth/WS/SSE/blob edge.
- `novaic-gateway/gateway/db/schema.py`: states `gateway.db` stores operations and auth tables only; active baseline creates `users`, `refresh_tokens`, and `config`; retired business/orchestration tables are dropped.
- `novaic-gateway/gateway/db/access.py`: owns global Gateway DB initialization through `common.db.Database`.
- `novaic-gateway/gateway/entity/defs.py` and `defs_users.py`: only local entity definitions are `users` and `refresh-tokens`.
- `novaic-gateway/gateway/entity/store.py`: `AuthEntityStore` handles only `users` and `refresh-tokens` in local SQLite.
- `novaic-gateway/gateway/infra/auth.py`: password/JWT auth reads `users` and writes `refresh_tokens`.
- `novaic-gateway/tests/test_pr152_gateway_boundary.py`: asserts Gateway stays a thin boundary and has no generic business entity client.

## Disposition

Gateway is a current state owner only for:

- local auth users;
- refresh tokens;
- small local config defaults.

Gateway is not a current owner for product entities, task orchestration, VM lifecycle, session messages, SSH keys, or Entangled sync versions.

Future Postgres boundary:

- Migrate `users`, `refresh_tokens`, and `config` to `novaic_gateway`.
- Do not migrate the zero-row legacy tables unless a later code audit finds live writers.
- After successful PG cutover and stabilization, clean obsolete zero-row tables by archiving the old SQLite file rather than recreating those tables in PG.

Backup expectations:

- Until Gateway cutover, `/opt/novaic/data/gateway.db` must be included in filesystem backups because it contains auth state and live refresh tokens.
- Before Gateway PG cutover, capture row counts and optionally expire or invalidate old `refresh_tokens` if token continuity is not required.
- After cutover, rely on `pg_dump`/Postgres backup for `novaic_gateway`.

## No-Cutover Statement

P021 only classified Gateway state. It did not change Gateway schema, service config, runtime mode, or data.

