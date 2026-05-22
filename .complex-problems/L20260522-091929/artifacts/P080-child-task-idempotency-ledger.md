# Port Task Idempotency Ledger To Postgres

## Problem

Task idempotency acquisition, completion, release, and diagnostics currently use SQLite-shaped SQL and Python timestamp parsing around `tq_idempotency_ledger`. The Postgres path must preserve in-progress leases, owner-token checks, completed-result reuse, contention counts, and duplicate behavior with native timestamptz and transaction-safe upserts. This belongs under P080 because idempotency guards external side effects and should be verified separately from task claim/mutation SQL.

## Success Criteria

- Postgres idempotency acquisition locks or atomically updates the `idempotency_key` row and preserves completed-result reuse.
- In-progress lease checks use native timestamptz comparisons instead of Python-side ISO parsing for the Postgres path.
- Completion updates require matching owner token and task id, preserving completed results as JSONB-compatible values.
- Release deletes only matching in-progress owner/task rows.
- Diagnostics return the same public shape without relying on tuple-only row access.
- Focused tests cover missing key, new acquisition, active in-progress duplicate, expired lease reacquire, completed duplicate, completion owner mismatch, release, and diagnostics ordering.
