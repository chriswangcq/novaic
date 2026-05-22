# Normalize Task Idempotency Diagnostics Across SQLite And Postgres

## Problem

`get_idempotency_diagnostics` currently assembles public diagnostics by tuple position, which is fragile for Postgres dict-like rows and can hide ordering or field-shape drift. The diagnostics path should be backend-neutral and preserve the same public response shape while the idempotency ledger moves to Postgres. This belongs under T080 because diagnostics are the visibility surface for contention and duplicate execution behavior.

## Success Criteria

- Diagnostics row handling works for sqlite tuple rows and Postgres dict-like row wrappers.
- The public diagnostic fields remain `idempotency_key`, `status`, `owner_token`, `task_id`, `contention_count`, `last_contended_at`, `lease_until`, and `updated_at`.
- `only_contended` keeps filtering by positive contention count.
- Ordering remains by contention count descending and updated time descending for both backends.
- Limit clamping remains unchanged.
- Focused tests cover dict-like row diagnostics, tuple row diagnostics, `only_contended`, ordering SQL shape, and public field shape.
