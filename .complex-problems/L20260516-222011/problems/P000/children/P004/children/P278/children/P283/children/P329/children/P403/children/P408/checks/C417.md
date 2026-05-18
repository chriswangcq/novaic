# Generic Queue infrastructure generation classification check

## Summary

`P408` is successful. The generic Queue infrastructure pass classified the noisy `generation` and `or 0` hits without confusing task/saga/lease FSM generations with live session-generation authority.

## Evidence

- `R391` records the targeted guard artifact and file-by-file classification.
- Focused generic FSM/task/saga/lease/suspected-dead tests passed: `40 passed in 0.34s`.
- The suspected-dead session-adjacent path is explicitly validated and covered by tests, not treated as generic noise.

## Criteria Map

- Inspect `queue_db.py`, `saga_repo.py`, `task_fsm.py`, and generic FSM hits: satisfied by `R391`.
- Distinguish generic FSM generations from session authority: satisfied by task/saga/lease/generic store classifications.
- Patch dangerous live session-adjacent defaults: no dangerous hit was found in this scope; suspected-dead path is already patched and tested.
- Add focused tests if changed: no code change; existing focused tests were rerun.
- Rerun generic Queue infrastructure guards: satisfied by `generic-queue-infra-guard.txt`.

## Execution Map

- `T397` executed as a bounded one-go classification.
- A first test command included a nonexistent test name; execution corrected the list by searching actual test files and reran the focused suite successfully.
- `R391` recorded the corrected verification.

## Stress Test

- The check specifically looked for session-adjacent danger inside `saga_repo.py` instead of classifying the whole file as generic. The suspected-dead path remains protected by explicit positive generation validation and tests.

## Residual Risk

- Non-blocking: sibling `P409` and `P410` still need to classify task handler/contract and worker counter hits.

## Result IDs

- `R391`
