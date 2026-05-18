# P395 session ledger generation helper classification check

## Summary

Success. Session ledger generation helpers now validate current state generation explicitly and focused tests cover malformed adapter input.

## Evidence

- `session_generation` and `next_generation` use `_require_non_negative_generation`.
- Old raw `int(current.get("generation") or 0)` patterns are gone from `session_ledger.py`.
- Focused test suite passed: 24 tests.

## Criteria Map

- Ledger helpers validate DB generation without accepting bool/malformed values: satisfied.
- Missing state remains correct: unchanged code still returns `1` with active scope and `0` without active scope.
- Targeted guard clean: satisfied.

## Execution Map

- R375 records helper patch, direct malformed-state test, stale test assertion cleanup, and verification.

## Stress Test

- The added test monkeypatches `get_state` to a bool generation so the adapter validation is exercised directly despite SQLite normally returning integer rows.

## Residual Risk

- Audit/generic FSM and round/stack-depth default classifications remain in sibling problems.

## Result IDs

- R375
