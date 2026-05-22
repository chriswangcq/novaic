# P007 Success Check: LLM Factory Runtime Uses Postgres

## Summary

P007 is successful. The live LLM Factory container has been rebuilt with Postgres support, configured through a root-only DSN file, restarted healthy, verified through both `/health` and DB-backed reads, and no longer holds the old SQLite DB open. The SQLite file is retained only as documented rollback.

## Evidence

- Result `R004` records deployment, final migration, cutover, rollback notes, and verification.
- Inside the running container, `FactoryDB` reports backend `postgres` and reads `29760` logs through the app DB path.
- `lsof` shows no holder for `/opt/novaic/llm-factory/data/llm_factory.db`.
- Postgres counts match the final pre-cutover migration report: `api_keys=6`, `models=771`, `user_keys=2`, `llm_logs=29760`.
- Body logging remains disabled/effectively empty: request and response body non-empty counts are zero.
- The service is healthy and existing core services remained healthy.

## Criteria Map

- Docker image/container uses Postgres-capable code: satisfied by deployed source, rebuilt image, and inside-container backend check.
- Runtime config uses Postgres via root-readable secret handling: satisfied by `database.dsn_file=/run/secrets/postgres_dsn` and host secret file `0600`.
- Migration rerun immediately before restart: satisfied by report `sqlite-to-postgres-20260522T015309Z.json`.
- Container healthy and `/health` ok: satisfied.
- Running container no longer holds SQLite DB open: satisfied by empty `lsof`.
- Postgres row counts valid after cutover: satisfied.
- Old SQLite retained as rollback with clear non-current label: satisfied by marker file and updated classification note.
- Rollback instructions recorded: satisfied by `/opt/novaic/llm-factory/POSTGRES_CUTOVER.md`.

## Execution Map

- P007 performed the production runtime cutover only after P005 backend support and P006 data migration had succeeded.
- It did not remove the SQLite rollback file.

## Stress Test

- Plausible failure mode: container cannot resolve Postgres because the two compose stacks are on different Docker networks. Coverage: compose was updated to join `novaic-postgres_default`; preflight and live container checks verified Postgres access.
- Plausible failure mode: health endpoint passes without touching DB. Coverage: inside-container DB read and DB-backed `/v1/config/models` read both succeeded.
- Plausible failure mode: rollback file is still mistaken as current. Coverage: `lsof` is empty, file has a non-current marker, permissions were tightened, and the central SQLite classification note was updated.

## Residual Risk

- If rollback is needed, SQLite may be behind Postgres writes made after cutover. That is inherent once Postgres becomes current; rollback instructions preserve operational path but do not imply automatic reverse replication.

## Result IDs

- R004
