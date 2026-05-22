# P089: Normalize Task Idempotency Diagnostics Across SQLite And Postgres

Status: done
Parent: P086
Root: P000
Source Ticket: T080 (split)
Source Check: none
Package: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P089
Body: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P089/README.md
Ticket(s): T083

## Problem
`get_idempotency_diagnostics` currently assembles public diagnostics by tuple position, which is fragile for Postgres dict-like rows and can hide ordering or field-shape drift. The diagnostics path should be backend-neutral and preserve the same public response shape while the idempotency ledger moves to Postgres. This belongs under T080 because diagnostics are the visibility surface for contention and duplicate execution behavior.

## Success Criteria
- Diagnostics row handling works for sqlite tuple rows and Postgres dict-like row wrappers.
- The public diagnostic fields remain `idempotency_key`, `status`, `owner_token`, `task_id`, `contention_count`, `last_contended_at`, `lease_until`, and `updated_at`.
- `only_contended` keeps filtering by positive contention count.
- Ordering remains by contention count descending and updated time descending for both backends.
- Limit clamping remains unchanged.
- Focused tests cover dict-like row diagnostics, tuple row diagnostics, `only_contended`, ordering SQL shape, and public field shape.

## Subproblems
- none

## Results
- R078

## Latest Check
C083

## Bodies
- Problem: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P089/README.md
- Ticket T083: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P089/tickets/T083.md
- Result R078: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P089/results/R078.md
- Check C083: problems/P000/children/P024/children/P028/children/P074/children/P080/children/P086/children/P089/checks/C083.md

## Follow-ups
- none
