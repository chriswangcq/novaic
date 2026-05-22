# Normalize Idempotency Diagnostics Row Handling

## Problem Definition

`get_idempotency_diagnostics` builds its public response by tuple indexes. That works with sqlite rows but is brittle for Postgres dict-like rows and makes it easy to miss public field drift while the idempotency ledger moves to Postgres.

## Proposed Solution

Refactor diagnostics row assembly in `queue_service/queue_db.py` to use the shared `_row_value` helper for each public field. Keep the existing SQL shape, `only_contended` filter, ordering, and limit clamping. Add focused fake DB tests for tuple rows and dict-like rows, including SQL assertions for the positive-contention filter, ordering, and clamped limit.

## Acceptance Criteria

- Diagnostics can read sqlite tuple rows and Postgres dict-like rows.
- Public diagnostic fields stay exactly `idempotency_key`, `status`, `owner_token`, `task_id`, `contention_count`, `last_contended_at`, `lease_until`, and `updated_at`.
- `contention_count` is returned as an integer with null/falsey values normalized to zero.
- `only_contended` keeps `COALESCE(contention_count, 0) > 0`.
- Both query forms keep ordering by contention count descending and updated time descending.
- Limit clamping remains `1..200`.

## Verification Plan

Add `tests/test_queue_postgres_idempotency_diagnostics.py` with fake sqlite tuple rows and fake Postgres dict-like rows. Cover public field shape, count normalization, only-contended SQL, ordering SQL, and limit clamping. Run the new focused tests plus P087/P088 idempotency tests and selected Queue Postgres regression tests.

## Risks

- A helper refactor can accidentally change field names or ordering; tests should assert exact keys.
- Diagnostics are not lifecycle-critical, but they are useful for production contention visibility.
- P089 should not change acquisition/completion semantics.

## Assumptions

- `_row_value` from P087 is available and can be reused for diagnostics.
- The existing SQL ordering and filter semantics are correct and should be preserved.
