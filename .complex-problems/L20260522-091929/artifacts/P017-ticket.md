# Define Queue Postgres JSONB Time Index and SQLite Assumption Map

## Problem Definition

The Queue PG migration needs cross-cutting SQL compatibility decisions before code implementation. Current SQLite code uses `json_each`, `json_extract`, `datetime(...)`, text timestamps, SQLite PRAGMAs, busy/locked string matching, partial indexes, and Python FIFO/sharded locks. If these are not translated explicitly, the PG version can pass simple tests while silently changing claim eligibility, stale recovery, outbox ordering, idempotency leases, or concurrency behavior.

## Proposed Solution

Produce a durable mapping artifact that defines:

- Postgres JSONB equivalents for every correctness-affecting SQLite JSON expression.
- Timestamp storage choice and comparison behavior for retry, heartbeat, stale cutoff, lease expiry, outbox ack/publish, and created/updated ordering.
- Required PG indexes and unique constraints based on P012 inventory and P015/P016 semantics.
- Replacement for SQLite busy/locked handling and generic SQLite retry loops.
- Classification of process-local Python locks after PG cutover.
- Explicit implementation blockers for unsafe or ambiguous assumptions.

The output is a design artifact only; runtime code changes remain later work.

## Acceptance Criteria

- JSON usage in task claim dependencies, task cancel, saga cancel, and state/context access is mapped to JSONB operators/functions and indexes where needed.
- Timestamp fields are assigned PG types and conversion/comparison rules.
- Required indexes/constraints are listed for task, saga, session, lease, outbox, and idempotency tables.
- SQLite busy handling in routes and `fsm/sqlite_store.py` is mapped to PG exception handling or removed.
- Python locks are classified as optional fairness/backpressure or removed from correctness.
- Implementation blockers are clear enough for P014 and coding tickets.

## Verification Plan

Review:

- P012 inventory index/schema evidence.
- `queue_service/queue_db.py` JSON and datetime usage.
- `queue_service/saga_repo.py` JSON and datetime usage.
- `queue_service/routes.py` SQLite busy/defer behavior.
- `queue_service/fsm/sqlite_store.py` busy retry and generic ordering behavior.
- `novaic-common/common/db/database.py` PRAGMAs and local lock wrapper.

Verify the final artifact against every P017 success criterion.

## Risks

- Choosing the wrong timestamp type can break stale recovery and retry ordering.
- Missing JSONB semantics for saga dependencies can make dependent tasks eligible too early.
- Missing partial indexes can make PG queue claim/recovery slow under production load.
- Leaving SQLite busy string matching in PG code can hide real database errors or skip useful retries.

## Assumptions

- P015 owns task/saga/lease transaction semantics.
- P016 owns session/outbox/idempotency replay semantics.
- Server runtime after cutover should be Postgres-only, with no SQLite fallback in production.

