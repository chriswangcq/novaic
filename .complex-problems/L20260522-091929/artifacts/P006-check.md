# P006 Success Check: LLM Factory Data Migration Snapshot Matches Postgres

## Summary

P006 is successful. The LLM Factory SQLite data was copied from a timestamped backup snapshot into Postgres, all required table counts match, body logging remains empty, and the migration is repeatable before runtime cutover.

## Evidence

- Result `R003` records the migration script, snapshot, report, counts, and health checks.
- Latest report `/opt/novaic/llm-factory/migration-reports/sqlite-to-postgres-20260522T014711Z.json` has `"ok": true`.
- Source and target counts match:
  - `api_keys=6`
  - `models=771`
  - `user_keys=2`
  - `llm_logs=29760`
- Source and target request/response body non-empty counts are both zero.
- The rollback snapshot exists with `0600 root:root`.
- The live service remained healthy and still holds the SQLite file, so runtime cutover was not accidentally performed.

## Criteria Map

- Timestamped SQLite backup before import: satisfied by `/opt/novaic/llm-factory/backups/llm_factory-pre-postgres-20260522T014711Z.db`.
- Pre-migration row counts recorded: satisfied in the JSON report.
- Rows imported into Postgres without exposing secrets: satisfied by parameterized migration and count-only logs/results.
- Postgres row counts match snapshot counts: satisfied for all four tables.
- Request/response body policy preserved: satisfied with zero non-empty bodies on both sides.
- Migration can be rerun before cutover: satisfied by rerunning the script successfully and keeping it as an artifact.

## Execution Map

- P006 copied data only. It did not rebuild/restart the Docker container and did not change the live runtime DB path.
- P007 remains responsible for rerunning the migration immediately before cutover, updating runtime config, and labeling the old SQLite file as rollback.

## Stress Test

- Plausible failure mode: live SQLite changes during copy cause inconsistent counts. Coverage: migration uses SQLite backup API to copy from a stable snapshot and compares that snapshot to Postgres.
- Plausible failure mode: failed migration leaves sensitive snapshots world-readable. Coverage: the script now sets `umask 077`; existing snapshots were tightened to `0600`.
- Plausible failure mode: rerun duplicates rows. Coverage: script truncates the target tables before importing while Postgres is not live, and a rerun produced matching counts.

## Residual Risk

- Any writes to SQLite after the latest snapshot are not yet in Postgres. This is expected and must be handled by P007 immediately before runtime cutover.

## Result IDs

- R003
