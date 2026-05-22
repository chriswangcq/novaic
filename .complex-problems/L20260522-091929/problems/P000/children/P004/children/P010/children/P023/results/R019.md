# T022 Result - Gateway/Cortex SQLite Boundary Synthesis

## Summary

Completed the documentation-only synthesis for Gateway and Cortex SQLite dispositions.

Created local artifact:

- `.complex-problems/L20260522-091929/artifacts/gateway-cortex-sqlite-boundaries.md`

Updated remote central note:

- `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md`

The remote update was an append-only documentation section:

- `2026-05-22 11:44 Asia/Shanghai - Gateway/Cortex PG Boundary Update`

## Classification Summary

Gateway:

- `gateway.db` remains active auth/ops state until Gateway PG cutover.
- Migrate `users`, `refresh_tokens`, and `config` to `novaic_gateway`.
- Do not migrate zero-row legacy/residue tables unless future code audit finds live writers.
- Keep `/opt/novaic/data/gateway.db` in filesystem backups until cutover and stabilization.

Cortex:

- `operational.sqlite3` is current durable operational state, not disposable cache.
- Migrate all five live operational tables to `novaic_cortex`: `cortex_operational_meta`, `scope_events`, `scope_projection`, `active_stack_projection`, and `payload_manifest`.
- Redis scope locks do not replace Cortex operational SQLite.
- Keep `/opt/novaic/data/cortex/operational.sqlite3` in filesystem backups until cutover and stabilization.

## Verification

- Local synthesis artifact exists and includes Gateway, Cortex, and no-cutover sections.
- Remote note tail shows the new timestamped section.
- Gateway health remained healthy:
  - `curl -fsS http://127.0.0.1:19999/api/health`
- Cortex readiness remained ok:
  - `curl -fsS http://127.0.0.1:19996/ready`

## No-Cutover Statement

No production service data, schema, runtime configuration, routing, or service restart was changed.
