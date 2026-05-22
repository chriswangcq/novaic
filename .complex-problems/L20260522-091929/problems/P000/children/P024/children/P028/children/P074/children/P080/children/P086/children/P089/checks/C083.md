# Idempotency Diagnostics Verified

## Summary

P089 is successful. Result `R078` normalizes idempotency diagnostics row handling so sqlite tuple rows and Postgres dict-like rows produce the same public response shape while preserving filters, ordering, and limit clamping.

## Evidence

- `get_idempotency_diagnostics` now reads fields through `_row_value` instead of tuple-only indexing.
- The public diagnostic keys are asserted exactly in focused tests.
- Dict-like Postgres rows and sqlite tuple rows are both covered.
- `only_contended` SQL still includes `COALESCE(contention_count, 0) > 0`.
- Both query forms still order by `contention_count DESC, updated_at DESC`.
- Limit clamping to `1..200` is tested.
- Verification passed with 5 focused diagnostics tests and 66 selected Queue/idempotency regression tests.

## Criteria Map

- Diagnostics row handling works for tuple and dict-like rows -> covered by sqlite tuple and Postgres dict-like row tests.
- Public fields remain unchanged -> exact key order asserted.
- `only_contended` keeps positive contention filtering -> SQL filter test covers this.
- Ordering remains by contention count then updated time descending -> SQL ordering asserted in both filtered and unfiltered forms.
- Limit clamping remains unchanged -> low and high bound tests cover `1` and `200`.
- Focused tests cover dict rows, tuple rows, filter, ordering, and public shape -> 5 focused tests passed.

## Execution Map

- T083 / R078 -> implemented row normalization, added focused diagnostics tests, and ran selected regression verification.

## Stress Test

- Failure mode: Postgres dict-like rows raise or return wrong values because diagnostics use integer indexes only. Covered by dict-like row test.
- Failure mode: public field shape drifts during refactor. Covered by exact key assertions.
- Failure mode: filter/order/limit silently changes. Covered by SQL and parameter assertions.

## Residual Risk

- Live Postgres runtime validation remains a later Queue staging problem.

## Result IDs

- R078
