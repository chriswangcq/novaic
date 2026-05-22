# Migrate llm-factory from SQLite to Postgres

## Problem

`llm-factory` is already Dockerized and has a small SQLite database, making it the safest first application migration to Postgres. The migration must preserve api keys, models, user keys, and logs while keeping request/response body logging disabled.

## Success Criteria

- `llm-factory` supports a Postgres DSN or adapter without permanent confusing dual paths.
- Existing SQLite data is migrated into `novaic_llm_factory` Postgres database with matching row counts.
- The service runs from Docker against Postgres and passes `/health` plus representative config/log queries.
- SQLite file is retained as rollback backup or archived with a clear non-current label.
- Rollback instructions are recorded.
