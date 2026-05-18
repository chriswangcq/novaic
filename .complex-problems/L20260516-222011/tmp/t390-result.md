# Session FSM event generation boundary result

## Summary

The session finalize decision no longer silently defaults a missing `event_generation` from the reducer payload to `0`. The result adapter now requires an explicit non-bool/non-negative event generation using the existing session generation validator.

## Done

- Replaced `event_generation=int(decision.payload.get("event_generation") or 0)` in `novaic-agent-runtime/queue_service/session_fsm.py` with `_require_non_negative_generation(..., "session finalize decision")`.
- Added `test_pure_session_fsm_requires_explicit_decision_event_generation` to prove a reducer/decision payload missing `event_generation` is rejected instead of silently defaulted.
- Preserved existing finalize accept/reject behavior for valid reducer outputs.

## Verification

- `PYTHONPATH=.:../novaic-common pytest -q tests/test_pr264_session_finalize_fsm_boundary.py` -> `5 passed in 0.03s`.
- `rg -n "event_generation=int|event_generation\\s*=\\s*int|event_generation.*or 0|get\\(\\\"event_generation\\\"\\) or 0" novaic-agent-runtime/queue_service/session_fsm.py novaic-agent-runtime/tests/test_pr264_session_finalize_fsm_boundary.py` returned no matches.

## Known Gaps

- This result only closes the session FSM `event_generation` boundary. The subagent wake `session_generation` boundary and final widened guard matrix remain separate child problems.

## Artifacts

- `novaic-agent-runtime/queue_service/session_fsm.py`
- `novaic-agent-runtime/tests/test_pr264_session_finalize_fsm_boundary.py`
