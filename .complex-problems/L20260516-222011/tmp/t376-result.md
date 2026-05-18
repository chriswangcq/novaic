# Residual live generation coercions closure result

## Summary

The P385 split closed the originally identified runtime and Cortex live generation coercions and then followed the guard trail until the widened matrix had no unclassified live residue. Runtime attach active generation, Cortex operational store generation, session finalize/event generation, subagent wake session generation, and suspected-dead session event generation now use explicit validation boundaries.

## Done

- P386/R370: runtime attach active session generation uses positive generation validation.
- P387/R371: Cortex operational store and active stack generation writes use non-negative generation validation.
- P388/R372/R381/R385: cross-repo guard matrix was rerun, follow-ups fixed remaining generation-like live risks, and the final widened matrix is classified.
- Added focused tests for bool/missing/negative/malformed generation cases where the boundaries are directly reachable.

## Verification

- P386 check C393 succeeded.
- P387 check C394 succeeded.
- P388 final check C410 succeeded after follow-ups.
- Final narrow guard: zero hits.
- Final widened guard: 47 fully classified non-session-authority hits.
- Focused runtime and Cortex test suites passed as recorded in R381 and R385.

## Known Gaps

- None for P385's scope.

## Artifacts

- Child results: R370, R371, R372, R381, R385.
- Guard outputs: `.complex-problems/L20260516-222011/tmp/p401-narrow-guard-final.txt`, `.complex-problems/L20260516-222011/tmp/p401-widened-guard-final.txt`.
