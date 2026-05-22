# T005 Result: LLM Factory Data Copied to Postgres and Validated

## Summary

Copied the live LLM Factory SQLite data into the dedicated `novaic_llm_factory` Postgres database using a timestamped SQLite snapshot and parameterized import script. Source and target row counts match for all four production tables.

The live `novaic-llm-factory` container still runs from SQLite; runtime cutover remains pending for P007.

## Done

- Created a reusable migration script on `api`:
  - `/opt/novaic/llm-factory/bin/migrate-sqlite-to-postgres.py`
- Created a migration venv with psycopg:
  - `/opt/novaic/llm-factory/.migration-venv`
- Used SQLite online backup to snapshot the live DB:
  - `/opt/novaic/llm-factory/backups/llm_factory-pre-postgres-20260522T014711Z.db`
- Imported data into Postgres tables:
  - `api_keys`
  - `user_keys`
  - `models`
  - `llm_logs`
- Re-ran the migration after adding `umask 077` to prove the replace/import path is repeatable.
- Pruned superseded migration-attempt snapshots/reports so only the latest authoritative snapshot/report remains.

## Verification

- Latest migration report:
  - `/opt/novaic/llm-factory/migration-reports/sqlite-to-postgres-20260522T014711Z.json`
- Source counts from SQLite snapshot:
  - `api_keys=6`
  - `models=771`
  - `user_keys=2`
  - `llm_logs=29760`
- Target counts in Postgres:
  - `api_keys=6`
  - `models=771`
  - `user_keys=2`
  - `llm_logs=29760`
- Body logging policy check:
  - source `request_body_nonempty=0`
  - source `response_body_nonempty=0`
  - target `request_body_nonempty=0`
  - target `response_body_nonempty=0`
- Backup permissions:
  - `/opt/novaic/llm-factory/backups/llm_factory-pre-postgres-20260522T014711Z.db` is `0600 root:root`.
- Live service health after migration:
  - `http://127.0.0.1:19990/health` returned `{"status":"ok","service":"llm-factory"}`.
- Live runtime still holds `/opt/novaic/llm-factory/data/llm_factory.db`, confirming no accidental cutover happened in this ticket.

## Known Gaps

- New SQLite writes after the P006 snapshot will not be in Postgres until the migration script is rerun. P007 should rerun it immediately before Docker cutover.
- The Docker runtime still points at SQLite and has not been rebuilt/restarted with the Postgres-capable source code.

## Artifacts

- Migration script: `/opt/novaic/llm-factory/bin/migrate-sqlite-to-postgres.py`
- Migration venv: `/opt/novaic/llm-factory/.migration-venv`
- SQLite rollback snapshot: `/opt/novaic/llm-factory/backups/llm_factory-pre-postgres-20260522T014711Z.db`
- Migration report: `/opt/novaic/llm-factory/migration-reports/sqlite-to-postgres-20260522T014711Z.json`
