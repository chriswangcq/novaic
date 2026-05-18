# Finalize Diagnostics Assertion Hardening Check

## Summary

Success. The one-go result is narrow, verified, and directly maps to the follow-up success criteria. The hardened tests now assert exact valid-close metadata, exact rejected-finalize metadata, unchanged active state on stale finalizes, and absence of false `session_finalized` events.

## Evidence

- `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py` now contains `_events_of_type` and exact event payload assertions for `session_finalized`, `session_closed`, and `session_finalize_rejected`.
- Focused compile completed successfully for `queue_service/session_repo.py`, `session_ledger.py`, `session_fsm.py`, and `tests/test_pr254_finalize_ownership.py`.
- Focused pytest completed successfully: `20 passed in 0.27s`.
- Residue search was constrained to finalize modules and the changed test file and showed diagnostics writes concentrated in `finalize_metadata` construction, explicit ledger recorders, and tests.

## Criteria Map

- Valid finalize event generation and payload: covered by exact assertions on `session_finalized`.
- Valid close metadata equality: covered by exact assertion that `session_closed.payload.metadata == expected_metadata`.
- Generation mismatch rejection: covered by active state assertions, no finalized-event assertion, and exact rejected payload assertions with stale generation `99`.
- Scope mismatch rejection: covered by active state assertions, no finalized-event assertion, and exact rejected payload assertions with `ended_scope_id == "stale-scope"`.
- Focused tests: `tests/test_pr254_finalize_ownership.py`, `tests/test_pr243_inbox_restart_cutover.py`, and `tests/test_pr233_active_inbox_dispatch.py` passed.
- Residue search: completed and did not expose another ambiguous finalize diagnostics writer in the checked boundary.

## Execution Map

- Changed one focused test file: `novaic-agent-runtime/tests/test_pr254_finalize_ownership.py`.
- No production code changes were needed for this follow-up.
- Recorded result R352.

## Stress Test

- The tests now exercise plausible failure modes where a stale generation or stale scope finalize could accidentally clear the active session or be recorded as a valid close. Both paths assert active state remains at generation `1` and no `session_finalized` event exists.

## Residual Risk

- Non-blocking: this follow-up validates the queue session finalize diagnostics binding. Cortex archive diagnostics propagation remains a separate open child under the parent finalize diagnostics problem.

## Result IDs

- R352
