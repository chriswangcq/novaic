# Cortex Operational SQLite Boundary Classification

Snapshot time: 2026-05-22 11:18-11:28 Asia/Shanghai  
Host: `api.gradievo.com`  
Scope: P022 Cortex-only read inventory and classification. No Cortex production cutover was attempted.

## Runtime Evidence

Cortex process:

```text
pid 3473596 root python -m novaic_cortex.main_cortex --host 127.0.0.1 --port 19996 --operational-sqlite-path /opt/novaic/data/cortex/operational.sqlite3 --redis-url redis://127.0.0.1:6379/0 ...
```

Sensitive auth flags were redacted during inventory.

Listener:

```text
127.0.0.1:19996 pid=3473596
```

Health/readiness:

```json
{"status":"ok","service":"cortex"}
{"status":"ok","checks":{"registry":"ok","blob_service":"ok","scope_locks":{"backend":"redis"}}}
```

## Live File Evidence

Active file:

```text
/opt/novaic/data/cortex/operational.sqlite3|135168|root:root|644|2026-05-19 16:12:30.828567939 +0800
```

No `operational.sqlite3-wal` or `operational.sqlite3-shm` was present in the `stat` check.

`lsof` did not show a long-lived holder for the DB at the inventory moment. This matches the local source pattern: `OperationalSqliteStore._connect()` opens a connection for each operation and closes it in `finally`.

## Live Schema and Row Counts

| table | rows | classification |
|---|---:|---|
| cortex_operational_meta | 1 | operational schema metadata, recreate or migrate |
| scope_events | 25 | durable operational event log, migrate to `novaic_cortex` |
| scope_projection | 26 | current operational projection/read model, migrate or rebuild only if a tested projector exists |
| active_stack_projection | 5 | current runtime control projection, migrate to preserve live stack state |
| payload_manifest | 90 | durable payload manifest/index, migrate to `novaic_cortex` |

No trigger rows were present in `sqlite_master`.

Index inventory:

```text
idx_scope_events_root_seq on scope_events
idx_scope_events_scope on scope_events
sqlite_autoindex_active_stack_projection_1 on active_stack_projection
sqlite_autoindex_cortex_operational_meta_1 on cortex_operational_meta
sqlite_autoindex_payload_manifest_1 on payload_manifest
sqlite_autoindex_scope_events_1 on scope_events
sqlite_autoindex_scope_events_2 on scope_events
sqlite_autoindex_scope_projection_1 on scope_projection
```

Schema dump:

```sql
CREATE TABLE cortex_operational_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
CREATE TABLE scope_events (
                    id TEXT PRIMARY KEY,
                    root_scope_id TEXT NOT NULL,
                    scope_id TEXT NOT NULL,
                    parent_scope_id TEXT,
                    event_type TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    reason TEXT,
                    payload_json TEXT NOT NULL,
                    occurred_at_ms INTEGER NOT NULL,
                    idempotency_key TEXT UNIQUE
                );
CREATE INDEX idx_scope_events_root_seq
                    ON scope_events(root_scope_id, occurred_at_ms, id);
CREATE INDEX idx_scope_events_scope
                    ON scope_events(scope_id, occurred_at_ms, id);
CREATE TABLE scope_projection (
                    root_scope_id TEXT NOT NULL,
                    scope_id TEXT NOT NULL,
                    scope_path TEXT,
                    parent_scope_id TEXT,
                    phase TEXT NOT NULL,
                    stack_depth INTEGER NOT NULL,
                    generation INTEGER NOT NULL,
                    skill_name TEXT,
                    name TEXT,
                    task TEXT,
                    opened_at_ms INTEGER,
                    closed_at_ms INTEGER,
                    close_reason TEXT,
                    updated_at_ms INTEGER NOT NULL,
                    PRIMARY KEY(root_scope_id, scope_id)
                );
CREATE TABLE active_stack_projection (
                    root_scope_id TEXT PRIMARY KEY,
                    top_scope_id TEXT,
                    frames_json TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    updated_at_ms INTEGER NOT NULL
                );
CREATE TABLE payload_manifest (
                    payload_ref TEXT PRIMARY KEY,
                    source_payload_ref TEXT,
                    root_scope_id TEXT NOT NULL,
                    scope_id TEXT,
                    step_ref TEXT,
                    blob_ref TEXT,
                    mime_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    sha256 TEXT NOT NULL,
                    status TEXT NOT NULL,
                    retention_class TEXT NOT NULL,
                    created_at_ms INTEGER NOT NULL,
                    updated_at_ms INTEGER NOT NULL,
                    error_json TEXT
                );
```

