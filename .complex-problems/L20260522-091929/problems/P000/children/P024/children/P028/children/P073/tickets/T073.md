# Implement Queue Postgres Schema And Database Boundary

## Problem Definition

Queue currently constructs `common.db.Database(Path(data_dir) / "queue.db")` directly and initializes a SQLite schema. To start the Queue Postgres migration, the codebase needs a queue-owned Postgres database boundary, schema initializer, and explicit runtime configuration that can be tested locally without touching production.

## Proposed Solution

Introduce Queue-specific database backend selection and a Postgres boundary in the queue service layer. Add a Postgres schema initializer for all queue tables using JSONB/timestamptz and required constraints/indexes from the design artifacts. Keep SQLite support only as the pre-cutover/local backend path while making Postgres an explicit configured backend with DSN/file input. Add tests for backend selection, schema SQL/initialization behavior, placeholder/transaction semantics, and health/readiness backend reporting.

## Acceptance Criteria

- Queue has explicit backend configuration for `sqlite` and `postgres`.
- Queue Postgres boundary can connect from DSN or DSN file without printing secrets.
- Queue Postgres schema covers every active queue table and index family.
- JSONB/timestamptz choices are represented in schema SQL.
- Postgres transaction helper supports the lock types the existing code passes, with no SQLite PRAGMA assumptions.
- Queue service health/readiness can report the selected backend/path without exposing secrets.
- Focused unit tests pass without production access.

## Verification Plan

Inspect existing `queue_service/main.py`, `queue_service/db/schema.py`, and `common.db` patterns; implement narrowly scoped schema/boundary/config tests; run queue-service focused pytest suites. Do not change production runtime in this child.

## Risks

- A premature common-db abstraction could disturb Gateway or other SQLite users; keep Queue-specific PG support scoped.
- Schema DDL may be large and easy to drift from SQLite schema; tests should assert table/index coverage.
- Repository SQL is not ported in this child, so the boundary must not pretend the whole Queue service is production-ready on Postgres.

## Assumptions

- Later child P074 will port repository SQL to Postgres.
- Later child P075 will build migration tooling.
- Production remains on SQLite until staging and cutover children close.
