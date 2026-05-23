# NovAIC SQLite state classification

Generated: 20260522T013250Z
Host: api.gradievo.com

This file records which SQLite files are current state owners and which files were cleaned as residue. It is intentionally placed beside the remaining SQLite files so empty or old DB files are not mistaken for current state owners.

| Path | Classification | Runtime evidence | Data evidence | Disposition |
|---|---|---|---|---|
| /opt/novaic/data/queue.db | archived/rollback-only non-current SQLite snapshot | Queue production now runs from `/opt/novaic/services/novaic-agent-runtime-pg` at commit `c7aa54517e84ffd6ed931c9f1f8b9c120b6343e9` with backend `postgres` and DSN file `<redacted-credential-path>`; `/health` and `/ready` passed on Postgres after active-path archive | Final freeze backup and archived active-path file are 378683392 bytes with SHA256 `07a65534bfd932694202c0a8f06df0426a1777b1bca5800d31c0f9d44df44153`; migration copied 25721 rows across 16 tables into Postgres `novaic_queue` | Active path cleaned; current state owner is Postgres `novaic_queue`. Retain rollback artifacts under `/opt/novaic/backups/queue-cutover/20260523T011125Z` through 2026-06-22 Asia/Shanghai or until an explicit cleanup ledger retires them. Restore only by stopping Queue and intentionally placing archived `queue.db` back at `/opt/novaic/data/queue.db`. |
| /opt/novaic/data/entangled.db | archived/rollback-only non-current SQLite snapshot | Entangled now runs on `127.0.0.1:19900` with `--db-backend postgres`, `--postgres-dsn-file`, and `--service-credential-file`; health/ready and production REST/WS smokes passed | Pre-cutover SQLite source and final active-path files are retained under `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z`; current state owner is Postgres `novaic_entangled` with 22 registered schemas | Active path cleaned; restore only for emergency rollback using `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/ENTANGLED_POSTGRES_CUTOVER.md`. |
| /opt/novaic/data/gateway.db | archived/rollback-only non-current SQLite snapshot | Gateway auth/config now uses Postgres database `novaic_gateway`; `/api/health` passed after cutover and `/opt/novaic/data/gateway.db` was removed from the active data path | Migrated `users=1`, `refresh credential records=26`, and `config=5`; rollback SQLite backup SHA256 `e201e7e90dc987f3bd5b5ff639369dbc2f4e4425287253e8549535baebde923f` is retained in `/opt/novaic/residue-archive/gateway-pg-cutover-20260522T041053Z` | Active path cleaned; restore only for emergency Gateway rollback using `/opt/novaic/residue-archive/gateway-pg-cutover-20260522T041053Z/GATEWAY_POSTGRES_CUTOVER.md`, with `gateway.db.removed-from-data-dir` as the intentional restore source. |
| /opt/novaic/data/cortex/operational.sqlite3 | archived/rollback-only non-current SQLite snapshot | Cortex operational store now uses Postgres database `novaic_cortex` via `--operational-store-backend postgres`; health/ready and representative scope-history read passed after cutover | Migrated `cortex_operational_meta=1`, `scope_events=25`, `scope_projection=26`, `active_stack_projection=5`, and `payload_manifest=90`; rollback SQLite backup SHA256 `da25f1d2292a2f39341d3b598c4836977467afaa8c6d9523512621c81812f0e7` is retained in `/opt/novaic/residue-archive/cortex-pg-cutover-20260522T082503Z` | Active path cleaned; restore only for emergency Cortex rollback using `/opt/novaic/residue-archive/cortex-pg-cutover-20260522T082503Z/CORTEX_POSTGRES_CUTOVER.md`, with `operational.sqlite3.removed-from-data-dir` as the intentional restore source. |
| /opt/novaic/llm-factory/data/llm_factory.db | rollback-only non-current SQLite snapshot | novaic-llm-factory now runs with database.backend=postgres and no longer holds this SQLite file open | 17649664 bytes; pre-cutover source had API credential records=6, models=771, user credential records=2, llm_logs=29760 | Retained only for rollback; current state owner is Postgres novaic_llm_factory. See /opt/novaic/llm-factory/POSTGRES_CUTOVER.md. |
| /opt/novaic/data/device.db | deleted/archived residue | Device startup/local SSH code was cleaned so this file is no longer initialized or referenced | 20480-byte archive; ssh_keys=0, vm_processes=0; actual device records are in entangled.db devices/agent_device_bindings | Removed from active path and archived at /opt/novaic/residue-archive/device-db-delete-20260522T020133Z/device.db. Restart and SSH-key route verification confirmed it is not recreated. |
| /opt/novaic/data/business.db | archive-residue | no lsof holder; no active runtime/startup reference found | 0 bytes | Moved to /opt/novaic/residue-archive/sqlite-20260522T013250Z/data/business.db. |
| /opt/novaic/services/novaic-gateway/development.db | archive-residue | untracked/ignored in gateway checkout; no active runtime/startup reference found | 0 bytes | Moved to /opt/novaic/residue-archive/sqlite-20260522T013250Z/services/novaic-gateway/development.db. |
| /opt/novaic/data/queue-db-backups/fsm-v18-20260507-135937/queue.db | retained historical backup | not opened by a process; path is under queue-db-backups | 116703232 bytes | Retain as named historical backup for now; do not treat as live DB. |

