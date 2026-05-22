# Gateway and Cortex SQLite Boundary Synthesis

Snapshot time: 2026-05-22 11:43 CST  
Host: `api.gradievo.com`  
Scope: P023 synthesis from P021 and P022. No service data, schema, runtime configuration, or cutover was changed.

## Source Artifacts

- P021: `.complex-problems/L20260522-091929/artifacts/gateway-sqlite-boundary.md`
- P022: `.complex-problems/L20260522-091929/artifacts/cortex-sqlite-boundary.md`
- Remote note checked: `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md`

## Gateway Disposition

Active SQLite file:

```text
/opt/novaic/data/gateway.db
```

Gateway is a current state owner only for the small edge/auth boundary:

| table | rows at P021 snapshot | disposition |
|---|---:|---|
| users | 1 | migrate to `novaic_gateway` |
| refresh_tokens | 26 | migrate to `novaic_gateway` or intentionally expire before cutover |
| config | 5 | migrate to `novaic_gateway` unless replaced by strict external config |

Gateway should not migrate the following zero-row legacy/residue tables unless a later code audit finds live writers:

- `entangled_sync_versions`
- `sessions`
- `session_messages`
- `ssh_keys`
- `vm_processes`
- `pipeline_tasks`
- `pc_clients`
- `sqlite_sequence`

Backup expectation: keep `/opt/novaic/data/gateway.db` in filesystem backups until Gateway is cut over to Postgres and stabilized. After cutover, back up `novaic_gateway` through Postgres backups and keep the old SQLite file only as rollback evidence for the agreed retention window.

## Cortex Disposition

Active SQLite file:

```text
/opt/novaic/data/cortex/operational.sqlite3
```

Cortex `operational.sqlite3` is current durable operational state, not disposable cache. Redis currently owns scope locks only; it does not replace the operational SQLite tables.

Migrate all live Cortex operational tables to `novaic_cortex` for the first Postgres cutover:

| table | rows at P022 snapshot | disposition |
|---|---:|---|
| cortex_operational_meta | 1 | recreate or migrate schema/version metadata |
| scope_events | 25 | migrate durable operational event log and idempotency source |
| scope_projection | 26 | migrate current operational projection unless a tested rebuild tool is accepted |
| active_stack_projection | 5 | migrate live runtime control projection |
| payload_manifest | 90 | migrate durable payload manifest/index |

First-cutover type policy:

- Use `jsonb` for `payload_json`, `frames_json`, and `error_json` if API output shape remains unchanged.
- Keep millisecond timestamp columns as `bigint` for the first cutover.
- Preserve `scope_events.idempotency_key` uniqueness.
- Preserve SQLite write-serialization semantics with Postgres transactions plus row locks or advisory locks where needed.

Backup expectation: keep `/opt/novaic/data/cortex/operational.sqlite3` in filesystem backups until Cortex is cut over to Postgres and stabilized. After cutover, back up `novaic_cortex` through Postgres backups while separately continuing backups for LogicalFS/Blob/workspace data.

## Central Note Status

The remote central note already marks Gateway as active auth/ops state and says to keep `gateway.db` until migration. It lacked the detailed table disposition from P021.

The remote central note described Cortex `operational.sqlite3` as `active-projection-cache`, which is weaker than the P022 classification. P022 found that the file is a current durable operational state owner and all five tables must be migrated for first cutover.

Action: append a documentation-only timestamped section to `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` with the updated Gateway/Cortex dispositions. Do not rewrite the existing table during this synthesis pass.

## No-Cutover Statement

P023 only synthesizes Gateway and Cortex SQLite classifications and updates documentation if stale. It does not change production data, service schemas, runtime configuration, or service routing.
