# P522 Attach Outbox Status Failure Result

## Summary

Repaired the attach outbox status failure by making the test explicitly drain the durable outbox boundary after attach dispatch.

## Done

- Diagnosed that attach delivery is intentionally `outbox_pending` from `SessionRepository.dispatch`.
- Updated `novaic-agent-runtime/tests/test_pr237_session_outbox_observe.py` to call `repo.outbox_dispatcher.drain_pending(session_key=session_key)` after attach dispatch.
- Added an assertion that the attach drain publishes exactly one effect.
- Reran the specific failing test successfully.

## Verification

- Diagnosis artifact: `.complex-problems/L20260516-222011/tmp/p522/diagnosis.md`
- Test log: `.complex-problems/L20260516-222011/tmp/p522/attach-outbox-status-pytest.log`
- Command: `cd novaic-agent-runtime && python -m pytest tests/test_pr237_session_outbox_observe.py::test_outbox_records_start_and_published_attach_effects_after_cutover`
- Result: `1 passed in 0.05s`

## Files Changed

- `novaic-agent-runtime/tests/test_pr237_session_outbox_observe.py`

## Known Gaps

- None for this failure.
