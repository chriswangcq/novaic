# T002 Result: SQLite State Classified and Proven Residue Archived

## Summary

Classified the SQLite state on `api.gradievo.com`, wrote a durable production note at `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md`, and archived two proven zero-byte residue files:

- `/opt/novaic/data/business.db`
- `/opt/novaic/services/novaic-gateway/development.db`

No active database was deleted. `device.db` was intentionally retained because Device startup code still initializes it even though its tables are empty and actual device entities live in Entangled.

## Done

- Enumerated SQLite files under `/opt/novaic/data`, `/opt/novaic/llm-factory/data`, and the gateway deployment directory where a zero-byte `development.db` was found.
- Captured size, mtime, table names, row counts, runtime process ownership, startup paths, and code-reference anchors.
- Classified:
  - `/opt/novaic/data/queue.db`: `defer-high-risk active-state-owner`
  - `/opt/novaic/data/entangled.db`: `active-state-owner`
  - `/opt/novaic/data/gateway.db`: `active auth/ops state`
  - `/opt/novaic/data/cortex/operational.sqlite3`: `active-projection-cache`
  - `/opt/novaic/llm-factory/data/llm_factory.db`: `migrate-candidate active-state-owner`
  - `/opt/novaic/data/device.db`: `live-empty local device auxiliary DB / cleanup candidate`
  - `/opt/novaic/data/business.db`: `archive-residue`
  - `/opt/novaic/services/novaic-gateway/development.db`: `archive-residue`
  - `/opt/novaic/data/queue-db-backups/fsm-v18-20260507-135937/queue.db`: `retained historical backup`
- Moved residue files to `/opt/novaic/residue-archive/sqlite-20260522T013250Z`.
- Wrote rollback notes in `/opt/novaic/residue-archive/sqlite-20260522T013250Z/README.md`.

## Verification

- Remaining SQLite scan no longer shows `/opt/novaic/data/business.db` or `/opt/novaic/services/novaic-gateway/development.db`.
- Archive contains:
  - `/opt/novaic/residue-archive/sqlite-20260522T013250Z/data/business.db`
  - `/opt/novaic/residue-archive/sqlite-20260522T013250Z/services/novaic-gateway/development.db`
  - `/opt/novaic/residue-archive/sqlite-20260522T013250Z/README.md`
  - `/opt/novaic/residue-archive/sqlite-20260522T013250Z/moved-files.txt`
- `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md` records all classifications and code-reference anchors.
- Health checks after cleanup passed:
  - `docker`, `novaic`, and `nginx` systemd services active.
  - `novaic-postgres` running healthy.
  - `novaic-llm-factory` running healthy.
  - Device `/health`: healthy.
  - Business `/health`: healthy.
  - Queue `/health`: healthy and still points at `/opt/novaic/data/queue.db`.
  - LLM Factory `/health`: ok.
  - `https://api.gradievo.com/health`: healthy.

## Known Gaps

- `device.db` is still present because deleting it without a code change would be unsafe/misleading: Device startup calls `init_database(..., db_file="device.db")`, and the current schema is also inconsistent with `ssh_keys.py` queries that reference `user_id`. This should become a separate code/schema cleanup or migration follow-up.
- `queue.db` is intentionally not migrated or compacted in this ticket because its FSM/outbox/lease semantics need a separate Postgres mapping.
- The historical `queue-db-backups/fsm-v18-20260507-135937/queue.db` backup was retained rather than deleted because it is a named backup with non-trivial data volume.

## Artifacts

- Production classification note: `/opt/novaic/data/SQLITE_STATE_CLASSIFICATION.md`
- Residue archive: `/opt/novaic/residue-archive/sqlite-20260522T013250Z`
- Archived business residue: `/opt/novaic/residue-archive/sqlite-20260522T013250Z/data/business.db`
- Archived gateway development residue: `/opt/novaic/residue-archive/sqlite-20260522T013250Z/services/novaic-gateway/development.db`
