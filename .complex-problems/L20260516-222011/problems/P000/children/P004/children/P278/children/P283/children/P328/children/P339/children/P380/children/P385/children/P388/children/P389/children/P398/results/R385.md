# Remaining generation-like guard hits closure result

## Summary

The P398 split closed the remaining suspicious generation-like guard hits. `event_generation` in the session FSM, `session_generation` in subagent wake, and the suspected-dead session event generation default were all converted to explicit validation boundaries. The final narrow guard is clean, and the remaining widened guard hits are classified as non-session-authority counters, rounds, audit adapters, or generic FSM generations.

## Done

- Closed R382/P399: session finalize `event_generation` now requires explicit non-negative generation from the reducer decision.
- Closed R383/P400: subagent wake `session_generation` now requires the shared positive session-generation contract.
- Closed R384/P401: final widened matrix classified all remaining hits and fixed the additional suspected-dead generation-0 risk.
- Added focused regression tests for each patched live boundary.

## Verification

- P399 check C405 succeeded.
- P400 check C406 succeeded.
- P401 check C407 succeeded.
- Final narrow guard has zero hits.
- Final widened guard has 47 fully classified hits.
- Focused runtime suite passed: `147 passed in 0.79s`.
- Additional focused suites passed: `46`, `62`, `55`, `41`, `22`, and `21` tests in the recorded verification runs.

## Known Gaps

- None for P398's scope. Remaining widened guard hits are intentionally retained and classified as non-session-authority.

## Artifacts

- Child results: R382, R383, R384.
- Guard outputs: `.complex-problems/L20260516-222011/tmp/p401-narrow-guard-final.txt`, `.complex-problems/L20260516-222011/tmp/p401-widened-guard-final.txt`.
- Main changed files include `session_fsm.py`, `subagent_wake.py`, `saga_repo.py`, and related focused tests.
