# T003 Result: LLM Factory Migrated From SQLite to Postgres

## Summary

Completed the LLM Factory migration from SQLite to Postgres through three closed child problems:

- P005: added and verified explicit Postgres backend support.
- P006: copied SQLite data into Postgres with row-count validation.
- P007: cut over the live Docker runtime to Postgres and labeled SQLite as rollback-only.

## Done

- LLM Factory source now supports both SQLite and Postgres.
- Production data was migrated to `novaic_llm_factory` Postgres.
- Live `novaic-llm-factory` container now runs with `database.backend=postgres`.
- Old SQLite DB remains available as rollback but is no longer the current state owner.
- Production classification docs and rollback notes were updated.

## Verification

- Child checks:
  - P005 check `C002`: success.
  - P006 check `C003`: success.
  - P007 check `C004`: success.
- Live runtime verification:
  - `novaic-llm-factory` healthy.
  - app backend inside container reports `postgres`.
  - `llm_logs` count through app backend is `29760`.
  - no open holder on `/opt/novaic/llm-factory/data/llm_factory.db`.
- Final Postgres counts:
  - `api_keys=6`
  - `models=771`
  - `user_keys=2`
  - `llm_logs=29760`
  - request/response body non-empty counts are `0`.

## Known Gaps

- SQLite rollback will become stale as new Postgres writes accumulate after cutover. This is expected after Postgres becomes the current state owner.
- Broader services (`queue`, `entangled`, `gateway`, `cortex`) are not migrated by this parent ticket; they are tracked by P004/root migration planning.

## Artifacts

- LLM Factory cutover notes: `/opt/novaic/llm-factory/POSTGRES_CUTOVER.md`
- Final migration report: `/opt/novaic/llm-factory/migration-reports/sqlite-to-postgres-20260522T015309Z.json`
- SQLite rollback marker: `/opt/novaic/llm-factory/data/llm_factory.db.NON_CURRENT_POSTGRES_CUTOVER.md`
- Ledger child results: R002, R003, R004
- Ledger child checks: C002, C003, C004
