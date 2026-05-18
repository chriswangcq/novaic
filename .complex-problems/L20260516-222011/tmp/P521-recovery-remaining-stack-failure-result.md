# P521 Recovery Remaining Stack Failure Result

## Summary

Repaired the recovery remaining-stack failure by aligning the test with the production semantics: a failed `wake_finalize` saga without explicit stack evidence must preserve `remaining_stack.known == False`.

## Done

- Diagnosed the production path through `saga_repo.py` and `session_recovery.py`.
- Updated `novaic-agent-runtime/tests/test_pr233_active_inbox_dispatch.py` to expect `known: False`.
- Reran the specific failing test successfully.

## Verification

- Diagnosis artifact: `.complex-problems/L20260516-222011/tmp/p521/diagnosis.md`
- Test log: `.complex-problems/L20260516-222011/tmp/p521/recovery-remaining-stack-pytest.log`
- Command: `cd novaic-agent-runtime && python -m pytest tests/test_pr233_active_inbox_dispatch.py::test_wake_finalize_failure_records_suspected_dead_event`
- Result: `1 passed in 0.06s`

## Files Changed

- `novaic-agent-runtime/tests/test_pr233_active_inbox_dispatch.py`

## Known Gaps

- None for this failure.