Cleanup archive: /opt/novaic/residue-archive/sqlite-20260522T013250Z


## Code reference anchors

- Entangled: `/opt/novaic/start.sh:186` launches `entangled.app.main --db-backend postgres --postgres-dsn-file <redacted-credential-path> --service-credential-file <redacted-credential-path>`; old `/opt/novaic/data/entangled.db*` files are rollback-only archive material.
- Gateway: `/opt/novaic/services/novaic-gateway/main_gateway.py:42` sets `ServiceConfig.GATEWAY_DB_FILE` to `$DATA_DIR/gateway.db`; `main_gateway.py:108` initializes gateway DB access.
- Business: `/opt/novaic/services/novaic-business/business/entity_store.py:4` says no local `gateway.db`/local-only DB; `/opt/novaic/services/novaic-business/main_subscriber.py:42` documents only logs + `entangled.db` under data dir. No `business.db` startup/reference was found.
- Device: `/opt/novaic/services/novaic-device/main_device.py:108-109` initializes `device.db`; `/opt/novaic/services/novaic-device/device/db_access.py:46` defaults to `device.db`; current durable device entities are accessed through EntityStore paths such as `device/devices.py`.
- Queue: production Queue now runs from `/opt/novaic/services/novaic-agent-runtime-pg` at commit `c7aa54517e84ffd6ed931c9f1f8b9c120b6343e9` with backend `postgres` and DSN file `<redacted-credential-path>`; legacy SQLite paths are rollback-only and must not be treated as current runtime state.
- Cortex: `/opt/novaic/start.sh:254` passes `--operational-sqlite-path $DATA_DIR/cortex/operational.sqlite3`.
- LLM Factory: `/opt/novaic/llm-factory/data/config.json:7` points to `/data/llm_factory.db`; app defaults live in `factory/config.py` and `factory/db.py`.
- Gateway `development.db`: `/opt/novaic/services/novaic-gateway/.gitignore:1` ignores `development.db`; no runtime/startup reference was found.

## 2026-05-22 11:44 Asia/Shanghai - Gateway/Cortex PG Boundary Update

Documentation-only update from ledger P023. No service data, schema, runtime configuration, or cutover was changed by this note.

### Gateway

`/opt/novaic/data/gateway.db` remains active auth/ops state until Gateway is cut over to Postgres. Current Gateway state to migrate into `novaic_gateway`: `users` (1 row), `refresh credential records` (26 rows), and `config` (5 rows). The zero-row legacy tables `entangled_sync_versions`, `sessions`, `session_messages`, `ssh_keys`, `vm_processes`, `pipeline_tasks`, `pc_clients`, and SQLite internal `sqlite_sequence` should not be migrated unless a later code audit finds live writers. Keep the SQLite file in filesystem backups until cutover and stabilization.

### Cortex

`/opt/novaic/data/cortex/operational.sqlite3` is current durable operational state, not disposable cache. Migrate all five live tables into `novaic_cortex` for the first Postgres cutover: `cortex_operational_meta` (1 row), `scope_events` (25 rows), `scope_projection` (26 rows), `active_stack_projection` (5 rows), and `payload_manifest` (90 rows). Redis currently owns scope locks only and does not replace these tables. Keep the SQLite file in filesystem backups until cutover and stabilization.

## 2026-05-22 12:12 Asia/Shanghai - Gateway Postgres Cutover

Gateway auth/config state has been migrated from `/opt/novaic/data/gateway.db` to Postgres database `novaic_gateway`. Migrated row counts: `users=1`, `refresh credential records=26`, `config=5`. Gateway now starts with `--db-backend postgres --postgres-dsn-file <redacted-credential-path>`.

