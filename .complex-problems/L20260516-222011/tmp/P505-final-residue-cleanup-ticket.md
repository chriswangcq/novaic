# Final Residue Cleanup

## Problem Definition

P504 found three high-confidence cleanup candidates in production code: an unused deprecated phase constants module, a stale deprecated polling separator comment, and an optional `remaining_stack` signature that conflicts with the required finalize contract.

## Proposed Solution

Delete the unused constants module, remove the stale client comment, and tighten `SessionRepository.session_ended` so `remaining_stack` is typed and copied as a required dictionary. Then run focused tests/guards that cover session finalize, recovery, legacy cleanup, and any import fallout from removing the constants module.

## Acceptance Criteria

- `novaic-agent-runtime/task_queue/constants.py` is removed if it has no imports or references.
- `novaic-agent-runtime/task_queue/client.py` no longer contains the stale “Deprecated Message polling removed” separator.
- `SessionRepository.session_ended` no longer presents `remaining_stack` as optional while requiring it.
- Focused runtime/session tests pass.
- A final search shows no references to the removed constants remain.

## Verification Plan

Run repository-wide reference search for the constants module before deletion, apply the minimal cleanup, rerun focused tests, and save final guard/diff artifacts under the ledger tmp directory.

## Risks

- Hidden import paths could still depend on `task_queue.constants`; the reference sweep and test run must catch this.
- Tightening the type signature must not change runtime behavior beyond making the contract clearer.

## Assumptions

- The constants module is genuinely unused because P504 found only self-references.
- P506 will rerun the broader final verification suite after P505 source cleanup.
