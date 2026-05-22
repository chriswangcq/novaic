# NovAIC SQLite state classification

Generated: 20260522T013250Z
Host: api.gradievo.com

This file records which SQLite files are current state owners and which files were cleaned as residue. It is intentionally placed beside the remaining SQLite files so empty or old DB files are not mistaken for current state owners.

| Path | Classification | Runtime evidence | Data evidence | Disposition |
|---|---|---|---|---|
| /opt/novaic/data/queue.db | defer-high-risk active-state-owner | queue-service and workers open this file; start.sh launches queue-service with --data-dir /opt/novaic/data | 378683392 bytes; task/saga/session/worker FSM tables with thousands of rows | Keep on SQLite until FSM/outbox/lease semantics are mapped to Postgres transactions/JSONB/locking. Do not delete. |
| /opt/novaic/data/entangled.db | archived/rollback-only non-current SQLite snapshot | Entangled now runs on `127.0.0.1:19900` with `--db-backend postgres`, `--postgres-dsn-file`, and `--service-token-file`; health/ready and production REST/WS smokes passed | Pre-cutover SQLite source and final active-path files are retained under `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z`; current state owner is Postgres `novaic_entangled` with 22 registered schemas | Active path cleaned; restore only for emergency rollback using `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/ENTANGLED_POSTGRES_CUTOVER.md`. |
| /opt/novaic/data/gateway.db | active auth/ops state | Gateway starts with --data-dir /opt/novaic/data and main_gateway.py initializes gateway.db | 176128 bytes; users=1, refresh_tokens=26, config=5 | Keep until Gateway auth/ops migration. Do not delete. |
| /opt/novaic/data/cortex/operational.sqlite3 | active-projection-cache | Cortex starts with --operational-sqlite-path /opt/novaic/data/cortex/operational.sqlite3 | 135168 bytes; active_stack_projection=5, payload_manifest=90, scope_projection=26 | Keep as Cortex operational projection until Cortex migration/design says otherwise. |
| /opt/novaic/llm-factory/data/llm_factory.db | rollback-only non-current SQLite snapshot | novaic-llm-factory now runs with database.backend=postgres and no longer holds this SQLite file open | 17649664 bytes; pre-cutover source had api_keys=6, models=771, user_keys=2, llm_logs=29760 | Retained only for rollback; current state owner is Postgres novaic_llm_factory. See /opt/novaic/llm-factory/POSTGRES_CUTOVER.md. |
| /opt/novaic/data/device.db | deleted/archived residue | Device startup/local SSH code was cleaned so this file is no longer initialized or referenced | 20480-byte archive; ssh_keys=0, vm_processes=0; actual device records are in entangled.db devices/agent_device_bindings | Removed from active path and archived at /opt/novaic/residue-archive/device-db-delete-20260522T020133Z/device.db. Restart and SSH-key route verification confirmed it is not recreated. |
| /opt/novaic/data/business.db | archive-residue | no lsof holder; no active runtime/startup reference found | 0 bytes | Moved to /opt/novaic/residue-archive/sqlite-20260522T013250Z/data/business.db. |
| /opt/novaic/services/novaic-gateway/development.db | archive-residue | untracked/ignored in gateway checkout; no active runtime/startup reference found | 0 bytes | Moved to /opt/novaic/residue-archive/sqlite-20260522T013250Z/services/novaic-gateway/development.db. |
| /opt/novaic/data/queue-db-backups/fsm-v18-20260507-135937/queue.db | retained historical backup | not opened by a process; path is under queue-db-backups | 116703232 bytes | Retain as named historical backup for now; do not treat as live DB. |

Cleanup archive: /opt/novaic/residue-archive/sqlite-20260522T013250Z


## Code reference anchors

- Entangled: `/opt/novaic/start.sh:186` launches `entangled.app.main --db-backend postgres --postgres-dsn-file /opt/novaic/postgres/secrets/novaic_entangled_dsn --service-token-file /opt/novaic/postgres/secrets/entangled_production_service_token`; old `/opt/novaic/data/entangled.db*` files are rollback-only archive material.
- Gateway: `/opt/novaic/services/novaic-gateway/main_gateway.py:42` sets `ServiceConfig.GATEWAY_DB_FILE` to `$DATA_DIR/gateway.db`; `main_gateway.py:108` initializes gateway DB access.
- Business: `/opt/novaic/services/novaic-business/business/entity_store.py:4` says no local `gateway.db`/local-only DB; `/opt/novaic/services/novaic-business/main_subscriber.py:42` documents only logs + `entangled.db` under data dir. No `business.db` startup/reference was found.
- Device: `/opt/novaic/services/novaic-device/main_device.py:108-109` initializes `device.db`; `/opt/novaic/services/novaic-device/device/db_access.py:46` defaults to `device.db`; current durable device entities are accessed through EntityStore paths such as `device/devices.py`.
- Queue: `/opt/novaic/services/novaic-agent-runtime/queue_service/main.py:135` uses `$NOVAIC_DATA_DIR/queue.db`; worker assembly also derives `Path(args.data_dir) / "queue.db"`.
- Cortex: `/opt/novaic/start.sh:254` passes `--operational-sqlite-path $DATA_DIR/cortex/operational.sqlite3`.
- LLM Factory: `/opt/novaic/llm-factory/data/config.json:7` points to `/data/llm_factory.db`; app defaults live in `factory/config.py` and `factory/db.py`.
- Gateway `development.db`: `/opt/novaic/services/novaic-gateway/.gitignore:1` ignores `development.db`; no runtime/startup reference was found.

