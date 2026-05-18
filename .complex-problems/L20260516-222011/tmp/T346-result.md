# Wake finalize mutation payload propagation result

## Summary

Verified and tightened wake-finalize mutation payload propagation. A single finalize payload test now covers Cortex scope-end, session-ended, sleeping, and completed payload builders together, including required identity fields and missing/zero generation rejection.

## Done

- Updated `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`.
- Added `_build_set_sleeping_payload` and `_build_set_subagent_completed_payload` to the finalize payload contract test.
- Asserted terminal status payloads carry `scope_id`, positive `session_generation`, `agent_id`, and `subagent_id`.
- Asserted completed payload still preserves `result: None`.
- Extended missing/zero generation rejection tests to sleeping/completed payload builders as well as session-ended and Cortex scope-end.

## Verification

- `python3 -m py_compile task_queue/sagas/wake_finalize.py` passed.
- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr43_last_scope_wiring.py tests/test_pr254_finalize_ownership.py tests/test_pr311_saga_compensation_outbox_cutover.py tests/test_finalize_summary_boundary.py` passed: 30 tests.
- Aggregate focused suite passed again: 109 tests.
- Source guard over `task_queue/sagas/wake_finalize.py` found no `last_scope_id`, `last_scope_archived_at`, generation defaulting, or `ctx.get("session_generation") or 0` residue.

## Known Gaps

- None for wake-finalize mutation payload propagation.

## Artifacts

- Test file: `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`