`/opt/novaic/data/gateway.db` is no longer the active Gateway state owner. Treat it as rollback-only evidence until the retention window expires. Backup and rollback notes are stored at `/opt/novaic/residue-archive/gateway-pg-cutover-20260522T041053Z/`.

### Gateway active-path cleanup addendum

After confirming Gateway was healthy on Postgres and no process held `/opt/novaic/data/gateway.db`, the active-path SQLite file was moved out of `/opt/novaic/data`. The removed file is retained as rollback evidence at `/opt/novaic/residue-archive/gateway-pg-cutover-20260522T041053Z/gateway.db.removed-from-data-dir`.

## 2026-05-22 16:43 Asia/Shanghai - Cortex Postgres Cutover

Cortex operational state has been migrated from `/opt/novaic/data/cortex/operational.sqlite3` to Postgres database `novaic_cortex`. Migrated row counts: `cortex_operational_meta=1`, `scope_events=25`, `scope_projection=26`, `active_stack_projection=5`, and `payload_manifest=90`.

Cortex now starts with `--operational-store-backend postgres --operational-postgres-dsn-file <redacted-credential-path>`. `/health` and `/ready` passed after restart, and `/v1/scope/history` returned `history_backend=postgres` for a representative scope-history read.

After confirming no process held `/opt/novaic/data/cortex/operational.sqlite3`, the active-path SQLite file was moved out of `/opt/novaic/data/cortex`. The removed file is retained as rollback evidence at `/opt/novaic/residue-archive/cortex-pg-cutover-20260522T082503Z/operational.sqlite3.removed-from-data-dir`. The pre-cutover backup remains at `/opt/novaic/residue-archive/cortex-pg-cutover-20260522T082503Z/operational.sqlite3`.

## 2026-05-22 20:38 Asia/Shanghai - Entangled Postgres Cutover

Entangled entity/sync state has been migrated from `/opt/novaic/data/entangled.db` to Postgres database `novaic_entangled`. Production Entangled now runs on `127.0.0.1:19900` with `--db-backend postgres`, `--postgres-dsn-file <redacted-credential-path>`, and `--service-credential-file <redacted-credential-path>`.

Post-cutover verification passed: health/ready returned HTTP 200 with 22 registered entities, Business and Device schemas registered successfully, REST create/update/delete smoke on `models` cleaned up its test row, WebSocket schema/snapshot/delta/reconnect smoke passed, and no process held `/opt/novaic/data/entangled.db*`.

After verification, active-path SQLite files were moved out of `/opt/novaic/data` into `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z`. Rollback notes are stored at `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/ENTANGLED_POSTGRES_CUTOVER.md`. Treat Entangled SQLite files as rollback-only evidence, not current state.


## 2026-05-23 10:17 Asia/Shanghai - Queue Postgres Cutover

Queue FSM/outbox/idempotency state has been migrated from `/opt/novaic/data/queue.db` to Postgres database `novaic_queue`. The final freeze backup is stored at `/opt/novaic/backups/queue-cutover/20260523T011125Z/queue.db` and has SHA256 `07a65534bfd932694202c0a8f06df0426a1777b1bca5800d31c0f9d44df44153`. Migration copied 25721 rows across 16 Queue tables, and independent verification found no count, semantic, or consistency mismatches.

Production Queue now runs from `/opt/novaic/services/novaic-agent-runtime-pg` at commit `c7aa54517e84ffd6ed931c9f1f8b9c120b6343e9` with backend `postgres` and DSN file `<redacted-credential-path>`. Post-cutover checks passed: `/health` reports `database_backend=postgres`, `/ready` returns HTTP 200, smoke tests exercised task, saga, idempotency, session, worker lease, outbox, scheduler, subscriber, and gateway paths, and no process held `/opt/novaic/data/queue.db` after restart.

After verification, `/opt/novaic/data/queue.db`, `/opt/novaic/data/queue.db-wal`, and `/opt/novaic/data/queue.db-shm` were moved out of the active data path into `/opt/novaic/backups/queue-cutover/20260523T011125Z/archived-active-sqlite-20260523T021156Z`. Treat these SQLite files as rollback-only evidence, not current state. Rollback and retention details are recorded in `/opt/novaic/backups/queue-cutover/20260523T011125Z/QUEUE_POSTGRES_CUTOVER.md`. Retain the Queue SQLite rollback artifacts through 2026-06-22 Asia/Shanghai; retiring them later requires a separate explicit cleanup decision after Postgres stability and backup coverage are confirmed.
