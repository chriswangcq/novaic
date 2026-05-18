# P386 runtime attach active generation validation check

## Summary

Success. The targeted live attach-path generation coercion was replaced with explicit positive generation validation and focused runtime checks passed.

## Evidence

- `novaic-agent-runtime/queue_service/session_repo.py` now uses `_require_positive_generation(current_active.get("generation"), "active session attach")` in the attach path.
- Compile check for `queue_service/session_repo.py` passed.
- Focused runtime test subset passed: 26 tests.

## Criteria Map

- Runtime attach active session generation uses existing positive generation validator: satisfied.
- Focused runtime tests still pass for attach/finalize/session state behavior: satisfied by the focused 26-test subset.
- Source guard no longer reports this raw attach-path coercion: satisfied for the targeted `session_generation = int(current_active...)` pattern.

## Execution Map

- R370 records the code patch, compile check, focused tests, and residual adapter-code note for later classification.

## Stress Test

- The focused runtime test subset includes generation-checked attach tests and session finalize/FSM boundary tests that exercise the surrounding state machine behavior.

## Residual Risk

- `session_repo.py` still has generation adapter coercions in non-attach reconstruction paths; those are intentionally left for the cross-repo guard matrix classification rather than this narrow problem.

## Result IDs

- R370
