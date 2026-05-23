# Remaining Service Postgres Cutovers Result

## Summary

Completed the service cutover work for Gateway, Cortex, Entangled, and Queue: each has a Postgres-backed production runtime path, production SQLite active paths have been moved out of `/opt/novaic/data`, row-count/semantic checks and health/smoke checks are recorded in child results, and rollback snapshots/notes exist. A final classification audit found one remaining documentation gap: the central SQLite classification table still has stale top-row classifications for Gateway and Cortex even though their live SQLite paths are gone and later addenda document their Postgres cutovers.

## Done

- P025 cut Gateway auth/config state over to Postgres `novaic_gateway`, preserving the intended `users`, `refresh_tokens`, and `config` state while excluding retired zero-row tables.
- P026 cut Cortex operational state over to Postgres `novaic_cortex`, preserving the five operational tables and runtime control-plane behavior.
- P027 cut Entangled entity/sync state over to Postgres `novaic_entangled`, preserving schema registration, sync versions, transition atomicity, row shape, REST/WS behavior, and startup persistence.
- P028 cut Queue FSM/outbox/idempotency/session/lease state over to Postgres `novaic_queue`, including implementation, staging validation, production migration, restart, smokes, active-path archive, and rollback documentation.
- Created a final read-only SQLite classification audit artifact to compare the central classification rows with live path presence.

## Verification

- Child checks `C028`, `C035`, `C074`, and `C150` are all success.
- Gateway, Cortex, Entangled, and Queue child results each record production cutover evidence, backup/rollback artifacts, health/readiness or API smoke verification, and cleanup notes.
- Final classification audit shows `/opt/novaic/data/queue.db`, `/opt/novaic/data/entangled.db`, `/opt/novaic/data/gateway.db`, and `/opt/novaic/data/cortex/operational.sqlite3` no longer exist in the live data path.
- Final classification audit shows Queue and Entangled top-level rows are rollback/non-current, and LLM Factory remains a rollback-only SQLite snapshot outside this remaining-services child problem.
- Final classification audit also shows stale active top-level rows for `/opt/novaic/data/gateway.db` and `/opt/novaic/data/cortex/operational.sqlite3`, which need a documentation follow-up before the parent problem can be considered fully closed.

## Known Gaps

- `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` still classifies `/opt/novaic/data/gateway.db` as active auth/ops state in its top table row.
- `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` still classifies `/opt/novaic/data/cortex/operational.sqlite3` as active-projection-cache in its top table row.
- These are documentation/classification residue gaps, not evidence that the live files still exist; the audit shows both live paths are absent.

## Artifacts

- Child result IDs: `R028`, `R034`, `R070`, `R134`
- Child check IDs: `C028`, `C035`, `C074`, `C150`
- Final classification audit: `.complex-problems/L20260522-091929/artifacts/final-sqlite-classification-audit.json`
- Queue final live status: `.complex-problems/L20260522-091929/artifacts/queue-final-post-cutover-status.json`
- Queue cleanup notes update: `.complex-problems/L20260522-091929/artifacts/queue-cleanup-notes-update-report.json`