## Code Ownership Evidence

Relevant local source:

- `novaic-cortex/novaic_cortex/main_cortex.py`: requires `--operational-sqlite-path`, installs Redis scope locks, and builds the workspace registry with the operational store.
- `novaic-cortex/novaic_cortex/registry.py`: states the registry is not a production state authority; durable control-plane state lives in `OperationalSqliteStore`, while workspace files are owned by LogicalFS/Blob authority.
- `novaic-cortex/novaic_cortex/operational_store.py`: explicitly says the SQLite database is the authority for operational records; owns schema and CRUD for all five tables.
- `novaic-cortex/novaic_cortex/scope_transition_events.py`: appends/list scope transition events through `scope_events`.
- `novaic-cortex/novaic_cortex/active_stack_projection.py`: calls the active stack a runtime authority and stores active stack projection plus audit events.
- `novaic-cortex/novaic_cortex/workspace.py`: writes `scope_projection` and `payload_manifest` through the operational store.
- `novaic-cortex/novaic_cortex/api.py`: reads active stack/scope projections for runtime endpoints; readiness reports `scope_locks` backend as Redis.
- `novaic-cortex/tests/test_operational_store.py`: exercises persistence, idempotency, projection survival after reopen, and schema migration behavior.

## Disposition

Cortex `operational.sqlite3` is a current state owner, not residue.

Table disposition:

- `scope_events`: durable operational event log and idempotency source. Migrate.
- `scope_projection`: materialized read/control model. It may be derivable in theory, but there is no accepted rebuild tool in this task, and active code reads it directly. Migrate for first PG cutover.
- `active_stack_projection`: live runtime control projection. Migrate for first PG cutover.
- `payload_manifest`: durable semantic manifest for payload/blob references. Migrate.
- `cortex_operational_meta`: schema/version metadata. Recreate or migrate; preserve schema version evidence.

Future Postgres boundary:

- Move all five tables into `novaic_cortex`.
- Use `jsonb` for `payload_json`, `frames_json`, and `error_json` if the adapter preserves current API output shape.
- Keep `occurred_at_ms`, `opened_at_ms`, `closed_at_ms`, `updated_at_ms`, and `created_at_ms` as bigint milliseconds for first cutover.
- Preserve `scope_events.idempotency_key` uniqueness and semantic idempotency conflict behavior.
- Preserve `BEGIN IMMEDIATE` write-serialization semantics with Postgres transactions and either row locks or advisory locks where no row exists yet.
- Do not confuse this with all Cortex persistence. Workspace files, context event JSONL streams, and Blob/LogicalFS data remain outside this SQLite file.

Backup expectations:

- Until Cortex cutover, `/opt/novaic/data/cortex/operational.sqlite3` must be backed up because it owns live operational control-plane state.
- Before cutover, capture row counts for all five tables and full `scope_events` idempotency-key count.
- After cutover, rely on `pg_dump`/Postgres backup for `novaic_cortex`, while separately backing up LogicalFS/Blob/workspace data.

## No-Cutover Statement

P022 only classified Cortex operational SQLite state. It did not change Cortex schema, service config, runtime mode, or data.

