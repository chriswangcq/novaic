# P401 check: success

## Summary

R384 satisfies P401. The one-go matrix pass was checked skeptically: it found and fixed one additional live session event authority issue before recording the final matrix. After that, the narrow guard is clean, the widened guard is fully classified, and focused runtime/Cortex tests pass.

## Evidence

- Narrow guard final output contains zero lines.
- Widened guard final output contains 47 lines, all classified in R384.
- The previously unclassified suspected-dead session event generation default was removed and covered by tests.
- Focused runtime tests passed: 147 tests.
- Cortex API counter/round tests passed with the required service dependency paths: 21 tests.

## Criteria Map

- Rerun widened guard after live-boundary children: satisfied.
- Classify every remaining hit: satisfied by R384 matrix buckets.
- Patch any remaining live authority hit: satisfied by the `session_suspected_dead` generation fix.
- Provide concise matrix with evidence: satisfied in R384.
- Rerun narrow guard and focused tests: satisfied.

## Execution Map

- R384 patched `saga_repo.py` suspected-dead generation handling.
- R384 updated `test_pr245_suspected_dead_recovery.py` and `test_pr311_saga_compensation_outbox_cutover.py`.
- R384 recorded final guard files under the ledger tmp directory.

## Stress Test

- The new orphan wake-finalize failure test exercises the exact failure mode where the old code would have written a session event using generation `0`.
- The matrix intentionally keeps the widened guard broad enough to catch false positives, then classifies them rather than narrowing the regex until risk disappears.

## Residual Risk

- Non-blocking: The widened guard still prints legitimate generic counters and generic FSM generation fields. They are not live session-generation authority, and the final matrix records why they remain.

## Result IDs

- R384
