# Copy LLM Factory SQLite Data Into Postgres

## Problem Definition

The live `novaic-llm-factory` container still uses `/opt/novaic/llm-factory/data/llm_factory.db`. The dedicated Postgres database `novaic_llm_factory` now has backend support and schema, but production rows must be copied and validated before runtime cutover.

## Proposed Solution

Create a consistent SQLite backup snapshot, record source row counts from the snapshot, import `api_keys`, `user_keys`, `models`, and `llm_logs` into Postgres with conflict-safe upserts/inserts, then compare Postgres row counts to the snapshot counts. Keep the migration script/artifacts on the `api` host so P007 can rerun the import immediately before cutover if needed.

## Acceptance Criteria

- A timestamped SQLite backup snapshot exists before import.
- Pre-migration row counts are recorded for `api_keys`, `models`, `user_keys`, and `llm_logs`.
- Postgres receives the rows without exposing secrets in logs.
- Postgres row counts match the SQLite snapshot counts for all four tables.
- Request/response body columns remain empty or consistent with the current no-body-logging policy.
- The migration artifact can be safely rerun before cutover.

## Verification Plan

Use `sqlite3 .backup` or equivalent to snapshot the live SQLite DB, run a parameterized Python migration through psycopg using the Postgres secret file, verify row counts in both SQLite and Postgres, verify request/response body non-empty counts, and confirm the live `llm-factory` service remains healthy because runtime is not cut over in this ticket.

## Risks

- Live SQLite may receive new rows after the snapshot; P007 should rerun the migration immediately before cutover.
- Secret material in `api_keys` and `user_keys` must not be printed.
- Re-running the import must not duplicate rows or corrupt existing rows.

## Assumptions

- It is acceptable for Postgres to hold a migrated copy before the service runtime is cut over.
- The current row volume is small enough for a simple parameterized migration.
