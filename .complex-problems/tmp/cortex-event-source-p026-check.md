# P026 success check

## Summary

Success. R031 closes P026: tool-step recording now has an event-first write path through `ToolStepRecorded`, preserves final payload refs and target scope ids, and leaves legacy step files classified as transitional projections rather than authoritative source.

## Evidence

- P035/C030 closed step normalization and payload-ref finalization.
- P036/C031 closed `/v1/steps/write` event emission.
- P037/C032 closed boundary audit and found no direct-only tool-result write bypass.
- Focused tests and full Cortex suite passed after the implementation.
- Static scan evidence in R030 shows `api.py:steps_write` is the only runtime caller of `Workspace.write_step`.

## Criteria Map

- `/v1/steps/write` appends `ToolStepRecorded` events: met by P036/R029 and tests.
- Event payloads preserve call id, tool name, status, observation, payload ref, and scope id: met by focused assertions, including blob-ref replacement and deepest child scope.
- Legacy step files, if still created, are projection/debug artifacts only: met by P037/R030 classification.
- Tests verify event stream content and no hidden payload file read is required for projection: met because focused tests inspect event payloads directly and projection uses event observation/payload_ref rather than reading payload files.

## Execution Map

- Parent P026 ticket T030 split into P035, P036, and P037.
- All child problems are checked successful.
- R031 consolidates child results and does not introduce unverified implementation.

## Stress Test

- Verified payload-less tool result path.
- Verified large payload externalization to blob ref before event append.
- Verified deepest active skill-scope routing.
- Verified no remaining direct-only tool-step write path by static scan.
- Full Cortex test suite: `445 passed`.

## Residual Risk

- Transitional legacy step readers and file writes remain, but they are explicitly deferred to read-cutover and cleanup phases.
- Scope lifecycle event cutover remains next in P027 and is not part of P026.

## Result IDs

- R031
