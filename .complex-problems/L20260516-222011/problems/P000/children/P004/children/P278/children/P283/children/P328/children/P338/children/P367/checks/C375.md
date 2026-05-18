# Session Finalize Diagnostics Binding Recheck

## Summary

Success. The original diagnostics-binding audit identified weak proof, and the follow-up hardened the tests. Queue session finalize diagnostics are now verified as explicit metadata bound to scope and generation for valid finalizes, stale generation rejection, and stale scope rejection.

## Evidence

- R351 established the implementation source map: `SessionRepository.session_ended` constructs `finalize_metadata` before mutation and passes it to explicit ledger recorders.
- R352 hardened `tests/test_pr254_finalize_ownership.py` to assert exact finalized, closed, and rejected event payloads.
- Focused compile succeeded for queue session finalize modules and the changed test file.
- Focused pytest succeeded: `20 passed in 0.27s`.
- Residue search over `session_repo.py`, `session_ledger.py`, `session_fsm.py`, and the changed test file showed diagnostics writes concentrated in the explicit metadata path and tests.

## Criteria Map

- Stale generation finalize is rejected and does not close or restart the active session: covered by R352 active-state and no-finalized-event assertions.
- Stale finalize rejection payload records the stale finalize's reason/stack as rejected metadata, not as a valid close: covered by R352 exact `session_finalize_rejected` payload assertions for generation `99`.
- Valid finalize records the intended reason, generation, scope, and remaining stack: covered by R352 exact `session_finalized` payload assertions.
- Closed/restart transition metadata uses the same finalize metadata produced before mutation: covered for closed transition by R352 exact `session_closed.payload.metadata == expected_metadata`; restart metadata path remains separately covered in pending restart tests included in focused pytest.

## Execution Map

- T357 recorded the initial audit result R351 and exposed the missing proof.
- Follow-up P370/T358 recorded result R352 after hardening the tests and running verification.

## Stress Test

- The hardened tests exercise both stale generation and stale scope finalizes, the two high-risk paths where old or wrong wake completions could otherwise be mistaken for a valid current close.

## Residual Risk

- Non-blocking for P367: Cortex archive diagnostics propagation is not part of this queue session binding child and remains tracked by sibling child problems under P338.

## Result IDs

- R351
- R352