## 2026-05-22 11:44 Asia/Shanghai - Gateway/Cortex PG Boundary Update

Documentation-only update from ledger P023. No service data, schema, runtime configuration, or cutover was changed by this note.

### Gateway

`/opt/novaic/data/gateway.db` remains active auth/ops state until Gateway is cut over to Postgres. Current Gateway state to migrate into `novaic_gateway`: `users` (1 row), `refresh_tokens` (26 rows), and `config` (5 rows). The zero-row legacy tables `entangled_sync_versions`, `sessions`, `session_messages`, `ssh_keys`, `vm_processes`, `pipeline_tasks`, `pc_clients`, and SQLite internal `sqlite_sequence` should not be migrated unless a later code audit finds live writers. Keep the SQLite file in filesystem backups until cutover and stabilization.

### Cortex

`/opt/novaic/data/cortex/operational.sqlite3` is current durable operational state, not disposable cache. Migrate all five live tables into `novaic_cortex` for the first Postgres cutover: `cortex_operational_meta` (1 row), `scope_events` (25 rows), `scope_projection` (26 rows), `active_stack_projection` (5 rows), and `payload_manifest` (90 rows). Redis currently owns scope locks only and does not replace these tables. Keep the SQLite file in filesystem backups until cutover and stabilization.

## 2026-05-22 12:12 Asia/Shanghai - Gateway Postgres Cutover

Gateway auth/config state has been migrated from `/opt/novaic/data/gateway.db` to Postgres database `novaic_gateway`. Migrated row counts: `users=1`, `refresh_tokens=26`, `config=5`. Gateway now starts with `--db-backend postgres --postgres-dsn-file /opt/novaic/postgres/secrets/novaic_gateway_dsn`.

`/opt/novaic/data/gateway.db` is no longer the active Gateway state owner. Treat it as rollback-only evidence until the retention window expires. Backup and rollback notes are stored at `/opt/novaic/residue-archive/gateway-pg-cutover-20260522T041053Z/`.

### Gateway active-path cleanup addendum

After confirming Gateway was healthy on Postgres and no process held `/opt/novaic/data/gateway.db`, the active-path SQLite file was moved out of `/opt/novaic/data`. The removed file is retained as rollback evidence at `/opt/novaic/residue-archive/gateway-pg-cutover-20260522T041053Z/gateway.db.removed-from-data-dir`.

## 2026-05-22 16:43 Asia/Shanghai - Cortex Postgres Cutover

Cortex operational state has been migrated from `/opt/novaic/data/cortex/operational.sqlite3` to Postgres database `novaic_cortex`. Migrated row counts: `cortex_operational_meta=1`, `scope_events=25`, `scope_projection=26`, `active_stack_projection=5`, and `payload_manifest=90`.

Cortex now starts with `--operational-store-backend postgres --operational-postgres-dsn-file /opt/novaic/postgres/secrets/novaic_cortex_dsn`. `/health` and `/ready` passed after restart, and `/v1/scope/history` returned `history_backend=postgres` for a representative scope-history read.

After confirming no process held `/opt/novaic/data/cortex/operational.sqlite3`, the active-path SQLite file was moved out of `/opt/novaic/data/cortex`. The removed file is retained as rollback evidence at `/opt/novaic/residue-archive/cortex-pg-cutover-20260522T082503Z/operational.sqlite3.removed-from-data-dir`. The pre-cutover backup remains at `/opt/novaic/residue-archive/cortex-pg-cutover-20260522T082503Z/operational.sqlite3`.

## 2026-05-22 20:38 Asia/Shanghai - Entangled Postgres Cutover

Entangled entity/sync state has been migrated from `/opt/novaic/data/entangled.db` to Postgres database `novaic_entangled`. Production Entangled now runs on `127.0.0.1:19900` with `--db-backend postgres`, `--postgres-dsn-file /opt/novaic/postgres/secrets/novaic_entangled_dsn`, and `--service-token-file /opt/novaic/postgres/secrets/entangled_production_service_token`.

Post-cutover verification passed: health/ready returned HTTP 200 with 22 registered entities, Business and Device schemas registered successfully, REST create/update/delete smoke on `models` cleaned up its test row, WebSocket schema/snapshot/delta/reconnect smoke passed, and no process held `/opt/novaic/data/entangled.db*`.

After verification, active-path SQLite files were moved out of `/opt/novaic/data` into `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z`. Rollback notes are stored at `/opt/novaic/residue-archive/entangled-cutover-20260522T110431Z/ENTANGLED_POSTGRES_CUTOVER.md`. Treat Entangled SQLite files as rollback-only evidence, not current state.
