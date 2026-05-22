# Add Explicit Postgres Backend Support to LLM Factory

## Problem

`llm-factory` currently appears to use a SQLite-oriented database layer and config path. Before migrating production data, the service needs an explicit, tested Postgres backend path that can run against the `novaic_llm_factory` database without confusing dual-state.

This belongs under the LLM Factory migration split because data migration and Docker cutover cannot be safe until the application can intentionally talk to Postgres.

## Success Criteria

- The current `llm-factory` database/config implementation is inspected and documented.
- A Postgres-capable adapter/config path exists, or an existing one is confirmed with evidence.
- The Postgres schema for `api_keys`, `models`, `user_keys`, and `llm_logs` is created idempotently.
- SQLite remains available as a rollback backend until cutover is complete.
- Local or container-level smoke tests verify basic read/write operations against Postgres.
