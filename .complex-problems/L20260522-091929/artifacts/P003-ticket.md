# Migrate LLM Factory SQLite State to Postgres

## Problem Definition

`llm-factory` is currently running in Docker on `api.gradievo.com` and stores state in `/opt/novaic/llm-factory/data/llm_factory.db`. It is the lowest-risk first application database migration candidate because it is already containerized and has small, well-bounded tables: `api_keys`, `models`, `user_keys`, and `llm_logs`.

The new Postgres foundation already has a dedicated `novaic_llm_factory` database and role. The service must be migrated without losing keys/models/logs and without re-enabling request/response body logging.

## Proposed Solution

1. Inspect the `novaic-llm-factory` database layer and configuration to determine whether Postgres support already exists or must be added.
2. If needed, implement a small database backend boundary that supports both SQLite rollback and Postgres runtime.
3. Create a migration/export path from the existing SQLite tables into `novaic_llm_factory` Postgres with idempotent schema creation and row-count validation.
4. Back up the SQLite DB before mutation, run the migration, and update the Docker configuration to point `llm-factory` at Postgres.
5. Restart only the `novaic-llm-factory` container, verify `/health`, verify table row counts in Postgres, verify request/response body logging remains disabled, and keep the old SQLite file clearly labeled as rollback rather than current state.

## Acceptance Criteria

- The existing SQLite `llm_factory.db` is backed up before migration.
- `llm-factory` can run against the `novaic_llm_factory` Postgres database through an explicit config/adapter path.
- Postgres contains the migrated `api_keys`, `models`, `user_keys`, and `llm_logs` data with row counts matching the pre-migration SQLite counts.
- The Docker service is restarted against Postgres and returns healthy from `http://127.0.0.1:19990/health`.
- Request and response body logging remain disabled.
- The old SQLite database remains available as a timestamped rollback artifact or is renamed/archived with a clear non-current label.
- Rollback instructions are recorded.

## Verification Plan

Capture pre-migration SQLite row counts, build or adjust the service image/config if Postgres support is missing, migrate data into Postgres, compare row counts, restart the container, verify health, inspect logs for DB errors, and confirm `llm_factory.db` is not held open by the running container after cutover. Record rollback steps and artifact paths.

## Risks

- The current app may be SQLite-specific, requiring code changes before cutover.
- Type differences between SQLite and Postgres can corrupt booleans, JSON, timestamps, or generated IDs if migrated naively.
- Restarting the factory can interrupt model-key routing if the new DB config is wrong.
- Keeping both SQLite and Postgres paths without a clear label could create confusing dual-state.

## Assumptions

- `llm-factory` is still the safest first application migration because it is containerized and has limited table count.
- The `novaic_llm_factory` Postgres role/database from P001 is available and healthy.
- Short `llm-factory` restart downtime is acceptable if rollback is immediate.
