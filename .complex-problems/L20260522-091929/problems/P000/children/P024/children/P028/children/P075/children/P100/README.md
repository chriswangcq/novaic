# Implement Queue SQLite To Postgres Copy Execution

## Problem

After planning exists, the migration must copy all active Queue tables from SQLite into a clean Postgres target while preserving identities and converting SQLite JSON text into native Postgres JSONB-compatible values. This must be implemented as reusable code rather than a one-off shell/manual procedure.

## Success Criteria

- Initializes or verifies the current Postgres Queue schema before copy.
- Copies every active Queue table and `config` from SQLite to Postgres in the planned order.
- Preserves primary keys, natural IDs, event/outbox integer IDs, idempotency keys, generations, and timestamps.
- Converts JSON text columns into native dict/list/scalar values for Postgres JSONB binding while leaving non-JSON fields unchanged.
- Fails safely on malformed JSON or unexpected target contents with a structured report error.
- Tests cover representative task/saga/session/lease/outbox/idempotency rows using fake Postgres execution and SQLite fixture input.
