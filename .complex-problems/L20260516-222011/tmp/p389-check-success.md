# P389 check: success after follow-up

## Summary

P389 is now solved with R381 plus follow-up result R385. The first result closed the scoped narrow session-generation defaults, and the follow-up closed the remaining unclassified widened hits, including an additional suspected-dead generation-0 risk found during the final matrix pass.

## Evidence

- R381: patched session finalize, session repo/ledger, audit/projection, and selected round/stack-depth boundaries; narrow guard was clean.
- R385: patched remaining `event_generation`, subagent wake `session_generation`, and suspected-dead session event generation; final matrix classified the remaining widened hits.
- Final narrow guard: zero hits.
- Final widened guard: 47 hits, all classified as non-session-authority counters/rounds/audit/generic FSM generations.
- Focused runtime verification: 147-test suite passed, plus child-specific suites passed.

## Criteria Map

- Audit all widened hits: satisfied by R384 matrix included in R385.
- Replace live control-plane session generation coercions: satisfied by R381/R385 patches.
- Classify audit/projection/generic counter adapters: satisfied by R384 matrix.
- Add focused regression tests: satisfied for session FSM, subagent wake, suspected-dead event, and surrounding runtime paths.
- Rerun guards and provide final clean matrix: satisfied; narrow clean and widened fully classified.

## Execution Map

- T380 split produced R381.
- P389 check C404 found remaining gaps and created P398.
- P398 produced R385 and checked successful.
- This check cites both R381 and R385.

## Stress Test

- The follow-up deliberately reran the broad guard instead of relying on the narrow regex. It caught one extra live authority issue, which was patched before success.

## Residual Risk

- Non-blocking: Generic FSM generations remain in task/saga/lease infrastructure and are explicitly outside session-generation authority.

## Result IDs

- R381
- R385
