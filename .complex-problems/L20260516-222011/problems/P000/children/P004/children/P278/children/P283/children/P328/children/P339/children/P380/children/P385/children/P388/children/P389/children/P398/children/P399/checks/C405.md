# P399 check: success

## Summary

R382 solves the scoped event-generation boundary. The previous silent `event_generation` fallback was removed, the replacement rejects missing reducer output explicitly, and the targeted source guard plus focused tests pass.

## Evidence

- Implementation now calls `_require_non_negative_generation(decision.payload.get("event_generation"), "session finalize decision")`.
- The added monkeypatch test proves a decision payload without `event_generation` raises instead of becoming `0`.
- Targeted guard found no raw `event_generation` int/default pattern in the changed file/test.
- Focused test file passed.

## Criteria Map

- Inspect path and classify: satisfied; this is session finalize decision output/event-sequencing metadata and must be explicit.
- Remove silent fallback: satisfied by replacing `int(... or 0)` with the validator.
- Focused regression test: satisfied by `test_pure_session_fsm_requires_explicit_decision_event_generation`.
- Targeted guard: satisfied, no matches.
- Result documents classification: satisfied in R382.

## Execution Map

- R382 patched `novaic-agent-runtime/queue_service/session_fsm.py`.
- R382 updated `novaic-agent-runtime/tests/test_pr264_session_finalize_fsm_boundary.py`.

## Stress Test

- The test injects an impossible/bad reducer output with no `event_generation`, which is the exact plausible failure hidden by the old default.

## Residual Risk

- Non-blocking: this only covers the event-generation child. Parent P398 still has the subagent wake and matrix children open.

## Result IDs

- R382
