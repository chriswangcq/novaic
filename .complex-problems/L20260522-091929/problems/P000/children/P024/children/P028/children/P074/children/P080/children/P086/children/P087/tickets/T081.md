# Port Idempotency Acquisition Lease Path To Postgres

## Problem Definition

`TaskQueue.acquire_idempotency_execution` is still written as a SQLite-style read-then-write flow. It parses `lease_until` in Python and assumes result values are JSON strings. In Postgres mode this should instead make the acquisition decision under a database transaction using native timestamptz comparison and JSONB-compatible result handling.

## Proposed Solution

Add backend-aware helper paths for idempotency acquisition in `queue_service/queue_db.py`. Keep the current sqlite behavior as the sqlite branch, and implement a Postgres branch that locks the selected `tq_idempotency_ledger` row with `FOR UPDATE` before deciding. If no row exists, insert the `in_progress` row. If a row is completed, return the stored result without double-decoding native JSONB values. If another owner has an active lease, update contention metadata and return `in_progress`. If the lease is expired or the owner is renewing its own lease, update owner/task/lease metadata and return `acquired`.

Add small helper functions for result normalization and backend-specific acquisition SQL so the behavior is testable without a live Postgres server.

## Acceptance Criteria

- Postgres acquisition selects the target ledger row with `FOR UPDATE` or uses an equivalent atomic statement.
- Postgres lease-active checks compare `lease_until` to the current timestamp in SQL or a Postgres-native predicate, not by Python ISO parsing.
- Completed duplicate rows return the same public `{"action": "completed", "result": ...}` shape for native JSONB dict/list values and sqlite JSON strings.
- Active in-progress duplicate rows owned by another token return `{"action": "in_progress"}` and update `contention_count`, `last_contended_at`, and `updated_at`.
- Expired lease and same-owner renewal paths update the row to the new owner/task/lease metadata and return `{"action": "acquired"}`.
- Existing no-key behavior remains `{"action": "acquired"}`.

## Verification Plan

Add focused tests, likely in `tests/test_queue_postgres_idempotency_acquisition.py`, using a fake Postgres DB similar to the current task mutation tests. Cover no key, missing row insert, completed duplicate with native dict result, active duplicate contention update, expired lease reacquire, same-owner renewal, and sqlite compatibility for completed JSON strings. Run those tests plus selected task worker idempotency/retry tests and current queue Postgres mutation/boundary tests.

## Risks

- Fake DB tests validate SQL and behavior shape but not full concurrent execution; live contention remains a later staging validation item.
- Same-owner renewal semantics must match existing worker expectations or retries can behave differently.
- Result normalization must not hide malformed legacy sqlite values.

## Assumptions

- P073 schema already defines `tq_idempotency_ledger.result` as JSONB and `lease_until` as timestamptz in Postgres.
- Completion and release ownership semantics are handled by P088.
- Diagnostics row-shape normalization is handled by P089.
