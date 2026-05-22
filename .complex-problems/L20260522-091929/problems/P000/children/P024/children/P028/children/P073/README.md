# Implement Queue Postgres Schema And Database Boundary

## Problem

Queue currently uses a SQLite-specific `common.db.Database` boundary and schema under `queue_service/db/schema.py`. Before repositories can be ported, Queue needs an explicit Postgres database boundary and schema that preserve table ownership, primary/unique keys, JSONB/timestamptz choices, indexes, transaction behavior, and startup configuration without a production SQLite fallback.

## Success Criteria

- A Queue Postgres schema exists for all active task, saga, session, worker lease, outbox, config, and idempotency tables.
- JSON columns use the agreed JSONB behavior and timestamp columns use the agreed timestamptz behavior.
- Required primary keys, unique idempotency constraints, partial indexes, candidate indexes, and JSON expression indexes are represented.
- Queue runtime can be configured explicitly for `sqlite` or `postgres` during development/cutover, with production intended to use Postgres.
- Unit tests verify schema generation/initialization and database-boundary transaction behavior without touching production.
